import logging
import numpy as np
from utils.quaternion_conversions import quat_from_euler_angles, quat_as_euler_angles
from utils.quaternion_operations import hamilton_product, quat_conjugate, quat_interp
from .exceptions import HeadingDetectionException

_logger = logging.getLogger(__name__)
# from numba import jit as _jit


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
    
    # Initialize
    q_test = np.zeros((yaw_result.size , 4))
    q_test[:,0] = 1
    q_pos = np.zeros((1 , 4))
    q_pos[:,0] = 1
    q_neg = np.zeros((1 , 4))
    q_neg[:,0] = 1
    nr_pos = 0
    nr_neg = 0
    # Separe positive and negative heading, to do separate statistic
    for j in range(0, yaw_result.size):
        q_test = quat_from_euler_angles(yaw_result[j],[0, 0, 1])
        # Count positive and negative yaw
        if q_test[:,0]*q_test[:,3]>0 and q_test[:,1]==0 and q_test[:,2]==0:
            nr_pos+=1
            q_pos = np.concatenate((q_pos, q_test),axis=0)
        else:
            nr_neg+=1
            q_neg = np.concatenate((q_neg, q_test),axis=0)
            
    
    ## Discard first identity quaternion
    q_pos=q_pos[1:nr_pos+1]
    q_neg=q_neg[1:nr_neg+1]
    # Control two distribution spread    
    # Set distribution std threshold
    std_TH = 10
    a_pos = quat_as_euler_angles(q_pos)
    a_pos = a_pos[a_pos[:,2] != 0][:,2]
    a_neg = quat_as_euler_angles(q_neg)
    a_neg = a_neg[a_neg[:,2] != 0][:,2]

    
    # Positive
    if a_pos.size != 0:
        m_yaw_pos = np.median(a_pos)
        if np.std(a_pos) < std_TH:
            ok_pos = True
        else:
            # Try to give an heading value anyway cutting distribution tails, but warning
            temp=a_pos[np.abs(a_pos-m_yaw_pos)<15]
            if np.std(temp)<std_TH:
                q_pos=[]
                q_pos = quat_from_euler_angles(temp, [0, 0, 1])
                nr_pos=temp.size
                ok_pos = True
                _logger.warning("Not a good heading distribution.")
            else:
                ok_pos = False
    else:
        ok_pos = False
    
    # Negative
    if a_neg.size != 0:
        m_yaw_neg = np.median(a_neg)
        if np.std(a_neg) < std_TH:
            ok_neg = True
        else:
            # Try to give an heading value anyway cutting distribution tails, but warning
            temp=a_neg[np.abs(a_neg-m_yaw_neg)<15]
            if np.std(temp)<std_TH:
                q_neg=[]
                q_neg = quat_from_euler_angles(temp, [0, 0, 1])
                nr_neg=temp.size
                ok_neg = True
                _logger.warning("Not a good heading distribution.")
            else:
                ok_neg = False
    else:
        ok_neg = False
            
    if not ok_pos and  not ok_neg:
        _logger.warning("Heading value not found")
        # Worse case, no valid heading found
        raise HeadingDetectionException()

        qH = np.array((1, 0, 0, 0))
    else:
        # Initialize avg quaternions and weights
        q_avg = np.array((1, 0, 0, 0))
        q_avg_pos = np.array((1, 0, 0, 0))
        q_avg_neg = np.array((1, 0, 0, 0))
        w_pos=nr_pos/(nr_pos+nr_neg)
        w_neg=nr_neg/(nr_pos+nr_neg)
        
        if ok_pos==True:
            # Positive avg quaternion
            for j in range(0, nr_pos):
                q_temp=quat_interp([1, 0, 0, 0],q_pos[j,:],1/nr_pos)
                q_avg_pos=hamilton_product(q_avg_pos,q_temp)
        else:
            q_avg_pos = np.array((1, 0, 0, 0))
            w_pos=0
        
        if ok_neg==True:
            # Positive avg quaternion
            for j in range(0, nr_neg):
                q_temp=quat_interp([1, 0, 0, 0],q_neg[j,:],1/nr_neg)
                q_avg_neg=hamilton_product(q_avg_neg,q_temp)
        else:
            q_avg_neg = np.array((1, 0, 0, 0))
            w_neg = 0
        
        ## Compute weighted average
        q_avg=quat_interp(q_avg_pos,q_avg_neg,w_neg)
        a_yaw = quat_as_euler_angles(q_avg)
        # Discard yaw angles that are zeros
        yaw_result = a_yaw[2]
        qH = quat_from_euler_angles(yaw_result, [0, 0, 1])        

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


# @_jit("f8[::1](f8[::1], intc)", nopython=True, cache=True)
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
