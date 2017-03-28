# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 10:21:01 2016

@author: court
"""

import numpy as np

import quatOps as qo
import quatConvs as qc

"""
Special Calibratin Script, to be run before regular calibration and before
regular coord frame transformation. Special conditions for athlete position,
but can be used for quick tests by equating the paths to a set of the athlet
data representative of standing still.

"""


def _special_hip_calib(hip_data):
    
    """
    Special hip calibration analyzes data taken while subject is standing
    neutrally, after 3 deep breaths.
    Must be run before special feet calib and before regular calib. Pay
    attention to sensor model and orientation.
    
    Returns transforms that describe hip position in body frame "neutral
    position" with respect to adjusted inertial frame.
    
    
    Arg:
        full table of raw data
        
    Returns:
        hip_pitch_transform and hip_roll_transform
    
    """
            
    # TODO(Courtney): incorporate bow into calculation of hip_asf_transform
            
    # rotation from sensor frame to adjusted sensor frame
#    hip_asf_transform = qo.quat_prod([0.70710678,0.70710678,0,0],
#                                      [0.70710678,0,0,0.70710678])
            # FOR OLD SENSORS RUNNING SIDE TO SIDE
#    hip_asf_transform = [0.70710678,0,-0.70710678,0]
            # FOR OLD SENSORS RUNNING UP AND DOWN: -90 degrees about y axis
    rot_y = np.array([np.sqrt(.5), 0, np.sqrt(.5), 0])[np.newaxis, :]
    rot_x = np.array([np.sqrt(.5), np.sqrt(.5), 0, 0])[np.newaxis, :]
    # FOR NEW SENSORS: 90 deg about y axis, -90 deg about x axis
    hip_asf_transform = qo.quat_prod(rot_y, rot_x)
    
    hip_asf = qo.quat_prod(hip_data, hip_asf_transform)
    
    # create storage for variables and calculate instantaneous hip offsets
    
    hip_asf_eul = qc.quat_to_euler(hip_asf)
    length = len(hip_data)

    # create offset using pitch
    hip_asf_pitch_offset = np.hstack((np.zeros((length, 1)),
                                      hip_asf_eul[:, 1].reshape(-1, 1),
                                      np.zeros((length, 1))))
    hip_pitch_transform_inst = qc.euler_to_quat(hip_asf_pitch_offset)

    # create offset using roll
    hip_asf_roll_offset = np.hstack((hip_asf_eul[:, 1].reshape(-1, 1),
                                     np.zeros((length, 2))))
    hip_roll_transform_inst = qc.euler_to_quat(hip_asf_roll_offset)

    # get average of transform values over time
    hip_pitch_transform = qo.quat_norm(qo.quat_avg(hip_pitch_transform_inst))
    hip_roll_transform = qo.quat_norm(qo.quat_avg(hip_roll_transform_inst))

    return hip_pitch_transform.reshape(-1, 1), hip_roll_transform.reshape(-1, 1)
    
    
def _special_foot_calib(foot_data, hip_data, hip_pitch_transform):
    
    """
    Special feet calibration analyzes data recorded while subject is seated,
    legs forward, knees bent at 90 degrees, weight off of feet. Uses imperfect
    hip analysis to get feet _roll_transform, but that value is independent of
    hips and so error should be negligible. Must be run before regular calib.
    Pay attention to sensor model and orientation.
    
    Args:
        raw foot and hip orientation data from special feet calibration session,
        hip_pitch_transform from special hip calibration
        
    Returns:
        foot_roll_transform for one foot
    
    """
    hip_pitch_transform = hip_pitch_transform.reshape(1, -1)
    # TODO(Courtney): incorporate bow into calculation of hip_asf_transform

    # rotation from sensor frame to adjusted sensor frame
#    hip_asf_transform = qo.quat_prod([0.70710678,0.70710678,0,0],
#                                      [0.70710678,0,0,0.70710678])
# FOR OLD SENSORS RUNNING SIDE TO SIDE
#    hip_asf_transform = [0.70710678,0,-0.70710678,0]
# FOR OLD SENSORS RUNNING UP AND DOWN: -90 degrees about y axis
    rot_y = np.array([np.sqrt(.5), 0, np.sqrt(.5), 0])[np.newaxis, :]
    rot_x = np.array([np.sqrt(.5), np.sqrt(.5), 0, 0])[np.newaxis, :]
    # FOR NEW SENSORS: 90 deg about y axis, -90 deg about x axis
    hip_asf_transform = qo.quat_prod(rot_y, rot_x)
    
    # calculate adjusted sensor frame
    hip_asf = qo.quat_prod(hip_data, hip_asf_transform)
    
    # calculate adjusted inertial frame
    hip_asf_eul = qc.quat_to_euler(hip_asf)
    hip_asf_yaw = np.hstack((np.zeros((len(hip_data), 2)),
                                 hip_asf_eul[:, 2].reshape(-1, 1)))
    hip_aif = qc.euler_to_quat(hip_asf_yaw)
    
    # find yaw offset of foot from body adjusted inertial frame
    foot_asf = qo.find_rot(hip_aif, foot_data)
    foot_asf_components = qc.quat_to_euler(foot_asf)
    # create offset using yaw
    length = len(hip_data)
    foot_asf_yaw_offset = np.hstack((np.zeros((length, 2)),
                                     foot_asf_components[:, 2].reshape(-1, 1)))
    foot_yaw_transform = qc.euler_to_quat(foot_asf_yaw_offset)
    
    # use yaw offset from aif to determine foot_asf for this recording period
    foot_asfj = qo.quat_prod(foot_data, qo.quat_conj(foot_yaw_transform))
    
    # Isolate roll offset
    foot_asfj_components = qc.quat_to_euler(foot_asfj)
    foot_asfj_roll_offset = np.hstack((foot_asfj_components[:, 0].reshape(-1, 1),
                                       np.zeros((length, 2))))
    foot_roll_transform_inst = qc.euler_to_quat(foot_asfj_roll_offset)

    # get average foot_roll_transform value over recording period
    foot_roll_transform = qo.quat_avg(foot_roll_transform_inst).reshape(-1, 1)
    
    return foot_roll_transform
    
    
def run_special_calib(data):
    """
    Runs special hip and feet calibration analyses. Takes separate data paths,
    extracts relevant data, and outputs global variables needed in downstream
    analytics.
    
    Args:
        full raw data from special hip calibration, full raw data from special
        
    Returns:
        hip_pitch_ and hip_roll_transform s
        lf_ and rf_ roll_transform s
        
    """
#    hip_length = len(hip_data)
#    feet_length = len(feet_data)
#    length = np.min([hip_length, feet_length])
#    hip_data = hip_data[0:hip_length]
#    feet_data = feet_data[0:length]

    hip_data = np.vstack([data['HqW'], data['HqX'],
                          data['HqY'], data['HqZ']]).T
#    _logger('DONE WITH HIP SUBSET')
    left_data = np.vstack([data['LqW'], data['LqX'],
                           data['LqY'], data['LqZ']]).T
#    _logger('DONE WITH LEFT SUBSET')
    right_data = np.vstack([data['RqW'], data['RqX'],
                            data['RqY'], data['RqZ']]).T

    hip_data = qo.quat_norm(hip_data)
    lf_data = qo.quat_norm(left_data)
    rf_data = qo.quat_norm(right_data)

    # calculate hip transforms
    hip_pitch_transform, hip_roll_transform = _special_hip_calib(hip_data)

    # calculate feet transforms
    lf_roll_transform = _special_foot_calib(lf_data, hip_data,
                                            hip_pitch_transform)
    rf_roll_transform = _special_foot_calib(rf_data, hip_data,
                                            hip_pitch_transform)
    
    # reshape and return values
    return hip_pitch_transform.reshape(-1, 1),\
            hip_roll_transform.reshape(-1, 1),\
            lf_roll_transform.reshape(-1, 1),\
            rf_roll_transform.reshape(-1, 1)


#def _logger(message, info=True):
#    if AWS:
#        if info:
#            logger.info(message)
#        else:
#            logger.warning(message)
#    else:
#        print message
