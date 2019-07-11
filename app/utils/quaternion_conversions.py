# -*- coding: utf-8 -*-
"""
Created on Wed Sep 28 17:42:39 2016

@author: court
"""

import numpy as np
from .quaternion_operations import quat_prod


"""
############################################################################
Conversions between quaternions and Euler angles, using embedded direction
cosine matrices
############################################################################
"""


def quat_to_euler(w, x, y, z):
    """
    Function that transforms quaternion into Euler angles, assuming WXYZ
    arrangement

    Args:
        w: quaternions w-component. must be Nx1 array
        x: quaternions x-component
        y: quaternions y-component
        z: quaternions x-component

    Returns:
        psi: euler angle measuring rotaion about x axis (roll)
        theta: euler angle measuring rotaion about y axis (pitch)
        phi: euler angle measuring rotaion about z axis (yaw)
    """

    # Normalise
    magnitude = np.sqrt(w ** 2 + x ** 2 + y ** 2 + z ** 2)
    w /= magnitude
    x /= magnitude
    y /= magnitude
    x /= magnitude

    # YAW COMPONENT
    d = 2 * x * y + 2 * w * z
    e = 1 - 2 * y**2 - 2*z**2
    psi = np.arctan2(d, e)

    # PITCH COMPONENT
    c = -x * z + w * y
    c[c > .5] = .5
    c[c < -.5] = -.5
    theta = np.arcsin(2*c)

    # ROLL COMPONENT
    a = 1 - 2 * x**2 - 2*y**2
    b = 2 * (y * z) + 2 * w * x
    phi = np.arctan2(b, a)

    knockout = np.where((np.abs(w) + np.abs(x) + np.abs(y - 1) + np.abs(z)) < 1e-8)
    if any(knockout):
        psi[knockout] = 0
        theta[knockout] = np.pi
        phi[knockout] = 0

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
    roll = euler_data[:, 0].astype(float)
    pitch = euler_data[:, 1].astype(float)
    yaw = euler_data[:, 2].astype(float)

    # compute real and imaginary components of intermediate quaternions
    real_roll = np.cos(0.5 * roll).reshape(-1, 1)
    imag_roll = np.sin(0.5 * roll).reshape(-1, 1)
    real_pitch = np.cos(0.5 * pitch).reshape(-1, 1)
    imag_pitch = np.sin(0.5 * pitch).reshape(-1, 1)
    real_yaw = np.cos(0.5 * yaw).reshape(-1, 1)
    imag_yaw = np.sin(0.5 * yaw).reshape(-1, 1)

    # compile the intermediate quaternions
    roll_quat = np.hstack((real_roll, imag_roll))
    roll_quat = np.hstack((roll_quat, np.zeros((len(euler_data), 2))))

    pitch_quat = np.hstack((real_pitch, np.zeros((len(euler_data), 1))))
    pitch_quat = np.hstack((pitch_quat, imag_pitch))
    pitch_quat = np.hstack((pitch_quat, np.zeros((len(euler_data), 1))))

    yaw_quat = np.hstack((real_yaw, np.zeros((len(euler_data), 2))))
    yaw_quat = np.hstack((yaw_quat, imag_yaw))

    # combine intermediate quaternions to get final
    q = quat_prod(quat_prod(yaw_quat, pitch_quat), roll_quat)

    return q


def quat_force_euler_angle(quaternion, phi=None, theta=None, psi=None):
    euler_angles = quat_to_euler(
        quaternion[:, 0],
        quaternion[:, 1],
        quaternion[:, 2],
        quaternion[:, 3],
    )
    if phi is not None:
        euler_angles[:, 0] = phi
    if theta is not None:
        euler_angles[:, 1] = theta
    if psi is not None:
        euler_angles[:, 2] = psi
    return euler_to_quat(euler_angles)


def quat_from_euler_angles(angle, versor):
    """Compute quaternion from Euler angles (in degrees)."""
    angle = np.radians(angle)
    versor = np.atleast_2d(versor)
    w = np.cos(angle/2) * np.ones_like(versor[:,0])
    x = np.sin(angle/2) * versor[:,0]
    y = np.sin(angle/2) * versor[:,1]
    z = np.sin(angle/2) * versor[:,2]
    return np.stack((w, x, y, z), axis=-1)


def quat_as_euler_angles(q):
    """Compute Euler angles from quaternion(s) (in degrees)."""
    q = np.asanyarray(q, dtype=float)
    angles = np.zeros((*q.shape[:-1], 3))
    w = q[...,0]
    x = q[...,1]
    y = q[...,2]
    z = q[...,3]
    angles[...,0] = np.arctan2(2*y*z + 2*w*x, 1 - 2*x**2 - 2*y**2)
    angles[...,1] = np.arcsin(-2*x*z + 2*w*y)
    angles[...,2] = np.arctan2(2*x*y + 2*w*z, 1 - 2*y**2 - 2*z**2)
    return np.degrees(angles)