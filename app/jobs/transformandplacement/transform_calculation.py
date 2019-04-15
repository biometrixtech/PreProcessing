from __future__ import print_function

import math
import numpy as np

from utils.quaternion_conversions import euler_to_quat, quat_to_euler, quat_force_euler_angle
from utils.quaternion_operations import quat_conj, quat_avg


def compute_transform(data, placement, sensors=3):
    data.reset_index(inplace=True, drop=True)
    start, end = detect_still(data, sensors, placement[1])
    data = data.loc[start:end, :]
    data.reset_index(inplace=True, drop=True)

    quat0 = data.loc[:, ['quat_0_w', 'quat_0_x', 'quat_0_y', 'quat_0_z']].values.reshape(-1, 4)
    quat1 = data.loc[:, ['quat_1_w', 'quat_1_x', 'quat_1_y', 'quat_1_z']].values.reshape(-1, 4)
    quat2 = data.loc[:, ['quat_2_w', 'quat_2_x', 'quat_2_y', 'quat_2_z']].values.reshape(-1, 4)

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
    hip_euler = quat_to_euler(
        hip_quaternion[:, 0],
        hip_quaternion[:, 1],
        hip_quaternion[:, 2],
        hip_quaternion[:, 3],
    )
    hip_yaw_value = hip_euler[:, 2]
    hip_neutral_euler = np.array([[0, 0, hip_yaw_value - math.pi / 2]])
    hip_neutral_quaternion = quat_conj(euler_to_quat(hip_neutral_euler))

    return (left_body_frame_quaternion.tolist()[0],
            hip_body_frame_quaternion.tolist()[0],
            right_body_frame_quaternion.tolist()[0],
            hip_neutral_quaternion.tolist()[0])


def detect_still(data, file_name, sensors=3, hip=1):
    """Detect part of data with activity for placement detection
    """
    acc_mag_0 = np.sqrt(data.acc_0_x ** 2 + data.acc_0_y ** 2 + data.acc_0_z ** 2)
    acc_mag_1 = np.sqrt(data.acc_1_x ** 2 + data.acc_1_y ** 2 + data.acc_1_z ** 2)
    acc_mag_2 = np.sqrt(data.acc_2_x ** 2 + data.acc_2_y ** 2 + data.acc_2_z ** 2)
    if sensors == 3:
        total_acc_mag = acc_mag_0 + acc_mag_1 + acc_mag_2
    elif sensors == 1:
        total_acc_mag = acc_mag_0 if hip == 0 else acc_mag_1 if hip == 1 else acc_mag_2
    acc_mag_sd = total_acc_mag.rolling(50).std(center=True)
    min_acc_mag_sd = np.min(acc_mag_sd)
    if min_acc_mag_sd > .5:
        print('Possibly not still')
    min_sd_loc = np.where(acc_mag_sd==min_acc_mag_sd)[0][0]

    return min_sd_loc - 25, min_sd_loc + 25
