# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 11:34:14 2016

@author: court
"""

import numpy as np
import pandas as pd

import quatOps as qo
import quatConvs as qc
import accelerationTransformation as at


"""
#############################################INPUT/OUTPUT####################################################
Input: csv file containing relevant raw data. All raw data is in sensor frame with respect to global frame.
Output: data for orientations in body frame, accelerations in adjusted inertial frame

FIRST: Run special calibration and calibration scripts with relevant data sets.

Conceptual explanations to be given under:
https://sites.google.com/a/biometrixtech.com/wiki/home/preprocessing/anatomical/concepts
#############################################################################################################
"""


def transform_data(data, hip_bf_transform,lf_bf_transform,rf_bf_transform,
                   lf_n_transform,rf_n_transform,hip_n_transform):

    """
    Takes raw data set for full session to transformed coordinate frames.
    Orientation with respect to body frame
    and acceleration data with respect to adjusted inertial frame.
    
    Makes use of global variables set with special calibration and calibration
    scripts.
    
    """
    
    
    # divide data
    hip_quat_db = np.hstack([data.HqW, data.HqX, data.HqY, data.HqZ])
    lf_quat_db = np.hstack([data.LqW, data.LqX, data.LqY, data.LqZ])
    rf_quat_db = np.hstack([data.RqW, data.RqX, data.RqY, data.RqZ])
    hip_acc_db = np.hstack([data.HaX, data.HaY, data.HaZ])
    lf_acc_db=np.hstack([data.LaX, data.LaY, data.LaZ])
    rf_acc_db=np.hstack([data.RaX, data.RaY, data.RaZ])
    epoch_time = np.array(data.epoch_time)
    
    # create storage for vars
    hip_quat=np.empty_like(hip_quat_db)
    lf_quat=np.empty_like(lf_quat_db)
    rf_quat=np.empty_like(rf_quat_db)
    hip_acc=hip_acc_db
    lf_acc=lf_acc_db
    rf_acc=rf_acc_db
    
    # normalize sensor quaternion data
    for i in range(len(hip_quat)):
        hip_quat[i]=qo.quat_norm(hip_quat_db[i].tolist())
        lf_quat[i]=qo.quat_norm(lf_quat_db[i].tolist())
        rf_quat[i]=qo.quat_norm(rf_quat_db[i].tolist())

    # create storage space for bf data
    hip_bf_quat=np.zeros_like(hip_quat)
    hip_bf_eul=np.zeros_like(hip_acc)
    lf_bf_quat=np.zeros_like(lf_quat)
    lf_bf_eul=np.zeros_like(lf_acc)
    rf_bf_quat=np.zeros_like(rf_quat)
    rf_bf_eul=np.zeros_like(rf_acc)
    
    # take hip sensor frame and add hip_bf_coordtrans to get hip bf
    for i in range(len(hip_quat)):
        hip_bf_quat[i]=qo.quat_prod(hip_quat[i],hip_bf_transform)
        hip_bf_eul[i]=qc.quat_to_euler(hip_bf_quat[i])
        
        # take feet_sf and add feet_bf_transform to get feet_bf
        lf_bf_quat[i]=qo.quat_prod(lf_quat[i],lf_bf_transform)
        lf_bf_eul[i]=qc.quat_to_euler(lf_bf_quat[i])
        rf_bf_quat[i]=qo.quat_prod(rf_quat[i],rf_bf_transform)
        rf_bf_eul[i]=qc.quat_to_euler(rf_bf_quat[i])
        
    # call accelerationTransformation
    hip_aif_acc,lf_aif_acc,rf_aif_acc=\
            at.acceleration_transform(hip_quat,lf_quat,rf_quat,hip_acc,lf_acc,
                                      rf_acc,hip_bf_eul,lf_bf_eul,rf_bf_eul)
    
    # convert body frame quaternions to respective "neutral" orientations
    #for comparison in balanceCME, operated through runAnalytics
    lf_neutral=np.empty_like(hip_quat)
    hip_neutral=np.empty_like(hip_quat)
    hip_bf_yaw=np.empty((len(hip_quat),1))
    hip_yaw_quat=np.empty_like(hip_quat)
    rf_neutral=np.empty_like(hip_quat)
    
    for i in range(len(hip_quat)):
        lf_neutral[i]=qo.quat_prod(lf_bf_quat[i],lf_n_transform)
        hip_bf_yaw[i]=qc.quat_to_euler(hip_bf_quat[i])[2]
        hip_yaw_quat[i]=tuple(qc.euler_to_quat(0,0,hip_bf_yaw[i].item()))
        hip_neutral[i]=qo.quat_prod(hip_yaw_quat[i],hip_n_transform)
        rf_neutral[i]=qo.quat_prod(rf_bf_quat[i],rf_n_transform)
    
    # consolidate transformed data
    epoch_time_pd = pd.DataFrame(epoch_time)
    lf_aif_acc_pd = pd.DataFrame(lf_aif_acc)
    lf_bf_eul_pd = pd.DataFrame(lf_bf_eul)
    lf_bf_quat_pd = pd.DataFrame(lf_bf_quat)
    
    hip_aif_acc_pd = pd.DataFrame(hip_aif_acc)
    hip_bf_eul_pd = pd.DataFrame(hip_bf_eul)
    hip_bf_quat_pd = pd.DataFrame(hip_bf_quat)

    rf_aif_acc_pd = pd.DataFrame(rf_aif_acc)
    rf_bf_eul_pd = pd.DataFrame(rf_bf_eul)
    rf_bf_quat_pd = pd.DataFrame(rf_bf_quat)
    
    frames_transformed = [epoch_time_pd, lf_aif_acc_pd, lf_bf_eul_pd,
                          lf_bf_quat_pd,hip_aif_acc_pd,hip_bf_eul_pd,
                          hip_bf_quat_pd,rf_aif_acc_pd, rf_bf_eul_pd,
                          rf_bf_quat_pd]
    transformed_pd = pd.concat(frames_transformed, axis=1)
    transformed_data = transformed_pd.values
    
    # consolidate neutral data
    lf_neutral_pd = pd.DataFrame(lf_neutral)
    hip_neutral_pd = pd.DataFrame(hip_neutral)
    rf_neutral_pd = pd.DataFrame(rf_neutral)
    
    frames_neutral = [lf_neutral_pd,hip_neutral_pd,rf_neutral_pd]
    neutral_pd = pd.concat(frames_neutral, axis=1)
    neutral_data = neutral_pd.values
    
    return transformed_data,neutral_data

    
if __name__ == '__main__':
    
    
    import time
    start_time = time.time()
    ####READ IN DATA ~ Will change when we call from the database#####
    path = 'C:\Users\court\Desktop\BioMetrix\Research\Quaternions\Subject2_rawData.csv'
# replace with func name from coordinateFrameTransform script    
    data,neut_data= transformData(path,hip_bf_coordTrans,lf_bf_coordTrans,rf_bf_coordTrans)
     
     
    np.savetxt("Subject2_Transformed_Data.csv",data, delimiter=",")
#    np.savetxt("Subject2_Neutral_Data.csv",neut_data, delimiter=",")
    
    
    print "My program took", time.time() - start_time, "to run"