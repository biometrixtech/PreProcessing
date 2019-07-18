import logging
import numpy as np
from utils.quaternion_conversions import quat_from_euler_angles, quat_as_euler_angles
from utils.quaternion_operations import hamilton_product, quat_conjugate
from .exceptions import HeadingDetectionException

_logger = logging.getLogger(__name__)
from numba import jit as _jit


def heading_hip_finder(hip_ref_quat):
    """
    Heading values finder for hip sensor.

    Parameters
    ----------
    hip_ref_quat : array_like
        Raw hip sensor reference quaternion

    Returns
    -------
    hip_heading_quat : array_like
        Heading hip quaternion.
    """
    # k versor rotation
    k = hamilton_product(hamilton_product(hip_ref_quat, [0, 0, 0, 1]), quat_conjugate(hip_ref_quat))
    # Heading quaternion computation
    hip_heading_quat = quat_from_euler_angles(np.degrees(np.arctan2(k[2], k[1])) - 180, [0, 0, 1])
    return hip_heading_quat


def heading_foot_finder(q_refC0, q_refC2, start_marching_phase, stop_marching_phase):
    """
    Heading values finder for foot sensors

    Parameters
    ----------
    q_refC0, q_refC2 : array_like
        Data BFT compensated left and right foot (data = [q]).

    start_marching_phase, stop_marching_phase : number
        index values of start and stopping samples of marching phase

    Returns
    -------
    qH0, qH2 : array_like
        Heading quaternions for left foot and right foot.
    """

    # if np.isnan(start_marching_phase) or np.isnan(stop_marching_phase):
    #     _logger.warning("No valid marching phase interval found in either foot sensors data")
    #     qH0 = np.array((1., 0., 0., 0.))
    #     qH2 = np.array((1., 0., 0., 0.))
    # else:
    try:
        qH0 = heading_calculus(q_refC0[start_marching_phase:stop_marching_phase,:])
    except HeadingDetectionException:
        raise HeadingDetectionException("Could not detect heading for sensor0")
    try:
        qH2 = heading_calculus(q_refC2[start_marching_phase:stop_marching_phase,:])
    except HeadingDetectionException:
        raise HeadingDetectionException("Could not detect heading for sensor2")

    return qH0, qH2


def heading_calculus(q):
    """
    Find heading value exploiting the marching phase protocol.

    Parameters
    ----------
    q : array_like
        Quaternion BF transformed between start and stop marching phase.

    Returns
    -------
    q_H : numpy.ndarray
        Quaternion of heading rotation.

    See Also
    --------
    find_marching
    heading_detection
    """
    ## Variables Initialization
    pitch_threshold = 20
    q_yaw = np.zeros_like(q)
    q_yaw[:,0] = 1

    # Compute delta quaternion for each couple, with q[0,:] fixed
    q_D = hamilton_product(quat_conjugate(q[0,:]), q)
    qyp = np.apply_along_axis(lambda q: heading_detection(q, 500), 1, q_D)
    qy = qyp[:,0,:]
    qp = qyp[:,1,:]
    a_tmp = quat_as_euler_angles(qp)
    sel = a_tmp[:,1] > pitch_threshold
    q_yaw[sel] = qy[sel]
    q_pitch = qp

    a_yaw = quat_as_euler_angles(q_yaw)
    # Discard yaw angles that are zeros
    yaw_result = a_yaw[a_yaw[:,2] != 0][:,2]

    # Search for any outliers
    m_yaw = np.median(yaw_result)
    sel = np.logical_and(np.abs(m_yaw - a_yaw[:,2]) > 90, a_yaw[:,2] != 0)
    q_yaw[sel] = hamilton_product([0, 0, 0, 1], q_yaw[sel])
    q_pitch[sel] = quat_conjugate(q_pitch[sel])

    a_yaw = quat_as_euler_angles(q_yaw)
    # Discard yaw angles that are zeros
    yaw_result = a_yaw[a_yaw[:,2] != 0][:,2]
    yaw_mean = np.mean(yaw_result)

    # Set distribution std threshold
    std_TH = 10

    if np.std(yaw_result) > std_TH or np.isnan(yaw_mean):
        raise HeadingDetectionException()
    else:
        qH = quat_from_euler_angles(yaw_mean, [0, 0, 1])

    return qH


def heading_detection(q_delta, niter):
    """Heading detection algorithm."""

    x = _gd(q_delta, niter)
    q_yaw = np.array((x[0], 0, 0, x[1]))
    q_pitch = np.array((x[2], 0, x[3], 0))

    if q_pitch[0] * q_pitch[2] < 0:
        q_yaw = hamilton_product([0, 0, 0, 1], q_yaw)
        q_pitch = quat_conjugate(q_pitch)

    return q_yaw, q_pitch


@_jit("f8[::1](f8[::1], intc)", nopython=True, cache=True)
def _gd(q_delta, niter):
    # Bear in mind that that when q_yaw corresponds to x(1) the algorithm will fail
    x = np.array((1., 0., 1., 0.)) # Initialization of x as identity quaternions
    # delta quaternion
    qdw, qdi, qdj, qdk = q_delta

    # Gradient descent step factor
    gamma = 0.2

    J = np.empty((6, 4))
    f = np.empty(6)
    for _ in range(1, niter):
        # Update of current iteration variables
        qyw, qyk, qpw, qpj = x
        # Jacobian definition
        J[0,:] = [2*qdw*qyw, 2*qdw*qyk, -1, 0]
        J[1,:] = [2*qdj*qyk+2*qdi*qyw, 2*qdj*qyw-2*qdi*qyk, 0, 0]
        J[2,:] = [2*qdj*qyw-2*qdi*qyk, -2*qdj*qyk-2*qdi*qyw, 0, -1]
        J[3,:] = [2*qdk*qyw, 2*qdk*qyk, 0, 0]
        J[4,:] = [2*qyw, 2*qyk, 0, 0]
        J[5,:] = [0, 0, 2*qpw, 2*qpj]
        # Minimization function
        f[0] = qdw*qyk**2 + qdw*qyw**2 - qpw
        f[1] = -qdi*qyk**2 + 2*qdj*qyk*qyw + qdi*qyw**2
        f[2] = -qdj*qyk**2 - 2*qdi*qyk*qyw + qdj*qyw**2 - qpj
        f[3] = qdk*qyk**2 + qdk*qyw**2
        f[4] = qyk**2 + qyw**2 - 1
        f[5] = qpj**2 + qpw**2 - 1
        # Update step
        x -= gamma * J.T @ f

    return x
