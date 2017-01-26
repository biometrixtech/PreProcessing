# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 05:34:54 2016

@author: court
"""
import numpy as np
import quatOps as qo
import quatConvs as qc
   
 
def calculate_rot_CMEs(lf_quat, hip_quat, rf_quat, lf_neutral, hip_neutral,
                       rf_neutral, phase_lf, phase_rf):
    """
    Calculates the offset of an athlete from a "neutral" position.

    Args:
        lf_quat: instantaneous left foot quaternions in body frame
        hip_quat: instantaneous hip quaternions in body frame
        rf_quat: instantaneous right foot quaternions in body frame
        lf_neutral: quaternion encoding of neutral lf body frame position as
            calculated in calibration
            "Euler" components:
                [0] neutral roll
                [1] neutral pitch
                [2] neutral difference between foot yaw and hip yaw
        hip_neutral: quaternion encoding of neutral hip body frame position as
            calculated in calibration
            "Euler" components:
                [0] neutral roll
                [1] neutral
                [2] 0, as a placeholder
        rf_neutral: quaternion encoding of neutral rf body frame position as
            calculated in calibration
            "Euler" components:
                [0] neutral roll
                [1] neutral pitch
                [2] neutral difference between foot yaw and hip yaw
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
    lf_neutral_eul = qc.quat_to_euler(lf_neutral)
    hip_neutral_eul = qc.quat_to_euler(hip_neutral)
    rf_neutral_eul = qc.quat_to_euler(rf_neutral)
    del lf_quat, hip_quat, rf_quat, lf_neutral, hip_neutral, rf_neutral
    
    length = len(lf_eul)
    # divide into single axes
    lf_roll = qc.euler_to_quat(np.hstack((lf_eul[:, 0].reshape(-1, 1),
                                          np.zeros((length, 2)))))
    hip_roll = qc.euler_to_quat(np.hstack((hip_eul[:, 0].reshape(-1, 1),
                                           np.zeros((length, 2)))))
    rf_roll = qc.euler_to_quat(np.hstack((rf_eul[:, 0].reshape(-1, 1),
                                          np.zeros((length, 2)))))
#    lf_pitch = qc.euler_to_quat(np.hstack((np.zeros((length, 1)),
#                                           lf_eul[:, 1].reshape(-1, 1),
#                                           np.zeros((length, 1)))))
#    hip_pitch = qc.euler_to_quat(np.hstack((np.zeros((length, 1)),
#                                            hip_eul[:, 1].reshape(-1, 1),
#                                            np.zeros((length, 1)))))
#    rf_pitch = qc.euler_to_quat(np.hstack((np.zeros((length, 1)),
#                                           rf_eul[:, 1].reshape(-1, 1),
#                                           np.zeros((length, 1)))))
    hip_yaw = qc.euler_to_quat(np.hstack((np.zeros((length, 2)),
                                          hip_eul[:, 2].reshape(-1, 1))))
    lf_raw_yaw = qc.euler_to_quat(np.hstack((np.zeros((length, 2)),
                                             lf_eul[:, 2].reshape(-1, 1))))
    rf_raw_yaw = qc.euler_to_quat(np.hstack((np.zeros((length, 2)),
                                             rf_eul[:, 2].reshape(-1, 1))))
    lf_yaw = qo.find_rot(lf_raw_yaw, hip_yaw)
    rf_yaw = qo.find_rot(rf_raw_yaw, hip_yaw)
    del lf_eul, rf_eul, hip_eul
    
    lf_neutral_roll = qc.euler_to_quat(np.hstack((lf_neutral_eul[:,
                                                  0].reshape(-1, 1),
                                                  np.zeros((length, 2)))))
    hip_neutral_roll = qc.euler_to_quat(np.hstack((hip_neutral_eul[:,
                                                   0].reshape(-1, 1),
                                                   np.zeros((length, 2)))))
    rf_neutral_roll = qc.euler_to_quat(np.hstack((rf_neutral_eul[:,
                                                  0].reshape(-1, 1),
                                                  np.zeros((length, 2)))))
#    lf_neutral_pitch = qc.euler_to_quat(np.hstack((np.zeros((length, 1)),
#                                        lf_neutral_eul[:, 1].reshape(-1, 1),
#                                        np.zeros((length, 1)))))
#    hip_neutral_pitch = qc.euler_to_quat(np.hstack((np.zeros((length, 1)),
#                                         hip_neutral_eul[:, 1].reshape(-1, 1),
#                                         np.zeros((length, 1)))))
#    rf_neutral_pitch = qc.euler_to_quat(np.hstack((np.zeros((length, 1)),
#                                        rf_neutral_eul[:, 1].reshape(-1, 1),
#                                        np.zeros((length, 1)))))
#    hip_neutral_yaw = qc.euler_to_quat(np.hstack((np.zeros((length, 2)),
#                                       hip_eul[:, 2].reshape(-1, 1))))
    lf_neutral_yaw = qc.euler_to_quat(np.hstack((np.zeros((length, 2)),
                                      lf_neutral_eul[:, 2].reshape(-1, 1))))
    rf_neutral_yaw = qc.euler_to_quat(np.hstack((np.zeros((length, 2)),
                                      rf_neutral_eul[:, 2].reshape(-1, 1))))
    del lf_neutral_eul, rf_neutral_eul, hip_neutral_eul
    # contralateral hip drop
        # hip roll
    hip_rot_lf = _cont_rot_CME(hip_roll, phase_lf, [1, 4], hip_neutral_roll)
    hip_rot_rf = _cont_rot_CME(hip_roll, phase_rf, [2, 5], hip_neutral_roll)
    contra_hip_drop_lf = hip_rot_lf.reshape(-1, 3)[:, 0]
    contra_hip_drop_lf = contra_hip_drop_lf* - 1 # fix so superior > 0
    contra_hip_drop_rf = hip_rot_rf.reshape(-1, 3)[:, 0]
    del hip_neutral_roll, hip_rot_lf, hip_rot_rf
    
    # ankle roll
        # foot roll
    roll_lf = _cont_rot_CME(lf_roll, phase_lf, [0, 1, 4], lf_neutral_roll)
    roll_rf = _cont_rot_CME(rf_roll, phase_rf, [0, 2, 5], rf_neutral_roll)
    ankle_rot_lf = roll_lf.reshape(-1, 3)[:, 0]
    ankle_rot_lf = ankle_rot_lf*-1 # fix so medial > 0
    ankle_rot_rf = roll_rf.reshape(-1, 3)[:, 0]
    del lf_neutral_roll, rf_neutral_roll, roll_lf, roll_rf
    # foot position
        # foot yaw
    yaw_lf = _cont_rot_CME(lf_yaw, phase_lf, [0, 1, 4], lf_neutral_yaw)
    yaw_rf = _cont_rot_CME(rf_yaw, phase_rf, [0, 2, 5], rf_neutral_yaw)
    foot_position_lf = yaw_lf.reshape(-1, 3)[:, 2]
    foot_position_lf = foot_position_lf*-1 # fix so medial > 0
    foot_position_rf = yaw_rf.reshape(-1, 3)[:, 2]
    del lf_neutral_yaw, rf_neutral_yaw, yaw_lf, yaw_rf
    
#    # hip rot - THIS IS MEANINGLESS - PLACEHOLDER AND PROOF OF CONCEPT
#        # hip yaw
#    yaw_hip = _cont_rot_CME(hip_yaw, phase_lf, [0, 1, 2, 3, 4, 5],
#                            hip_neutral_yaw)
#    hip_rot = yaw_hip.reshape(-1, 3)[:,2]
#    hip_rot = hip_rot*-1 # fix so clockwise > 0


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
#    print comparison
    for i in range(len(comparison)):
        if state[i] not in states:
            comparison[i] = np.array([np.nan, np.nan, np.nan])
        else:
            pass

    return comparison
            
    
if __name__ == "__main__":
    pass

