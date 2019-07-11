from numpy import newaxis as _nx

import numpy as np
from utils.quaternion_operations import hamilton_product, quat_conjugate


def axl_correction(q_corr, axl_heading_corr):
    """
    Acceleration corection with orientations drift corrected.

    Parameters
    ----------
    q_corr : array_like
        Orientations drift corrected.
    axl_heading_corr : array_like
        Accelerations heading corrected.

    Returns
    -------
    axl_corr : array_like
        Accelerations corrected and gravity comnpensated.
    """
    q_corr = np.asanyarray(q_corr, dtype=float)
    axl_heading_corr = np.asanyarray(axl_heading_corr, dtype=float)
    z = np.zeros(axl_heading_corr.shape[0])

    axl_corr = hamilton_product(hamilton_product(q_corr, np.c_[z, axl_heading_corr]), quat_conjugate(q_corr))[..., 1:]
    axl_corr -= [0, 0, 1000]
    return axl_corr