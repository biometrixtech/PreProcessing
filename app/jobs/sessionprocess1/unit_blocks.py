import numpy as np

from scipy.signal import butter, filtfilt


def define_unit_blocks(accel):
    """
    Define unit blocks based on total acceleration
    """
    # filter acceleration data
    accel = _filter_data(accel.values.reshape(-1,), cutoff=6)
    # initial definition of active as > 5m/s^2
    active = accel >= 5.
    # filter out instances of inactive that are too short
    ranges, length = _zero_runs(active, 0)
    for r, l in zip(ranges, length):
        if l < 50:
            active[r[0]:r[1]] = 1
    # filter out instances of active that are too short
    ranges, length = _zero_runs(active, 1)
    for r, l in zip(ranges, length):
        if l < 100:
            active[r[0]:r[1]] = 0
    ranges, length = _zero_runs(active, 1)

    # check for active blocks that have high peak accel, remove the rest
    # TODO: in the next phase flag the peak accel for better division grouping of blocks
    for r, l in zip(ranges, length):
        if l > 100:
            perc_high = len(np.where(accel[r[0]:r[1]] >= 15)[0]) / float(l)
            if perc_high < 0.005:
                active[r[0]:r[1]] = 0

    return active.astype(int).reshape(-1, 1)


def _zero_runs(col_dat, value):
    """
    Determine the start and end of each impact.

    Args:
        col_dat: array, right/left foot phase
        value: int, indicator for right/left foot impact phase
    Returns:
        ranges: 2d array, start and end of each impact for right/left foot
    """

    # determine where column data is the relevant impact phase value
    isnan = np.array(np.array(col_dat == value).astype(int)).reshape(-1, 1)
    if isnan[0] == 1:
        t_b = 1
    else:
        t_b = 0

    # mark where column data changes to and from NaN
    absdiff = np.abs(np.ediff1d(isnan, to_begin=t_b))
    if isnan[-1] == 1:
        absdiff = np.concatenate([absdiff, [1]], 0)
    del isnan  # not used in further computations

    # determine the number of consecutive NaNs
    ranges = np.where(absdiff == 1)[0].reshape((-1, 2))
    length = ranges[:, 1] - ranges[:, 0]

    return ranges, length


def _filter_data(x, cutoff=12, fs=100, order=4):
    """
    Forward-backward lowpass butterworth filter
    defaults:
        cutoff freq: 12hz
        sampling rage: 100hz
        order: 4
    """
    nyq = 0.5 * fs
    normal_cutoff = cutoff/nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return filtfilt(b, a, x, axis=0)
