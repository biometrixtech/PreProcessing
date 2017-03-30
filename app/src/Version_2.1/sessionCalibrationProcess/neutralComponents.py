# -*- coding: utf-8 -*-
"""
Created on Wed Jan 04 11:00:40 2017

@author: court
"""

import numpy as np
import quatOps as qo
import quatConvs as qc


def run_neutral_computations(standing_data, lf_bf_transform,
                             hip_bf_transform, rf_bf_transform):

    """
    Computes components of neutral positions for an athlete based on their
    calibration data. Note the definitions in Returns: transforms are not true
    transforms, but rather compilations of values to be used directly and in
    computations of neutral values.

    Args:
        - sitting data: from base calibration,
        - standing data: from either base orsession calibration (most recent
          valid file),
        - lf_bf_transform: quat value to convert lf sensor data to body frame
        - hip_bf_transform: quat value to convert hip sensor data to body frame
        - rf_bf_transform: quat value to convert rf sensor data to body frame

    Returns:
        - lf_n_transform: quaternion form of neutral left foot offset yaw from
          hip body frame, roll, and pitch, in ZYX rotation order, returned as
          x, y, z order
        - hip_n_transform: quaternion form of neutral hip roll and pitch, in
          ZYX rotation order, returned as x, y, z order
        - rf_n_transform: quaternion form of neutral right foot offset yaw from
          hip body frame, roll, and pitch, in ZYX rotation order, returned as
          x, y, z order

    """

    # divide data into relevant quaternions
#    sitting_lf_data = np.array([sitting_data['LqW'], sitting_data['LqX'],
#                                  sitting_data['LqY'],
#                                  sitting_data['LqZ']]).transpose()
#    sitting_rf_data = np.array([sitting_data['RqW'], sitting_data['RqX'],
#                                  sitting_data['RqY'],
#                                  sitting_data['RqZ']]).transpose()
    standing_hip_data = np.array([standing_data['HqW'], standing_data['HqX'],
                                   standing_data['HqY'],
                                   standing_data['HqZ']]).transpose()
    standing_lf_data = np.array([standing_data['LqW'], standing_data['LqX'],
                                   standing_data['LqY'],
                                   standing_data['LqZ']]).transpose()
    standing_rf_data = np.array([standing_data['RqW'], standing_data['RqX'],
                                   standing_data['RqY'],
                                   standing_data['RqZ']]).transpose()

    # reshape transform values
    lf_bf_transform = lf_bf_transform.reshape(1, -1)
    rf_bf_transform = rf_bf_transform.reshape(1, -1)
    hip_bf_transform = hip_bf_transform.reshape(1, -1)

    # normalize orientation data
#    sitting_lf_data = qo.quat_norm(sitting_lf_data)
#    sitting_rf_data = qo.quat_norm(sitting_rf_data)
    standing_hip_data = qo.quat_norm(standing_hip_data)
    standing_lf_data = qo.quat_norm(standing_lf_data)
    standing_rf_data = qo.quat_norm(standing_rf_data)

    # convert to body frame
#    sitting_lf_bf = qo.quat_prod(sitting_lf_data, lf_bf_transform)
#    sitting_rf_bf = qo.quat_prod(sitting_rf_data, rf_bf_transform)
    standing_hip_bf = qo.quat_prod(standing_hip_data, hip_bf_transform)
    standing_lf_bf = qo.quat_prod(standing_lf_data, lf_bf_transform)
    standing_rf_bf = qo.quat_prod(standing_rf_data, rf_bf_transform)

    # average body frame data
#    sitting_lf_bf_avg = qo.quat_avg(sitting_lf_bf)
#    sitting_rf_bf_avg = qo.quat_avg(sitting_rf_bf)
    standing_hip_bf_avg = qo.quat_avg(standing_hip_bf)
    standing_lf_bf_avg = qo.quat_avg(standing_lf_bf)
    standing_rf_bf_avg = qo.quat_avg(standing_rf_bf)

    # calculate euler angle components of averaged body frame data
#    sitting_lf_eul = qc.quat_to_euler(sitting_lf_bf_avg)
#    sitting_rf_eul = qc.quat_to_euler(sitting_rf_bf_avg)
    standing_hip_eul = qc.quat_to_euler(standing_hip_bf_avg)
    standing_lf_eul = qc.quat_to_euler(standing_lf_bf_avg)
    standing_rf_eul = qc.quat_to_euler(standing_rf_bf_avg)

    # save components of neutral hip transform
    hip_neutral_roll = standing_hip_eul[0, 0]
    hip_neutral_pitch = standing_hip_eul[0, 1]
    hip_neutral_yaw = 0

    # save components of neutral feet transforms
    lf_neutral_roll = standing_lf_eul[0, 0]
    lf_neutral_pitch = standing_lf_eul[0, 1]
    lf_yaw_quat = qo.find_rot(qc.euler_to_quat(standing_lf_eul),
                              qc.euler_to_quat(standing_hip_eul))
    lf_neutral_yaw = qc.quat_to_euler(lf_yaw_quat)[0, 2]

    rf_neutral_roll = standing_rf_eul[0, 0]
    rf_neutral_pitch = standing_rf_eul[0, 1]
    rf_yaw_quat = qo.find_rot(qc.euler_to_quat(standing_rf_eul),
                              qc.euler_to_quat(standing_hip_eul))
    rf_neutral_yaw = qc.quat_to_euler(rf_yaw_quat)[0, 2]

    # compile transform values
    lf_n_transform_eul = np.array([lf_neutral_roll, lf_neutral_pitch,
                                   lf_neutral_yaw])
    hip_n_transform_eul = np.array([hip_neutral_roll, hip_neutral_pitch,
                                   hip_neutral_yaw])
    rf_n_transform_eul = np.array([rf_neutral_roll, rf_neutral_pitch,
                                   rf_neutral_yaw])
    lf_n_transform = qc.euler_to_quat(lf_n_transform_eul.reshape(1, 3))
    hip_n_transform = qc.euler_to_quat(hip_n_transform_eul.reshape(1, 3))
    rf_n_transform = qc.euler_to_quat(rf_n_transform_eul.reshape(1, 3))

    return lf_n_transform, hip_n_transform, rf_n_transform
