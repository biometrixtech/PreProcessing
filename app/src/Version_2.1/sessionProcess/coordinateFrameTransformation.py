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
#############################################INPUT/OUTPUT######################
Input: csv file containing relevant raw data. All raw data is in sensor frame
with respect to global frame.
Output: data for orientations in body frame, accelerations in adjusted
        inertial frame

FIRST: Run special calibration and calibration scripts with relevant data sets.

Conceptual explanations to be given under:
https://sites.google.com/a/biometrixtech.com/wiki/home/preprocessing/
anatomical/concepts
##############################################################################
"""


def transform_data(data, hip_bf_transform, lf_bf_transform, rf_bf_transform,
                   lf_n_transform, rf_n_transform, hip_n_transform):

    """
    Takes raw data set for full session to transformed coordinate frames.
    Orientation with respect to body frame
    and acceleration data with respect to adjusted inertial frame.
    
    Makes use of global variables set with special calibration and calibration
    scripts.
    
    """
    hip_bf_transform = hip_bf_transform.reshape(1, -1)
    lf_bf_transform = lf_bf_transform.reshape(1, -1)
    rf_bf_transform = rf_bf_transform.reshape(1, -1)
    lf_n_transform = lf_n_transform.reshape(1, -1)
    rf_n_transform = rf_n_transform.reshape(1, -1)
    hip_n_transform = hip_n_transform.reshape(1, -1)
    
    # divide data
    hip_quat_db = np.hstack([data.HqW, data.HqX, data.HqY,
                             data.HqZ]).reshape(-1, 4)
    lf_quat_db = np.hstack([data.LqW, data.LqX, data.LqY,
                            data.LqZ]).reshape(-1, 4)
    rf_quat_db = np.hstack([data.RqW, data.RqX, data.RqY,
                            data.RqZ]).reshape(-1, 4)
    hip_acc = np.hstack([data.HaX, data.HaY, data.HaZ]).reshape(-1, 3)
    lf_acc = np.hstack([data.LaX, data.LaY, data.LaZ]).reshape(-1, 3)
    rf_acc = np.hstack([data.RaX, data.RaY, data.RaZ]).reshape(-1, 3)
    epoch_time = np.array(data.epoch_time).reshape(-1, 1)
    
    
    # normalize sensor quaternion data
    hip_quat = qo.quat_norm(hip_quat_db)
    lf_quat = qo.quat_norm(lf_quat_db)
    rf_quat = qo.quat_norm(rf_quat_db)

    length = len(hip_quat)

    # take hip sensor frame and add hip_bf_coordtrans to get hip bf

    hip_bf_quat = qo.quat_prod(hip_quat, hip_bf_transform)
    hip_bf_eul = qc.quat_to_euler(hip_bf_quat)

    # take feet_sf and add feet_bf_transform to get feet_bf, divide into
        # axial components
    lf_bf_quat = qo.quat_prod(lf_quat, lf_bf_transform)
    lf_bf_eul = qc.quat_to_euler(lf_bf_quat)
    lf_bf_yaw = np.hstack((np.zeros((length, 2)),
                           lf_bf_eul[:, 2].reshape(-1, 1)))
    lf_bf_yaw = qc.euler_to_quat(lf_bf_yaw)
    rf_bf_quat = qo.quat_prod(rf_quat, rf_bf_transform)
    rf_bf_eul = qc.quat_to_euler(rf_bf_quat)
    rf_bf_yaw = np.hstack((np.zeros((length, 2)),
                           rf_bf_eul[:, 2].reshape(-1, 1)))
    rf_bf_yaw = qc.euler_to_quat(rf_bf_yaw)

    # call accelerationTransformation
    hip_aif_acc, lf_aif_acc, rf_aif_acc =\
            at.acceleration_transform(hip_quat, lf_quat, rf_quat, hip_acc,
                                      lf_acc, rf_acc, hip_bf_eul, lf_bf_eul,
                                      rf_bf_eul)
    
    # convert body frame quaternions to respective "neutral" orientations
    #for comparison in balanceCME, operated through runAnalytics
    lf_n_transform = qc.quat_to_euler(lf_n_transform)
    rf_n_transform = qc.quat_to_euler(rf_n_transform)
    hip_n_transform_eul = qc.quat_to_euler(hip_n_transform)
    lf_n_roll = np.full((length, 1), lf_n_transform[0, 0], float)
    rf_n_roll = np.full((length, 1), rf_n_transform[0, 0], float)
    lf_n_pitch = np.full((length, 1), lf_n_transform[0, 1], float)
    rf_n_pitch = np.full((length, 1), rf_n_transform[0, 1], float)
    lf_n_yaw = np.full((length, 1), lf_n_transform[0, 2], float)
    rf_n_yaw = np.full((length, 1), rf_n_transform[0, 2], float)
    hip_n_roll =  np.full((length, 1), hip_n_transform_eul[0, 0], float)
    hip_n_pitch = np.full((length, 1), hip_n_transform_eul[0, 1], float)

    rot_y = np.array([[np.sqrt(.5), 0, np.sqrt(.5), 0]])
    rot_x = np.array([[np.sqrt(.5), np.sqrt(.5), 0, 0]])
    # FOR NEW SENSORS: 90 deg about y axis, -90 deg about x axis
    hip_asf_transform = qo.quat_prod(rot_y, rot_x)

    # calculate adjusted sensor frame
    hip_asf = qo.quat_prod(hip_quat, hip_asf_transform)

    hip_aif_comp = qc.quat_to_euler(hip_asf)[:, 2].reshape(-1, 1)

    # construct neutral hip data
    hip_neutral = np.hstack((hip_n_roll, hip_n_pitch, hip_aif_comp))
    
    lf_neutral = np.hstack((lf_n_roll, lf_n_pitch, lf_n_yaw))
    rf_neutral = np.hstack((rf_n_roll, rf_n_pitch, rf_n_yaw))

    hip_neutral = qc.euler_to_quat(hip_neutral)
    lf_neutral = qc.euler_to_quat(lf_neutral)
    rf_neutral = qc.euler_to_quat(rf_neutral)
    
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
                          lf_bf_quat_pd, hip_aif_acc_pd, hip_bf_eul_pd,
                          hip_bf_quat_pd, rf_aif_acc_pd, rf_bf_eul_pd,
                          rf_bf_quat_pd]
    transformed_pd = pd.concat(frames_transformed, axis=1)
    transformed_data = transformed_pd.values
    
    # consolidate neutral data
    lf_neutral_pd = pd.DataFrame(lf_neutral)
    hip_neutral_pd = pd.DataFrame(hip_neutral)
    rf_neutral_pd = pd.DataFrame(rf_neutral)
    
    frames_neutral = [lf_neutral_pd, hip_neutral_pd, rf_neutral_pd]
    neutral_pd = pd.concat(frames_neutral, axis=1)
    neutral_data = neutral_pd.values
    
    return transformed_data, neutral_data

    
if __name__ == '__main__':
    pass
#    import time
#    start_time = time.time()
#    ####READ IN DATA ~ Will change when we call from the database#####
#    path = 'C:\Users\court\Desktop\BioMetrix\Research\Quaternions\
#Subject2_rawData.csv'
## replace with func name from coordinateFrameTransform script
#    data, neut_data= transform_data(path, hip_bf_coordTrans, lf_bf_coordTrans,
#                                    rf_bf_coordTrans)

#    np.savetxt("Subject2_Transformed_Data.csv", data, delimiter=",")
##    np.savetxt("Subject2_Neutral_Data.csv",neut_data, delimiter=",")

#    print "My program took", time.time() - start_time, "to run"
