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
but can be used for quick tests by equating the paths to a set of the athlete 
data representative of standing still.

"""


def _special_hip_calib(data):
    
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
    
    # extract hip data
    hip_datadb = np.array([data['HqW'], data['HqX'], data['HqY'], data['HqZ']]).transpose() 

    # create storage for values and fill with normalized orientations
    hip_data=np.empty_like(hip_datadb)
    
    for i in range(len(hip_data)):
        
        hip_data[i]=qo.quat_norm(hip_datadb[i].tolist())
            
    # TODO(Courtney): incorporate bow into calculation of hip_asf_transform 
            
    # rotation from sensor frame to adjusted sensor frame 
#    hip_asf_transform = qo.quat_prod([0.70710678,0.70710678,0,0],
#                                      [0.70710678,0,0,0.70710678])  # FOR OLD SENSORS RUNNING SIDE TO SIDE
#    hip_asf_transform = [0.70710678,0,-0.70710678,0]  # FOR OLD SENSORS RUNNING UP AND DOWN: -90 degrees about y axis
    hip_asf_transform = qo.quat_prod([0.707106781186548,0,0.707106781186548,0],
                                      [0.707106781186548,0.707106781186548,0,0])  # FOR NEW SENSORS: 90 deg about y axis, -90 deg about x axis
    
    # create storage for values and calculate adjusted sensor frame
    hip_asf=np.zeros((len(hip_data),4))
    
    for i in range(len(hip_data)):
       
        hip_asf[i] = qo.quat_prod(hip_data[i],hip_asf_transform)
    
    # create storage for variables and calculate instantaneous hip offsets    
    hip_pitch_transform_inst=np.zeros_like(hip_asf)
    hip_roll_transform_inst=np.zeros_like(hip_asf)
        
    for i in range(len(hip_asf)):
            
        hip_asf_eX,hip_asf_eY,hip_asf_eZ = qc.quat_to_euler(hip_asf[i])
        hip_pitch_transform_inst[i] = qc.euler_to_quat(0,hip_asf_eY,0) # create offset using pitch
        hip_roll_transform_inst[i] = qc.euler_to_quat(hip_asf_eX,0,0) # create offset using roll

    # get average of transform values over time
    hip_pitch_transform = qo.quat_norm(qo.quat_avg(hip_pitch_transform_inst))
    hip_roll_transform = qo.quat_norm(qo.quat_avg(hip_roll_transform_inst))
    
    return hip_pitch_transform,hip_roll_transform
    
    
def _special_foot_calib(foot_data,hip_data,hip_pitch_transform):
    
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

    # TODO(Courtney): incorporate bow into calculation of hip_asf_transform 

    # rotation from sensor frame to adjusted sensor frame 
#    hip_asf_transform = qo.quat_prod([0.70710678,0.70710678,0,0],
#                                      [0.70710678,0,0,0.70710678]) # FOR OLD SENSORS RUNNING SIDE TO SIDE
#    hip_asf_transform = [0.70710678,0,-0.70710678,0]  # FOR OLD SENSORS RUNNING UP AND DOWN: -90 degrees about y axis
    hip_asf_transform = qo.quat_prod([0.707106781186548,0,0.707106781186548,0],
                                      [0.707106781186548,0.707106781186548,0,0])  # FOR NEW SENSORS: 90 deg about y axis, -90 deg about x axis
    
    # create storage for values and calculate adjusted sensor frame
    hip_asf=np.zeros_like(hip_data)
    
    for i in range(len(hip_data)):
       
        hip_asf[i] = qo.quat_prod(hip_data[i],hip_asf_transform)
    
    # use hip_pitch_transform to get from hip_asf to hip_aif
    hip_pitch_transform_conj=qo.quat_conj(hip_pitch_transform)
    hip_aif=np.zeros_like(hip_asf)
    
    for i in range(len(hip_asf)):
        
        hip_aif[i] = qo.quat_prod(hip_asf[i],hip_pitch_transform_conj)
    
    # Create storage for values and calculate instantaneous transform values
    foot_asf=np.zeros_like(foot_data) # len(data)xwid(data)
    foot_asf_components=np.zeros((len(foot_data),3)) # len(data)x3
    foot_yaw_transform=np.zeros((len(foot_data),4)) # 1x4
    foot_asfj=np.zeros_like(foot_data) # len(data)xwid(data)
    foot_asfj_components=np.zeros((len(foot_data),3)) # len(data)x3
    foot_roll_transform_inst=np.zeros((len(foot_data),4)) # len(data)xwid(data)
    
    # find yaw offset of foot from body adjusted inertial frame
    for i in range(len(hip_aif)):  
        foot_asf[i] = qo.find_rot(hip_aif[i],foot_data[i])
        foot_asf_components[i] = qc.quat_to_euler(foot_asf[i])   
        foot_yaw_transform[i] = qc.euler_to_quat(0,0,foot_asf_components[i][2]) # create offset using yaw 
    
    # use yaw offset from aif to determine foot_asf for this recording period
    for i in range(len(foot_data)):
        foot_asfj[i]=qo.quat_prod(foot_data[i],qo.quat_conj(foot_yaw_transform[i]))
    
        # Isolate roll offset
        foot_asfj_components[i] = qc.quat_to_euler(foot_asfj[i])
        foot_roll_transform_inst[i] = tuple(qc.euler_to_quat(foot_asfj_components[i][2],0,0))
    
    # get average foot_roll_transform value over recording period
    foot_roll_transform = qo.quat_avg(foot_roll_transform_inst)
    
    return foot_roll_transform
    
    
def run_special_calib(hip_data,feet_data):
    
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
    
    # calculate hip transforms from special hip calibration
    hip_pitch_transform,hip_roll_transform=_special_hip_calib(hip_data)
    
    # divide data from special feet calibration
    hipf_datadb=feet_data[['HqW','HqX','HqY','HqZ']]
    lf_datadb=feet_data[['LqW','LqX','LqY','LqZ']]
    rf_datadb=feet_data[['RqW','RqX','RqY','RqZ']]
    hipf_data=np.empty_like(hipf_datadb)
    lf_data=np.empty_like(lf_datadb)
    rf_data=np.empty_like(rf_datadb)
        
    for i in range(len(feet_data)):
        
        hipf_data[i]=qo.quat_norm(hipf_datadb[i].tolist())
        lf_data[i]=qo.quat_norm(lf_datadb[i].tolist())
        rf_data[i]=qo.quat_norm(rf_datadb[i].tolist())

    # calculate feet transforms from special feet calibration
    lf_roll_transform=_special_foot_calib(lf_data,hipf_data,hip_pitch_transform)
    rf_roll_transform=_special_foot_calib(rf_data,hipf_data,hip_pitch_transform)
    
    # reshape and return values
    return hip_pitch_transform.reshape(-1,1),hip_roll_transform.reshape(-1,1),lf_roll_transform.reshape(-1,1),rf_roll_transform.reshape(-1,1)
