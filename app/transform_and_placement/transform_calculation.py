from __future__ import print_function

import math
import numpy as np

from quatConvs import euler_to_quat, quat_to_euler
from quatOps import quat_conj, quat_avg


def compute_transform(data, placement):
    data.reset_index(inplace=True, drop=True)
    start, end = detect_still(data)
    data = data.loc[start:end, :]
    data.reset_index(inplace=True, drop=True)

    quat0 = data.loc[:, ['qW0', 'qX0', 'qY0', 'qZ0']].values.reshape(-1, 4)
    quat1 = data.loc[:, ['qW1', 'qX1', 'qY1', 'qZ1']].values.reshape(-1, 4)
    quat2 = data.loc[:, ['qW2', 'qX2', 'qY2', 'qZ2']].values.reshape(-1, 4)

    left_quaternions = quat0 if placement[0] == 0 else quat1 if placement[0] == 1 else quat2
    hip_quaternions = quat0 if placement[1] == 0 else quat1 if placement[1] == 1 else quat2
    right_quaternions = quat0 if placement[2] == 0 else quat1 if placement[2] == 1 else quat2

    return compute_transform_from_average(
        quat_avg(left_quaternions),
        quat_avg(hip_quaternions),
        quat_avg(right_quaternions)
    )


def compute_transform_from_average(left_quaternion, hip_quaternion, right_quaternion):
    # Force the foot yaw values to be zero, and conjugate the body frame transform
    left_body_frame_quaternion = quat_conj(quat_force_euler_angle(left_quaternion, psi=0))
    hip_body_frame_quaternion = quat_conj(quat_force_euler_angle(hip_quaternion, psi=0))
    right_body_frame_quaternion = quat_conj(quat_force_euler_angle(right_quaternion, psi=0))

    # The neutral quaternion is a yaw rotation of pi/2 + the neutral yaw value
    hip_euler = quat_to_euler(hip_quaternion)
    hip_yaw_value = hip_euler[:, 2]
    hip_neutral_euler = np.array([[0, 0, hip_yaw_value - math.pi / 2]])
    hip_neutral_quaternion = quat_conj(euler_to_quat(hip_neutral_euler))

    return (left_body_frame_quaternion.tolist()[0],
            hip_body_frame_quaternion.tolist()[0],
            right_body_frame_quaternion.tolist()[0],
            hip_neutral_quaternion.tolist()[0])


def detect_still(data):
    """Detect part of data with activity for placement detection
    """
    thresh = 5.  # threshold to detect balance phase
    bal_win = 125  # sampling window to determine balance phase
    acc_mag_0 = np.sqrt(data.aX0 ** 2 + data.aY0 ** 2 + data.aZ0 ** 2)
    acc_mag_1 = np.sqrt(data.aX1 ** 2 + data.aY1 ** 2 + data.aZ1 ** 2)
    acc_mag_2 = np.sqrt(data.aX2 ** 2 + data.aY2 ** 2 + data.aZ2 ** 2)
    total_acc_mag = acc_mag_0 + acc_mag_1 + acc_mag_2

    dummy_balphase = []  # dummy variable to store indexes of balance phase

    abs_acc = total_acc_mag.reshape(-1, 1)  # creating an array of absolute acceleration values
    len_acc = len(total_acc_mag)  # length of acceleration value

    for i in range(len_acc - bal_win + 1):
        # check if all the points within bal_win of current point are within
        # movement threshold
        if len(np.where(abs_acc[i:i + bal_win] <= thresh)[0]) == bal_win:
            dummy_balphase += range(i, i + bal_win)

    if len(dummy_balphase) == 0:
        raise Exception('Could not identify a long enough still window')

    # determine the unique indexes in the dummy list
    start_bal = np.unique(dummy_balphase)
    start_bal = np.sort(start_bal)
    still = np.zeros(len(data))
    still[start_bal] = 1
    change = np.ediff1d(still, to_begin=still[0])
    start = np.where(change == 1)[0]
    end = np.where(change == -1)[0]

    # if data ends with movement, assign final point as end of movement
    if len(start) != len(end):
        end = np.append(end, len(data))

    for i in range(len(end)):
        end[i] = min([end[i], start[i] + 300])
        if end[i] - start[i] >= 125:
            return start[i], end[i] # return the first section of data where we have enough points


def quat_force_euler_angle(quaternion, phi=None, theta=None, psi=None):
    euler_angles = quat_to_euler(quaternion)
    if phi is not None:
        euler_angles[:, 0] = phi
    if theta is not None:
        euler_angles[:, 1] = theta
    if psi is not None:
        euler_angles[:, 2] = psi
    return euler_to_quat(euler_angles)

