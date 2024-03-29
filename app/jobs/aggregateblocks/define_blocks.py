"""
Aggregate unit blocks into active blocks
"""
from utils import get_ranges, filter_data
from scipy.signal import find_peaks
from .blocks import ActiveBlock, CadenceZone


import numpy as np
import pandas as pd


def define_active_blocks(active):
    """
    Aggregate unit blocks into active blocks
    """
    # get ranges for activity blocks
    ab_ranges = get_ranges(active, 1)
    active_blocks = []
    if len(ab_ranges) > 0:  # make sure there's at least one active range ind ata
        ab = ActiveBlock()
        ab.start_index = ab_ranges[0][0]
        if len(ab_ranges) == 1:
            ab.end_index = ab_ranges[0][1]
            active_blocks.append(ab)

        for i in range(1, len(ab_ranges)):
            if ab_ranges[i][0] - ab_ranges[i - 1][1] > 100 * 10:
                ab.end_index = ab_ranges[i - 1][1]
                active_blocks.append(ab)
                ab = ActiveBlock()
                ab.start_index = ab_ranges[i][0]
            if i == len(ab_ranges) - 1:
                ab.end_index = ab_ranges[i][1]
                active_blocks.append(ab)

    return active_blocks


def define_cadence_zone(data):
    block_ranges = get_ranges(data.active.values, 1)
    cadence_zone = np.zeros(len(data))
    all_cadence = np.zeros(len(data))
    euler_y = data.euler_lf_y.values
    euler_y[np.where(np.isnan(euler_y))[0]] = 0
    euler_y = filter_data(euler_y, filt='band', highcut=35) * 180 / np.pi
    for br in block_ranges:
        euler_y_block = euler_y[br[0]: br[1]]
        peaks, peak_heights = find_peaks(euler_y_block, height=20, distance=30)
        if len(peaks) > 10:
            cadence = _get_cadence(peaks)
            peaks += br[0]
            start_index = 10
            mean_initial_cadence = np.nanmean(cadence[:start_index])
            if np.isnan(mean_initial_cadence):
                initial_cadence = 100
            else:
                initial_cadence = int(mean_initial_cadence)
            current_zone = _get_cadence_zone(initial_cadence)
            cadence_zone[br[0]:peaks[start_index]] = current_zone.value
            last_updated_index = peaks[start_index]
            for i in range(start_index, len(cadence)):
                if i == len(cadence) - 1:  # end of the block
                    cadence_zone[last_updated_index:br[1]] = current_zone.value
                elif np.isnan(cadence[i]):
                    continue
                elif _get_cadence_zone(cadence[i]) == current_zone:
                    cadence_zone[last_updated_index:peaks[i]] = current_zone.value
                    last_updated_index = peaks[i]
                else:
                    if peaks[i] - last_updated_index >= 1000:
                        current_zone = _get_cadence_zone(cadence[i])
                        cadence_zone[last_updated_index:peaks[i]] = current_zone.value
                        last_updated_index = peaks[i]
            r_l_peaks, r_l_cadence = interpolate_cadence(peaks, cadence)
            all_cadence[r_l_peaks] = r_l_cadence

    data['cadence_zone'] = cadence_zone
    data['cadence'] = all_cadence


def _get_cadence_zone(cadence):
    if cadence <= 130:
        return CadenceZone.walking
    elif 130 < cadence <= 165:
        return CadenceZone.jogging
    elif 165 < cadence <= 195:
        return CadenceZone.running
    else:
        return CadenceZone.sprinting


def _get_cadence(peaks):
    peak_diff = np.ediff1d(peaks, to_begin=0).astype(float)
    peak_diff[0] = peak_diff[1]
    peak_diff = pd.Series(peak_diff).rolling(window=3, center=True).mean().values
    peak_diff[np.where(peak_diff > 400)[0]] = np.nan
    peak_diff[0] = peak_diff[1]
    peak_diff[-1] = peak_diff[-2]
    cadence = 100 / peak_diff * 60 * 2
    cadence = pd.Series(cadence).rolling(window=3, center=True).mean().values
    cadence[0] = cadence[1]
    cadence[-1] = cadence[-2]

    return cadence

def interpolate_cadence(peaks, cadence):
    x = [int((peaks[i-1] + peaks[i]) / 2) for i in range(1, len(peaks))]
    x.extend(peaks.tolist())
    x = sorted(x)
    y = np.interp(x, xp=peaks, fp=cadence)
    return x, y
