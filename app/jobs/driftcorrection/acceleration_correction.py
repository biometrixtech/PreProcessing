from numpy import newaxis as _nx

import numpy as np
from utils.quaternion_operations import hamilton_product, quat_conjugate
from utils.quaternion_conversions import quat_as_euler_angles, quat_from_euler_angles


def axl_correction(q_corr, axl_heading_corr, Foot):
    """
    Acceleration corection with orientations drift corrected.

    Parameters
    ----------
    q_corr : array_like
        Orientations drift corrected.
    axl_heading_corr : array_like
        Accelerations heading corrected.
    Foot : logic_value
        Define foot or hip sensor 

    Returns
    -------
    axl_corr : array_like
        Accelerations corrected and gravity comnpensated.
    """
    q_corr = np.asanyarray(q_corr, dtype=float)
    axl_heading_corr = np.asanyarray(axl_heading_corr, dtype=float)
    z = np.zeros(axl_heading_corr.shape[0])
    
    if Foot:
        axl_corr = hamilton_product(hamilton_product(q_corr, np.c_[z, axl_heading_corr]), quat_conjugate(q_corr))[...,1:]
        axl_corr -= [0, 0, 1000]
    else:
        a_temp = quat_as_euler_angles(q_corr)
        q_temp_yaw =  quat_from_euler_angles(a_temp[...,2], [0, 0, 1])
        axl_temp = hamilton_product(hamilton_product(q_corr, np.c_[z, axl_heading_corr]), quat_conjugate(q_corr))[...,1:]
        axl_corr = hamilton_product(hamilton_product(quat_conjugate(q_temp_yaw),np.c_[z, axl_temp]), q_temp_yaw)[...,1:]
        axl_corr -= [0, 0, 1000]        
    
    return axl_corr
