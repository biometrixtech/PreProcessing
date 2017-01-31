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

Conceptual explanations to be given under:
https://sites.google.com/a/biometrixtech.com/wiki/home/preprocessing/
    anatomical/concepts
Further documentation of code to be given under:
https://drive.google.com/drive/folders/0Bzd7PD0NIJ7ZZmJ5aVRsUnVOZ3c
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
##        return np.array([[np.nan, np.nan, np.nan]])
#        print np.where(np.isnan(q))

    q = qo.quat_norm(q)

    a = 2*q[:, 0]**2 - 1 + 2*q[:, 1]**2
    b = 2*(q[:, 1]*q[:, 2] - q[:, 0]*q[:, 3])
    c = 2*(q[:, 1]*q[:, 3] + q[:, 0]*q[:, 2])
    d = 2*(q[:, 2]*q[:, 3] - q[:, 0]*q[:, 1])
    e = 2*q[:, 0]**2 - 1 + 2*q[:, 3]**2
    c[c >1] = 1
    phi = np.arctan2(d, e)
    theta = -np.arcsin(c)
    psi = np.arctan2(b, a)
    
    # delete variables that are not used further in computations
    del a, b, d, e    
    
    if any(c > .999999999):
        q1 = q[c > .999999999]
        psi[c > .999999999] = 0
        theta[c > .999999999] = -np.pi/2
        phi[c > .999999999] = np.arctan2(-2*(q1[:, 1]*q1[:, 2] + q1[:, 0] * q1[:, 3]),
                                         -2*(q1[:, 1]*q1[:, 3] - q1[:, 0]*q1[:, 2]))
    elif any(c < -.999999999):
        q1 = q[c < -.999999999]
        psi[c < -.999999999] = 0
        theta[c < -.999999999] = np.pi/2
        phi[c < -.999999999] = np.arctan2(2*(q1[:, 1]*q1[:, 2] + q1[:, 0] \
                                          *q1[:, 3]), 2*(q1[:, 1]*q1[:, 3] \
                                          - q1[:, 0]*q1[:, 2]))
    elif any(np.sum(np.abs(q - np.array([[0, 0, 1, 0]])) \
             < np.array([[1e-8]*4]), axis=1) == 4):
        ind = np.sum(np.abs(q - np.array([[0, 0, 1, 0]])) \
                     < np.array([[1e-8]*4]), axis=1) == 4
        phi[ind] = 0
        theta[ind] = np.pi
        psi[ind] = 0

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
    missing_data = False
    if np.isnan(euler_data).any():
        missing_data = True
    if missing_data:
        nan_row = np.unique(np.where(np.isnan(euler_data))[0])
        euler_data = np.delete(euler_data, (nan_row), axis=0)

    psi = euler_data[:, 0]
    theta = euler_data[:, 1]
    phi = euler_data[:, 2]
    del euler_data  # not used in further computations
    
    # calculate intermediate values with Euler angle
    a = np.cos(phi)*np.cos(theta)
    b = -np.sin(phi)*np.cos(psi)+np.cos(phi)*np.sin(theta)*np.sin(psi)
    c = np.sin(phi)*np.sin(psi)+np.cos(phi)*np.sin(theta)*np.cos(psi)
    d = np.sin(phi)*np.cos(theta)
    e = np.cos(phi)*np.cos(psi)+np.sin(phi)*np.sin(theta)*np.sin(psi)
    f = -np.cos(phi)*np.sin(psi)+np.sin(phi)*np.sin(theta)*np.cos(psi)
    g = -np.sin(theta)
    h = np.cos(theta)*np.sin(psi)
    k = np.cos(theta)*np.cos(psi)
    
    # delete variables that are not used in further computations
    del psi, theta, phi

    # use intermediate values to calculate elements of quaternion matrix
    A = (a-e-k)/3
    B = (d+b)/3
    C = (g+c)/3
    D = (f-h)/3
    E = (d+b)/3
    F = (e-a-k)/3
    G = (h+f)/3
    H = (g-c)/3
    I = (g+c)/3
    J = (h+f)/3
    K = (k-a-e)/3
    L = (b-d)/3
    M = (f-h)/3
    N = (g-c)/3
    O = (b-d)/3
    P = (a+e+k)/3
    
    # delete variables that are not used in further computations
    del a, b, c, d, e, f, g, h, k

    # construct the quaternion matrix
    Q = np.array([[A, B, C, D],
                  [E, F, G, H],
                  [I, J, K, L],
                  [M, N, O, P]])
    Q = Q.swapaxes(0, 2)
    
    # delete variables that are not used in further computations
    del A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P

    # find the maximum eigenvalue of the quaternion matrix
    [D, V] = np.linalg.eig(Q)

    max_eig = np.argmax(D, 1)
    del D, Q
    # find the eigenvector containing the largest eigenvalue and extract the
        # quaternion from its components.
    q = np.zeros((len(max_eig), 4))

    for row in range(len(max_eig)):
        try:
            q[row, :] = V[row, :, max_eig[row]]
        except Warning:
            warnings.filterwarnings("ignore")
            q[row, :] = V[row, :, max_eig[row]]
    q = np.vstack([q[:, 3], q[:, 0], q[:, 1], q[:, 2]]).T
    if missing_data:
        for i in nan_row:
            q = np.insert(q, i, [np.nan]*4, axis=0)
    
    return q