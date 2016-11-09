# -*- coding: utf-8 -*-
"""
Created on Sat Oct 01 20:27:33 2016

@author: court
"""

import numpy as np

import quatOps as qo
import quatConvs as qc


"""
#############################################INPUT/OUTPUT####################################################
Inputs: hip_data,lf_data,rf_data,hip_acc,lf_acc,rf_acc,hip_bf_eul,lf_bf_eul,rf_bf_eul
Outputs: hip_acc_aif,lf_acc_aif,rf_acc_aif

Transform acceleration in x, y, and z directions with respect to the sensor frame. Convert to the adjusted 
inertial frame.

Script called on by coordinateFrameTransformationUpgrade.py, dependent on quatOps and quatConvs
#############################################################################################################
"""


def acceleration_transform(hip_data,lf_data,rf_data,hip_acc,lf_acc,rf_acc,
                           hip_bf_eul,lf_bf_eul,rf_bf_eul):
                               
    """ Take raw orientation and acceleration from all sensors,
    plus body frames in terms of euler angles.
    Use orientation data and body frame data to convert acceleration into the 
    adjusted inertial frame.
    """
    
    # Create storage for data
    hip_aif=np.zeros_like(hip_data)
    lf_aif=np.zeros_like(rf_data)
    rf_aif=np.zeros_like(rf_data)
    hip_s2aif_rot=np.zeros_like(hip_data)
    lf_s2aif_rot=np.zeros_like(lf_data)
    rf_s2aif_rot=np.zeros_like(rf_data)
    hip_acc_aif=np.zeros_like(hip_acc)
    lf_acc_aif=np.zeros_like(lf_acc)
    rf_acc_aif=np.zeros_like(rf_acc)
    
    for i in range(len(hip_acc)):            
        #take hip_bf and use q2eul to get to hip_bf
        #remove pitch and roll to get hip_aif
        #apply vect_rot to get to HaXYZ
        #do same for feet
        
        # find hip adjusted inertial frame as isolated yaw from bf orientations
        hip_aif[i]=tuple(qc.euler_to_quat(0,0,hip_bf_eul[i][2]))
        lf_aif[i]=tuple(qc.euler_to_quat(0,0,lf_bf_eul[i][2]))
        rf_aif[i]=tuple(qc.euler_to_quat(0,0,rf_bf_eul[i][2]))
        
        # calculate instantaneous rotation transform value from sensor to aif
        hip_s2aif_rot[i]=tuple(qo.find_rot(hip_data[i],hip_aif[i]))
        lf_s2aif_rot[i]=tuple(qo.find_rot(lf_data[i],lf_aif[i]))
        rf_s2aif_rot[i]=tuple(qo.find_rot(rf_data[i],rf_aif[i]))
        
        # rotate vector with calculated rotation
        hip_acc_aif[i]=tuple(qo.vect_rot(hip_acc[i],hip_s2aif_rot[i]))
        lf_acc_aif[i]=tuple(qo.vect_rot(lf_acc[i],lf_s2aif_rot[i]))
        rf_acc_aif[i]=tuple(qo.vect_rot(rf_acc[i],rf_s2aif_rot[i]))
        
        # subtract effect of gravity (1G from z axis) and convert from units of G/1000 to m/s**2
        hip_acc_aif[i]=(np.array(hip_acc_aif[i].tolist())-[0,0,1000])*0.00980665
        lf_acc_aif[i]=(np.array(lf_acc_aif[i].tolist())-[0,0,1000])*0.00980665
        rf_acc_aif[i]=(np.array(rf_acc_aif[i].tolist())-[0,0,1000])*0.00980665
    
    return hip_acc_aif,lf_acc_aif,rf_acc_aif
    
    
if __name__ == '__main__':
    ####READ IN DATA ~ Will change when we call from the database#####
    path = 'C:\Users\court\Desktop\BioMetrix\PreProcessing-master\PreProcessing\app\test\data\anatomicalCalibration\Good.csv'
#    data = su.Analytics(path, 0, 0, 100)
#    body = TransformData(data.hipdataset)