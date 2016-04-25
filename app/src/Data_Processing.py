# -*- coding: utf-8 -*-
"""
Created on Fri Feb 26 11:08:09 2016

@author: Brian
"""

import numpy as np
import pandas as pd

class WrongShapeError(ValueError):
    pass

class QuatFormError(ValueError):
    pass

class DivideByZeroError(ValueError):
    pass

####Function to compute the product between two quaternions...order matters!
def QuatProd(q1, q2):
    if 'matrix' not in str(type(q1)) or 'matrix' not in str(type(q2)):
        raise QuatFormError
    
    if q1.shape != (1,4) or q2.shape != (1,4):
        raise QuatFormError
    
    if np.linalg.norm(q1) == 0 or np.linalg.norm(q2) == 0:
        raise DivideByZeroError
        
    s1 = q1[0,0] #float
    s2 = q2[0,0] # float
    v1 = q1[0,1:4] # 1x3 vector
    v2 = q2[0,1:4] # 1x3 vector
    
    prod = np.zeros((1,4)) # create storage vector for product
    prod[0,0] = s1*s2 - v1.dot(v2.transpose()) #first term of product...contains 1x3 dot 1x3 vec...returns float
    prod[0,1:4] = s1*v2 + s2*v1 + np.cross(v1, v2) #returns 1x3 vector combination of dot and cross product    
    prod = np.matrix(prod)    
    return prod

####Function that returns conjugate of input quaternion  
def QuatConj(q):
    if 'matrix' not in str(type(q)):
        raise QuatFormError
    
    if q.shape != (1,4):
        raise QuatFormError
    
    if np.linalg.norm(q) == 0:
        raise DivideByZeroError
        
    conj = np.matrix([q[0,0], -q[0,1], -q[0,2], -q[0,3]]) #first term unchanged, last three terms are negative of inital quaternion
    conj = conj/np.linalg.norm(conj) #normalize the quaternion by dividing by magnitude see line 74 for hardcoded example 
    return conj

####function that transforms quaternion into rotation matrix
def q2dcm(q):
    if 'matrix' not in str(type(q)):
        raise QuatFormError
    
    if q.shape != (1,4):
        raise QuatFormError
    
    if np.linalg.norm(q) == 0:
        raise DivideByZeroError
        
    q = q/np.linalg.norm(q) #normalize quaternion
    dcm = np.matrix([[1-2*q[0,2]**2-2*q[0,3]**2, 2*q[0,1]*q[0,2]-2*q[0,0]*q[0,3], 2*q[0,0]*q[0,2]+2*q[0,1]*q[0,3]],
                    [2*q[0,0]*q[0,3]+2*q[0,2]*q[0,1], 1-2*q[0,1]**2-2*q[0,3]**2, -2*q[0,1]*q[0,0]+2*q[0,2]*q[0,3]],
                    [-2*q[0,0]*q[0,2]+2*q[0,1]*q[0,3], 2*q[0,1]*q[0,0]+2*q[0,2]*q[0,3], 1-2*q[0,2]**2-2*q[0,1]**2]])  
    ###above defines a 3x3 rotation matrix indexes are defined by [row, column] input into function is a 1x4 vector
    return dcm

####function used to calculate the yaw offset quaternion
def yaw_offset(q):
    f_dcm = q2dcm(q) #call q2dcm to convert quaternion to rotation matrix
    yaw = np.arctan2(f_dcm[1,0], f_dcm[0,0]) #calculate yaw of transformation using rotation matrix
    q0 = np.cos(yaw/2) #compute first term of offset quaternion
    if yaw < 0:
        q3 = -np.sqrt(1-q0**2) #compute 4th term of offset quaternion
    else:
        q3 = np.sqrt(1-q0**2)
    yaw_fix = np.matrix([q0, 0, 0, q3]) #build yaw offset quaternion
    return yaw_fix


####READ IN DATA ~ Will change when we call from the database#####
datapath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\First Pass CMEs\\Double Leg\\Hips\\vicon2_Hips_dblsquat_set1normal.csv'
data = pd.read_csv(datapath) #read in data; csv read in is just a stand in for now
mdata = data.as_matrix() #convert csv into matrix
bodyframe = []
sensframe = []
iters = len(mdata)

###This section takes the t=0 quaternion and computes the yaw in order to create the yaw offset    
q0 = np.matrix([mdata[0,13], mdata[0,14], mdata[0,15], mdata[0,16]]) #t=0 quaternion
yaw_fix = yaw_offset(q0) #uses yaw offset function above to compute yaw offset quaternion
yfix_c = QuatConj(yaw_fix) #uses quaternion conjugate function to return conjugate of yaw offset

####This section cycles through the already collected data and applies the various transformation...
####our application obviously will have the data arriving in real time so there will be no need for the for loop
for i in range(0, iters):
    output_body = np.zeros((1,16)) #creates output vector that will house: quaternion, euler angles, acc, gyr, and mag data in body frame
    output_sens = np.zeros((1,9)) #creates output vector that will house: acc (less gravity), gyr, and mag in sensor frame
    quat = np.matrix([mdata[i,13], mdata[i,14], mdata[i,15], mdata[i,16]]) #collect most recent quaternion from dataset (will be arriving in real time)
    acc = np.matrix([0, mdata[i,4], mdata[i,5], mdata[i,6]]) #collect most recent raw accel from dataset (will be arriving in real time) and create into quaternion by adding first term equal to zero
    gyr = np.matrix([0, mdata[i,10], mdata[i,11], mdata[i,12]]) #collect most recent raw gyro from dataset (will be arriving in real time) and create into quaternion by adding first term equal to zero
    mag = np.matrix([0, mdata[i,7], mdata[i,8], mdata[i,9]]) #collect most recent raw mag from dataset (will be arriving in real time) and create into quaternion by adding first term equal to zero
    fixed_q = QuatProd(yfix_c, quat) #quaternion product of conjugate of yaw offset and quaternion from data, remember order matters!
    fixed_q = fixed_q/np.sqrt(fixed_q[0,0]**2 + fixed_q[0,1]**2 + fixed_q[0,2]**2 + fixed_q[0,3]**2)#normalize quaternion, with hard coding of finding norm   
    output_body[0,0:4] = fixed_q #assign corrected quaternion to body output vector
    dcm = q2dcm(fixed_q) #call function to turn corrected quaternion into rotation matrix
    roll = np.arctan2(dcm[2,1], dcm[2,2]) #compute roll...must use arctan2! Inputs come from rotation matrix
    pitch = np.arcsin(-dcm[2,0]) #compute pitch...inputs come from rotation matrix
    yaw = np.arctan2(dcm[1,0], dcm[0,0]) #compute yaw...must use arctan2! Inputs come from rotation matrix      
    output_body[0,4:7] = [roll, pitch, yaw] #assign set of euler angles to body output vector
    corr_acc = QuatProd(fixed_q, QuatProd(acc, QuatConj(fixed_q))) #correct acceleration by multiplying corrected quat*acc vector*conj. of corrected vector (moves accel into body frame)
    corr_acc = (corr_acc - [0,0,0,1000])*.00980665 #remove gravity vector from corrected accel data
    output_body[0,7:10] = [corr_acc[0,1], corr_acc[0,2], corr_acc[0,3]] #add corrected accel data to body output vector
    corr_gyr = QuatProd(fixed_q, QuatProd(gyr, QuatConj(fixed_q))) #transform gyro data into body frame using same formula used for accel
    output_body[0,10:13] = [corr_gyr[0,1], corr_gyr[0,2], corr_gyr[0,3]] #add corrected gyro data to body output vector
    corr_mag = QuatProd(fixed_q, QuatProd(mag, QuatConj(fixed_q))) #transform mag data into body frame using same formula used for accel
    output_body[0,13:16] = [corr_mag[0,1], corr_mag[0,2], corr_mag[0,3]] #add corrected mag data to body output vector   
    
    sens_acc = QuatProd(QuatConj(fixed_q), QuatProd(corr_acc, fixed_q)) #now undo corrected accel rotation but leaving gravity negation to put accel data back into original sensor frame less the gravity vector (cont.)
    ## this is dont by reversing corr_acc equation...now its conj. corrected quat*corrected accel*corrected quat
    output_sens[0,0:3] = [sens_acc[0,1], sens_acc[0,2], sens_acc[0,3]] #add gravity-less accel data to sensor output vector
    output_sens[0,3:6] = [gyr[0,1], gyr[0,2], gyr[0,3]] #add raw gyr data to sensor output vector
    output_sens[0,6:9] = [mag[0,1], mag[0,2], mag[0,3]] #add raw mag data to sensor output vector
    ##appends each output vector to respective frame (used for saving to my computer...might be done differently in app)    
    bodyframe.append(output_body[0,:]) 
    sensframe.append(output_sens[0,:])

####Creates dataframe for body and sensor outputs along with adding column names 
body = pd.DataFrame(bodyframe, columns=["qW", "qX", "qY", "qZ", "EulerX", "EulerY", "EulerZ", "AccX", "AccY", "AccZ", "gyrX", "gyrY", "gyrZ", "magX", "magY", "magZ"]) #body frame column names
sens = pd.DataFrame(sensframe, columns=["accX", "accY", "accZ", "gyrX", "gyrY", "gyrZ", "magX", "magY", "magZ"]) #sensor frame column names

    
    
