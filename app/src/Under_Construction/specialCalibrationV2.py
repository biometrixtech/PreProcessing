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

def special_hip_calib(data):
    
    """
    Special hip calibration analyzes data taken while subject is standing neutrally, after 3 deep breaths.
    Must be run before special feet calib and before regular calib. Pay attention to sensor model and orientation.
    
    """
#    d=calibration_preprocessing(hip_path)
#    print d.data.LaX
        
    hip_datadb = np.array([data['HqW'], data['HqX'], data['HqY'], data['HqZ']]).transpose() 
#    hip_accdb = np.array([data['HaX'], data['HaY'], data['HaZ']]).transpose()
#    lf_accdb=np.array([data['LaX'], data['LaY'], data['LaZ']]).transpose()
#    rf_accdb=np.array([data['RaX'], data['RaY'], data['RaZ']]).transpose()

#    timestamp = np.array(data['epoch_time']).transpose()
    
    # create storage for vars
    hip_data=np.empty_like(hip_datadb)
#    hip_acc=hip_accdb
#    lf_acc=lf_accdb
#    rf_acc=rf_accdb
    
    for i in range(len(hip_data)):
        hip_data[i]=qo.quat_n(hip_datadb[i].tolist())
            
    ##### Transform hip sensor frame to hip adjusted sensor frame
        # TODO(Courtney): incorporate bow into calculation of hip_asf_coordTrans 
    # rotation from sensor frame to adjusted sensor frame 
    hip_asf_coordTrans = qo.quat_prod([0.70710678,0.70710678,0,0],[0.70710678,0,0,0.70710678]) # FOR OLD SENSORS RUNNING SIDE TO SIDE
#    hip_asf_coordTrans = [0.70710678,0,-0.70710678,0]  # FOR OLD SENSORS RUNNING UP AND DOWN: -90 degrees about y axis
#    hip_asf_coordTrans = qo.quat_prod([0.707106781186548,0,0.707106781186548,0],[0.707106781186548,0.707106781186548,0,0]) 
                # FOR NEW SENSORS: 90 deg about y axis, -90 deg about x axis
        
    hip_asf=np.zeros((len(hip_data),4))
    
    for i in range(len(hip_data)):
       
        hip_asf[i] = qo.quat_prod(hip_data[i],hip_asf_coordTrans) #.reshape(1,4)
        
    hip_pitch_transform_inst=np.zeros_like(hip_asf)
    hip_roll_transform_inst=np.zeros_like(hip_asf)
        
    for i in range(len(hip_asf)):
            
        hip_asf_eX,hip_asf_eY,hip_asf_eZ = qc.q2eul(hip_asf[i])

        hip_pitch_transform_inst[i] = qc.eul2q(0,hip_asf_eY,0) # create offset quaternion using only pitch offset
        hip_roll_transform_inst[i] = qc.eul2q(hip_asf_eX,0,0) # create offset quaternion using only roll offset

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
#    print foot_data
    ##### Transform hip sensor frame to hip adjusted sensor frame
        # TODO(Courtney): incorporate bow into calculation of hip_asf_coordTrans 
    # rotation from sensor frame to adjusted sensor frame 
    hip_asf_coordTrans = qo.quat_prod([0.70710678,0.70710678,0,0],[0.70710678,0,0,0.70710678]) # FOR OLD SENSORS RUNNING SIDE TO SIDE
#    hip_asf_coordTrans = [0.70710678,0,-0.70710678,0]  # FOR OLD SENSORS RUNNING UP AND DOWN: -90 degrees about y axis
#    hip_asf_coordTrans = qo.quat_prod([0.707106781186548,0,0.707106781186548,0],[0.707106781186548,0.707106781186548,0,0]) 
                # FOR NEW SENSORS: 90 deg about y axis, -90 deg about x axis
        
    hip_asf=np.zeros_like(hip_data)
    
    for i in range(len(hip_data)):
       
        hip_asf[i] = qo.quat_prod(hip_data[i],hip_asf_coordTrans) #.reshape(1,4)
    
    # use hip_pitch_transform to get from hip_asf to hip_aif (rotation about y axis)
    hip_pitch_transform_conj=qo.quat_conj(hip_pitch_transform)

    hip_aif=np.zeros_like(hip_asf)
    
    for i in range(len(hip_asf)):
        
        hip_aif[i] = qo.quat_prod(hip_asf[i],hip_pitch_transform_conj)
    
    # Extract feet_yaw_t for ft trans and feet_pitch_t for balanceCME
    feet_asf=np.zeros_like(foot_data) # len(data)xwid(data)
    feet_asf_components=np.zeros((len(foot_data),3)) # len(data)x3
    feet_yaw_transform_inst=np.zeros((len(foot_data),4)) # 1x4
    feet_pitch_transform_inst=np.zeros((len(foot_data),4)) # 1x4
    
    for i in range(len(hip_aif)):  
        feet_asf[i] = qo.find_rot(hip_aif[i],foot_data[i])
        feet_asf_components[i] = qc.q2eul(feet_asf[i])   
        feet_yaw_transform_inst[i] = qc.eul2q(0,0,feet_asf_components[i][2]) # create offset quaternion using only yaw offset
        feet_pitch_transform_inst[i] = qc.eul2q(0,feet_asf_components[i][1],0) # create offset quaternion using only pitch offset
    
    # GET AVERAGE OF FEET_YAW_TRANSFORM_INST DATA OVER RECORDING PERIOD
    feet_yaw_transform = qo.quat_avg(feet_yaw_transform_inst)
    
    ##### Import feet sensor frame data for special calibration phase

    # create storage for data
    feet_asfj=np.zeros_like(foot_data) # len(data)xwid(data)
    feet_asfj_components=np.zeros((len(foot_data),3)) # len(data)x3
    feet_roll_transform_inst=np.zeros((len(foot_data),4)) # len(data)xwid(data)
    
    #### use yaw offset from hip_aif to determine feet_asf for this separate recording period
#    print 'hello1'
    for i in range(len(foot_data)):
        feet_asfj[i]=qo.quat_prod(foot_data[i],feet_yaw_transform)
    
        #### Isolate roll offset
        feet_asfj_components[i] = qc.q2eul(feet_asfj[i])
#        print 'hello'
#        print feet_asf_components[i]
        feet_roll_transform_inst[i] = tuple(qc.eul2q(feet_asfj_components[i][2],0,0))
    
    #### GET AVERAGE OF FEET_ROLL_TRANSFORM_INST DATA OVER RECORDING PERIOD
    feet_roll_transform = qo.quat_avg(feet_roll_transform_inst)
    
    return feet_roll_transform
    
    
def runSpecialCalib(hip_data,feet_data):
    
    """ 
    Runs special hip and feet calibration analyses. Takes separate data paths, extracts relevant
    data, and outputs global variables needed in downstream analytics:
    hip_pitch_ and hip_roll_transforms, as well as feet _roll_transforms.
    
    """
    
        
    hip_pitch_transform,hip_roll_transform=special_hip_calib(hip_data)
    
#    feetdata=pd.read_csv(feet_path)
    hipf_datadb=feet_data[['HqW','HqX','HqY','HqZ']]
    lf_datadb=feet_data[['LqW','LqX','LqY','LqZ']]
    rf_datadb=feet_data[['RqW','RqX','RqY','RqZ']]
    
    # create storage for vars
    hipf_data=np.empty_like(hipf_datadb)
    lf_data=np.empty_like(lf_datadb)
    rf_data=np.empty_like(rf_datadb)
        
    for i in range(len(hip_data)):
        hipf_data[i]=qo.quat_n(hipf_datadb[i].tolist())
        lf_data[i]=qo.quat_n(lf_datadb[i].tolist())
        rf_data[i]=qo.quat_n(rf_datadb[i].tolist())

    lf_roll_transform=special_feet_calib(lf_data,hipf_data,hip_pitch_transform)
    rf_roll_transform=special_feet_calib(rf_data,hipf_data,hip_pitch_transform)
    return hip_pitch_transform.reshape(-1,1),hip_roll_transform.reshape(-1,1),lf_roll_transform.reshape(-1,1),rf_roll_transform.reshape(-1,1)
        
        
    
    
if __name__ == '__main__':
#    
#    import time
#    start_time = time.time()
    import time
    import pandas as pd
    
    ####READ IN DATA ~ Will change when we call from the database#####
    hip_path = 'C:\\Users\\court\\Desktop\\BioMetrix\\analytics execution\\analytics execution\\team1_Subj3_returnToPlay__anatomicalCalibration.csv'
    feet_path = 'C:\\Users\\court\\Desktop\\BioMetrix\\analytics execution\\analytics execution\\team1_Subj3_returnToPlay__anatomicalCalibration.csv'

    hip_pitch_transform,hip_roll_transform,lf_roll_transform,rf_roll_transform=runSpecialCalib(hip_path,feet_path)
    
    print "My program took", time.time() - start_time, "to run"
    
    hip_full_data = np.genfromtxt(hip_path, dtype=float, delimiter=',', names=True)
    
    hip_pitch_transform,hip_roll_transform = special_hip_calib(hip_full_data)
    
    foot_data=hip_full_data[['LqW','LqX','LqY','LqZ']]
    hip_data=hip_full_data[['HqW','HqX','HqY','HqZ']]
    
    feet_roll_transform = special_feet_calib(foot_data,hip_data,hip_pitch_transform)
    
    
    
#if __name__ == "__main__":
    
#
#    
#    data_path = 'Subject4_rawData.csv'
##    data = pd.read_csv(data_path)
#    start_time = time.time()
#    hip_pitch_transform,hip_roll_transform,lf_roll_transform,rf_roll_transform=runSpecialCalib(hip_path,feet_path)
#    print "My program took", time.time() - start_time, "to run" 