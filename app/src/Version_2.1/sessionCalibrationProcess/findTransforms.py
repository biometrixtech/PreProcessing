# -*- coding: utf-8 -*-
"""
Created on Wed Apr 12 15:19:00 2017

@author: court
"""

import numpy as np
import quatOps as qo
import quatConvs as qc

#%% Run Transform Calculations

def run_transform_calculations(data):
    """
    Function to calculate from calibration data several values which will allow
    for transformation of practice data into relevant frames, namely, body
    frame and a neutral frame (hips only).

    Arg:
        - data: calibration data in full sensor format

    Returns:
        - lf_bf_transform: value which, when applied, will rotate raw data from
            the left foot directly into the body frame
        - hip_bf_transform: value which, when applied, will rotate raw data
            from the hip foot directly into the body frame
        - rf_bf_transform: value which, when applied, will rotate raw data from
            the right foot directly into the body frame
        - hip_n_transform: average value of body frame data from a standing
            neutral position in calibration, from which, roll and pitch can be
            used to define a neutral position for the hips for all time, to
            which instantaneous practice data can be compared

    Note: hip_n_transform assumes no motion during calibration. When bow is
        incorporated, this will need to be applied to the data filtered against
        motion in order to retain its relevance.

    """
    #%% Data Prep

    # divide into left, hip, right data
    hip_data = np.array([data['HqW'], data['HqX'], data['HqY'],
                           data['HqZ']]).transpose()
    lf_data = np.array([data['LqW'], data['LqX'], data['LqY'],
                          data['LqZ']]).transpose()
    rf_data = np.array([data['RqW'], data['RqX'], data['RqY'],
                          data['RqZ']]).transpose()

    # normalize orientation data
    hip_data = qo.quat_norm(hip_data)
    lf_data = qo.quat_norm(lf_data)
    rf_data = qo.quat_norm(rf_data)

    #%% Transform Calculations

    # calculate body frame and neutral transform values
    lf_bf_transform, hip_bf_transform, rf_bf_transform = _find_body_frame(
                                                         lf_data, hip_data,
                                                         rf_data)

    hip_n_transform = _find_neutral(hip_data, hip_bf_transform)

    return lf_bf_transform, hip_bf_transform, rf_bf_transform, hip_n_transform


#%% Body Frame Calculations

def _find_body_frame(lf_data, hip_data, rf_data):

    """
    Function to calculate from calibration data several values which will allow
    for transformation of practice data into relevant frames, namely, the body
    frame.

    Arg:
        - lf_data: quaternions from the left foot during calibration
        - hip_data: quaternions from the hip during calibration
        - rf_data: quaternions from the right foot during calibration

    Returns:
        - lf_bf_transform: value which, when applied, will rotate raw data from
            the left foot directly into the body frame
        - hip_bf_transform: value which, when applied, will rotate raw data
            from the hip foot directly into the body frame
        - rf_bf_transform: value which, when applied, will rotate raw data from
            the right foot directly into the body frame
    """

    #%% Hip Calculations

    # rotate hip data by ASF transform

    rot_y = np.array([np.sqrt(.5), 0, np.sqrt(.5), 0])[np.newaxis, :]
    rot_x = np.array([np.sqrt(.5), np.sqrt(.5), 0, 0])[np.newaxis, :]
    # FOR NEW SENSORS: 90 deg about y axis, -90 deg about x axis
    hip_asf_transform = qo.quat_prod(rot_y, rot_x)

    hip_asf = qo.quat_prod(hip_data, hip_asf_transform)
    
    #   divide hip data into axial components

    hip_asf_eul = qc.quat_to_euler(hip_asf)

    # save yaw component as hip AIF

    hip_aif = qc.euler_to_quat(np.hstack((np.zeros((len(hip_data), 2)),
                                 hip_asf_eul[:, 2].reshape(-1, 1))))

    # average and save roll and pitch components as intermediate transforms

    hip_pitch_transform = qc.euler_to_quat(np.hstack((np.hstack((np.zeros((
                                           len(hip_data), 1)),
                                           hip_asf_eul[:, 1].reshape(-1, 1))),
                                           np.zeros((len(hip_data), 1)))))

    hip_pitch_transform = qo.quat_conj(qo.quat_avg(hip_pitch_transform))

    hip_roll_transform = qc.euler_to_quat(np.hstack((hip_asf_eul[:,
                                          0].reshape(-1, 1),
                                          np.zeros((len(hip_data), 2)))))

    hip_roll_transform = qo.quat_conj(qo.quat_avg(hip_roll_transform))

    # save hip body frame transform as combo of ASF, roll, and pitch transforms

    hip_bf_transform = qo.quat_prod(hip_asf_transform, hip_pitch_transform)
    hip_bf_transform = qo.quat_prod(hip_bf_transform, hip_roll_transform)

    #%% Feet Calculations

    # body frame transformations are relationship of feet to hip AIF

    lf_bf_transform = qo.quat_avg(qo.find_rot(lf_data, hip_aif))
    rf_bf_transform = qo.quat_avg(qo.find_rot(rf_data, hip_aif))

    return lf_bf_transform, hip_bf_transform, rf_bf_transform


#%% Find Neutral Transform for Hip Data

def _find_neutral(hip_data, hip_bf_transform):

    """
    Function to define the hip neutral transform value, which will contain the
    information necessary to define neutral hip positions for all points in
    time of practice.

    Args:
        - hip_data: quaternions from the hip during calibration
        - hip_bf_transform: value which, when applied, will rotate raw data
            from the hip foot directly into the body frame

    """

    #%% Neutral Hip Data Calculation

    # frame conversion of neutral data

    hip_bf_data = qo.quat_prod(hip_data, hip_bf_transform)

    # averaging of neutral data

    hip_n_transform = qo.quat_avg(hip_bf_data)

    return hip_n_transform