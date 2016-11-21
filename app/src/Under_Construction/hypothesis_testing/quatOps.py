# -*- coding: utf-8 -*-
"""
Created on Wed Sep 28 17:42:39 2016

@author: court
"""

# import relevant packages
import numpy as np
from sklearn.preprocessing import normalize

"""
#########################################################################################
Library of functions for pure quaternion operations.
Conceptual explanations to be given under:
https://sites.google.com/a/biometrixtech.com/wiki/home/preprocessing/anatomical/concepts
Further documentation of code to be given under:
https://drive.google.com/drive/folders/0Bzd7PD0NIJ7ZZmJ5aVRsUnVOZ3c
#########################################################################################
"""


def quat_prod(q1, q2):
    
    """
    Function to compute the product between two quaternions... q1 followed by 
    a rotation of q2.
    
    Args:
        Two quaternions, the first an orientation to be rotated by the second.
        
    Return:
        Quaternion representing the final orientation.
    
    """

    # normalize rotation quaternion
    q2=quat_norm(q2)
    
    # create storage for quaternion
    prod = np.zeros(q1.shape)
    
    # calculate product quaternion's elements
    prod[:,0] = q1[:,0]*q2[:,0]-q1[:,1]*q2[:,1]-q1[:,2]*q2[:,2]-q1[:,3]*q2[:,3]
    prod[:,1] = q1[:,0]*q2[:,1]+q1[:,1]*q2[:,0]+q1[:,2]*q2[:,3]-q1[:,3]*q2[:,2]
    prod[:,2] = q1[:,0]*q2[:,2]-q1[:,1]*q2[:,3]+q1[:,2]*q2[:,0]+q1[:,3]*q2[:,1]
    prod[:,3] = q1[:,0]*q2[:,3]+q1[:,1]*q2[:,2]-q1[:,2]*q2[:,1]+q1[:,3]*q2[:,0]
    
    return prod
    
def _vector_quat_prod(q1, q2):
    
    """
    Function to compute the product between two quaternions during vector
    rotation - does not include normalization step of regular quaternion
    multiplication.
    
    Args:
        Two quaternions, the first an orientation to be rotated by the second.
        
    Return:
        Quaternion representing the final orientation.

    """
    
    # create storage for quaternion
    prod = np.zeros(q1.shape)
#    print q1
    
    # calculate product quaternion's elements
    prod[:,0] = q1[:,0]*q2[:,0]-q1[:,1]*q2[:,1]-q1[:,2]*q2[:,2]-q1[:,3]*q2[:,3]
    prod[:,1] = q1[:,0]*q2[:,1]+q1[:,1]*q2[:,0]+q1[:,2]*q2[:,3]-q1[:,3]*q2[:,2]
    prod[:,2] = q1[:,0]*q2[:,2]-q1[:,1]*q2[:,3]+q1[:,2]*q2[:,0]+q1[:,3]*q2[:,1]
    prod[:,3] = q1[:,0]*q2[:,3]+q1[:,1]*q2[:,2]-q1[:,2]*q2[:,1]+q1[:,3]*q2[:,0]
    
    return prod



def quat_norm(q):
    """
    Function that normalizes a quaternion
    
    """
    
    # Find the magnitude and divide
    mag = np.linalg.norm(q, axis=1).reshape(-1,1)
    qn = q/mag
    
    return qn
   
 
def quat_conj(q):
    
    """
    Function that returns conjugate of input quaternion.
    
    """
    
    # first term unchanged, last three terms are negative of inital quaternion    
    conj = np.vstack([q[:,0], -q[:,1], -q[:,2], -q[:,3]]).T
    
    # normalize the conjugate
    conj = quat_norm(conj)
    
    return conj


def vect_rot(v,q):
    
    """
    Function that rotates a vector v by rotation quaternion q.
    
    Args:
        v: 3D vector to be rotated
        q: 4D rotation quaternion
        
    Return:
        3D rotated vector
        
    """
    
    # Create storage for variable values
    rot_vect = np.zeros(q.shape)
    
    # Prepare values for rotation
    V = np.hstack((np.zeros((len(v),1)),v)) # Convert 3D matrix to "quaternion" form
    q=quat_norm(q) # Normalize the rotation quaternion

    # rotate vector as rot_vect = QVQ^(-1) and extract 3D values
    rot_vect = quat_prod(_vector_quat_prod(quat_conj(q),V),q)
    rot_vect=rot_vect[:,1:]
    
    return rot_vect


def find_rot(q1,q2):
    
    """
    Function that finds rotation between first and second quaternions.
    
    """
    
    # Create storage vector for product
    rot_q = np.zeros(q1.shape)
    
    # rotation between normalized quaternions Q1 and Q2 produced as rot_q = Q1^(-1)Q2
    rot_q = quat_prod(quat_conj(quat_norm(q1)), quat_norm(q2)) 
    
    return rot_q


def quat_avg(data):
    
    """
    Function that "averages" a column of quaternions into a single quaternion.
    
    """
    
    # Average data along columns
    avg_quat=np.mean(data,0).reshape(1,-1)
    
    # Normalize the single quaternion produced
    avg_quat=quat_norm(avg_quat)
    
    return avg_quat