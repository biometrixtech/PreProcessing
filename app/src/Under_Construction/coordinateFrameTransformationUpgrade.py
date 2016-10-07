# -*- coding: utf-8 -*-
"""
Created on Thu Sep 29 12:27:55 2016

@author: court
"""

import numpy as np
import pandas as pd

import quatOps as qo
import quatConvs as qc

import anatomicalCalibrationUpgrade as ac
import accelerationTransformationUpgrade as at


"""
#############################################INPUT/OUTPUT####################################################
Input: csv file containing relevant raw data. Standing calibration and sitting calibration scripts should be run 
        to get relevant _transform values, then those values input appropriately, then will run regular session
        data sets. All raw data is in sensor frame with respect to global frame.
Output: data for orientations in body frame, accelerations in adjusted inertial frame

Conceptual explanations to be given under:
https://sites.google.com/a/biometrixtech.com/wiki/home/preprocessing/anatomical/concepts
#############################################################################################################
"""
def transformData(path):
#### import raw hip and feet data (quaternions only)

    data=pd.read_csv(path)
    hip_data=data[['HqW','HqX','HqY','HqZ']]
    lf_data=data[['LqW','LqX','LqY','LqZ']]
    rf_data=data[['RqW','RqX','RqY','RqZ']]
    hip_acc=data[['HaX','HaY','HaZ']]
    lf_acc=data[['LaX','LaY','LaZ']]
    rf_acc=data[['RaX','RaY','RaZ']]
    timestamp=data[['Time']]
    

    # take hip sensor frame into aif, get all _bf_coordTrans values to get to body frames
    hip_aif,hip_bf_coordTrans,hip_pitch_transform = ac.s2aif(hip_data) # if special hip calibration already done, input hip_pitch_transform as 2nd argument
    lf_bf_coordTrans,lf_roll_transform=ac.feetTrans(lf_data,hip_aif) # if special foot calibration already done, input lf_roll_transform as 3rd argument
    rf_bf_coordTrans,rf_roll_transform=ac.feetTrans(rf_data,hip_aif) # if special foot calibration already done, input rf_roll_transform as 3rd argument
    
    # create storage space for data
    hip_bf=np.zeros((len(hip_aif),4))
    hip_bf_eul=np.zeros((len(hip_aif),3))
    lf_bf=np.zeros((len(hip_aif),4))
    rf_bf=np.zeros((len(hip_aif),4))
    lf_bf_eul=np.zeros((len(hip_aif),3))
    rf_bf_eul=np.zeros((len(hip_aif),3))
    
    # take hip sensor frame and add hip_bf_coordtrans to get hip bf
    for i in range(len(hip_data)):
        hip_bf[i,:]=qo.quat_n(hip_bf[i,:])
        hip_bf[i,:]=qo.quat_prod(hip_data.ix[i,:],hip_bf_coordTrans)
        hip_bf_eul[i,:]=qc.q2eul(hip_bf[i,:])
        
        # take feet_sf and add feet_bf_transform to get feet_bf
        lf_bf[i,:]=qo.quat_n(lf_bf[i,:])
        lf_bf[i,:]=qo.quat_prod(lf_data.ix[i,:],lf_bf_coordTrans)
        rf_bf[i,:]=qo.quat_n(rf_bf[i,:])
        rf_bf[i,:]=qo.quat_prod(rf_data.ix[i,:],rf_bf_coordTrans)
        lf_bf_eul[i,:]=qc.q2eul(lf_bf[i,:])
        rf_bf_eul[i,:]=qc.q2eul(rf_bf[i,:])
        
    # call accelerationTransformation
    hip_acc_aif,lf_acc_aif,rf_acc_aif=at.accelerationTransform(hip_data,lf_data,rf_data,hip_acc,lf_acc,rf_acc,hip_bf_eul,lf_bf_eul,rf_bf_eul)
    
    # consolidate data
    transformed_data = np.zeros((len(data),31))
    transformed_data = timestamp
    transformed_data = np.hstack((transformed_data, lf_acc_aif))
    transformed_data = np.hstack((transformed_data, lf_bf_eul))
    transformed_data = np.hstack((transformed_data, lf_bf))
    transformed_data = np.hstack((transformed_data, hip_acc_aif))
    transformed_data = np.hstack((transformed_data, hip_bf_eul))
    transformed_data = np.hstack((transformed_data, hip_bf))
    transformed_data = np.hstack((transformed_data, rf_acc_aif))
    transformed_data = np.hstack((transformed_data, rf_bf_eul))
    transformed_data = np.hstack((transformed_data, rf_bf))
    
    return transformed_data,hip_bf_coordTrans,lf_roll_transform,rf_roll_transform
    
if __name__ == '__main__':
    ####READ IN DATA ~ Will change when we call from the database#####
    path = 'C:\Users\court\Desktop\BioMetrix\Research\Quaternions\StandingData100Values.csv'
# replace with func name from coordinateFrameTransform script    
    data,hip_pitch_transform,lf_roll_transform,rf_roll_transform = transformData(path)