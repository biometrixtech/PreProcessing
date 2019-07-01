from __future__ import print_function

import math
import numpy as np
import pandas as pd

from utils import get_ranges
from utils.quaternion_conversions import euler_to_quat, quat_to_euler, quat_force_euler_angle
from utils.quaternion_operations import quat_conj, quat_avg


def compute_transform(data):
    data.reset_index(inplace=True, drop=True)
    start_still_0, end_still_0, start_march_0, end_march_0 = detect_march_and_still_ankle(data, 0)
    start_still_2, end_still_2, start_march_2, end_march_2 = detect_march_and_still_ankle(data, 2)
    start_march_hip = max([start_march_0, start_march_2])
    end_march_hip = min([end_march_0, end_march_2])
    start_still_hip, end_still_hip = detect_still(data[start_march_hip - 75:start_march_hip], sensor=1)
    start_still_hip += start_march_hip - 75
    end_still_hip += start_march_hip - 75

    # start, end = detect_still(data, sensors, placement[1])
    # data = data.loc[start:end, :]
    # data.reset_index(inplace=True, drop=True)

    quat0 = data.loc[start_still_0:end_still_0, ['quat_0_w', 'quat_0_x', 'quat_0_y', 'quat_0_z']].values.reshape(-1, 4)
    quat1 = data.loc[start_still_hip:end_still_hip, ['quat_1_w', 'quat_1_x', 'quat_1_y', 'quat_1_z']].values.reshape(-1, 4)
    quat2 = data.loc[start_still_2:end_still_2, ['quat_2_w', 'quat_2_x', 'quat_2_y', 'quat_2_z']].values.reshape(-1, 4)

    # quaternion_0 = quat0 if placement[0] == 0 else quat1 if placement[0] == 1 else quat2
    # hip_quaternions = quat0 if placement[1] == 0 else quat1 if placement[1] == 1 else quat2
    # right_quaternions = quat0 if placement[2] == 0 else quat1 if placement[2] == 1 else quat2
    (
     bf_0,
     bf_hip,
     bf_2,
     hip_neutral
     ) = compute_transform_from_average(
             quat_avg(quat0),
             quat_avg(quat1),
             quat_avg(quat2)
             )
    return bf_0, bf_hip, bf_2, hip_neutral, start_march_0,  end_march_0, start_march_hip, end_march_hip, start_march_2, end_march_2


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


def detect_march(static):
    static = fix_short_static(static)
    ranges, lengths = get_ranges(static, 8, True)
    for r, length in zip(ranges, lengths):
        if length >= 400:
            return r[0], min(r[1], r[0] + int(6 * 97.52))
    return 0, 0


def fix_short_static(static):
    ranges, length = get_ranges(static, 0, True)
    for r, l in zip(ranges, length):
        if l < 15:
            static[r[0]: r[1]] = 8
    return static


def detect_still(data, sensor=0):
    """Detect part of data without activity for neutral reference
    """
    euler = quat_to_euler(
        data[f'quat_{sensor}_w'],
        data[f'quat_{sensor}_x'],
        data[f'quat_{sensor}_y'],
        data[f'quat_{sensor}_z'],
    )
    euler_x = euler[:, 0] * 180 / np.pi
    euler_y = euler[:, 1] * 180 / np.pi
    sd_x = pd.Series(euler_x).rolling(25).std(center=True)
    sd_y = pd.Series(euler_y).rolling(25).std(center=True)
    sd_tilt = sd_x + sd_y

    min_sd_tilt = np.min(sd_tilt)
    min_sd_loc = np.where(sd_tilt == min_sd_tilt)[0][0]
    start = min_sd_loc - 12
    end = min_sd_loc + 12

    x_diff = max(euler_x[start:end]) - min(euler_x[start:end])
    y_diff = max(euler_y[start:end]) - min(euler_y[start:end])
    max_diff = max(x_diff, y_diff)

    still_present = data[f'corrupt_{sensor}'][start:end].values == 0
    still = sum(still_present)
    if still > 0 or max_diff < 1:
        return start, end
    else:
        raise ValueError(f'could not detect still for sensor{sensor}')


def detect_march_and_still_ankle(data, sensor):
    # get march
    start_march, end_march = detect_march(data[f'corrupt_{sensor}'][int(8 * 97.52):int(20*97.52)])
    if end_march != 0:
        start_march += int(8 * 97.52)
        end_march += int(8 * 97.52)
        start_still, end_still = detect_still(data[start_march - 75:start_march], sensor=0)
        start_still += start_march - 75
        end_still += start_march - 75
        return start_still, end_still, start_march, end_march
