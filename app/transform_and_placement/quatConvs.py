# -*- coding: utf-8 -*-
"""
Created on Wed Sep 28 17:42:39 2016

@author: court
"""

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

    q = qo.quat_norm(q)

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
    
    if any(np.sum(np.abs(q - np.array([[0, 0, 1, 0]])) \
             < np.array([[1e-8]*4]), axis=1) == 4):
        ind = np.sum(np.abs(q - np.array([[0, 0, 1, 0]])) \
                     < np.array([[1e-8]*4]), axis=1) == 4
        psi[ind] = 0
        theta[ind] = np.pi
        phi[ind] = 0
    else:
        pass

    return np.vstack([phi, theta, psi]).T


def euler_to_quat(euler_data):
    """Function that transforms set of Euler angles into quaternion, assuming
    ZYX config.

    Args:
        euler_data: Euler angles consisting of the following angles in order
            psi: euler angle measuring rotaion about x axis (roll)
            theta: euler angle measuring rotaion about y axis (pitch)
            phi: euler angle measuring rotaion about z axis (yaw)

    Returns:
        single (WXYZ) quaternion transformation of given euler angles

    """

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

    return q
