# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 09:21:40 2016

@author: court
"""


import numpy as np

import quatOps as qo
import quatConvs as qc



"""
#############################################INPUT/OUTPUT###################
Inputs: raw orientation data for regular calibration
Outputs: _bf_transform to allow for direct calculation of body frame from
sensor frame for full data sets. Also,
        _n_transform values to take body frame data to neutral position
        for use in CME analytics.
        
Pay attention to sensor model and orientation.

Script called upon by coordinateFrameTransformation.py, dependent on  QuatOps,
and quatConvs
###########################################################################
"""

    

def _sensor_to_aif(hip_data, hip_pitch_transform):
    
    """
    Use hip sensor frame and transform values from special calibration session
    to find the adjusted inertial frame during calibration. Also, find value
    by which all hip sensor data can be multiplied by in order to put it into
    the body frame (hip_bf_transform)

    Args: raw hip data and the hip_pitch_ and hip_roll_ transforms, as
    calculated during special calibration.
    
    Returns: hip data in the adjusted inertial frame, hip_bf_transform
    
    """
    
    # TODO(Courtney): incorporate bow into calculation of hip_asf_transform
    # rotation from sensor frame to adjusted sensor frame
#    hip_asf_transform = qo.quat_prod([0.70710678,0.70710678,0,0],
#                                      [0.70710678,0,0,0.70710678])
    # FOR OLD SENSORS RUNNING SIDE TO SIDE (sensor on right)
#    hip_asf_transform = [0.70710678,0,-0.70710678,0]
    # FOR OLD SENSORS RUNNING UP AND DOWN: -90 degrees about y axis
    hip_pitch_transform = hip_pitch_transform.T
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

    # calculate hip_bf_transform to get from sf to corrected bf
    hip_bf_transform = qo.quat_prod(hip_asf_transform,
                                    hip_pitch_transform).reshape(-1, 1)

    return hip_aif, hip_bf_transform


def _feet_transform_calculations(foot_data, hip_aif, foot_roll_transform):
    
    """Function to calculate transform values for a foot.
    
    Args:
        foot orientation data, adjusted inertial frame data taken from the hips
        during regular calibration, and foot_roll_transform value calculated
        during special feet calibration.
        
    Returns:
        foot_bf_transform, foot_yaw_transform, and foot_pitch_trasnform

    """
    # Extract feet_yaw_t for ft trans and feet_pitch_t for balanceCME
    foot_roll_transform = foot_roll_transform.T
    foot_asf = qo.find_rot(foot_data, hip_aif)
    foot_asf_components = qc.quat_to_euler(foot_asf)

    # create offset using yaw
    length = len(foot_data)
    foot_yaw_offset = np.hstack((np.zeros((length, 2)),
                                 foot_asf_components[:, 2].reshape(-1, 1)))
    foot_yaw_transform_inst = qc.euler_to_quat(foot_yaw_offset)

    # create offset using pitch
    foot_pitch_offset = np.hstack((np.zeros((length, 1)),
                                   foot_asf_components[:, 1].reshape(-1, 1),
                                   np.zeros((length, 1))))
    foot_pitch_transform_inst = qc.euler_to_quat(foot_pitch_offset)

    # average transform values over recording periods
    foot_yaw_transform = qo.quat_avg(foot_yaw_transform_inst)
    foot_pitch_transform = qo.quat_avg(foot_pitch_transform_inst)

    # calculate feet_bf_transform
    foot_bf_transform = qo.quat_prod(foot_yaw_transform,
                                     foot_roll_transform)

    return foot_bf_transform.reshape(-1, 1),\
    foot_yaw_transform.reshape(-1, 1), foot_pitch_transform.reshape(-1, 1)


def run_calib(data, hip_pitch_transform, hip_roll_transform,
              lf_roll_transform, rf_roll_transform):
    
    """
    Function to run regular calibration calculations and output final transform
    values as relevant to coordinate frame transformation.
    
    Args:
        full data, hip_pitch_ and hip_roll_transform from special hip
        calibration, lf_roll_ and rf_roll_ transform from special foot calib.
        
    Returns:
        hip_bf_, rf_bf_, and lf_bf_ transforms to take sensor data from each
        sensor directly to body frame,
        hip_n_, rf_n_, and lf_n_ transforms to calculate quaternions
        representative of nuetral position for each adjusted inertial frame
    
    """

    # divide data object into useful components
    hip_datadb = np.array([data['HqW'], data['HqX'], data['HqY'],
                           data['HqZ']]).transpose()
    lf_datadb = np.array([data['LqW'], data['LqX'], data['LqY'],
                          data['LqZ']]).transpose()
    rf_datadb = np.array([data['RqW'], data['RqX'], data['RqY'],
                          data['RqZ']]).transpose()

    # normalize orientation data
    hip_data = qo.quat_norm(hip_datadb)
    lf_data = qo.quat_norm(lf_datadb)
    rf_data = qo.quat_norm(rf_datadb)

    # take hip sensor frame into aif, get all _bf_transform values to get to body frames
    hip_aif, hip_bf_transform = _sensor_to_aif(hip_data, hip_pitch_transform)
    lf_bf_transform, lf_yaw_transform, lf_pitch_transform =\
            _feet_transform_calculations(lf_data, hip_aif, lf_roll_transform)
    rf_bf_transform, rf_yaw_transform, rf_pitch_transform =\
            _feet_transform_calculations(rf_data, hip_aif, rf_roll_transform)

    lf_bf_transform = lf_bf_transform.reshape(1, -1)
    rf_bf_transform = rf_bf_transform.reshape(1, -1)
    hip_bf_transform = hip_bf_transform.reshape(1, -1)

    return hip_bf_transform, lf_bf_transform, rf_bf_transform


if __name__ == '__main__':
    pass
#    import time
#    start_time = time.time()
#    ####READ IN DATA ~ Will change when we call from the database#####
#    path = 'C:\\Users\\court\Desktop\\BioMetrix\\baseFeet_p
    #roperty_testing\\test_data.csv'
#    data = np.genfromtxt(path, delimiter = ',', dtype = float, names = True)
#    print time.time() - start_time
#    hip_bf_transform,lf_bf_transform,rf_bf_transform,lf_n_transform,
    #rf_n_transform,hip_n_transform=run_calib(data,hip_pitch_transform,
    #hip_roll_transform,
#             lf_roll_transform,rf_roll_transform)
#
#    print "My program took", time.time() - start_time, "to run"
