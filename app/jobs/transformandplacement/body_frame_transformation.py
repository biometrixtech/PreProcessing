import numpy as np
import pandas as pd


def body_frame_tran(data, qC0, qCH, qC2):
    """
    Compute Body Frame Transformation both for orientations and accelerations,
    using the whole quaternion at reset index point.

    Parameters
    ----------
    data : was array_like, all raw data matrix (n x 25). Now a pandas dataframe
    qc0, qc2 : reference quaternions for ankle sensors 0, 2; lists with 4 elements in order of w,x,y,z
    qCH : reference quarternion for hip sensor, list with 4 elements in order of w,x,y,z

    Returns
    -------
    output : numpy.ndarray
        Compensated data matrix (n x 25).
    """
    data = np.asanyarray(data.values)
    output = np.copy(data)
    z = np.zeros(data.shape[0])

    # Reset Orientation
    # qC0 = data[reset_index, 5: 9]
    # qCH = data[reset_index,13:17]
    # qC2 = data[reset_index,21:25]

    # Orientations correction: left, hip, right
    # ensure order of columns matches what's expected

    output[:, 5: 9] = hamilton_product(data[:, 5: 9], quat_conj(qC0))
    output[:,13:17] = hamilton_product(data[:,13:17], quat_conj(qCH))
    output[:,21:25] = hamilton_product(data[:,21:25], quat_conj(qC2))

    output[:, 5: 9] /= np.linalg.norm(output[:, 5: 9], axis=1, keepdims=True)
    output[:,13:17] /= np.linalg.norm(output[:, 13:17], axis=1, keepdims=True)
    output[:,21:25] /= np.linalg.norm(output[:, 21:25], axis=1, keepdims=True)

    # Accelerations correction: left, hip, right
    output[:, 2: 5] = hamilton_product(hamilton_product(qC0, np.c_[z, data[:, 2: 5]]), quat_conj(qC0))[..., 1:]
    output[:,10:13] = hamilton_product(hamilton_product(qCH, np.c_[z, data[:, 10:13]]), quat_conj(qCH))[..., 1:]
    output[:,18:21] = hamilton_product(hamilton_product(qC2, np.c_[z, data[:, 18:21]]), quat_conj(qC2))[..., 1:]

    return output


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


def quat_conj(q):
    """Compute the conjugate of the given quaternion(s)."""
    return np.asanyarray(q, dtype=float) * np.array((1., -1., -1., -1.))
