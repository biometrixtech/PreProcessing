import copy
import numpy as np
from utils import get_ranges


def flag_data_for_removal(data):
    ground_phases = [2, 3]
    _phase_lf = copy.copy(data.phase_lf.values)
    _phase_lf[np.array([i in ground_phases for i in _phase_lf])] = 0
    steps_lf = get_steps(_phase_lf)

    corr_points = np.where(data.correction_points_hip == 1)[0]
    removal_flag = np.zeros(len(data))
    for i in range(1, len(corr_points)):
        left_steps_between_corr_points = len(np.where((steps_lf[:, 0] > corr_points[i-1]) & (steps_lf[:, 1] < corr_points[i]))[0])
        if left_steps_between_corr_points > 10:
            removal_flag[corr_points[i-1]:corr_points[i]] = 1

    ranges, lengths = get_ranges(removal_flag, 0, True)
    for r, l in zip(ranges, lengths):
        if l < 300:
            removal_flag[r[0]: r[1]] = 1
    data.loc[:, 'remove'] = removal_flag


def get_steps(_phase):
    # get index ranges for ground contacts
    ranges, lengths = get_ranges(_phase, 0, True)
    length_index = np.where((lengths <= 150) & (lengths >= 13))
    ranges = ranges[length_index]
    return ranges
