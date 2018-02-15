# -*- coding: utf-8 -*-
from __future__ import print_function

import errno
import logging
import numpy as np
import pandas as pd
import os
import pickle
import sys
from collections import namedtuple
from keras.models import load_model
from math import sqrt
import boto3
from scipy.signal import butter, filtfilt

import columnNames as cols
import runAnalytics
from decode_data import read_file
from .quatOps import quat_conj, quat_prod, quat_multi_prod, vect_rot, quat_force_euler_angle, quat_avg
from .quatConvs import quat_to_euler, euler_to_quat

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.info('Loading sessionProcess')

Config = namedtuple('Config', [
    'AWS',
    'ENVIRONMENT',
    'MS_MODEL_PATH',
    'MS_MODEL',
    'MS_SCALER_PATH',
    'MS_SCALER',
])


def mkdir(path):
    """
    Create a directory, but don't fail if it already exists
    :param path:
    """
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def load_user_mass(data):
    return float(data.get('UserMass', 160)) * 0.453592


def load_grf_model(config):
    path = os.path.join(config.MS_MODEL_PATH, config.MS_MODEL)
    logger.info("Loading grf model from {}".format(path))
    return load_model(path)


def load_grf_scaler(config):
    path = os.path.join(config.MS_SCALER_PATH, config.MS_SCALER)
    logger.info("Loading grf scaler from {}".format(path))
    with open(path) as model_file:
        return pickle.load(model_file)


def make_quaternion_array(quaternion, length):
    return np.array([quaternion for i in range(length)])


def _zero_runs(col_dat, static):
    """
    Determine the start and end of each impact.
    
    Args:
        col_dat: array, algorithm indicator
        static: int, indicator for static algorithm
    Returns:
        ranges: 2d array, start and end of each static algorithm use
        length: length of 
    """

    # determine where column data is the relevant impact phase value
    isnan = np.array(np.array(col_dat==static).astype(int)).reshape(-1, 1)
    
    if isnan[0] == 1:
        t_b = 1
    else:
        t_b = 0

    # mark where column data changes to and from NaN
    absdiff = np.abs(np.ediff1d(isnan, to_begin=t_b))
    if isnan[-1] == 1:
        absdiff = np.concatenate([absdiff, [1]], 0)
    del isnan  # not used in further computations

    # determine the number of consecutive NaNs
    ranges = np.where(absdiff == 1)[0].reshape((-1, 2))
    length = ranges[:, 1] - ranges[:, 0]

    return ranges, length


def detect_long_dynamic(dyn_vs_static):
    """
    Determine if the data is corrupt because of drift or short switch from dynamic to static algorithm
    Data is said to be corrupt if
    1) There are frequent short switches from dynamic to static algorithm within
       short period of time, currently defined as 5 switches with 4 or fewer points within 5 s
    2) Too much drift has accumulated if the algorithm does not switch to static from dynamic for
       extended period of time, currently defined as no static algorithm of 30 points or more for
       more than 10 mins
    
    """
    min_length = 10 * 100
    bad_switch_len = 30
    range_static, length_static = _zero_runs(dyn_vs_static, 0)
    short_static = np.where(length_static <= bad_switch_len)[0]
    short_static_range = range_static[short_static, :]
    if len(short_static_range) > 0:
        for i, j in zip(short_static_range[:, 0], short_static_range[:, 1]):
            dyn_vs_static[i:j] = 8
    range_dyn, length_dyn= _zero_runs(dyn_vs_static, 8)
    long_dynamic = np.where(length_dyn >= min_length)[0]
    long_dyn_range = range_dyn[long_dynamic, :]
    return long_dyn_range


def drift_filter(quats):
    n = len(quats)
    euls_org = quat_to_euler(quats)

    #Filtered angles
    normal_cutoff = .1 / (100/2)
    b, a = butter(3, normal_cutoff, 'low', analog=False)
    euls = filtfilt(b, a, euls_org, axis=0)

    comp_quat = quat_prod(euler_to_quat( np.hstack((np.zeros((n, 1)), euls[:,1].reshape(-1,1), np.zeros((n, 1)) )) ),
                          euler_to_quat( np.hstack((euls[:,0].reshape(-1,1), np.zeros((n, 2)) )) ))


    # To reverse the offset created by filtering, get the average of first few points in data
    # and substract that from compensation
    s = 50 + 50
    e = s + 50
    # get the average
    avg_quat = quat_avg(comp_quat[s:e, :])
    cutoff_angle = 10. /180 * np.pi
    if np.mean(euls_org[0:25, 0], axis=0) < cutoff_angle and np.mean(euls_org[0:25, 1], axis=0) < cutoff_angle:
        euls_avg_quat = quat_to_euler(avg_quat)
        
        offset_correction = quat_prod(euler_to_quat(np.array([0., euls_avg_quat[0, 1], 0.]).reshape(-1, 3)),
                                      euler_to_quat(np.array([euls_avg_quat[0, 0], 0., 0.]).reshape(-1, 3)) )

        # substract the offset correction from compensation
        comp_quat = quat_prod(comp_quat, quat_conj(offset_correction))

    # apply compensation to quats
    quat_filt = quat_prod(quats, quat_conj(comp_quat))

    return quat_filt


def apply_data_transformations(sdata, bf_transforms, hip_neutral_transform):
    '''
    Use the body frame transforms and the hip neutral transform calculated
    during calibration to convert the data in the raw sensor frame to
    coordinate frames which are useful, namely, the adjusted inertial frame
    for acceleration and the body frame for orientation.

    Args:
        sdata - data frame
        bf_transforms - 3 (4x1) transform values (left, hip, and right)
            calculated from data of the user standing still during calibration,
            which can be used to convert practice data to the body frame
        hip_neutral_transform - (4x1) transform value which includes the yaw
            misalignment of the hip in a neutral position, as recorded from a
            user standing still during calibration, with a correction of 90
            degrees to correct for known additional offset of the hip sensor
            frame from the body frame

    Returns:
        sdata - data frame with acceleration and orientation data overwritten
        to be in the correct coordinate frames

    '''

    # Number of records
    row_count = sdata.shape[0]

    # Create arrays of the transformation quaternions
    q_bftransform_left = make_quaternion_array(bf_transforms['Left'], row_count)
    q_bftransform_hip = make_quaternion_array(bf_transforms['Hip'], row_count)
    q_bftransform_right = make_quaternion_array(bf_transforms['Right'], row_count)
    q_neutraltransform_hip = make_quaternion_array(hip_neutral_transform, row_count)

    # Extract the orientation quaternions from the data
    q_sensor_left = sdata.loc[:, ['LqW', 'LqX', 'LqY', 'LqZ']].values.reshape(-1, 4)
    q_sensor_hip = sdata.loc[:, ['HqW', 'HqX', 'HqY', 'HqZ']].values.reshape(-1, 4)
    q_sensor_right = sdata.loc[:, ['RqW', 'RqX', 'RqY', 'RqZ']].values.reshape(-1, 4)

    # Apply body frame transform to transform pitch and roll in feet
    q_bf_left = quat_prod(q_sensor_left, q_bftransform_left)
    q_bf_right = quat_prod(q_sensor_right, q_bftransform_right)

    # Rotate left foot by 180º
    yaw_180 = make_quaternion_array([0, 0, 0, 1], row_count)
    q_bf_left = quat_prod(q_bf_left, yaw_180)

    # insert transformed values for ankle sensors into dataframe
    sdata.loc[:, ['LqW', 'LqX', 'LqY', 'LqZ']] = q_bf_left
    sdata.loc[:, ['RqW', 'RqX', 'RqY', 'RqZ']] = q_bf_right

    # filter the data for drift for each subset of data with long dynamic activity (>10s)
    # and insert back into the data frame to update dynamic part with filtered data and static part
    # is left as before
    # left food
    dynamic_range_lf = detect_long_dynamic(sdata.corrupt_lf.values[:].reshape(-1, 1))
    for i, j in zip(dynamic_range_lf[:, 0], dynamic_range_lf[:, 1]):
        print('i: {}, j: {}'.format(i, j))
        s = i - 50
        e = j
        if s < 0:
            s = 0
            pad = i
        else:
            pad = 50
        lf_quat = drift_filter(sdata.loc[s:e, ['LqW', 'LqX', 'LqY', 'LqZ']].values.reshape(-1,4))
        sdata.loc[i:j, ['LqW', 'LqX', 'LqY', 'LqZ']] = lf_quat[pad:, :]

    # right foot
    dynamic_range_rf = detect_long_dynamic(sdata.corrupt_rf.values[:].reshape(-1, 1))
    for i, j in zip(dynamic_range_rf[:, 0], dynamic_range_rf[:, 1]):
        s = i - 50
        e = j
        if s < 0:
            s = 0
            pad = i
        else:
            pad = 50
        rf_quat = drift_filter(sdata.loc[s:e, ['RqW', 'RqX', 'RqY', 'RqZ']].values.reshape(-1,4))
        sdata.loc[i:j, ['RqW', 'RqX', 'RqY', 'RqZ']] = rf_quat[pad:, :]

    # Rotate hip sensor by 90º plus the hip neutral transform, find the body
    # frame of the hip data
    yaw_90 = make_quaternion_array([sqrt(2)/2, 0, 0, -sqrt(2)/2], row_count)    
    q_bf_hip = quat_multi_prod(q_neutraltransform_hip, q_sensor_hip, q_bftransform_hip, yaw_90)

    # insert transformed values for hip into dataframe
    sdata.loc[:, ['HqW', 'HqX', 'HqY', 'HqZ']] = q_bf_hip
    # repeat drift filtering for hip sensor
    dynamic_range_h = detect_long_dynamic(sdata.corrupt_h.values[:].reshape(-1, 1))
    for i, j in zip(dynamic_range_h[:, 0], dynamic_range_h[:, 1]):
        s = i - 50
        e = j
        if s < 0:
            s = 0
            pad = i
        else:
            pad = 50
        h_quat = drift_filter(sdata.loc[s:e, ['HqW', 'HqX', 'HqY', 'HqZ']].values.reshape(-1,4))
        sdata.loc[i:j, ['HqW', 'HqX', 'HqY', 'HqZ']] = h_quat[pad:, :]

    # for acceleration transformation, get the bodyframe transformed quaternions
    # this included both transformation and drift filtering
    q_bf_left = sdata.loc[:, ['LqW', 'LqX', 'LqY', 'LqZ']].values.reshape(-1, 4)
    q_bf_hip = sdata.loc[:, ['HqW', 'HqX', 'HqY', 'HqZ']].values.reshape(-1, 4)
    q_bf_right = sdata.loc[:, ['RqW', 'RqX', 'RqY', 'RqZ']].values.reshape(-1, 4)

    # Isolate the yaw component of the instantaneous sensor orientations
    q_bf_yaw_left = quat_force_euler_angle(q_bf_left, phi=0, theta=0)
    q_bf_yaw_hip = quat_force_euler_angle(q_bf_hip, phi=0, theta=0)
    q_bf_yaw_right = quat_force_euler_angle(q_bf_right, phi=0, theta=0)

    # After filtering trasnformed quaternions, reverse transformation to get filtered raw quats
    q_bf_left = quat_prod(q_bf_left, quat_conj(yaw_180))
    q_sensor_left = quat_prod(q_bf_left, quat_conj(q_bftransform_left))
    q_sensor_right = quat_prod(q_bf_right, quat_conj(q_bftransform_right))
    q_sensor_hip = quat_multi_prod(quat_conj(q_neutraltransform_hip),
                                        q_bf_hip, quat_conj(yaw_90),
                                        quat_conj(q_bftransform_hip))

    # Extract the sensor-frame acceleration values and create imaginary quaternions
    acc_sensor_left = sdata.loc[:, ['LaX', 'LaY', 'LaZ']].values.reshape(-1, 3)
    acc_sensor_hip = sdata.loc[:, ['HaX', 'HaY', 'HaZ']].values.reshape(-1, 3)
    acc_sensor_right = sdata.loc[:, ['RaX', 'RaY', 'RaZ']].values.reshape(-1, 3)

    # Transform left sensor
    acc_aiftransform_left = quat_prod(quat_conj(q_sensor_left), q_bf_yaw_left)
    acc_aif_left = vect_rot(acc_sensor_left, acc_aiftransform_left)

    # Apply hip transformation
    acc_aiftransform_hip = quat_multi_prod(
        quat_conj(q_bf_yaw_hip),
        q_neutraltransform_hip,
        q_sensor_hip,
    )
    acc_aif_hip = vect_rot(acc_sensor_hip, quat_conj(acc_aiftransform_hip))

    # Transform right sensor
    acc_aiftransform_right = quat_prod(quat_conj(q_sensor_right), q_bf_yaw_right)
    acc_aif_right = vect_rot(acc_sensor_right, acc_aiftransform_right)

    # Re-insert the updated values
    sdata.loc[:, ['LaX', 'LaY', 'LaZ']] = acc_aif_left
    sdata.loc[:, ['HaX', 'HaY', 'HaZ']] = acc_aif_hip
    sdata.loc[:, ['RaX', 'RaY', 'RaZ']] = acc_aif_right

    # subtract the effects of gravity
    sdata = apply_acceleration_normalisation(sdata)

    return sdata


def apply_acceleration_normalisation(sdata):
    # Remove the effects of gravity
    sdata.LaZ -= 9.80665
    sdata.HaZ -= 9.80665
    sdata.RaZ -= 9.80665
    return sdata

def flag_data_quality(data, filename):
    big_jump = 30
    baseline_az = np.nanmean(data.loc[0:100, ['LaZ', 'HaZ', 'RaZ']], axis=0).reshape(1, 3)
    diff = data.loc[:, ['LaZ', 'HaZ', 'RaZ']].values - baseline_az
    high_accel = (diff >= big_jump).astype(int)
    for i in range(3):
        if high_accel[0, i] == 1:
            t_b = 1
        else:
            t_b = 0
        absdiff = np.abs(np.ediff1d(high_accel[:, i], to_begin=t_b)).reshape(-1, 1)
        if high_accel[-1, i] == 1:
            absdiff = np.concatenate([absdiff, np.array([[1]])], 0)
        ranges = np.where(absdiff == 1)[0].reshape((-1, 2))
        length = ranges[:, 1] - ranges[:, 0]
        accel_error_count = len(np.where(length > 10)[0])
        if accel_error_count > 5:
            send_notification(filename, accel_error_count)
            break
 
 
def send_notification(filename, accel_error_count): 
    message = 'Possible acceleration issue with file: {} with {} instances of possible jumps'.format(filename, accel_error_count) 
    subject = 'Accel Data quality: {}'.format(filename) 
    sns_client = boto3.client('sns') 
    sns_topic = 'arn:aws:sns:{}:887689817172:data-quality-{}'.format( 
            os.environ['AWS_DEFAULT_REGION'], 
            os.environ['ENVIRONMENT'] 
        )
    print(sns_topic)
    response = sns_client.publish(TopicArn=sns_topic, 
                                  Message=message, 
                                  Subject=subject) 
 

def script_handler(working_directory, file_name, data):

    logger.info('Received sessionProcess request for {}'.format(file_name))

    try:
        config = Config(
            AWS=False,
            ENVIRONMENT=os.environ['ENVIRONMENT'],
            MS_MODEL_PATH='/net/efs/globalmodels',
            MS_MODEL=os.environ['MS_MODEL'],
            MS_SCALER_PATH='/net/efs/globalscalers',
            MS_SCALER=os.environ['MS_SCALER'],
        )
        mkdir(os.path.join(working_directory, 'sessionprocess2'))

        logger.info("STARTED PROCESSING!")

        # GRF
        # load model
        grf_fit = load_grf_model(config=config)
        sc = load_grf_scaler(config=config)

        logger.info("LOADING DATA")

        # read sensor data
        logger.info(data)
        logger.info(data.get('SensorDataFileVersion'))
        logger.info(file_name)
        if data.get('SensorDataFileVersion', '2.3') == '1.0':
            sdata = pd.read_csv(os.path.join(working_directory, 'downloadandchunk', file_name))
        else:
            sdata = read_file(os.path.join(working_directory, 'downloadandchunk', file_name), data.get('Placement'))
            if len(sdata) == 0:
                logger.warning("Sensor data is empty!", info=False)
                return "Fail!"
            logger.info("DATA LOADED!")
            #### ADD Checks for weird acceleration jumps 
            flag_data_quality(sdata, file_name)
            # Output debug CSV
            # fileobj = open(os.path.join(os.path.join(working_directory, 'sessionprocess2', file_name + '_pretransform')), 'wb')
            # sdata.to_csv(fileobj, na_rep='', columns=[
            #     'LqW', 'LqX', 'LqY', 'LqZ',
            #     'LaX', 'LaY', 'LaZ',
            #     'HqW', 'HqX', 'HqY', 'HqZ',
            #     'HaX', 'HaY', 'HaZ',
            #     'RqW', 'RqX', 'RqY', 'RqZ',
            #     'RaX', 'RaY', 'RaZ',
            # ])

            # Apply normalisation transforms
            sdata = apply_data_transformations(sdata, data['BodyFrameTransforms'], data['HipNeutralYaw'])
            # sdata = apply_acceleration_normalisation(sdata)

        # # Output debug CSV
        # fileobj = open(os.path.join(os.path.join(working_directory, 'sessionprocess2', file_name + '_posttransform')), 'wb')
        # sdata.to_csv(fileobj, na_rep='', columns=[
        #     'LqW', 'LqX', 'LqY', 'LqZ',
        #     'LaX', 'LaY', 'LaZ',
        #     'HqW', 'HqX', 'HqY', 'HqZ',
        #     'HaX', 'HaY', 'HaZ',
        #     'RqW', 'RqX', 'RqY', 'RqZ',
        #     'RaX', 'RaY', 'RaZ',
        # ])
        # s3_client = boto3.client('s3')
        # s3_client.upload_file(os.path.join(working_directory, 'sessionprocess2', file_name + '_posttransform'), 'biometrix-decode', file_name + '_transformed')
        # read user mass
        mass = load_user_mass(data)

        size = len(sdata)
        sdata['obs_index'] = np.array(range(size)).reshape(-1, 1) + 1

        # Process the data
        # and pass it as argument to run_session as
        file_version = data.get('SensorDataFileVersion', '2.3')
        hip_n_transform = data.get('HipNTransform', None)

        #### SAVE DEBUG DATA
        import save_file
        save_file.save_file(sdata, file_name)
 
        output_data_batch = runAnalytics.run_session(sdata, file_version, mass, grf_fit, sc, hip_n_transform)

        # Prepare data for dumping
        output_data_batch = output_data_batch.replace('None', '')
        output_data_batch = output_data_batch.round(5)

        # Output data
        fileobj = open(os.path.join(os.path.join(working_directory, 'sessionprocess2', file_name)), 'wb')
        output_data_batch.to_csv(fileobj, index=False, na_rep='', columns=cols.column_session2_out)
        del output_data_batch

        logger.info('Outcome: Success!')
        return 'Success'

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise
