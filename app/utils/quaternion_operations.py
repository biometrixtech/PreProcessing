# -*- coding: utf-8 -*-
"""
Created on Wed Sep 28 17:42:39 2016

@author: court
"""

import numpy as np


"""
############################################################################
Conceptual explanations to be given under:
https://sites.google.com/a/biometrixtech.com/wiki/home/preprocessing/anatomical/concepts
Further documentation of code to be given under:
https://drive.google.com/drive/folders/0Bzd7PD0NIJ7ZZmJ5aVRsUnVOZ3c
##########################################################################
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
    q2 = quat_norm(q2)

    # create storage for quaternion and divide into scalar and vector parts
    prod = np.zeros(q1.shape)
    s1 = q1[:, 0]
    s2 = q2[:, 0]
    v1 = q1[:, 1:4]
    v2 = q2[:, 1:4]
    del q1, q2

    # calculate product quaternion's elements
    s3 = s1*s2 - np.sum(v1*v2, axis=1)
    v3 = v2*s1[:, np.newaxis] + v1*s2[:, np.newaxis] + np.cross(v1, v2)
    prod = np.hstack((s3.reshape(len(s1), 1), v3))

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

    # create storage for quaternion and divide into scalar and vector parts
    prod = np.zeros(q1.shape)
    s1 = q1[:, 0]
    s2 = q2[:, 0]
    v1 = q1[:, 1:4]
    v2 = q2[:, 1:4]
    del q1, q2

    # calculate product quaternion's elements
    s3 = s1*s2 - np.sum(v1*v2, axis=1)
    v3 = v2*s1[:, np.newaxis] + v1*s2[:, np.newaxis] + np.cross(v1, v2)
    prod = np.hstack((s3.reshape(len(s1), 1), v3))

    return prod


def quat_multi_prod(*quaternions):
    if len(quaternions) == 0:
        raise ValueError('Must supply at least one argument')
    elif len(quaternions) == 1:
        return quaternions[0]
    else:
        return quat_prod(quaternions[0], quat_multi_prod(*quaternions[1:]))


def quat_norm(q):
    """
    Function that normalizes a quaternion
    """
    
    # Find the magnitude and divide
    mag = np.linalg.norm(q, axis=1).reshape(-1, 1)
    qn = q/mag
    
    return qn


def quat_conj(q):
    """
    Function that returns conjugate of input quaternion.
    """

    # first term unchanged, last three terms are negative of inital quaternion
    conj = np.vstack([q[:, 0], -q[:, 1], -q[:, 2], -q[:, 3]]).T

    # normalize the conjugate
    conj = quat_norm(conj)
    
    return conj


def vect_rot(v, q):
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
    # Convert 3D matrix to "quaternion" form
    V = np.hstack((np.zeros((len(v), 1)), v))
    del v
    q = quat_norm(q) # Normalize the rotation quaternion

    # rotate vector as rot_vect = QVQ^(-1) and extract 3D values
    rot_vect = quat_prod(_vector_quat_prod(quat_conj(q), V), q)
    rot_vect = rot_vect[:, 1:]

    return rot_vect


def find_rot(q1, q2):
    """
    Function that finds rotation between first and second quaternions.
    """

    # Create storage vector for product
    rot_q = np.zeros(q1.shape)

    # rotation between normalized quaternions Q1 and Q2 as rot_q=Q1^(-1)Q2
    rot_q = quat_prod(quat_conj(quat_norm(q1)), quat_norm(q2))

    return rot_q


def quat_avg(data):
    """
    Function that "averages" a column of quaternions into a single quaternion.
    """

    # Average data along columns
    avg_quat = np.nanmean(data, 0).reshape(1, -1)
    del data

    # Normalize the single quaternion produced
    avg_quat = quat_norm(avg_quat)

    return avg_quat


def hamilton_product(p, q):
    """
    Perform the Hamilton product between quaternions.

    Parameters
    ----------
    p, q : array_like, list of array_like
        Quaternions.

    Returns
    -------
    output : numpy.ndarray
        The Hamilton product of p and q. If the are arrays of quaternions,
        the array of the products is returned.
    """
    p = np.asanyarray(p, dtype=float)
    q = np.asanyarray(q, dtype=float)

    w = p[...,0]*q[...,0] - p[...,1]*q[...,1] - p[...,2]*q[...,2] - p[...,3]*q[...,3]
    x = p[...,0]*q[...,1] + p[...,1]*q[...,0] + p[...,2]*q[...,3] - p[...,3]*q[...,2]
    y = p[...,0]*q[...,2] - p[...,1]*q[...,3] + p[...,2]*q[...,0] + p[...,3]*q[...,1]
    z = p[...,0]*q[...,3] + p[...,1]*q[...,2] - p[...,2]*q[...,1] + p[...,3]*q[...,0]
    return np.squeeze(np.stack((w, x, y, z), axis=-1))


def quat_conjugate(q):
    """Compute the conjugate of the given quaternion(s)."""
    return np.asanyarray(q, dtype=float) * np.array((1., -1., -1., -1.))


def quat_interp(p, q, alpha):
    """
    Perform a SPHERICAL LINEAR INTERPOLATION (SLERP) of two quaternions.

    Parameters
    ----------
    p, q : array_like
        Quaternions.
    alpha : number, list of numbers
        The interpolation coefficient(s).

    Returns
    -------
    output : numpy.ndarray
        Interpolation between p and q at alpha.
    """
    p = np.asanyarray(p, dtype=float)
    q = np.asanyarray(q, dtype=float)

    # Normalize the quaternions
    p = p / np.linalg.norm(p)
    q = q / np.linalg.norm(q)

    # Abs of dot product between p and q
    dot_pr = p @ q
    abs_dot = np.abs(dot_pr)

    p = p[np.newaxis,:]
    q = q[np.newaxis,:]
    alpha = np.asanyarray(alpha)
    alpha = alpha[...,np.newaxis]

    # Setup scale factors s and t
    if abs_dot >= 1:
        s = 1 - alpha
        t = alpha
    else:
        # Theta is the angle between the two quaternions
        theta = np.arccos(abs_dot)
        sin_theta = np.sin(theta)
        s = np.sin((1-alpha)*theta) / sin_theta
        t = np.sin(alpha*theta) / sin_theta

    # Sign inversion if needed
    if dot_pr < 0:
        t = -t

    # Interpolation and normalisation of output quaternion
    out = p * s + q * t
    return np.squeeze(out / np.linalg.norm(out, axis=1, keepdims=True))
