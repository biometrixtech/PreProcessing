# -*- coding: utf-8 -*-
"""
Created on Wed Sep 28 17:42:39 2016

@author: court
"""

# import relevant packages
import warnings
import numpy as np
import quatOps as qo


"""
############################################################################
Conversions between quaternions and Euler angles, using embedded direction
cosine matrices
############################################################################
"""


def quat_to_euler(q):
    """Function that transforms quaternion into Euler angles, assuming ZYX
    config.

    Args:
        q: quaternions. must be nx4 array, n>=1

    Returns:
        psi: euler angle measuring rotaion about x axis (roll)
        theta: euler angle measuring rotaion about y axis (pitch)
        phi: euler angle measuring rotaion about z axis (yaw)

    """
#    if np.isnan(q).any():
#        return np.array([[np.nan, np.nan, np.nan]])

    q = qo.quat_norm(q)

##%% DANIELE'S CODE
#    # calculate relevant elements of direction cosine matrix
#    d = 2*(q[:, 0]*q[:, 1] + q[:, 2]*q[:, 3])
#    e = 1 - 2*(q[:, 1]**2 + q[:, 2]**2)
#    psi = np.arctan2(d, e)
#    
#    c = q[:, 0]*q[:, 2] - q[:, 1]*q[:, 3]
#    c[c > .5] = .5
#    c[c < -.5] = -.5
#    theta = np.arcsin(2*c)
#    
#    a = 1 - 2*(q[:, 2]**2 + q[:, 3]**2)
#    b = 2*(q[:, 0]*q[:, 3] + q[:, 1]*q[:, 2])
#    phi = np.arctan2(b, a)
#    
#    if any(c > .49999999):
#        print "theta is 90"
#        q1 = q[c > .49999999]
#        psi[c > .49999999] = 0    ######### SWITCH PHI AND PSI FOR TEST
#        theta[c > .49999999] = np.pi/2
#        phi[c > .49999999] = -2*np.arctan2(q1[:, 1], q1[:, 0])
#    elif any(c < -.49999999):
#        print "theta is -90"
#        q1 = q[c < -.49999999]
#        psi[c < -.49999999] = 0       ######### SWITCH PHI AND PSI FOR TEST
#        theta[c < -.49999999] = -np.pi/2
#        phi[c < -.49999999] = 2*np.arctan2(q1[:, 1], q1[:, 0])
#    elif any(np.sum(np.abs(q - np.array([[0, 0, 1, 0]])) \
#             < np.array([[1e-8]*4]), axis=1) == 4):
#        ind = np.sum(np.abs(q - np.array([[0, 0, 1, 0]])) \
#                     < np.array([[1e-8]*4]), axis=1) == 4
#        psi[ind] = 0
#        theta[ind] = np.pi
#        phi[ind] = 0

#%% DANIELE'S CODE w/out singularity handling
    # calculate relevant elements of direction cosine matrix

    # YAW COMPONENT
    d = 2*q[:, 1]*q[:, 2]+2*q[:, 0]*q[:, 3]
    e = 1-2*q[:, 2]**2-2*q[:, 3]**2
    psi = np.arctan2(d, e)

    # PITCH COMPONENT
    c = -q[:, 1]*q[:, 3]+q[:, 0]*q[:, 2]
    c[c > .5] = .5
    c[c < -.5] = -.5
    theta = np.arcsin(2*c)
    
    
    # ROLL COMPONENT
    a = 1-2*q[:, 1]**2-2*q[:, 2]**2
    b = 2*(q[:, 2]*q[:, 3])+2*q[:, 0]*q[:, 1]
    phi = np.arctan2(b, a)
    
    if any(c > .4995):
        print "theta is 90"
        q1 = q[c > .4995]
        psi[c > .4995] = np.nan    ######### SWITCH PHI AND PSI FOR TEST
        theta[c > .4995] = np.nan
        phi[c > .4995] = np.nan
    elif any(c < -.4995):
        print "theta is -90"
        q1 = q[c < -.4995]
        psi[c < -.4995] = np.nan       ######### SWITCH PHI AND PSI FOR TEST
        theta[c < -.4995] = np.nan
        phi[c < -.4995] = np.nan
    elif any(np.sum(np.abs(q - np.array([[0, 0, 1, 0]])) \
             < np.array([[1e-8]*4]), axis=1) == 4):
        ind = np.sum(np.abs(q - np.array([[0, 0, 1, 0]])) \
                     < np.array([[1e-8]*4]), axis=1) == 4
        psi[ind] = 0
        theta[ind] = np.pi
        phi[ind] = 0
#%% OUR CODE
#    a = 2*q[:, 0]**2 - 1 + 2*q[:, 1]**2
#    b = 2*(q[:, 1]*q[:, 2] - q[:, 0]*q[:, 3])
#    c = 2*(q[:, 1]*q[:, 3] + q[:, 0]*q[:, 2])
#    d = 2*(q[:, 2]*q[:, 3] - q[:, 0]*q[:, 1])
#    e = 2*q[:, 0]**2 - 1 + 2*q[:, 3]**2
#    c[c >1] = 1
#    phi = np.arctan2(d, e)
#    theta = -np.arcsin(c)
#    psi = np.arctan2(b, a)
#    if any(c > .999999999):
#        q1 = q[c > .999999999]
#        psi[c > .999999999] = 0
#        theta[c > .999999999] = -np.pi/2
#        phi[c > .999999999] = np.arctan2(-2*(q1[:, 1]*q1[:, 2] + q1[:, 0] * q1[:, 3]),
#                                         -2*(q1[:, 1]*q1[:, 3] - q1[:, 0]*q1[:, 2]))
#    elif any(c < -.999999999):
#        q1 = q[c < -.999999999]
#        psi[c < -.999999999] = 0
#        theta[c < -.999999999] = np.pi/2
#        phi[c < -.999999999] = np.arctan2(2*(q1[:, 1]*q1[:, 2] + q1[:, 0] \
#                                          *q1[:, 3]), 2*(q1[:, 1]*q1[:, 3] \
#                                          - q1[:, 0]*q1[:, 2]))
#    elif any(np.sum(np.abs(q - np.array([[0, 0, 1, 0]])) \
#             < np.array([[1e-8]*4]), axis=1) == 4):
#        ind = np.sum(np.abs(q - np.array([[0, 0, 1, 0]])) \
#                     < np.array([[1e-8]*4]), axis=1) == 4
#        phi[ind] = 0
#        theta[ind] = np.pi
#        psi[ind] = 0

#%% NASA'S CODE

#    q0 = q[:, 0]
#    q1 = q[:, 1]
#    q2 = q[:, 2]
#    q3 = q[:, 3]
#
#    m11 = 1-2*(q2**2 + q3**2)
#    m21 = 2*(q1*q2 + q0*q3)
#    m31 = 2*(q1*q3 - q0*q2)
#    m32 = 2*(q2*q3 + q0*q1)
#    m33 = 1 - 2*(q1**2 + q2**2)
#
#    theta1 = np.arctan2(m21, m11)
#    theta2 = np.arctan2(-m31, np.sqrt(1-m31**2))
#    theta3 = np.arctan2(-m32, m33)

#    phi = theta1
#    theta = theta2
#    psi = theta3
#%%

    return np.vstack([phi, theta, psi]).T


def euler_to_quat(euler_data):
    """Function that transforms set of Euler angles into quaternion, assuming
    ZYX config.

    Args:
        Euler angles consisting of the following angles in order
        psi: euler angle measuring rotaion about x axis (roll)
        theta: euler angle measuring rotaion about y axis (pitch)
        phi: euler angle measuring rotaion about z axis (yaw)

    Returns:
        single (WXYZ) quaternion transformation of given euler angles

    """
    if len(euler_data[0]) != 3:
        print "INPUT DATA FOR EULER TO QUAT IS NOT CORRECT FORM"
##%% OUR CODE
#    psi = euler_data[:, 0]
#    theta = euler_data[:, 1]
#    phi = euler_data[:, 2]
#    # calculate intermediate values with Euler angle
#    a = np.cos(phi)*np.cos(theta)
#    b = -np.sin(phi)*np.cos(psi)+np.cos(phi)*np.sin(theta)*np.sin(psi)
#    c = np.sin(phi)*np.sin(psi)+np.cos(phi)*np.sin(theta)*np.cos(psi)
#    d = np.sin(phi)*np.cos(theta)
#    e = np.cos(phi)*np.cos(psi)+np.sin(phi)*np.sin(theta)*np.sin(psi)
#    f = -np.cos(phi)*np.sin(psi)+np.sin(phi)*np.sin(theta)*np.cos(psi)
#    g = -np.sin(theta)
#    h = np.cos(theta)*np.sin(psi)
#    k = np.cos(theta)*np.cos(psi)
#
#    # use intermediate values to calculate elements of quaternion matrix
#    A = (a-e-k)/3
#    B = (d+b)/3
#    C = (g+c)/3
#    D = (f-h)/3
#    E = (d+b)/3
#    F = (e-a-k)/3
#    G = (h+f)/3
#    H = (g-c)/3
#    I = (g+c)/3
#    J = (h+f)/3
#    K = (k-a-e)/3
#    L = (b-d)/3
#    M = (f-h)/3
#    N = (g-c)/3
#    O = (b-d)/3
#    P = (a+e+k)/3
#
#    # construct the quaternion matrix
#    Q = np.array([[A, B, C, D],
#                  [E, F, G, H],
#                  [I, J, K, L],
#                  [M, N, O, P]])
#    Q = Q.swapaxes(0, 2)
#
#    # find the maximum eigenvalue of the quaternion matrix
#    [D, V] = np.linalg.eig(Q)
#
#    max_eig = np.argmax(D, 1)
#    # find the eigenvector containing the largest eigenvalue and extract the
#        # quaternion from its components.
#    q = np.zeros((len(max_eig), 4))
#
#    for row in range(len(max_eig)):
#        try:
#            q[row, :] = V[row, :, max_eig[row]]
#        except Warning:
#            warnings.filterwarnings("ignore")
#            q[row, :] = V[row, :, max_eig[row]]
#    q = np.vstack([q[:, 3], q[:, 0], q[:, 1], q[:, 2]]).T

#%% NASA'S CODE
#    theta1 = euler_data[:, 0]
#    theta2 = euler_data[:, 1]
#    theta3 = euler_data[:, 2]
#
#    s1 = np.sin(0.5*theta1)
#    s2 = np.sin(0.5*theta2)
#    s3 = np.sin(0.5*theta3)
#    c1 = np.cos(0.5*theta1)
#    c2 = np.cos(0.5*theta2)
#    c3 = np.cos(0.5*theta3)
#
#    q1 = s1*s2*s3 + c1*c2*c3
#    q2 = -s1*s2*c3 + s3*c1*c2
#    q3 = s1*s3*c2 + s2*c1*c3
#    q4 = s1*c2*c3 - s2*s3*c1
##    print q1.shape
##    print q2.shape
##    print q1[:, np.newaxis].shape
#
#    q = np.hstack((q1[:, np.newaxis], q2[:, np.newaxis]))
#    q = np.hstack((q, q3[:, np.newaxis]))
#    q = np.hstack((q, q4[:, np.newaxis]))
#    print q.shape

#%% Code Derived from Daniele's Methods

    # isolate roll, pitch, and yaw
    roll = euler_data[:, 0]
    pitch = euler_data[:, 1]
    yaw = euler_data[:, 2]

    # compute real and imaginary components of intermediate quaternions
    real_roll = np.cos(0.5*roll).reshape(-1, 1)
    imag_roll = np.sin(0.5*roll).reshape(-1, 1)
    real_pitch = np.cos(0.5*pitch).reshape(-1, 1)
    imag_pitch = np.sin(0.5*pitch).reshape(-1, 1)
    real_yaw = np.cos(0.5*yaw).reshape(-1, 1)
    imag_yaw = np.sin(0.5*yaw).reshape(-1, 1)

    # compile the intermediate quaternions
    roll_quat = np.hstack((real_roll, imag_roll))
    roll_quat = np.hstack((roll_quat, np.zeros((len(euler_data), 2))))

    pitch_quat = np.hstack((real_pitch, np.zeros((len(euler_data), 1))))
    pitch_quat = np.hstack((pitch_quat, imag_pitch))
    pitch_quat = np.hstack((pitch_quat, np.zeros((len(euler_data), 1))))

    yaw_quat = np.hstack((real_yaw, np.zeros((len(euler_data), 2))))
    yaw_quat = np.hstack((yaw_quat, imag_yaw))

    # combine intermediate quaternions to get final
    q = qo.quat_prod(qo.quat_prod(yaw_quat, pitch_quat), roll_quat)
#    print roll_quat, 'R'
#    print pitch_quat, 'P'
#    print yaw_quat, 'Y'

#%%
    return q