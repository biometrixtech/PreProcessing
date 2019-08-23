from utils import filter_data, get_ranges
from scipy.signal import find_peaks
import pandas as pd
import numpy as np


def flag_change_of_direction(acc_hip_z, euler_hip_z_hc):
    look_backs = 6
    steps_to_remove = 6
    change_of_direction = np.zeros(len(acc_hip_z))

    # get steps
    acc_hip_z = filter_data(acc_hip_z, filt='low', highcut=4)
    peaks, peak_heights = find_peaks(acc_hip_z, height=1.5, distance=20)
    heading_diff = np.zeros(len(peaks))

    if len(peaks) > (look_backs * 2 + 1):
        headings_at_peak = []
        for peak in peaks:
            headings_at_peak.append(euler_hip_z_hc[peak])

        # handle switching between -180 and 180
        headings_at_peak = [-i if i < 0 else i for i in headings_at_peak]

        # smooth headings
        headings_at_peak = pd.Series(headings_at_peak).rolling(window=3, center=True).mean().values
        headings_at_peak[0] = headings_at_peak[1]

        # get difference between current step and 6 steps before (3 on each side)
        for i in range(look_backs, len(headings_at_peak) - 1):
            heading_diff[i] = np.abs(headings_at_peak[i] - headings_at_peak[i-look_backs])

        # find indices where change is > 40 degrees
        heading_change_indices = np.where(heading_diff > 40)[0].astype(list)

        # mark "steps_to_remove" steps before and after identified heading change point
        for i in heading_change_indices:
            change_of_direction[peaks[i - steps_to_remove]:peaks[min([i + steps_to_remove, len(peaks) - 1])]] = 1

        # remove linear motion data if two change of direction happen close to each other (2s)
        ranges, lengths = get_ranges(change_of_direction, 0, True)
        for r, l in zip(ranges, lengths):
            if l < 200:
                change_of_direction[r[0]:r[1]] = 1

    return change_of_direction
