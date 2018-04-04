 # -*- coding: utf-8 -*-
from math import sqrt
import numpy as np

from scipy.signal import butter, filtfilt

from .quatOps import quat_conj, quat_prod, quat_multi_prod, vect_rot, quat_force_euler_angle, quat_avg
from .quatConvs import quat_to_euler, euler_to_quat


def apply_data_transformations(sdata, bf_transforms, hip_neutral_transform):
    """
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

    """

    # Number of records
    row_count = sdata.shape[0]

    # Create arrays of the transformation quaternions
    q_bftransform = make_quaternion_array(bf_transforms['Hip'], row_count)
    q_neutraltransform = make_quaternion_array(hip_neutral_transform, row_count)

    # Extract the orientation quaternions from the data
    q_sensor = sdata.loc[:, ['qW', 'qX', 'qY', 'qZ']].values.reshape(-1, 4)




    # Rotate hip sensor by 90º plus the hip neutral transform, find the body
    # frame of the hip data
    yaw_90 = make_quaternion_array([sqrt(2)/2, 0, 0, - sqrt(2)/2], row_count)    
    q_bf = quat_multi_prod(q_neutraltransform, q_sensor, q_bftransform, yaw_90)

    # insert transformed values for hip into dataframe
    sdata.loc[:, ['qW', 'qX', 'qY', 'qZ']] = q_bf

    # filter the data for drift for each subset of data with long dynamic activity (>10s)
    # and insert back into the data frame to update dynamic part with filtered data and static part
    # is left as before
    dynamic_range = detect_long_dynamic(sdata.corrupt.values[:].reshape(-1, 1))
    for i, j in zip(dynamic_range[:, 0], dynamic_range[:, 1]):
        s = i - 50
        e = j
        if s < 0:
            s = 0
            pad = i
        else:
            pad = 50
        filt_quats = drift_filter(sdata.loc[s:e, ['qW', 'qX', 'qY', 'qZ']].values.reshape(-1, 4))
        sdata.loc[i:j, ['qW', 'qX', 'qY', 'qZ']] = filt_quats[pad:, :]

    # for acceleration transformation, get the bodyframe transformed quaternions
    # this included both transformation and drift filtering
    q_bf = sdata.loc[:, ['qW', 'qX', 'qY', 'qZ']].values.reshape(-1, 4)

    # Isolate the yaw component of the instantaneous sensor orientations
    q_bf_yaw = quat_force_euler_angle(q_bf, phi=0, theta=0)

    # After filtering trasnformed quaternions, reverse transformation to get filtered raw quats
    q_sensor = quat_multi_prod(quat_conj(q_neutraltransform),
                                   q_bf, quat_conj(yaw_90),
                                   quat_conj(q_bftransform))

#     Extract the sensor-frame acceleration values and create imaginary quaternions
    acc_sensor = sdata.loc[:, ['aX', 'aY', 'aZ']].values.reshape(-1, 3)

    # Apply hip transformation
    acc_aiftransform = quat_multi_prod(
        quat_conj(q_bf_yaw),
        q_neutraltransform,
        q_sensor,
    )
    acc_aif = vect_rot(acc_sensor, quat_conj(acc_aiftransform))


    # Re-insert the updated values
    sdata.loc[:, ['aX', 'aY', 'aZ']] = acc_aif

    # subtract the effects of gravity
    sdata = apply_acceleration_normalisation(sdata)

    return sdata

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
    isnan = np.array(np.array(col_dat == static).astype(int)).reshape(-1, 1)
    
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
    range_dyn, length_dyn = _zero_runs(dyn_vs_static, 8)
    long_dynamic = np.where(length_dyn >= min_length)[0]
    long_dyn_range = range_dyn[long_dynamic, :]
    return long_dyn_range


def drift_filter(quats):
    n = len(quats)
    euls_org = quat_to_euler(quats)

    # Filtered angles
    normal_cutoff = .1 / (100/2)
    b, a = butter(3, normal_cutoff, 'low', analog=False)
    euls = filtfilt(b, a, euls_org, axis=0)

    comp_quat = quat_prod(euler_to_quat(np.hstack((np.zeros((n, 1)), euls[:, 1].reshape(-1, 1), np.zeros((n, 1))))),
                          euler_to_quat(np.hstack((euls[:, 0].reshape(-1, 1), np.zeros((n, 2))))))

    # To reverse the offset created by filtering, get the average of first few points in data
    # and substract that from compensation
    s = 50 + 50
    e = s + 50
    # get the average
    avg_quat = quat_avg(comp_quat[s:e, :])
    cutoff_angle = 10. / 180 * np.pi
    if np.mean(euls_org[0:25, 0], axis=0) < cutoff_angle and np.mean(euls_org[0:25, 1], axis=0) < cutoff_angle:
        euls_avg_quat = quat_to_euler(avg_quat)
        
        offset_correction = quat_prod(euler_to_quat(np.array([0., euls_avg_quat[0, 1], 0.]).reshape(-1, 3)),
                                      euler_to_quat(np.array([euls_avg_quat[0, 0], 0., 0.]).reshape(-1, 3)))

        # substract the offset correction from compensation
        comp_quat = quat_prod(comp_quat, quat_conj(offset_correction))

    # apply compensation to quats
    quat_filt = quat_prod(quats, quat_conj(comp_quat))

    return quat_filt

def apply_acceleration_normalisation(sdata):
    # Remove the effects of gravity
#    sdata.LaZ -= 9.80665
    sdata.aZ -= 9.80665
#    sdata.RaZ -= 9.80665
    return sdata

def make_quaternion_array(quaternion, length):
    return np.array([quaternion for _ in range(length)])

