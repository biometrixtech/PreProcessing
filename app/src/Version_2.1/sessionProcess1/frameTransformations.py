# -*- coding: utf-8 -*-
"""
Created on Thu Apr 20 16:18:01 2017

@author: court
"""
import numpy as np
import quatConvs as qc
import quatOps as qo
import accelerationTransformation as at

def transform_frames(data, lf_bf_transform, hip_bf_transform, rf_bf_transform,
                     hip_n_transform):

    """
    Function to transform data into frames appropriate to allow fundamental and
    advanced analiytical processing. Orientation data is to be converted to the
    body frame and acceleration data is to be converted to the adjusted
    inertial frame. Returned are two arrays, one of data for the actual athlete
    position in real time, and one for real time "neutral" versions of the
    data, to be used in further processing comparisons.

    Args:
        - data: full data array
        - lf_bf_transform: quaternion to rotate left foot to body frame
        - hip_bf_transform: quaternion to rotate hip to body frame
        - rf_bf_transform: quaternion to rotate right foot to body frame
        - hip_n_transform: quaternion to rotate hip to its instantaneous
            neutral position

    Returns:
        - transformed_data: array with orientation in body frame and
            acceleration in adjusted inertial frame
        - neutral_data: array with orientation in neutral version of body frame
            as calculated during calibration

    """

    #%% Prep Parameters

    # reshape transforms
    hip_bf_transform = hip_bf_transform.reshape(1, -1)
    lf_bf_transform = lf_bf_transform.reshape(1, -1)
    rf_bf_transform = rf_bf_transform.reshape(1, -1)
    hip_n_transform = hip_n_transform.reshape(1, -1)

    # divide data into relevant parts
    lf_quats = np.hstack([data.LqW, data.LqX, data.LqY,
                          data.LqZ]).reshape(-1, 4)
    hip_quats = np.hstack([data.HqW, data.HqX, data.HqY,
                           data.HqZ]).reshape(-1, 4)
    rf_quats = np.hstack([data.RqW, data.RqX, data.RqY,
                          data.RqZ]).reshape(-1, 4)

    lf_acc = np.hstack([data.LaX, data.LaY, data.LaZ]).reshape(-1, 3)
    hip_acc = np.hstack([data.HaX, data.HaY, data.HaZ]).reshape(-1, 3)
    rf_acc = np.hstack([data.RaX, data.RaY, data.RaZ]).reshape(-1, 3)

    epoch_time = np.array(data.epoch_time).reshape(-1, 1)

    # normalize data
    lf_quats = qo.quat_norm(lf_quats)
    hip_quats = qo.quat_norm(hip_quats)
    rf_quats = qo.quat_norm(rf_quats)

    # find length of data
    length = len(hip_quats)

    #%% Transform Data into Body Frame

    # transform hip data
    lf_bf_quats = qo.quat_prod(lf_quats, lf_bf_transform)
    lf_bf_euls = qc.quat_to_euler(lf_bf_quats)

    hip_bf_quats = qo.quat_prod(hip_quats, hip_bf_transform)
    hip_bf_euls = qc.quat_to_euler(hip_bf_quats)

    rf_bf_quats = qo.quat_prod(rf_quats, rf_bf_transform)
    rf_bf_euls = qc.quat_to_euler(rf_bf_quats)

    #%% Transform Acceleration

    # call accelerationTransformation
    hip_aif_acc, lf_aif_acc, rf_aif_acc =\
            at.acceleration_transform(hip_quats, lf_quats, rf_quats, hip_acc,
                                      lf_acc, rf_acc, hip_bf_euls, lf_bf_euls,
                                      rf_bf_euls)

    #%% Gather Transformed Data for Movement Table Use

    transformed_data = np.hstack((epoch_time, lf_aif_acc, lf_bf_euls,
                                  lf_bf_quats, hip_aif_acc, hip_bf_euls,
                                  hip_bf_quats, rf_aif_acc, rf_bf_euls,
                                  rf_bf_quats))

    #%% Transform Data into Neutral Versions, for balanceCME Calculations

    # divide static neutral and instantaneous hip data into axial components
    static_hip_neut = qc.quat_to_euler(hip_n_transform)
    neutral_hip_roll = static_hip_neut[0, 0]
    neutral_hip_pitch = static_hip_neut[0, 1]

    neutral_hip_roll = np.full((length, 1), neutral_hip_roll, float)
    neutral_hip_pitch = np.full((length, 1), neutral_hip_pitch, float)
    inst_hip_yaw = qc.quat_to_euler(hip_bf_quats)[:, 2].reshape(-1, 1)

    # combine select data to define neutral hip data
    hip_neutral_euls = np.hstack((neutral_hip_roll, neutral_hip_pitch,
                                  inst_hip_yaw))

    # define hip adjusted inertial frame using instantaneous hip yaw
    hip_aif_euls = np.hstack((np.zeros((length, 2)), inst_hip_yaw))

    # convert all Euler angles to quaternions and return as relevant output
    hip_aif = qc.euler_to_quat(hip_aif_euls)
    hip_neutral = qc.euler_to_quat(hip_neutral_euls)

    lf_neutral = hip_aif # in perfectly neutral stance, lf bf := hip AIF
    rf_neutral = hip_aif # in perfectly neutral stance, rf bf := hip AIF

    neutral_data = np.hstack((lf_neutral, hip_neutral, rf_neutral))

    return transformed_data, neutral_data