# -*- coding: utf-8 -*-
"""
Created on Thu Nov 16 12:00:29 2017

@author: court
"""
from aws_xray_sdk.core import xray_recorder
import numpy as np
import utils.quaternion_operations as qo


@xray_recorder.capture('app.jobs.sessionprocess.detect_geometry.extract_geometry')
def extract_geometry(qL, qH, qR):
    """
    Function to interpret quaternion data geometrically.
    Explanation given here: https://sites.google.com/a/biometrixtech.com/wiki/home/preprocessing/anatomical/methods-tried/general-math-methods/geometry-extraction

    Args:
        qL = left foot quaternions
        qH = hip quaternions
        qR = right foot quaternions

    Returns:
        adduction_L: tilt of left foot about x axis
        flexion_L: tilt of left foot about y axis
        adduction_H: tilt of hip about x axis
        flexion_H: tilt of hip about y axis
        adduction_R: tilt of right foot about x axis
        flexion_R: tilt of right foot about y axis

    """

    k_v = np.array([0, 0, 0, 1]).reshape(-1, 4)
    
    v_kR = qo.quat_prod(qo.quat_prod(qR.reshape(-1, 4), k_v),
                        qo.quat_conj(qR.reshape(-1, 4)))
    v_kL = qo.quat_prod(qo.quat_prod(qL.reshape(-1, 4), k_v),
                        qo.quat_conj(qL.reshape(-1, 4)))
    v_kH = qo.quat_prod(qo.quat_prod(qH.reshape(-1, 4), k_v),
                        qo.quat_conj(qH.reshape(-1, 4)))
    
    j_v = np.array([0, 0, 1, 0]).reshape(-1, 4)
    
    v_jR = qo.quat_prod(qo.quat_prod(qR.reshape(-1, 4), j_v),
                        qo.quat_conj(qR.reshape(-1, 4)))
    v_jL = qo.quat_prod(qo.quat_prod(qL.reshape(-1, 4), j_v),
                        qo.quat_conj(qL.reshape(-1, 4)))
    v_jH = qo.quat_prod(qo.quat_prod(qH.reshape(-1, 4), j_v),
                        qo.quat_conj(qH.reshape(-1, 4)))
    
    i_v = np.array([0, 1, 0, 0]).reshape(-1, 4)
    
    v_iR = qo.quat_prod(qo.quat_prod(qR.reshape(-1, 4), i_v),
                        qo.quat_conj(qR.reshape(-1, 4)))
    v_iL = qo.quat_prod(qo.quat_prod(qL.reshape(-1, 4), i_v),
                        qo.quat_conj(qL.reshape(-1, 4)))
    v_iH = qo.quat_prod(qo.quat_prod(qH.reshape(-1, 4), i_v),
                        qo.quat_conj(qH.reshape(-1, 4)))
    
    n = len(qH)
    z_cross_l = np.zeros((n, 1))
    z_cross_h = np.zeros((n, 1))
    z_cross_r = np.zeros((n, 1))
    
    z_cross_l[v_kL[:, 3] < 0] = 1
    z_cross_h[v_kH[:, 3] < 0] = 1
    z_cross_r[v_kR[:, 3] < 0] = 1
    
    flexion_l = np.arctan2(v_iL[:, 3], (np.sqrt(v_iL[:, 1] ** 2 + v_iL[:, 2] ** 2))) * 180 / np.pi
    flexion_h = np.arctan2(v_iH[:, 3], (np.sqrt(v_iH[:, 1]**2 + v_iH[:, 2]**2))) * 180 / np.pi
    flexion_r = np.arctan2(v_iR[:, 3], (np.sqrt(v_iR[:, 1]**2 + v_iR[:, 2]**2))) * 180 / np.pi
    
    adduction_l = np.arctan2(v_jL[:, 3], np.sqrt(v_jL[:, 1]**2 + v_jL[:, 2]**2)) * 180 / np.pi
    adduction_h = np.arctan2(v_jH[:, 3], np.sqrt(v_jH[:, 1]**2 + v_jH[:, 2]**2)) * 180 / np.pi
    adduction_r = np.arctan2(v_jR[:, 3], np.sqrt(v_jR[:, 1]**2 + v_jR[:, 2]**2)) * 180 / np.pi
    
    for i in range(n - 1):
    
        # Left foot
        if z_cross_l[i] == 1 and z_cross_l[i - 1] == 0:
    
            # Found a window - search for the values at the boundaries
            bound2_index = i
            
            while z_cross_l[bound2_index] == 1 and z_cross_l[bound2_index + 1] == 1 and bound2_index < (len(z_cross_l) - 2):
                    bound2_index = bound2_index + 1
    
            if flexion_l[i] < 0:
                if flexion_l[i - 1] < flexion_l[bound2_index + 1]:
                    mirroring_value = flexion_l[i - 1]
                else:
                    mirroring_value = flexion_l[bound2_index + 1]
    
            else:
                if flexion_l[i - 1] > flexion_l[bound2_index + 1]:
                    mirroring_value = flexion_l[i - 1]
                else:
                    mirroring_value = flexion_l[bound2_index + 1]
    
            for k in range(i, bound2_index):
                flexion_l[k] = mirroring_value - (flexion_l[k] - mirroring_value)

    for i in range(n - 1):
        # Right foot
        if z_cross_r[i] == 1 and z_cross_r[i - 1] == 0:
    
            # Found a window - search for the values at the boundaries
            bound2_index = i
            
            while z_cross_r[bound2_index] == 1 and z_cross_r[bound2_index + 1] == 1 and bound2_index < (len(z_cross_r) - 2):
                    bound2_index = bound2_index + 1
    
            if flexion_r[i] < 0:
                if flexion_r[i - 1] < flexion_r[bound2_index + 1]:
                    mirroring_value = flexion_r[i - 1]
                else:
                    mirroring_value = flexion_r[bound2_index + 1]
    
            else:
                if flexion_r[i - 1] > flexion_r[bound2_index + 1]:
                    mirroring_value = flexion_r[i - 1]
                else:
                    mirroring_value = flexion_r[bound2_index + 1]
            
            for k in range(i, bound2_index):
                flexion_r[k] = mirroring_value - (flexion_r[k] - mirroring_value)

    for i in range(n - 1):
    
        # Hip
        if z_cross_h[i] == 1 and z_cross_h[i - 1] == 0:
            # Found a window - search for the values at the boundaries
            bound2_index = i
            
            while z_cross_h[bound2_index] == 1 and z_cross_h[bound2_index + 1] == 1 and bound2_index < (len(z_cross_h) - 2):
                    bound2_index = bound2_index + 1    
    
            if flexion_h[i] < 0:
                if flexion_h[i - 1] < flexion_h[bound2_index + 1]:
                    mirroring_value = flexion_h[i - 1]
                else:
                    mirroring_value = flexion_h[bound2_index + 1]
            else:
                if flexion_h[i - 1] > flexion_h[bound2_index + 1]:
                    mirroring_value = flexion_h[i - 1]
                else:
                    mirroring_value = flexion_h[bound2_index + 1]
    
            for k in range(i, bound2_index):
                flexion_h[k] = mirroring_value - (flexion_h[k] - mirroring_value)

    flexion_l = -flexion_l / 180 * np.pi
    flexion_h = -flexion_h / 180 * np.pi
    flexion_r = -flexion_r / 180 * np.pi
    adduction_l = adduction_l / 180 * np.pi
    adduction_h = adduction_h / 180 * np.pi
    adduction_r = adduction_r / 180 * np.pi
    
    return adduction_l, flexion_l, adduction_h, flexion_h, adduction_r, flexion_r
