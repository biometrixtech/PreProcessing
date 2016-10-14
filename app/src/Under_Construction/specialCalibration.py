# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 10:21:01 2016

@author: court
"""

import numpy as np
import pandas as pd

import quatOps as qo
import quatConvs as qc
"""
Special Calibratin Script, to be run before regular calibration and before regular coord frame transformation.
Special conditions for athlete position, but can be used for quick tests by equating the paths to a set of the 
athlete data representative of standing still.

"""
#class EmptyTransformValError(ValueError):
#
#    print 'Need to perform Special Hip Calibration!'

def special_hip_calib(hip_data):
    
    """
    Special hip calibration analyzes data taken while subject is standing neutrally, after 3 deep breaths.
    Must be run before special feet calib and before regular calib. Pay attention to sensor model and orientation.
    
    """
    
    ##### Transform hip sensor frame to hip adjusted sensor frame
        # TODO(Courtney): incorporate bow into calculation of hip_asf_coordTrans 
    # rotation from sensor frame to adjusted sensor frame 
    hip_asf_coordTrans = qo.quat_prod([0.70710678,0.70710678,0,0],[0.70710678,0,0,0.70710678]) # FOR OLD SENSORS RUNNING SIDE TO SIDE
#    hip_asf_coordTrans = [0.70710678,0,-0.70710678,0]  # FOR OLD SENSORS RUNNING UP AND DOWN: -90 degrees about y axis
#    hip_asf_coordTrans = qo.quat_prod([0.707106781186548,0,0.707106781186548,0],[0.707106781186548,0.707106781186548,0,0]) 
                # FOR NEW SENSORS: 90 deg about y axis, -90 deg about x axis
        
    hip_asf=np.zeros((len(hip_data),4))
    
    for i in range(len(hip_data)):
       
        hip_asf[i,:] = qo.quat_prod(hip_data[i,:],hip_asf_coordTrans) #.reshape(1,4)
        
    hip_pitch_transform_inst=np.zeros((len(hip_asf),4))
    hip_roll_transform_inst=np.zeros((len(hip_asf),4))
        
    for i in range(len(hip_asf)):
            
        hip_asf_eX,hip_asf_eY,hip_asf_eZ = qc.q2eul(hip_asf[i,:])

        hip_pitch_transform_inst[i,:] = qc.eul2q(0,hip_asf_eY,0) # create offset quaternion using only pitch offset
        hip_roll_transform_inst[i,:] = qc.eul2q(hip_asf_eX,0,0) # create offset quaternion using only roll offset

    # GET AVERAGE OF HIP_PITCH_ and _ROLL_ TRANSFORM dATA OVER RECORDING PERIOD
    hip_pitch_transform = qo.quat_n(qo.quat_avg(hip_pitch_transform_inst))
    hip_roll_transform = qo.quat_n(qo.quat_avg(hip_roll_transform_inst))
    
    return hip_pitch_transform,hip_roll_transform
    
    
def special_feet_calib(foot_data,hip_data,hip_pitch_transform):
    
    """
    Special feet calibration analyzes data recorded while subject is seated, legs forward, knees bent at 
    90 degrees, weight off of feet. Uses imperfect hip analysis to get feet _roll_transform, but that value
    is independent of hips and so error should be negligible. Must be run before regular calib. Pay attention 
    to sensor model and orientation.
    
    """
    
#    if hip_pitch_transform == []:
#        
#        raise EmptyTransformValError
    
    ##### Transform hip sensor frame to hip adjusted sensor frame
        # TODO(Courtney): incorporate bow into calculation of hip_asf_coordTrans 
    # rotation from sensor frame to adjusted sensor frame 
    hip_asf_coordTrans = qo.quat_prod([0.70710678,0.70710678,0,0],[0.70710678,0,0,0.70710678]) # FOR OLD SENSORS RUNNING SIDE TO SIDE
#    hip_asf_coordTrans = [0.70710678,0,-0.70710678,0]  # FOR OLD SENSORS RUNNING UP AND DOWN: -90 degrees about y axis
#    hip_asf_coordTrans = qo.quat_prod([0.707106781186548,0,0.707106781186548,0],[0.707106781186548,0.707106781186548,0,0]) 
                # FOR NEW SENSORS: 90 deg about y axis, -90 deg about x axis
        
    hip_asf=np.zeros((len(hip_data),4))
    
    for i in range(len(hip_data)):
       
        hip_asf[i,:] = qo.quat_prod(hip_data[i,:],hip_asf_coordTrans) #.reshape(1,4)
    
    # use hip_pitch_transform to get from hip_asf to hip_aif (rotation about y axis)
    hip_pitch_transform_conj=qo.quat_conj(hip_pitch_transform)

    hip_aif=np.zeros((len(hip_asf),4))
    for i in range(len(hip_asf)):
        
        hip_aif[i,:] = qo.quat_prod(hip_asf[i,:],hip_pitch_transform_conj)
    
    # Extract feet_yaw_t for ft trans and feet_pitch_t for balanceCME
    feet_asf=np.zeros((len(foot_data),4))
    feet_asf_components=np.zeros((len(foot_data),3))
    feet_yaw_transform_inst=np.zeros((len(foot_data),4))
    feet_pitch_transform_inst=np.zeros((len(foot_data),4))
    
    for i in range(len(hip_aif)):  
        feet_asf[i,:] = qo.find_rot(hip_aif[i,:],foot_data[i,:])
        feet_asf_components[i,:] = qc.q2eul(feet_asf[i,:])   
        feet_yaw_transform_inst[i,:] = qc.eul2q(0,0,feet_asf_components[i,2]) # create offset quaternion using only yaw offset
        feet_pitch_transform_inst[i,:] = qc.eul2q(0,feet_asf_components[i,1],0) # create offset quaternion using only pitch offset
    
    # GET AVERAGE OF FEET_YAW_TRANSFORM_INST DATA OVER RECORDING PERIOD
    feet_yaw_transform = qo.quat_avg(feet_yaw_transform_inst)
    
    ##### Import feet sensor frame data for special calibration phase

    # create storage for data
    feet_asfj=np.zeros((len(foot_data),4))
    feet_asfj_components=np.zeros((len(foot_data),3))
    feet_roll_transform_inst=np.zeros((len(foot_data),4))
    
    #### use yaw offset from hip_aif to determine feet_asf for this separate recording period
    for i in range(len(foot_data)):
        feet_asfj[i,:]=qo.quat_prod(foot_data[i,:],feet_yaw_transform)
    
        #### Isolate roll offset
        feet_asfj_components[i,:] = qc.q2eul(feet_asfj[i,:])
        feet_roll_transform_inst[i,:] = qc.eul2q(feet_asfj_components[i,2],0,0)
    
    #### GET AVERAGE OF FEET_ROLL_TRANSFORM_INST DATA OVER RECORDING PERIOD
    feet_roll_transform = qo.quat_avg(feet_roll_transform_inst)
    
    return feet_roll_transform
    
    
def runSpecialCalib(hip_path,feet_path):
    
    """ 
    Runs special hip and feet calibration analyses. Takes separate data paths, extracts relevant
    data, and outputs global variables needed in downstream analytics:
    hip_pitch_ and hip_roll_transforms, as well as feet _roll_transforms.
    
    """
    
    hipdata=pd.read_csv(hip_path)
    hip_datadb=hipdata[['HqW','HqX','HqY','HqZ']]
    
    # create storage for vars
    hip_data=np.empty((len(hip_datadb),4))
    
    for i in range(len(hip_data)):
        hip_data[i,:]=qo.quat_n(hip_datadb.ix[i,:])
        
    hip_pitch_transform,hip_roll_transform=special_hip_calib(hip_data)
    
    feetdata=pd.read_csv(feet_path)
    hipf_datadb=feetdata[['HqW','HqX','HqY','HqZ']]
    lf_datadb=feetdata[['LqW','LqX','LqY','LqZ']]
    rf_datadb=feetdata[['RqW','RqX','RqY','RqZ']]
    
    # create storage for vars
    hipf_data=np.empty((len(hipf_datadb),4))
    lf_data=np.empty((len(lf_datadb),4))
    rf_data=np.empty((len(rf_datadb),4))
    
    for i in range(len(hipf_data)):
        hipf_data[i,:]=qo.quat_n(hipf_datadb.ix[i,:])
        lf_data[i,:]=qo.quat_n(lf_datadb.ix[i,:])
        rf_data[i,:]=qo.quat_n(rf_datadb.ix[i,:])

    lf_roll_transform=special_feet_calib(lf_data,hipf_data,hip_pitch_transform)
    rf_roll_transform=special_feet_calib(rf_data,hipf_data,hip_pitch_transform)
    
    return hip_pitch_transform,hip_roll_transform,lf_roll_transform,rf_roll_transform
        
        
    
    
if __name__ == '__main__':
    
    import time
    start_time = time.time()
    
    ####READ IN DATA ~ Will change when we call from the database#####
    hip_path = 'C:\Users\court\Desktop\BioMetrix\Research\Quaternions\subject6_sd.csv'
    feet_path = 'C:\Users\court\Desktop\BioMetrix\Research\Quaternions\subject6_sd.csv'

    hip_pitch_transform,hip_roll_transform,lf_roll_transform,rf_roll_transform=runSpecialCalib(hip_path,feet_path)
    
    print "My program took", time.time() - start_time, "to run"