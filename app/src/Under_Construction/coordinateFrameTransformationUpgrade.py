# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 11:34:14 2016

@author: court
"""

import numpy as np
import pandas as pd

import quatOps as qo
import quatConvs as qc

import accelerationTransformationUpgrade as at


"""
#############################################INPUT/OUTPUT####################################################
Input: csv file containing relevant raw data. All raw data is in sensor frame with respect to global frame.
Output: data for orientations in body frame, accelerations in adjusted inertial frame

FIRST: Run special calibration and calibration scripts with relevant data sets.

Conceptual explanations to be given under:
https://sites.google.com/a/biometrixtech.com/wiki/home/preprocessing/anatomical/concepts
#############################################################################################################
"""
def transformData(path):

    """
    Takes raw data set for full session to transformed coordinate frames. Orientation with respect to body frame
    and acceleration data with respect to adjusted inertial frame.
    
    Makes use of global variables set with special calibration and calibration scripts.
    
    """

    # import raw hip and feet data (quaternions only)
    data=pd.read_csv(path)
    hip_datadb=data[['HqW','HqX','HqY','HqZ']]
    lf_datadb=data[['LqW','LqX','LqY','LqZ']]
    rf_datadb=data[['RqW','RqX','RqY','RqZ']]
    hip_accdb=data[['HaX','HaY','HaZ']]
    lf_accdb=data[['LaX','LaY','LaZ']]
    rf_accdb=data[['RaX','RaY','RaZ']]
    timestamp=data[['Timestamp']]
    
    # create storage for vars
    hip_data=np.empty((len(hip_datadb),4))
    lf_data=np.empty((len(lf_datadb),4))
    rf_data=np.empty((len(rf_datadb),4))
    hip_acc=np.empty((len(hip_accdb),3))
    lf_acc=np.empty((len(lf_accdb),3))
    rf_acc=np.empty((len(rf_accdb),3))
    
    for i in range(len(hip_data)):
        hip_data[i,:]=qo.quat_n(hip_datadb.ix[i,:])
        lf_data[i,:]=qo.quat_n(lf_datadb.ix[i,:])
        rf_data[i,:]=qo.quat_n(rf_datadb.ix[i,:])
        hip_acc[i,:]=hip_accdb.ix[i,:]
        lf_acc[i,:]=lf_accdb.ix[i,:]
        rf_acc[i,:]=rf_accdb.ix[i,:]
    
    # create storage space for data
    hip_bf=np.zeros((len(hip_data),4))
    hip_bf_eul=np.zeros((len(hip_data),3))
    lf_bf=np.zeros((len(hip_data),4))
    rf_bf=np.zeros((len(hip_data),4))
    lf_bf_eul=np.zeros((len(hip_data),3))
    rf_bf_eul=np.zeros((len(hip_data),3))
    
    # take hip sensor frame and add hip_bf_coordtrans to get hip bf
    for i in range(len(hip_data)):
#        hip_bf[i,:]=qo.quat_n(hip_bf[i,:])
        hip_bf[i,:]=qo.quat_prod(hip_data[i,:],hip_bf_coordTrans)
        hip_bf_eul[i,:]=qc.q2eul(hip_bf[i,:])
        
        # take feet_sf and add feet_bf_transform to get feet_bf
#        lf_bf[i,:]=qo.quat_n(lf_bf[i,:])
        lf_bf[i,:]=qo.quat_prod(lf_data[i,:],lf_bf_coordTrans)
#        rf_bf[i,:]=qo.quat_n(rf_bf[i,:])
        rf_bf[i,:]=qo.quat_prod(rf_data[i,:],rf_bf_coordTrans)
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
    
    return transformed_data
    
if __name__ == '__main__':
    
    
    import time
    start_time = time.time()
    ####READ IN DATA ~ Will change when we call from the database#####
    path = 'C:\Users\court\Desktop\BioMetrix\Research\Quaternions\Subject6_rawData.csv'
# replace with func name from coordinateFrameTransform script    
    data= transformData(path)
     
     
np.savetxt("Subject_6_Sensor_Transformed_Data.csv",data, delimiter=",")
    
    print "My program took", time.time() - start_time, "to run"
