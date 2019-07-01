import numpy as np
import pandas as pd

from utils import get_ranges
from utils.quaternion_conversions import quat_to_euler


def detect_march_and_still(data):
    start_still_0, end_still_0, start_march_0, end_march_0 = _detect_march_and_still_ankle(data, 0)
    start_still_2, end_still_2, start_march_2, end_march_2 = _detect_march_and_still_ankle(data, 2)
    start_march_hip = max([start_march_0, start_march_2])
    end_march_hip = min([end_march_0, end_march_2])
    start_still_hip, end_still_hip = _detect_still(data[start_march_hip - 75:start_march_hip], sensor=1)
    start_still_hip += start_march_hip - 75
    end_still_hip += start_march_hip - 75

    return (start_march_0, end_march_0, start_still_0, end_still_0,
            start_march_hip, end_march_hip, start_still_hip, end_still_hip,
            start_march_2, end_march_2, start_still_2, end_still_2)


def _detect_march_and_still_ankle(data, sensor):
    # get march
    start_march, end_march = _detect_march(data[f'corrupt_{sensor}'][int(8 * 97.52):int(20*97.52)])
    if end_march != 0:
        start_march += int(8 * 97.52)
        end_march += int(8 * 97.52)
        start_still, end_still = _detect_still(data[start_march - 75:start_march], sensor=0)
        start_still += start_march - 75
        end_still += start_march - 75
        return start_still, end_still, start_march, end_march


def _detect_march(static):
    static = _fix_short_static(static)
    ranges, lengths = get_ranges(static, 8, True)
    for r, length in zip(ranges, lengths):
        if length >= 400:
            return r[0], min(r[1], r[0] + int(6 * 97.52))
    return 0, 0


def _fix_short_static(static):
    ranges, length = get_ranges(static, 0, True)
    for r, l in zip(ranges, length):
        if l < 15:
            static[r[0]: r[1]] = 8
    return static


def _detect_still(data, sensor=0):
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
