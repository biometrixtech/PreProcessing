# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 05:34:54 2016

@author: court
"""

import numpy as np
import quatOps as qo
import quatConvs as qc

def calculate_rot_CMEs(lf_quat, hip_quat, rf_quat, phase_lf, phase_rf):
    """
    Calculates the offset of an athlete from a "neutral" position.

    Args:
        lf_quat: instantaneous left foot quaternions in body frame
        hip_quat: instantaneous hip quaternions in body frame
        rf_quat: instantaneous right foot quaternions in body frame
        phase_lf: left foot phase
        phase_rf: right foot phase

    Returns:
        contra_hip_drop_lf: contralateral hip drop when left foot on ground
        contra_hip_drop_rf: contralateral hip drop when right foot on ground
        ankle_rot_lf: left ankle rotation when in contact with ground
        ankle_rot_rf: right ankle rotation when in contact with ground
        foot_position_lf: difference in left foot forward direction from
            neutral when on ground
        foot_position_rf: difference in right foot forward direction from
            neutral when on ground
        hip_rot: lateral rotation of hips from adjusted inertial frame,
            currently just a placeholder

    """

    # divide quats into Euler angles
    lf_eul = qc.quat_to_euler(lf_quat)
    hip_eul = qc.quat_to_euler(hip_quat)
    rf_eul = qc.quat_to_euler(rf_quat)

    length = len(lf_eul)

    neutral_eul = np.hstack((np.ones((length, 1)), np.zeros((length, 3))))

    # divide into single axes
    lf_roll = qc.euler_to_quat(np.hstack((lf_eul[:, 0].reshape(-1, 1),
                                          np.zeros((length, 2)))))
    hip_roll = qc.euler_to_quat(np.hstack((hip_eul[:, 0].reshape(-1, 1),
                                           np.zeros((length, 2)))))

    rf_roll = qc.euler_to_quat(np.hstack((rf_eul[:, 0].reshape(-1, 1),
                                          np.zeros((length, 2)))))
    lf_yaw = qc.euler_to_quat(np.hstack((np.zeros((length, 2)),
                                             lf_eul[:, 2].reshape(-1, 1))))
    rf_yaw = qc.euler_to_quat(np.hstack((np.zeros((length, 2)),
                                             rf_eul[:, 2].reshape(-1, 1))))
    hip_yaw = qc.euler_to_quat(np.hstack((np.zeros((length, 2)),
                                          hip_eul[:, 2].reshape(-1, 1))))

#%%
    del lf_eul, rf_eul, hip_eul

    # contralateral hip drop
        # hip roll
#    hip_rot_lf = _filt_rot_CME(hip_roll, phase_lf, [0, 1, 4, 6])
#    hip_rot_rf = _filt_rot_CME(hip_roll, phase_rf, [0, 2, 5, 7])
    hip_rot_lf = _filt_rot_CME(hip_roll, phase_lf, [0, 2, 3])
    hip_rot_rf = _filt_rot_CME(hip_roll, phase_rf, [0, 2, 3])
    contra_hip_drop_lf = hip_rot_lf.reshape(-1, 3)[:, 0]
    contra_hip_drop_lf = contra_hip_drop_lf* - 1 # fix so superior > 0
    contra_hip_drop_rf = hip_rot_rf.reshape(-1, 3)[:, 0]
    del hip_rot_lf, hip_rot_rf

    # ankle roll
        # foot roll
#    roll_lf = _filt_rot_CME(lf_roll, phase_lf, [0, 1, 4, 6])
#    roll_rf = _filt_rot_CME(rf_roll, phase_rf, [0, 2, 5, 7])
    roll_lf = _filt_rot_CME(lf_roll, phase_lf, [0, 2, 3])
    roll_rf = _filt_rot_CME(rf_roll, phase_rf, [0, 2, 3])
    ankle_rot_lf = roll_lf.reshape(-1, 3)[:, 0]
    ankle_rot_lf = ankle_rot_lf*-1 # fix so medial > 0
    ankle_rot_rf = roll_rf.reshape(-1, 3)[:, 0]
    del neutral_eul, roll_lf, roll_rf
  
    # foot position
        # foot yaw
#    yaw_lf = _cont_rot_CME(lf_yaw, phase_lf, [0, 1, 4, 6], hip_yaw)
#    yaw_rf = _cont_rot_CME(rf_yaw, phase_rf, [0, 2, 5, 7], hip_yaw)
    yaw_lf = _cont_rot_CME(lf_yaw, phase_lf, [0, 2, 3], hip_yaw)
    yaw_rf = _cont_rot_CME(rf_yaw, phase_rf, [0, 2, 3], hip_yaw)
    foot_position_lf = yaw_lf.reshape(-1, 3)[:, 2]
    foot_position_lf = foot_position_lf*-1 # fix so medial > 0
    foot_position_rf = yaw_rf.reshape(-1, 3)[:, 2]
    del hip_yaw, yaw_lf, yaw_rf

    return contra_hip_drop_lf, contra_hip_drop_rf, ankle_rot_lf, ankle_rot_rf,\
        foot_position_lf, foot_position_rf


def _cont_rot_CME(data, state, states, neutral):
    """
    Calculates the rotation of a body from its "neutral" position.

    Args:
        data: data to compare to neutral position
        state: state of data (usually instantaneous phase)
        states: states during which data should be compared to neutral
        neutral: neutral value to which data should be compared

    comparison: array comparing body position to neutral, consisting of
            [0] difference of body position from neutral roll
            [1] difference of body position from neutral pitch
            [2] difference of body position from neutral yaw

    """
    
    diff_quat = qo.find_rot(data, neutral)
    del data, neutral
    diff_eul = qc.quat_to_euler(diff_quat)
    del diff_quat
    comparison = (180/np.pi)*diff_eul
    comparison[(np.in1d(state, states) == False)] = np.array([np.nan,
                                                              np.nan, np.nan])

    return comparison


def _filt_rot_CME(data, state, states):
    """
    Calculates the rotation of a body from its "neutral" position.

    Args:
        data: data to compare to neutral position
        state: state of data (usually instantaneous phase)
        states: states during which data should be compared to neutral

    comparison: array of body position, filtered by relevant state

    """

    eul = qc.quat_to_euler(data)
    del data
    result = (180/np.pi)*eul
    result[(np.in1d(state, states) == False)] = np.array([np.nan,
                                                              np.nan, np.nan])

    return result


if __name__ == "__main__":
    pass

