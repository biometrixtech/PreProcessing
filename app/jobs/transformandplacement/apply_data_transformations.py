# -*- coding: utf-8 -*-

from math import sqrt
from scipy.signal import butter, filtfilt
import numpy as np

from utils.quaternion_operations import quat_conj, quat_prod, quat_multi_prod, vect_rot, quat_avg
from utils.quaternion_conversions import quat_to_euler, euler_to_quat, quat_force_euler_angle


def make_quaternion_array(quaternion, length):
    return np.array([quaternion for _ in range(length)])


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
    euls_org = quat_to_euler(
        quats[:, 0],
        quats[:, 1],
        quats[:, 2],
        quats[:, 3],
    )

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
        euls_avg_quat = quat_to_euler(
            avg_quat[:, 0],
            avg_quat[:, 1],
            avg_quat[:, 2],
            avg_quat[:, 3],
        )

        offset_correction = quat_prod(euler_to_quat(np.array([0., euls_avg_quat[0, 1], 0.]).reshape(-1, 3)),
                                      euler_to_quat(np.array([euls_avg_quat[0, 0], 0., 0.]).reshape(-1, 3)))

        # substract the offset correction from compensation
        comp_quat = quat_prod(comp_quat, quat_conj(offset_correction))

    # apply compensation to quats
    quat_filt = quat_prod(quats, quat_conj(comp_quat))

    return quat_filt


def apply_data_transformations(sdata, bf_transforms, hip_neutral_transform, sensor_position):
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
    q_bftransform_left = make_quaternion_array(bf_transforms['left'], row_count)
    q_bftransform_hip = make_quaternion_array(bf_transforms['hip'], row_count)
    q_bftransform_right = make_quaternion_array(bf_transforms['right'], row_count)
    q_neutraltransform_hip = make_quaternion_array(hip_neutral_transform, row_count)

    # Extract the orientation quaternions from the data
    q_sensor_left = sdata.loc[:, ['quat_lf_w', 'quat_lf_x', 'quat_lf_y', 'quat_lf_z']].values.reshape(-1, 4)
    q_sensor_hip = sdata.loc[:, ['quat_hip_w', 'quat_hip_x', 'quat_hip_y', 'quat_hip_z']].values.reshape(-1, 4)
    q_sensor_right = sdata.loc[:, ['quat_rf_w', 'quat_rf_x', 'quat_rf_y', 'quat_rf_z']].values.reshape(-1, 4)

    # Apply body frame transform to transform pitch and roll in feet
    q_bf_left = quat_prod(q_sensor_left, q_bftransform_left)
    q_bf_right = quat_prod(q_sensor_right, q_bftransform_right)

    # Rotate right and left foot by relevant angles based on their position on foot
    q_bf_left = apply_position_based_fixes(q_bf_left, sensor_position['left'], 'left')
    q_bf_right = apply_position_based_fixes(q_bf_right, sensor_position['right'], 'right')

    # insert transformed values for ankle sensors into dataframe
    sdata.loc[:, ['quat_lf_w', 'quat_lf_x', 'quat_lf_y', 'quat_lf_z']] = q_bf_left
    sdata.loc[:, ['quat_rf_w', 'quat_rf_x', 'quat_rf_y', 'quat_rf_z']] = q_bf_right

    # filter the data for drift for each subset of data with long dynamic activity (>10s)
    # and insert back into the data frame to update dynamic part with filtered data and static part
    # is left as before
    # left foot
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
        lf_quat = drift_filter(sdata.ix[s:e, ['quat_lf_w', 'quat_lf_x', 'quat_lf_y', 'quat_lf_z']].values.reshape(-1, 4))
        sdata.loc[i:j, ['quat_lf_w', 'quat_lf_x', 'quat_lf_y', 'quat_lf_z']] = lf_quat[pad:, :]

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
        rf_quat = drift_filter(sdata.ix[s:e, ['quat_rf_w', 'quat_rf_x', 'quat_rf_y', 'quat_rf_z']].values.reshape(-1, 4))
        sdata.loc[i:j, ['quat_rf_w', 'quat_rf_x', 'quat_rf_y', 'quat_rf_z']] = rf_quat[pad:, :]

    # Rotate hip sensor by 90º plus the hip neutral transform, find the body
    # frame of the hip data
    yaw_90 = make_quaternion_array([sqrt(2)/2, 0, 0, -sqrt(2)/2], row_count)
    q_bf_hip = quat_multi_prod(q_neutraltransform_hip, q_sensor_hip, q_bftransform_hip, yaw_90)

    # insert transformed values for hip into dataframe
    sdata.loc[:, ['quat_hip_w', 'quat_hip_x', 'quat_hip_y', 'quat_hip_z']] = q_bf_hip
    # repeat drift filtering for hip sensor
    dynamic_range_h = detect_long_dynamic(sdata.corrupt_hip.values[:].reshape(-1, 1))
    for i, j in zip(dynamic_range_h[:, 0], dynamic_range_h[:, 1]):
        s = i - 50
        e = j
        if s < 0:
            s = 0
            pad = i
        else:
            pad = 50
        h_quat = drift_filter(sdata.ix[s:e, ['quat_hip_w', 'quat_hip_x', 'quat_hip_y', 'quat_hip_z']].values.reshape(-1, 4))
        sdata.loc[i:j, ['quat_hip_w', 'quat_hip_x', 'quat_hip_y', 'quat_hip_z']] = h_quat[pad:, :]

    # for acceleration transformation, get the bodyframe transformed quaternions
    # this included both transformation and drift filtering
    q_bf_left = sdata.loc[:, ['quat_lf_w', 'quat_lf_x', 'quat_lf_y', 'quat_lf_z']].values.reshape(-1, 4)
    q_bf_hip = sdata.loc[:, ['quat_hip_w', 'quat_hip_x', 'quat_hip_y', 'quat_hip_z']].values.reshape(-1, 4)
    q_bf_right = sdata.loc[:, ['quat_rf_w', 'quat_rf_x', 'quat_rf_y', 'quat_rf_z']].values.reshape(-1, 4)

    # Isolate the yaw component of the instantaneous sensor orientations
    q_bf_yaw_left = quat_force_euler_angle(q_bf_left, phi=0, theta=0)
    q_bf_yaw_hip = quat_force_euler_angle(q_bf_hip, phi=0, theta=0)
    q_bf_yaw_right = quat_force_euler_angle(q_bf_right, phi=0, theta=0)

    # After filtering trasnformed quaternions, reverse transformation to get filtered raw quats
    q_bf_left = apply_position_based_fixes(q_bf_left, sensor_position['left'], 'left', True)
    q_bf_right = apply_position_based_fixes(q_bf_right, sensor_position['right'], 'right', True)
    q_sensor_left = quat_prod(q_bf_left, quat_conj(q_bftransform_left))
    q_sensor_right = quat_prod(q_bf_right, quat_conj(q_bftransform_right))
    q_sensor_hip = quat_multi_prod(quat_conj(q_neutraltransform_hip),
                                   q_bf_hip, quat_conj(yaw_90),
                                   quat_conj(q_bftransform_hip))

    # Extract the sensor-frame acceleration values and create imaginary quaternions
    acc_sensor_left = sdata.loc[:, ['acc_lf_x', 'acc_lf_y', 'acc_lf_z']].values.reshape(-1, 3)
    acc_sensor_hip = sdata.loc[:, ['acc_hip_x', 'acc_hip_y', 'acc_hip_z']].values.reshape(-1, 3)
    acc_sensor_right = sdata.loc[:, ['acc_rf_x', 'acc_rf_y', 'acc_rf_z']].values.reshape(-1, 3)

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
    sdata.loc[:, ['acc_lf_x', 'acc_lf_y', 'acc_lf_z']] = acc_aif_left
    sdata.loc[:, ['acc_hip_x', 'acc_hip_y', 'acc_hip_z']] = acc_aif_hip
    sdata.loc[:, ['acc_rf_x', 'acc_rf_y', 'acc_rf_z']] = acc_aif_right

    # subtract the effects of gravity
    sdata = apply_acceleration_normalisation(sdata)

    return sdata


def apply_acceleration_normalisation(sdata):
    # Remove the effects of gravity
    sdata.acc_lf_z -= 9.80665
    sdata.acc_hip_z -= 9.80665
    sdata.acc_rf_z -= 9.80665
    return sdata


def apply_position_based_fixes(data, case, foot, reverse=False):
    """case based transformation fix for each foot"""

    if case == 'ACE':
        if foot == 'left':
            error_angle = -105 / 180. * np.pi
        else:
            error_angle = -75 / 180. * np.pi

    elif case == 'ADE':
        if foot == 'left':
            error_angle = 75 / 180. * np.pi
        else:
            error_angle = 105 / 180. * np.pi

    elif case == 'BCE':
        if foot == 'left':
            error_angle = 75 / 180. * np.pi
        else:
            error_angle = 105 / 180. * np.pi

    elif case == 'BDE':
        if foot == 'left':
            error_angle = -105 / 180. * np.pi
        else:
            error_angle = -75 / 180. * np.pi

    elif case == 'ACF':
        if foot == 'left':
            error_angle = -22.5 / 180. * np.pi
        else:
            error_angle = -157.5 / 180. * np.pi
    elif case == 'ADF':
        if foot == 'left':
            error_angle = 157.5 / 180. * np.pi
        else:
            error_angle = 22.5 / 180. * np.pi
    elif case == 'BCF':
        if foot == 'left':
            error_angle = 157.5 / 180. * np.pi
        else:
            error_angle = 22.5 / 180. * np.pi

    elif case == 'BDF':
        if foot == 'left':
            error_angle = -22.5 / 180. * np.pi
        else:
            error_angle = -157.5 / 180. * np.pi
    else:
        error_angle = 90 / 180. * np.pi

    error = make_quaternion_array(euler_to_quat(np.array([0, 0, error_angle]).reshape(1, -1))[0].tolist(), len(data))

    if not reverse:
        data = quat_prod(data, quat_conj(error))
    else:
        data = quat_prod(data, error)
    return data
