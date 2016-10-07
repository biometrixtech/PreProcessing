# -*- coding: utf-8 -*-
"""
Created on Thu Sep 29 09:35:15 2016

@author: court
"""

import numpy as np

import quatOps as qo
import quatConvs as qc

#import setUp as su
#import dataObject as do
import specialFeetCalibration as fc


"""
#############################################INPUT/OUTPUT####################################################
Inputs: raw orientation data, transform values if available (calculated here if 'special' calibration)
Outputs: transform values to convert raw data directly to the body frame, hip_pitch_transform and
        feet_roll_transform for later processing as pelvic tilt and pronation trends
        
Hip: takes raw data, converts to adjusted sensor frame by rotating frame to align roughly with body forward x,
        against gravity positive z. If pitch_transform not given, calculates it as the pitch necessary to get
        x axis parallel with ground. These offsets combined to give hip_bf_coordTrans, which takes raw data
        directly to body frame. Adjusted inertial frame taken as ASF without pitch component. AIF and transform
        numbers yielded.
        
Feet: takes raw feet data, hip_aif, feet_roll_transform if available. feet_yaw_transform is offset between feet
        and hip_aif over standing calibration. If feet_roll_transform not available, calculates from special 
        sitting calibration. Transforms combined as feet_bf_coordTrans, which takes raw data immediately to 
        feet body frame.
Script called upon by coordinateFrameTransformationUpgrade.py, dependent on specialFeetCalibration.py, QuatOps,
quatConvs
#############################################################################################################
"""

def s2aif(hip_data,hip_pitch_transform=None):
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
        
        # Fill gaps in sensor data with value from previous measurement
#        for k in range(len(hip_data.ix[i,:])):
#            if hip_data.ix[i,k]==[]:
#                if i==0:
#                    a=hip_data.ix[i+1,k]
#                else:
#                    a=hip_data.ix[i-1,k]
#                hip_data.ix[i,k]=a
        
        hip_asf[i,:] = qo.quat_prod(hip_data.ix[i,:],hip_asf_coordTrans) #.reshape(1,4)

    #### If loop: If hip_pitch_t does not exist (special cal), pull out pitch from hip_asf
        # if hip_pitch_t does exist (regular cal), use pre-existing val
        # take pitch away from hip_asf to get to hip_aif

    # if not hip_pitch_transform == True: # if hip_pitch_transform is empty, calc during spec cal
    if hip_pitch_transform is None: # if hip_pitch_transform is empty, calc during spec cal

        hip_pitch_transform_inst=np.zeros((len(hip_asf),4))
        for i in range(len(hip_asf)):
            hip_asf_eX,hip_asf_eY,hip_asf_eZ = qc.q2eul(hip_asf[i,:])
            hip_pitch_transform_inst[i,:] = qc.eul2q(0,hip_asf_eY,0) # create offset quaternion using only pitch offset

        # GET AVERAGE OF HIP_PITCH_TRANSFORM dATA OVER RECORDING PERIOD
        hip_pitch_transform = qo.quat_n(qo.quat_avg(hip_pitch_transform_inst))

    else:
        pass

    # calculate hip_bf_coordTrans to get from sf to corrected bf
    hip_bf_coordTrans = qo.quat_prod(hip_asf_coordTrans,hip_pitch_transform)

    # use hip_pitch_transform to get from hip_asf to hip_aif (rotation about y axis)
    hip_pitch_transform_conj=qo.quat_conj(hip_pitch_transform)

    hip_aif=np.zeros((len(hip_asf),4))
    for i in range(len(hip_asf)):
        hip_aif[i,:] = qo.quat_prod(hip_asf[i,:],hip_pitch_transform_conj)

    return hip_aif,hip_bf_coordTrans,hip_pitch_transform

def feetTrans(footdata,hip_aif,feet_roll_transform=None):    

    # Extract feet_yaw_t
    feet_asf=np.zeros((len(footdata),4))
    feet_asf_components=np.zeros((len(footdata),3))
    feet_yaw_transform_inst=np.zeros((len(footdata),4))
    for i in range(len(hip_aif)):  
        feet_asf[i,:] = qo.find_rot(hip_aif[i,:],footdata.ix[i,:])
        feet_asf_components[i,:] = qc.q2eul(feet_asf[i,:])   
        feet_yaw_transform_inst[i,:] = qc.eul2q(0,0,feet_asf_components[i,0]) # create offset quaternion using only yaw offset
    
    # GET AVERAGE OF FEET_YAW_TRANSFORM_INST DATA OVER RECORDING PERIOD
    feet_yaw_transform = qo.quat_avg(feet_yaw_transform_inst)
        
    #### If loop: If feet_roll_transform exists, calculate feet_bf_coordtrans
       # else, do special feet_roll_transform
    
    if feet_roll_transform is None:
    # GO TO SPECIAL FEET CALIBRATION
        feet_roll_transform = fc.sittingFeetCal(footdata,feet_yaw_transform)
    else:
        pass
    
    #### calculate feet_bf_coordTrans
    feet_bf_coordTrans = qo.quat_prod(feet_yaw_transform,feet_roll_transform)
        
    return feet_bf_coordTrans,feet_roll_transform




if __name__ == '__main__':
    ####READ IN DATA ~ Will change when we call from the database#####
    path = 'C:\Users\court\Desktop\BioMetrix\PreProcessing-master\PreProcessing\app\test\data\anatomicalCalibration\Good.csv'
#    data = su.Analytics(path, 0, 0, 100)
#    body = TransformData(data.hipdataset)