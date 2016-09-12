# -*- coding: utf-8 -*-
"""
Created on Sat Aug 13 14:28:20 2016

@author: Brian
"""
import numpy as np
import pandas as pd

"""
#############################################INPUT/OUTPUT####################################################
Inputs: (1) data object that must contain raw accel, gyr, mag, and quat values; (1) 1x4 rotation quaternion 
that represents the conjugate of the global yaw offset, (1) 1x4 rotation quaternion that represents the local
yaw offset, (1) 1x4 quaternion that represents the correction for pitch and the local yaw offset

Outputs: (1) data object that houses adjusted inertial frame data (Euler is sensor-body frame) (acc-g, gyr,
mag, quat, Euler); (1) data object that houses sensor frame data (acc-g, gyr, mag)

Datasets: Preprocess_unittest.csv -> __main__ -> postprocessed_unittest.csv
#############################################################################################################
"""
class WrongShapeError(ValueError):
    pass

class QuatFormError(ValueError):
    pass

class DivideByZeroError(ValueError):
    pass

class ObjectMismatchError(TypeError):
    pass

####Function to compute the product between two quaternions...order matters!
def QuatProd(q1, q2):
    if 'matrix' not in str(type(q1)) or 'matrix' not in str(type(q2)):
        raise QuatFormError
    
    if q1.shape != (1,4) or q2.shape != (1,4):
        raise QuatFormError
        
    s1 = q1[0,0] #float
    s2 = q2[0,0] # float
    v1 = q1[0,1:4] # 1x3 vector
    v2 = q2[0,1:4] # 1x3 vector
    
    prod = np.zeros((1,4)) # create storage vector for product
    prod[0,0] = s1*s2 - v1.dot(v2.transpose()) #first term of product...contains 1x3 dot 1x3 vec...returns float
    prod[0,1:4] = s1*v2 + s2*v1 + np.cross(v1, v2) #returns 1x3 vector combination of dot and cross product    
    prod = np.matrix(prod)  ###return a matrix object 
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
    if yaw < 0:  ##necessary to account of difference in direction of offset
        q3 = -np.sqrt(1-q0**2) #compute 4th term of offset quaternion
    else:
        q3 = np.sqrt(1-q0**2) #compute 4th term of offset quaternion
    yaw_fix = np.matrix([q0, 0, 0, q3]) #build yaw offset quaternion
    return yaw_fix

def Calc_Euler(q):
    dcm = q2dcm(q)
    roll = np.arctan2(dcm[2,1], dcm[2,2]) #compute roll...must use arctan2! Inputs come from rotation matrix
    pitch = np.arcsin(-dcm[2,0]) #compute pitch...inputs come from rotation matrix
    yaw = np.arctan2(dcm[1,0], dcm[0,0]) #compute yaw...must use arctan2! Inputs come from rotation matrix      
    return [roll, pitch, yaw]

def clippedAccel(acc):
    limits = [2000, 4000, 8000, 16000]
    for i in range(len(limits)):
        if -4 < acc-limits[i] < 4:
            return 'clipped' 
            
def rotate_quatdata(data, rot, RemoveGrav=False):
    corr_data = QuatProd(rot, QuatProd(data, QuatConj(rot))) ##quat product of rotation quaternion * (data vector * rotation quat conjugate)
    if RemoveGrav:  #in case you are multiplying an acceleration vector you can remove a gravity component
        corr_data = (corr_data - [0,0,0,1000])*.00980665  #subtract gravity vector from body frame data
    else:
        pass
    return [corr_data[0,1], corr_data[0,2], corr_data[0,3]]
    
def FrameTransform(data, yaw_q, sensfr):   
    q0 = np.matrix([data['qW'], data['qX'], data['qY'], data['qZ']]) #t=0 quaternion
    yaw_fix = yaw_offset(q0) #uses yaw offset function above to body frame quaternion
    yfix_c = QuatConj(yaw_fix) #uses quaternion conjugate function to return conjugate of body frame
    yfix_c = QuatProd(QuatConj(yaw_q), yfix_c)
    
    output_body = np.zeros((1,11)) #creates output vector that will house: quaternion, euler angles, acc, gyr, and mag data in body frame
    quat = np.matrix([data['qW'], data['qX'], data['qY'], data['qZ']]) #collect most recent quaternion from dataset (will be arriving in real time)   
    acc = np.matrix([0, data['AccX'], data['AccY'], data['AccZ']]) #collect most recent raw accel from dataset (will be arriving in real time) and create into quaternion by adding first term equal to zero   
    fixed_q = QuatProd(yfix_c,quat) #quaternion product of conjugate of yaw offset and quaternion from data, remember order matters!
    sens_frame = QuatProd(QuatConj(sensfr), quat) #calculate body-sensor frame orientation
    output_body[0,0] = data['Timestamp']        
    output_body[0,1:5] = sens_frame #assign corrected quaternion to body output vector
    output_body[0,5:8] = Calc_Euler(sens_frame) #assign set of euler angles (frome body-sensor frame) to body output vector
    output_body[0,8:11] = rotate_quatdata(acc, fixed_q, RemoveGrav=True) #add corrected accel data to body output vector   
    return output_body          
    
if __name__ == '__main__':
    ####READ IN DATA ~ Will change when we call from the database#####
    path = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\Trial 4\\hips_062816_onsensor.csv'
    #path = 'C:\\Users\\Brian\\Downloads\\combined_Subject6_LESS_synced_1470672752025.csv'
    data = pd.read_csv(path)
    
    #FROM ANATOMICAL CALIBRATION
    yaw_q = np.matrix([1,0,0,1])/np.linalg.norm([1,0,0,1]) #This is an example stand in for the adjusted inertial frame offset
    align_q =np.matrix([1,0,0,1])/np.linalg.norm([1,0,0,1]) #This is an example stand in for the bodyframe align quaternion   
    
    iters = len(data)    
    for i in range(1, iters):#align reference frame flush with body part
        #check for clipped acceleration data, find data point with no slope
        if data['AccZ'].ix[i] - data['AccZ'].ix[i-1] == 0 and abs(data['AccZ'].ix[i]) > 1900:
            out = clippedAccel(data['AccZ'].ix[i])
            print(i, out)
        elif data['AccX'].ix[i] - data['AccX'].ix[i-1] == 0 and abs(data['AccX'].ix[i]) > 1900:
            out = clippedAccel(data['AccX'].ix[i])
            print(i, out)
        elif data['AccY'].ix[i] - data['AccX'].ix[i-1] == 0 and abs(data['AccX'].ix[i]) > 1900:
            out = clippedAccel(data['AccX'].ix[i])
            print(i, out)
        obody = FrameTransform(data.ix[i,:], yaw_q, align_q)