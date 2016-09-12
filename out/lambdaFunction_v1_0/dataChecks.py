# -*- coding: utf-8 -*-
"""
Created on Wed Aug 24 18:43:39 2016

@author: Brian
"""

import numpy as np

####function that transforms quaternion into rotation matrix
def q2dcm(q):        
    q = q/np.linalg.norm(q) #normalize quaternion
    dcm = np.matrix([[1-2*q[0,2]**2-2*q[0,3]**2, 2*q[0,1]*q[0,2]-2*q[0,0]*q[0,3], 2*q[0,0]*q[0,2]+2*q[0,1]*q[0,3]],
                    [2*q[0,0]*q[0,3]+2*q[0,2]*q[0,1], 1-2*q[0,1]**2-2*q[0,3]**2, -2*q[0,1]*q[0,0]+2*q[0,2]*q[0,3]],
                    [-2*q[0,0]*q[0,2]+2*q[0,1]*q[0,3], 2*q[0,1]*q[0,0]+2*q[0,2]*q[0,3], 1-2*q[0,2]**2-2*q[0,1]**2]])  
    ###above defines a 3x3 rotation matrix indexes are defined by [row, column] input into function is a 1x4 vector
    return dcm

def Calc_Euler(q):
    dcm = q2dcm(q)
    roll = np.arctan2(dcm[2,1], dcm[2,2]) #compute roll...must use arctan2! Inputs come from rotation matrix
    pitch = np.arcsin(-dcm[2,0]) #compute pitch...inputs come from rotation matrix
    yaw = np.arctan2(dcm[1,0], dcm[0,0]) #compute yaw...must use arctan2! Inputs come from rotation matrix      
    return [roll, pitch, yaw]

def angleArrays(data):
    eX = []
    eY = []
    eZ = []
    for i in range(len(data.qW)):
        quat = np.matrix([data.qW[i], data.qX[i], data.qY[i], data.qZ[i]])
        #calculate euler angles for quaternion and append to respective lists    
        eul = Calc_Euler(quat)
        eX.append(eul[0])
        eY.append(eul[1])
        eZ.append(eul[2])
    #create Euler attributes in data object
    data.EulerX = np.array(eX)
    data.EulerY = np.array(eY)
    data.EulerZ = np.array(eZ)
    return data

def quatCheck(data):
    for i in range(len(data.qW)):
        quat = np.matrix([data.qW[i], data.qX[i], data.qY[i], data.qZ[i]])
        if .99 > np.linalg.norm(quat) or  np.linalg.norm(quat) > 1.01:
            #set t=i quat to t=i-1 quaternion
            quat = np.matrix([data.qW[i-1], data.qX[i-1], data.qY[i-1], data.qZ[i-1]])
            data.qW[i] = data.qW[i-1]
            data.qX[i] = data.qX[i-1]
            data.qY[i] = data.qY[i-1]
            data.qZ[i] = data.qZ[i-1]
    
    return data
    
        
        
    