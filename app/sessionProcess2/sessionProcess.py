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

import columnNames as cols
import runAnalytics
from decode_data import read_file
from .quatOps import quat_conj, quat_prod, quat_multi_prod, vect_rot, quat_force_euler_angle

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

    # Rotate hip sensor by 90º plus the hip neutral transform, find the body
    # frame of the hip data
    yaw_90 = make_quaternion_array([sqrt(2)/2, 0, 0, -sqrt(2)/2], row_count)    
    q_bf_hip = quat_multi_prod(q_neutraltransform_hip, q_sensor_hip, q_bftransform_hip, yaw_90)

    # Isolate the yaw component of the instantaneous sensor orientations
    q_bf_yaw_left = quat_force_euler_angle(q_bf_left, phi=0, theta=0)
    q_bf_yaw_hip = quat_force_euler_angle(q_bf_hip, phi=0, theta=0)
    q_bf_yaw_right = quat_force_euler_angle(q_bf_right, phi=0, theta=0)

    # Extract the sensor-frame acceleration values and create imaginary quaternions
    acc_sensor_left = sdata.loc[:, ['LaX', 'LaY', 'LaZ']].values.reshape(-1, 3)
    acc_sensor_hip = sdata.loc[:, ['HaX', 'HaY', 'HaZ']].values.reshape(-1, 3)
    acc_sensor_right = sdata.loc[:, ['RaX', 'RaY', 'RaZ']].values.reshape(-1, 3)
#    print('acc_sensor_left = {}'.format(acc_sensor_left[1,:] * 1000 / 9.80655))
#    print('acc_sensor_hip = {}'.format(acc_sensor_hip[1,:] * 1000 / 9.80655))
#    print('acc_sensor_right = {}'.format(acc_sensor_right[1,:] * 1000 / 9.80655))

    # Transform left sensor
    acc_aiftransform_left = quat_prod(quat_conj(q_sensor_left), q_bf_yaw_left)
#    print('acc_aiftransform_left = {}'.format(acc_aiftransform_left[1,:]))
    acc_aif_left = vect_rot(acc_sensor_left, acc_aiftransform_left)
#    print('acc_aif_left = {}'.format(acc_aif_left[1,:] * 1000 / 9.80655))

    # Apply hip transformation
    acc_aiftransform_hip = quat_multi_prod(
        quat_conj(q_bf_yaw_hip),
        q_neutraltransform_hip,
        q_sensor_hip,
    )
#    print('acc_aiftransform_hip = {}'.format(acc_aiftransform_hip[1,:]))
    acc_aif_hip = vect_rot(acc_sensor_hip, quat_conj(acc_aiftransform_hip))
#    print('acc_aif_hip = {}'.format(acc_aif_hip[1,:] * 1000 / 9.80655))

    # Transform right sensor
    acc_aiftransform_right = quat_prod(quat_conj(q_sensor_right), q_bf_yaw_right)
#    print('acc_aiftransform_right = {}'.format(acc_aiftransform_right[1,:]))
    acc_aif_right = vect_rot(acc_sensor_right, acc_aiftransform_right)
#    print('acc_aif_right = {}'.format(acc_aif_right[1,:] * 1000 / 9.80655))

    # Re-insert the updated values
    sdata.loc[:, ['LqW', 'LqX', 'LqY', 'LqZ']] = q_bf_left
    sdata.loc[:, ['HqW', 'HqX', 'HqY', 'HqZ']] = q_bf_hip
    sdata.loc[:, ['RqW', 'RqX', 'RqY', 'RqZ']] = q_bf_right
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
