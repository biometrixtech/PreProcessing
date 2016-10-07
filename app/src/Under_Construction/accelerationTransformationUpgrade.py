# -*- coding: utf-8 -*-
"""
Created on Sat Oct 01 20:27:33 2016

@author: court
"""


import numpy as np

import quatOps as qo
import quatConvs as qc

#import setUp as su
#import dataObject as do
import coordinateFrameTransformationUpgrade as ft


"""
#############################################INPUT/OUTPUT####################################################
Inputs: hip_data,lf_data,rf_data,hip_acc,lf_acc,rf_acc,hip_bf_eul,lf_bf_eul,rf_bf_eul
Outputs: hip_acc_aif,lf_acc_aif,rf_acc_aif

Transform acceleration in x, y, and z directions with respect to the sensor frame. Convert to the adjusted 
inertial frame.
Script called on by coordinateFrameTransformationUpgrade.py, dependent on quatOps and quatConvs
#############################################################################################################
"""

def accelerationTransform(hip_data,lf_data,rf_data,hip_acc,lf_acc,rf_acc,hip_bf_eul,lf_bf_eul,rf_bf_eul):
    """ Take raw orientation and acceleration from all sensors, plus body frames in terms of euler angles.
    Use orientation data and body frame data to convert acceleration into the adjusted inertial frame.
    """
    # Create storage for data
    hip_aif=np.zeros((len(hip_acc),4))
    lf_aif=np.zeros((len(rf_acc),4))
    rf_aif=np.zeros((len(rf_acc),4))
    hip_s2aif_rot=np.zeros((len(hip_acc),4))
    lf_s2aif_rot=np.zeros((len(lf_acc),4))
    rf_s2aif_rot=np.zeros((len(rf_acc),4))
    hip_acc_aif=np.zeros((len(hip_acc),3))
    lf_acc_aif=np.zeros((len(lf_acc),3))
    rf_acc_aif=np.zeros((len(rf_acc),3))
    
    for i in range(len(hip_acc)):
            
        """take hip_bf and use q2eul to get to hip_bf
        remove pitch and roll to get hip_aif
        apply vect_rot to get to HaXYZ
        
        do same for feet"""
        
        # find hip adjusted inertial frame as isolated yaw from bf orientations
        hip_aif[i,:]=qc.eul2q(0,0,hip_bf_eul[i,2])
        lf_aif[i,:]=qc.eul2q(0,0,lf_bf_eul[i,2])
        rf_aif[i,:]=qc.eul2q(0,0,rf_bf_eul[i,2])
        
        # calculate instantaneous rotation transform value from sensor to aif
        hip_s2aif_rot[i,:]=qo.find_rot(hip_data.ix[i,:],hip_aif[i,:])
        lf_s2aif_rot[i,:]=qo.find_rot(lf_data.ix[i,:],lf_aif[i,:])
        rf_s2aif_rot[i,:]=qo.find_rot(rf_data.ix[i,:],rf_aif[i,:])
        
        # rotate vector with calculated rotation
        hip_acc_aif[i,:]=qo.vect_rot(hip_acc.ix[i,:],hip_s2aif_rot[i,:])
        lf_acc_aif[i,:]=qo.vect_rot(lf_acc.ix[i,:],lf_s2aif_rot[i,:])
        rf_acc_aif[i,:]=qo.vect_rot(rf_acc.ix[i,:],rf_s2aif_rot[i,:])
        
        # subtract effect of gravity (1G from z axis) and convert from units of G/1000 to m/s**2
        hip_acc_aif[i,:]=(hip_acc_aif[i,:]-[0,0,1000])*0.00980665
        lf_acc_aif[i,:]=(lf_acc_aif[i,:]-[0,0,1000])*0.00980665
        rf_acc_aif[i,:]=(rf_acc_aif[i,:]-[0,0,1000])*0.00980665
    
    return hip_acc_aif,lf_acc_aif,rf_acc_aif
    
    
if __name__ == '__main__':
    ####READ IN DATA ~ Will change when we call from the database#####
    path = 'C:\Users\court\Desktop\BioMetrix\PreProcessing-master\PreProcessing\app\test\data\anatomicalCalibration\Good.csv'
#    data = su.Analytics(path, 0, 0, 100)
#    body = TransformData(data.hipdataset)