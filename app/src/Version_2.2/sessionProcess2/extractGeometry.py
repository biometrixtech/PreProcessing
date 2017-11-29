# -*- coding: utf-8 -*-
"""
Created on Thu Nov 16 12:00:29 2017

@author: court
"""

import numpy as np
import quatOps as qo


def extract_geometry(qL, qH, qR):
    '''
    Function to interpret quaternion data geometrically
    
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

    '''

    k_v = np.array([0, 0, 0, 1]).reshape(-1, 4)
    
    v_kR = qo.quat_prod(qo.quat_prod(qR.reshape(-1, 4), k_v),
                        qo.quat_conj(qR.reshape(-1, 4)));
    v_kL = qo.quat_prod(qo.quat_prod(qL.reshape(-1, 4), k_v),
                        qo.quat_conj(qL.reshape(-1, 4)));
    v_kH = qo.quat_prod(qo.quat_prod(qH.reshape(-1, 4), k_v),
                        qo.quat_conj(qH.reshape(-1, 4)));
    
    j_v = np.array([0, 0, 1, 0]).reshape(-1, 4)
    
    v_jR = qo.quat_prod(qo.quat_prod(qR.reshape(-1, 4), j_v),
                        qo.quat_conj(qR.reshape(-1, 4)));
    v_jL = qo.quat_prod(qo.quat_prod(qL.reshape(-1, 4), j_v),
                        qo.quat_conj(qL.reshape(-1, 4)));
    v_jH = qo.quat_prod(qo.quat_prod(qH.reshape(-1, 4), j_v),
                        qo.quat_conj(qH.reshape(-1, 4)));
    
    i_v = np.array([0, 1, 0, 0]).reshape(-1, 4)
    
    v_iR = qo.quat_prod(qo.quat_prod(qR.reshape(-1, 4), i_v),
                        qo.quat_conj(qR.reshape(-1, 4)))
    v_iL = qo.quat_prod(qo.quat_prod(qL.reshape(-1, 4), i_v),
                        qo.quat_conj(qL.reshape(-1, 4)))
    v_iH = qo.quat_prod(qo.quat_prod(qH.reshape(-1, 4), i_v),
                        qo.quat_conj(qH.reshape(-1, 4)))
    
    n = len(qH)
    z_cross_L = np.zeros((n, 1))
    z_cross_R = np.zeros((n, 1))
    z_cross_H = np.zeros((n, 1))
    
    z_cross_L[v_kL[:, 3] < 0] = 1
    z_cross_H[v_kH[:, 3] < 0] = 1
    z_cross_R[v_kR[:, 3] < 0] = 1
    
    flexion_L = np.arctan2(v_iL[:, 3], (np.sqrt(v_iL[:, 1]**2
                           + v_iL[:, 2]**2))) * 180 / np.pi;
    flexion_H = np.arctan2(v_iH[:, 3], (np.sqrt(v_iH[:, 1]**2
                           + v_iH[:, 2]**2))) * 180 / np.pi;
    flexion_R = np.arctan2(v_iR[:, 3], (np.sqrt(v_iR[:, 1]**2
                           + v_iR[:, 2]**2))) * 180 / np.pi;
    
    adduction_L = np.arctan2(v_jL[:, 3], np.sqrt(v_jL[:, 1]**2
                             + v_jL[:, 2]**2)) * 180 / np.pi
    adduction_H = np.arctan2(v_jH[:, 3], np.sqrt(v_jH[:, 1]**2
                             + v_jH[:, 2]**2)) * 180 / np.pi
    adduction_R = np.arctan2(v_jR[:, 3], np.sqrt(v_jR[:, 1]**2
                             + v_jR[:, 2]**2)) * 180 / np.pi
    
    for i in range(n):
    
        # Left foot
        if z_cross_L[i] == 1 and z_cross_L[i - 1] == 0:
    
            # Found a window - search for the values at the boundaries
            bound2_index = i;
            
            while z_cross_L[bound2_index] == 1 and z_cross_L[bound2_index + 1] == 1 and bound2_index < (len(z_cross_L) - 2):
                    bound2_index = bound2_index + 1
    
            if flexion_L[i] < 0:
                if flexion_L[i - 1] < flexion_L[bound2_index + 1]:
                    mirroring_value = flexion_L[i - 1];
                else:
                    mirroring_value = flexion_L[bound2_index + 1]
    
            else:
                if flexion_L[i - 1] > flexion_L[bound2_index + 1]:
                    mirroring_value = flexion_L[i - 1]
                else:
                    mirroring_value = flexion_L[bound2_index + 1]
    
            for k in range(i, bound2_index):
                flexion_L[k] = mirroring_value - (flexion_L[k] - mirroring_value)
    
            # Move forward
            i = bound2_index + 1
    
    for i in range(n):
        # Right foot
        if z_cross_R[i] == 1 and z_cross_R[i - 1] == 0:
    
            # Found a window - search for the values at the boundaries
            bound2_index = i
            
            while z_cross_R[bound2_index] == 1 and z_cross_R[bound2_index + 1] == 1 and bound2_index < (len(z_cross_R) - 2):
                    bound2_index = bound2_index + 1
    
            if flexion_R[i] < 0:
                if flexion_R[i - 1] < flexion_R[bound2_index + 1]:
                    mirroring_value = flexion_R[i - 1]
                else:
                    mirroring_value = flexion_R[bound2_index + 1]
    
            else:
                if flexion_R[i - 1] > flexion_R[bound2_index + 1]:
                    mirroring_value = flexion_R[i - 1]
                else:
                    mirroring_value = flexion_R[bound2_index + 1]
            
            for k in range(i, bound2_index):
                flexion_R[k] = mirroring_value - (flexion_R[k] - mirroring_value)
    
            # Move forward
            i  = bound2_index + 1
    
    for i in range(n):
    
        # Hip
        if z_cross_H[i] == 1 and z_cross_H[i - 1] == 0:
            # Found a window - search for the values at the boundaries
            bound2_index = i
            
            while z_cross_H[bound2_index] == 1 and z_cross_H[bound2_index + 1] == 1 and bound2_index < (len(z_cross_H) - 2):
                    bound2_index = bound2_index + 1    
    
            if flexion_H[i] < 0:
                if flexion_H[i - 1] < flexion_H[bound2_index + 1]:
                    mirroring_value = flexion_H[i - 1]
                else:
                    mirroring_value=flexion_H[bound2_index + 1]
            else:
                if flexion_H[i - 1] > flexion_H[bound2_index + 1]:
                    mirroring_value = flexion_H[i - 1]
                else:
                    mirroring_value = flexion_H[bound2_index + 1]
    
            for k in range(i, bound2_index):
                flexion_H[k] = mirroring_value - (flexion_H[k] - mirroring_value)
            
            # Move forward
            i = bound2_index + 1
    
    flexion_L = -flexion_L
    flexion_H = -flexion_H
    flexion_R = -flexion_R
    
    return adduction_L, flexion_L, adduction_H, flexion_H, adduction_R, flexion_R
