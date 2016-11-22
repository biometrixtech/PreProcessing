# -*- coding: utf-8 -*-
"""
Created on Sat Oct 01 20:27:33 2016

@author: court
"""

import numpy as np

import quatOps as qo
import quatConvs as qc


"""
#############################################INPUT/OUTPUT######################
Inputs: hip_data, lf_data, rf_data, hip_acc, lf_acc, rf_acc, hip_bf_eul,
        lf_bf_eul, rf_bf_eul
Outputs: hip_acc_aif, lf_acc_aif, rf_acc_aif

Transform acceleration in x, y, and z directions with respect to the
   sensor frame. Convert to the adjusted 
inertial frame.

Script called on by coordinateFrameTransformation.py,
 dependent on quatOps and quatConvs
##########################################################################
"""


def acceleration_transform(hip_data, lf_data, rf_data, hip_acc, lf_acc, rf_acc,
                           hip_bf_eul, lf_bf_eul, rf_bf_eul):
                               
    """ Take raw orientation and acceleration from all sensors,
    plus body frames in terms of euler angles.
    Use orientation data and body frame data to convert acceleration into the 
    adjusted inertial frame.
    """
    
          
#    take hip_bf and use quat_to_euler to get to hip_bf
#    remove pitch and roll to get hip_aif
#    apply vect_rot to get to HaXYZ
#    do same for feet
        
    length = len(hip_data)
    # find hip adjusted inertial frame as isolated yaw from bf orientations
    hip_bf_yaw_offset = np.hstack((np.zeros((length, 2)),
                                   hip_bf_eul[:, 2].reshape(-1, 1)))
    hip_aif = qc.euler_to_quat(hip_bf_yaw_offset)
    
    lf_bf_yaw_offset = np.hstack((np.zeros((length, 2)),
                                  lf_bf_eul[:, 2].reshape(-1, 1)))
    lf_aif = qc.euler_to_quat(lf_bf_yaw_offset)
    
    rf_bf_yaw_offset = np.hstack((np.zeros((length, 2)),
                                  rf_bf_eul[:, 2].reshape(-1, 1)))
    rf_aif = qc.euler_to_quat(rf_bf_yaw_offset)
        
    # calculate instantaneous rotation transform value from sensor to aif
    hip_s2aif_rot = qo.find_rot(hip_data, hip_aif)
    lf_s2aif_rot = qo.find_rot(lf_data, lf_aif)
    rf_s2aif_rot = qo.find_rot(rf_data, rf_aif)
    
    # rotate vector with calculated rotation
    hip_acc_aif = qo.vect_rot(hip_acc, hip_s2aif_rot)
    lf_acc_aif = qo.vect_rot(lf_acc, lf_s2aif_rot)
    rf_acc_aif = qo.vect_rot(rf_acc, rf_s2aif_rot)
    
    # subtract effect of gravity (1G from z axis) and convert from units of G/1000 to m/s**2
    hip_acc_aif = (hip_acc_aif-[0, 0, 1000])*0.00980665
    lf_acc_aif = (lf_acc_aif-[0, 0, 1000])*0.00980665
    rf_acc_aif = (rf_acc_aif-[0, 0, 1000])*0.00980665
    
    return hip_acc_aif, lf_acc_aif, rf_acc_aif
    
    
if __name__ == '__main__':
    ####READ IN DATA ~ Will change when we call from the database#####
    path = 'C:\Users\court\Desktop\BioMetrix\PreProcessing-master\PreProcessing\app\test\data\anatomicalCalibration\Good.csv'
#    data = su.Analytics(path, 0, 0, 100)
#    body = TransformData(data.hipdataset)