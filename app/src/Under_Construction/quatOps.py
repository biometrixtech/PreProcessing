# -*- coding: utf-8 -*-
"""
Created on Wed Sep 28 17:42:39 2016

@author: court
"""

# import relevant packages
import numpy as np

"""
#########################################################################################
Library of functions for pure quaternion operations.
Conceptual explanations to be given under:
https://sites.google.com/a/biometrixtech.com/wiki/home/preprocessing/anatomical/concepts
Further documentation of code to be given under:
https://drive.google.com/drive/folders/0Bzd7PD0NIJ7ZZmJ5aVRsUnVOZ3c
#########################################################################################
"""

####Function to compute the product between two quaternions... q1 followed by a rotation of q2
def quat_prod(q1, q2):
        
    q2=quat_n(q2)
    prod = np.zeros(4)
    prod[0] = q1[0]*q2[0]-q1[1]*q2[1]-q1[2]*q2[2]-q1[3]*q2[3]
    prod[1] = q1[0]*q2[1]+q1[1]*q2[0]+q1[2]*q2[3]-q1[3]*q2[2]
    prod[2] = q1[0]*q2[2]-q1[1]*q2[3]+q1[2]*q2[0]+q1[3]*q2[1]    
    prod[3] = q1[0]*q2[3]+q1[1]*q2[2]-q1[2]*q2[1]+q1[3]*q2[0]
    return prod
    
def vquat_prod(q1, q2):
        
    prod = np.zeros(4)
    prod[0] = q1[0]*q2[0]-q1[1]*q2[1]-q1[2]*q2[2]-q1[3]*q2[3]
    prod[1] = q1[0]*q2[1]+q1[1]*q2[0]+q1[2]*q2[3]-q1[3]*q2[2]
    prod[2] = q1[0]*q2[2]-q1[1]*q2[3]+q1[2]*q2[0]+q1[3]*q2[1]    
    prod[3] = q1[0]*q2[3]+q1[1]*q2[2]-q1[2]*q2[1]+q1[3]*q2[0]
    return prod

####Function that returns conjugate of input quaternion  
def quat_conj(q):
    
    if np.linalg.norm(q) == 0:
        raise DivideByZeroError
        
    conj = np.matrix([q[0], -q[1], -q[2], -q[3]]) #first term unchanged, last three terms are negative of inital quaternion
    conj = conj/np.linalg.norm(conj) #normalize the quaternion by dividing by magnitude see line 74 for hardcoded example 
    conj = np.squeeze(np.asarray(conj))    
    return conj
    
    
####function that normalizes quaternions
def quat_n(q):

    qn = q/np.linalg.norm(q) # normalize the quaternion by dividing Euler Parameters by magnitude
    return qn
   
   
#### function that rotates a vector v by rotation quaternion q
def vect_rot(v,q):

    V = np.zeros((1,4)) # Create storage for variable values
    V = [0,v[0],v[1],v[2]] # Convert 3D matrix to "quaternion" form
    q=quat_n(q) # Normalize the rotation quaternion
    rotvect = np.zeros((1,4)) # Create storage for variable values
    rotvect = quat_prod(vquat_prod(quat_conj(q),V),q) # vector is rotated as rotvect = QVQ^(-1)
    rotvect=[rotvect[1],rotvect[2],rotvect[3]]
    return rotvect


#### Function that finds rotation between two quaternions
def find_rot(q1,q2):

    rotq = np.zeros((1,4)) # create storage vector for product
    rotq = quat_prod(quat_conj(quat_n(q1)),quat_n(q2)) # rotation between normalized quaternions Q1 and Q2 produced as rotq = Q1^(-1)Q2
    return rotq


#### Function that "averages" a string of quaternions
def quat_avg(data):
    avgquat=np.mean(data,0)
    avgquat=quat_n(avgquat)
    return avgquat