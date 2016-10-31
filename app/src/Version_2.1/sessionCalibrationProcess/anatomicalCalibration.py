# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 09:21:40 2016

@author: court
"""


import numpy as np

import quatOps as qo
import quatConvs as qc
from errors import ErrorId

"""
#############################################INPUT/OUTPUT####################################################
Inputs: raw orientation data for regular calibration
Outputs: _bf_transform to allow for direct calculation of body frame from sensor frame for full data sets. Also,
        _n_transform values to take body frame data to neutral position for use in CME analytics. 
        
Pay attention to sensor model and orientation.

Script called upon by coordinateFrameTransformationUpgrade.py, dependent on specialFeetCalibration.py, QuatOps,
quatConvs
#############################################################################################################
"""

   
def placement_check(left_acc,hip_acc,right_acc):
    
    """Perform quick check of sensor placement based on raw acceleration values, 
    relevant for beta test designs.
    
    Args:
        raw acceleration values for three sensors, each comprised of x, y, 
        and z components (9 components total).
    
    Returns: 
        Booleans representing placement and movement errors:
            bad_left_placement
            bad_hip_placement
            bad_right_placement
            moving
    
    """    
    # find mean acceleration values across time
    _left_mean=np.nanmean(left_acc,0)
    _hip_mean=np.nanmean(hip_acc,0)
    _right_mean=np.nanmean(right_acc,0)
    
    # find the maximum acceleration value experienced by each sensor
    _left_max=np.nanmax(left_acc)
    _hip_max=np.nanmax(hip_acc)
    _right_max=np.nanmax(right_acc)
    
    # left x should be pos and y should be neg
    if _left_mean[0]>200 and _left_mean[1]<-200 and np.absolute(_left_mean[2])<200:
        bad_left_placement=False
    else:
        bad_left_placement=True
        
    # hip y should be very neg and other axes minimally affected by grav
    if np.absolute(_hip_mean[0])<200 and _hip_mean[1]<-800 and np.absolute(_hip_mean[2])<200:
        bad_hip_placement=False
    else:
        bad_hip_placement=True
        
    # right x should be eg and y should be neg
    if _right_mean[0]<-200 and _right_mean[1]<-200 and np.absolute(_right_mean[2])<200:
        bad_right_placement=False
    else:
        bad_right_placement=True

    # magnitude of maximum acceleration should always be less than 2 Gs
    if _left_max>2000 or _hip_max>2000 or _right_max>2000:
        moving=True
    else:
        moving=False
        
    if bad_hip_placement and bad_left_placement and bad_right_placement:
        ind = ErrorId.all_sensors.value
    elif bad_hip_placement and bad_left_placement:
        ind = ErrorId.hip_left.value
    elif bad_hip_placement and bad_right_placement:
        ind = ErrorId.hip_right.value
    elif bad_hip_placement:
        ind = ErrorId.hip.value
    elif bad_left_placement and bad_right_placement:
        ind = ErrorId.left_right.value
    elif bad_left_placement:
        ind = ErrorId.left.value
    elif bad_right_placement:
        ind = ErrorId.right.value
    elif moving:
        ind = ErrorId.movement.value
    else:
        ind = ErrorId.no_error.value
        
    return ind
    

def _sensor_to_aif(hip_data,hip_pitch_transform,hip_roll_transform):
    
    """
    Use hip sensor frame and transform values from special calibration session
    to find the adjusted inertial frame during calibration. Also, find value
    by which all hip sensor data can be multiplied by in order to put it into
    the body frame (hip_bf_transform)
    
    Args: raw hip data and the hip_pitch_ and hip_roll_ transforms, as 
    calculated during special calibration.
    
    Returns: hip data in the adjusted inertial frame, hip_bf_transform
    
    """
    
    # TODO(Courtney): incorporate bow into calculation of HIP_ASF_TRANSFORM 
    # rotation from sensor frame to adjusted sensor frame 
#    HIP_ASF_TRANSFORM = qo.quat_prod([0.70710678,0.70710678,0,0],
#                                      [0.70710678,0,0,0.70710678]) # FOR OLD SENSORS RUNNING SIDE TO SIDE (sensor on right)
#    HIP_ASF_TRANSFORM = [0.70710678,0,-0.70710678,0]  # FOR OLD SENSORS RUNNING UP AND DOWN: -90 degrees about y axis
    HIP_ASF_TRANSFORM = qo.quat_prod([0.707106781186548,0,0.707106781186548,0],
                                      [0.707106781186548,0.707106781186548,0,0]) # FOR NEW SENSORS: 90 deg about y axis, -90 deg about x axis
    
    # create storage for values and calculate adjusted sensor frame
    hip_asf=np.zeros((len(hip_data),4))

    for i in range(len(hip_data)):
       
        hip_asf[i,:] = qo.quat_prod(hip_data[i,:],HIP_ASF_TRANSFORM)
        
    # calculate hip_bf_transform to get from sf to corrected bf
    hip_bf_transform = qo.quat_prod(HIP_ASF_TRANSFORM,hip_pitch_transform)

    # use hip_pitch_transform to get from hip_asf to hip_aif (rotation about y axis)
    hip_pitch_transform_conj=qo.quat_conj(hip_pitch_transform)
    
    # create storage for values and calculate adjusted inertial frame
    hip_aif=np.zeros((len(hip_asf),4))
    
    for i in range(len(hip_asf)):
        
        hip_aif[i,:] = qo.quat_prod(hip_asf[i,:],hip_pitch_transform_conj)

    return hip_aif,hip_bf_transform
    

def _feet_transform_calculations(foot_data,hip_aif,foot_roll_transform): 
    
    """Function to calculate transform values for a foot.
    
    Args:
        foot orientation data, adjusted inertial frame data taken from the hips
        during regular calibration, and foot_roll_transform value calculated
        during special feet calibration.
        
    Returns:
        foot_bf_transform, foot_yaw_transform, and foot_pitch_trasnform
        
    """

    # Create storage for values
    foot_asf=np.zeros((len(foot_data),4))
    foot_asf_components=np.zeros((len(foot_data),3))
    foot_yaw_transform_inst=np.zeros((len(foot_data),4))
    foot_pitch_transform_inst=np.zeros((len(foot_data),4))
    
    # Extract feet_yaw_t for ft trans and feet_pitch_t for balanceCME
    for i in range(len(hip_aif)):  
        
        foot_asf[i,:] = qo.find_rot(hip_aif[i,:],foot_data[i,:])
        foot_asf_components[i,:] = qc.quat_to_euler(foot_asf[i,:])   
        foot_yaw_transform_inst[i,:] = qc.quat_to_euler(0,0,foot_asf_components[i,2]) # create offset using yaw
        foot_pitch_transform_inst[i,:] = qc.quat_to_euler(0,foot_asf_components[i,1],0) # create offset using pitch
    
    # average transform values over recording periods
    foot_yaw_transform = qo.quat_avg(foot_yaw_transform_inst)
    foot_pitch_transform = qo.quat_avg(foot_pitch_transform_inst)
        
    # calculate feet_bf_transform
    foot_bf_transform = qo.quat_prod(foot_yaw_transform,foot_roll_transform)
    
    return foot_bf_transform,foot_yaw_transform,foot_pitch_transform


def run_calib(data,hip_pitch_transform,hip_roll_transform,
             lf_roll_transform,rf_roll_transform):
    
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
    hip_datadb = np.array([data['HqW'], data['HqX'], data['HqY'], data['HqZ']]).transpose() 
    lf_datadb = np.array([data['LqW'], data['LqX'], data['LqY'], data['LqZ']]).transpose() 
    rf_datadb = np.array([data['RqW'], data['RqX'], data['RqY'], data['RqZ']]).transpose() 
    
    # create storage for vars
    hip_data=np.empty_like(hip_datadb)
    lf_data=np.empty_like(lf_datadb)
    rf_data=np.empty_like(rf_datadb)
    
    # normalize orientation data
    for i in range(len(hip_data)):
        hip_data[i]=qo.quat_norm(hip_datadb[i].tolist())
        lf_data[i]=qo.quat_norm(lf_datadb[i].tolist())
        rf_data[i]=qo.quat_norm(rf_datadb[i].tolist())

    # take hip sensor frame into aif, get all _bf_transform values to get to body frames
    hip_aif,hip_bf_transform=_sensor_to_aif(hip_data,hip_pitch_transform,hip_roll_transform)
    lf_bf_transform,lf_yaw_transform,lf_pitch_transform=_feet_transform_calculations(lf_data,hip_aif,lf_roll_transform)
    rf_bf_transform,rf_yaw_transform,rf_pitch_transform=_feet_transform_calculations(rf_data,hip_aif,rf_roll_transform)

    # calculate _neutral_transform values
    lf_n_transform=qo.quat_prod(qo.quat_conj(hip_pitch_transform),lf_yaw_transform)
    lf_n_transform=qo.quat_prod(lf_n_transform,lf_pitch_transform)
    lf_n_transform=qo.quat_prod(lf_n_transform,lf_roll_transform)
    rf_n_transform=qo.quat_prod(qo.quat_conj(hip_pitch_transform),rf_yaw_transform)
    rf_n_transform=qo.quat_prod(rf_n_transform,rf_pitch_transform)
    rf_n_transform=qo.quat_prod(rf_n_transform,rf_roll_transform)
    hip_n_transform=qo.quat_prod(hip_pitch_transform,hip_roll_transform)
    
    return hip_bf_transform.reshape(-1,1),lf_bf_transform.reshape(-1,1),rf_bf_transform.reshape(-1,1),lf_n_transform.reshape(-1,1),rf_n_transform.reshape(-1,1),hip_n_transform.reshape(-1,1)
    
        
if __name__ == '__main__':
    
    import time
    start_time = time.time()
    
    ####READ IN DATA ~ Will change when we call from the database#####
    path = 'C:\Users\court\Desktop\BioMetrix\Research\Quaternions\Subject4_sd.csv'

    hip_bf_transform,lf_bf_transform,rf_bf_transform,lf_n_transform,rf_n_transform,hip_n_transform=runCalib(path)
    
    print "My program took", time.time() - start_time, "to run"