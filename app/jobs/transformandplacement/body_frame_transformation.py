import numpy as np

from utils.quaternion_operations import hamilton_product, quat_conjugate


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

    output[:, 5: 9] = hamilton_product(data[:, 5: 9], quat_conjugate(qC0))
    output[:,13:17] = hamilton_product(data[:, 13:17], quat_conjugate(qCH))
    output[:,21:25] = hamilton_product(data[:, 21:25], quat_conjugate(qC2))

    output[:, 5: 9] /= np.linalg.norm(output[:, 5: 9], axis=1, keepdims=True)
    output[:,13:17] /= np.linalg.norm(output[:, 13:17], axis=1, keepdims=True)
    output[:,21:25] /= np.linalg.norm(output[:, 21:25], axis=1, keepdims=True)

    # Accelerations correction: left, hip, right
    output[:, 2: 5] = hamilton_product(hamilton_product(qC0, np.c_[z, data[:, 2: 5]]), quat_conjugate(qC0))[..., 1:]
    output[:,10:13] = hamilton_product(hamilton_product(qCH, np.c_[z, data[:, 10:13]]), quat_conjugate(qCH))[..., 1:]
    output[:,18:21] = hamilton_product(hamilton_product(qC2, np.c_[z, data[:, 18:21]]), quat_conjugate(qC2))[..., 1:]

    return output
