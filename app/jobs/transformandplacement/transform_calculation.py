from __future__ import print_function

import math
import numpy as np

from utils.quaternion_conversions import euler_to_quat, quat_to_euler, quat_force_euler_angle
from utils.quaternion_operations import quat_conj, quat_avg


def compute_transform(data, start_still_0, end_still_0, start_still_hip, end_still_hip, start_still_2, end_still_2):
    data.reset_index(inplace=True, drop=True)
    quat0 = data.loc[start_still_0:end_still_0, ['quat_0_w', 'quat_0_x', 'quat_0_y', 'quat_0_z']].values.reshape(-1, 4)
    quat1 = data.loc[start_still_hip:end_still_hip, ['quat_1_w', 'quat_1_x', 'quat_1_y', 'quat_1_z']].values.reshape(-1, 4)
    quat2 = data.loc[start_still_2:end_still_2, ['quat_2_w', 'quat_2_x', 'quat_2_y', 'quat_2_z']].values.reshape(-1, 4)

    return compute_transform_from_average(
             quat_avg(quat0),
             quat_avg(quat1),
             quat_avg(quat2)
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
