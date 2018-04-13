# -*- coding: utf-8 -*-
"""
Created on Thu Nov 16 12:00:29 2017

@author: court
"""

import numpy as np
import quatOps as qo

def extract_geometry(quats):
    '''
    Function to interpret quaternion data geometrically.
    Explanation given here: https://sites.google.com/a/biometrixtech.com/wiki/home/preprocessing/anatomical/methods-tried/general-math-methods/geometry-extraction
    
    Args:
        quats = quaternions

    Returns:
        adduction: tilt of hip about x axis
        flexion: tilt of hip about y axis

    '''

    k_v = np.array([0, 0, 0, 1]).reshape(-1, 4)

    v_k = qo.quat_prod(qo.quat_prod(quats.reshape(-1, 4), k_v),
                       qo.quat_conj(quats.reshape(-1, 4)));
    
    j_v = np.array([0, 0, 1, 0]).reshape(-1, 4)

    v_j = qo.quat_prod(qo.quat_prod(quats.reshape(-1, 4), j_v),
                       qo.quat_conj(quats.reshape(-1, 4)));
    
    i_v = np.array([0, 1, 0, 0]).reshape(-1, 4)

    v_i = qo.quat_prod(qo.quat_prod(quats.reshape(-1, 4), i_v),
                       qo.quat_conj(quats.reshape(-1, 4)))
    
    n = len(quats)
    z_cross = np.zeros((n, 1))
    z_cross[v_k[:, 3] < 0] = 1
    

    flexion = np.arctan2(v_i[:, 3], (np.sqrt(v_i[:, 1]**2
                           + v_i[:, 2]**2))) * 180 / np.pi
    adduction = np.arctan2(v_j[:, 3], np.sqrt(v_j[:, 1]**2
                             + v_j[:, 2]**2)) * 180 / np.pi
    
    for i in range(n - 1):
    
        # Hip
        if z_cross[i] == 1 and z_cross[i - 1] == 0:
            # Found a window - search for the values at the boundaries
            bound2_index = i
            
            while z_cross[bound2_index] == 1 and z_cross[bound2_index + 1] == 1 and bound2_index < (len(z_cross) - 2):
                    bound2_index = bound2_index + 1    
    
            if flexion[i] < 0:
                if flexion[i - 1] < flexion[bound2_index + 1]:
                    mirroring_value = flexion[i - 1]
                else:
                    mirroring_value=flexion[bound2_index + 1]
            else:
                if flexion[i - 1] > flexion[bound2_index + 1]:
                    mirroring_value = flexion[i - 1]
                else:
                    mirroring_value = flexion[bound2_index + 1]
    
            for k in range(i, bound2_index):
                flexion[k] = mirroring_value - (flexion[k] - mirroring_value)
            
            # Move forward
            i = bound2_index + 1

    flexion = -flexion / 180 * np.pi
    adduction = adduction / 180 * np.pi
    
    return adduction, flexion
