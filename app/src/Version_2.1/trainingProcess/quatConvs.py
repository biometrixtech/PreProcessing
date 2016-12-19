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
    if np.isnan(q).any():
        return np.array([[np.nan, np.nan, np.nan]])

    q = qo.quat_norm(q)

    # calculate relevant elements of direction cosine matrix
    d = 2*(q[:, 0]*q[:, 1] + q[:, 2]*q[:, 3])
    e = 1 - 2*(q[:, 1]**2 + q[:, 2]**2)
    psi = np.arctan2(d, e)
    
    c = q[:, 0]*q[:, 2] - q[:, 1]*q[:, 3]
    c[c > .5] = .5
    c[c < -.5] = -.5
    theta = np.arcsin(2*c)
    
    a = 1 - 2*(q[:, 2]**2 + q[:, 3]**2)
    b = 2*(q[:, 0]*q[:, 3] + q[:, 1]*q[:, 2])
    phi = np.arctan2(b, a)
    
    if any(c > .49999999):
        print "theta is 90"
        q1 = q[c > .49999999]
        psi[c > .49999999] = 0
        theta[c > .49999999] = np.pi/2
        phi[c > .49999999] = -2*np.arctan2(q1[:, 1], q1[:, 0])
    elif any(c < -.49999999):
        print "theta is -90"
        q1 = q[c < -.49999999]
        psi[c < -.49999999] = 0
        theta[c < -.49999999] = -np.pi/2
        phi[c < -.49999999] = 2*np.arctan2(q1[:, 1], q1[:, 0])
    elif any(np.sum(np.abs(q - np.array([[0, 0, 1, 0]])) \
             < np.array([[1e-8]*4]), axis=1) == 4):
        ind = np.sum(np.abs(q - np.array([[0, 0, 1, 0]])) \
                     < np.array([[1e-8]*4]), axis=1) == 4
        psi[ind] = 0
        theta[ind] = np.pi
        phi[ind] = 0

    return np.vstack([psi, theta, phi]).T


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
    psi = euler_data[:, 0]
    theta = euler_data[:, 1]
    phi = euler_data[:, 2]
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

    # construct the quaternion matrix
    Q = np.array([[A, B, C, D],
                  [E, F, G, H],
                  [I, J, K, L],
                  [M, N, O, P]])
    Q = Q.swapaxes(0, 2)

    # find the maximum eigenvalue of the quaternion matrix
    [D, V] = np.linalg.eig(Q)

    max_eig = np.argmax(D, 1)
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

    return q
