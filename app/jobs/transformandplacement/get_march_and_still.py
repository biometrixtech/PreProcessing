import numpy as np
# import pandas as pd
from .exceptions import StillDetectionException, MarchDetectionException

from utils import get_ranges
from utils.quaternion_conversions import quat_to_euler


# constants
# march_detection_start = 550
# march_detection_end = 2000
samples_before_march = 250


def detect_march_and_still(data, start_sample):
    start_still_0, end_still_0, start_march_0, end_march_0 = _detect_march_and_still_ankle(data, 0, start_sample)
    start_still_2, end_still_2, start_march_2, end_march_2 = _detect_march_and_still_ankle(data, 2, start_sample)
    start_march_hip = max([start_march_0, start_march_2])
    end_march_hip = min([end_march_0, end_march_2])
    start_search_hip = min([start_march_0, start_march_2])  # start searching before the first ankle moves
    start_still_hip, end_still_hip = _detect_still(data[start_search_hip - samples_before_march:start_search_hip], sensor=1)
    start_still_hip += start_march_hip - samples_before_march
    end_still_hip += start_march_hip - samples_before_march

    return (start_march_0, end_march_0, start_still_0, end_still_0,
            start_march_hip, end_march_hip, start_still_hip, end_still_hip,
            start_march_2, end_march_2, start_still_2, end_still_2)


def _detect_march_and_still_ankle(data, sensor, start_sample):
    # get march
    march_detection_start = 550 + start_sample
    march_detection_end = 2000 + start_sample
    start_march, end_march = _detect_march(data[f'static_{sensor}'][march_detection_start:march_detection_end])
    if end_march != 0:
        start_march += march_detection_start
        end_march += march_detection_start
        start_still, end_still = _detect_still(data[start_march - samples_before_march:start_march], sensor=sensor)
        start_still += start_march - samples_before_march
        end_still += start_march - samples_before_march
        return start_still, end_still, start_march, end_march
    else:
        raise MarchDetectionException(f'Could not detect march for sensor{sensor}', sensor)


def _detect_march(static):
    static = _fix_short_static(static)
    ranges, lengths = get_ranges(static, 1, True)
    for r, length in zip(ranges, lengths):
        if length >= 400:
            return r[0], min(r[1], r[0] + int(600))
    return 0, 0


def _fix_short_static(static):
    ranges, length = get_ranges(static, 0, True)
    for r, l in zip(ranges, length):
        if l < 20:
            static[r[0]: r[1]] = 1
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
    static = data[f'static_{sensor}'].values
    x_diff = max(euler_x) - min(euler_x)
    y_diff = max(euler_y) - min(euler_y)
    max_diff_all = max(x_diff, y_diff)
    if max_diff_all > 20:  # too much movement/drift in the second prior
        raise StillDetectionException(f'could not detect still for sensor{sensor}', sensor)

    for i in np.arange(len(data) - 1, 25, -1):
        start = i - 25
        end = i
        # get the greatest change in angle in the window
        x_diff = max(euler_x[start:end]) - min(euler_x[start:end])
        y_diff = max(euler_y[start:end]) - min(euler_y[start:end])
        max_diff = max(x_diff, y_diff)

        # check the number of static samples in the window
        static_present = static[start:end] == 0
        static_count = sum(static_present)

        # if either is good, use the window
        if static_count >= 20 or max_diff < .75:
            return start, end
    raise StillDetectionException(f'could not detect still for sensor{sensor}', sensor)
