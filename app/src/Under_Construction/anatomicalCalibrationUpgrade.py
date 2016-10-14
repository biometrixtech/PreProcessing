# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 09:21:40 2016

@author: court
"""


import numpy as np
import pandas as pd

import quatOps as qo
import quatConvs as qc

"""
#############################################INPUT/OUTPUT####################################################
Inputs: raw orientation data for regular calibration
Outputs: _bf_coordTrans to allow for direct calculation of body frame from sensor frame for full data sets. Also,
        _n_transform values to take body frame data to neutral position for use in CME analytics. 
        
Pay attention to sensor model and orientation.

Script called upon by coordinateFrameTransformationUpgrade.py, dependent on specialFeetCalibration.py, QuatOps,
quatConvs
#############################################################################################################
"""

class EmptyTransformValError(ValueError):
    pass
#    print 'Need to perform Special Calibration!'

def s2aif(hip_data,hip_pitch_transform,hip_roll_transform):
    ##### Import hip sensor frame and feet sensor frame (quaternions only)
    
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
        
    # if hip_pitch_transform is empty, need to run Special Hip Calibration

    if hip_pitch_transform == [] or hip_roll_transform == []: 

        raise EmptyTransformValError

    else:
        pass

    # calculate hip_bf_coordTrans to get from sf to corrected bf
    hip_bf_coordTrans = qo.quat_prod(hip_asf_coordTrans,hip_pitch_transform)

    # use hip_pitch_transform to get from hip_asf to hip_aif (rotation about y axis)
    hip_pitch_transform_conj=qo.quat_conj(hip_pitch_transform)

    hip_aif=np.zeros((len(hip_asf),4))
    for i in range(len(hip_asf)):
        
        hip_aif[i,:] = qo.quat_prod(hip_asf[i,:],hip_pitch_transform_conj)

    return hip_aif,hip_bf_coordTrans#,hip_pitch_transform,hip_roll_transform

def feetTrans(footdata,hip_aif,feet_roll_transform):    

    # Extract feet_yaw_t for ft trans and feet_pitch_t for balanceCME
    feet_asf=np.zeros((len(footdata),4))
    feet_asf_components=np.zeros((len(footdata),3))
    feet_yaw_transform_inst=np.zeros((len(footdata),4))
    feet_pitch_transform_inst=np.zeros((len(footdata),4))
    
    for i in range(len(hip_aif)):  
        feet_asf[i,:] = qo.find_rot(hip_aif[i,:],footdata[i,:])
        feet_asf_components[i,:] = qc.q2eul(feet_asf[i,:])   
        feet_yaw_transform_inst[i,:] = qc.eul2q(0,0,feet_asf_components[i,2]) # create offset quaternion using only yaw offset
        feet_pitch_transform_inst[i,:] = qc.eul2q(0,feet_asf_components[i,1],0) # create offset quaternion using only pitch offset
    
    # GET AVERAGE OF FEET_YAW_TRANSFORM_INST DATA OVER RECORDING PERIOD
    feet_yaw_transform = qo.quat_avg(feet_yaw_transform_inst)
    
    # GET AVERAGE OF FEET_PITCH_TRANSFORM_INST DATA OVER RECORDING PERIOD
    feet_pitch_transform = qo.quat_avg(feet_pitch_transform_inst)
        
    #### If loop: If feet_roll_transform exists, calculate feet_bf_coordtrans
       # else, do special feet_roll_transform
    
    if feet_roll_transform == []:
        
        # GO TO SPECIAL FEET CALIBRATION
        raise EmptyTransformValError
        
    else:
        pass
    
    
    #### calculate feet_bf_coordTrans
    feet_bf_coordTrans = qo.quat_prod(feet_yaw_transform,feet_roll_transform)
    
        
    return feet_bf_coordTrans,feet_yaw_transform,feet_pitch_transform#,feet_roll_transform


def runCalib(path):
#### import raw hip and feet data (quaternions only)

    data=pd.read_csv(path)
    hip_datadb=data[['HqW','HqX','HqY','HqZ']]
    lf_datadb=data[['LqW','LqX','LqY','LqZ']]
    rf_datadb=data[['RqW','RqX','RqY','RqZ']]

    # create storage for vars
    hip_data=np.empty((len(hip_datadb),4))
    lf_data=np.empty((len(lf_datadb),4))
    rf_data=np.empty((len(rf_datadb),4))
    
    for i in range(len(hip_data)):
        hip_data[i,:]=qo.quat_n(hip_datadb.ix[i,:])
        lf_data[i,:]=qo.quat_n(lf_datadb.ix[i,:])
        rf_data[i,:]=qo.quat_n(rf_datadb.ix[i,:])

    # take hip sensor frame into aif, get all _bf_coordTrans values to get to body frames
    hip_aif,hip_bf_coordTrans=s2aif(hip_data,hip_pitch_transform,hip_roll_transform) # if special hip calibration already done, input hip_pitch_transform as 2nd argument
    lf_bf_coordTrans,lf_yaw_transform,lf_pitch_transform=feetTrans(lf_data,hip_aif,lf_roll_transform) # if special foot calibration already done, input lf_roll_transform as 3rd argument
    rf_bf_coordTrans,rf_yaw_transform,rf_pitch_transform=feetTrans(rf_data,hip_aif,rf_roll_transform) # if special foot calibration already done, input rf_roll_transform as 3rd argument

    # calculate _neutral_transform values
    lf_n_transform=qo.quat_prod(qo.quat_conj(hip_pitch_transform),lf_yaw_transform)
    lf_n_transform=qo.quat_prod(lf_n_transform,lf_pitch_transform)
    lf_n_transform=qo.quat_prod(lf_n_transform,lf_roll_transform)
    
    rf_n_transform=qo.quat_prod(qo.quat_conj(hip_pitch_transform),rf_yaw_transform)
    rf_n_transform=qo.quat_prod(rf_n_transform,rf_pitch_transform)
    rf_n_transform=qo.quat_prod(rf_n_transform,rf_roll_transform)
    
    hip_n_transform=qo.quat_prod(hip_pitch_transform,hip_roll_transform)
    
    return hip_bf_coordTrans,lf_bf_coordTrans,rf_bf_coordTrans,lf_n_transform,rf_n_transform,hip_n_transform
    
    
    
    
if __name__ == '__main__':
    
    import time
    start_time = time.time()
    
    ####READ IN DATA ~ Will change when we call from the database#####
    path = 'C:\Users\court\Desktop\BioMetrix\Research\Quaternions\subject6_sd.csv'

    hip_bf_coordTrans,lf_bf_coordTrans,rf_bf_coordTrans,lf_n_transform,rf_n_transform,hip_n_transform=runCalib(path)
    
    print "My program took", time.time() - start_time, "to run"
