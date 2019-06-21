from aws_xray_sdk.core import xray_recorder
import numpy as np

from utils import get_ranges, filter_data


@xray_recorder.capture('app.jobs.sessionprocess.unit_blocks.define_unit_blocks')
def define_unit_blocks(accel):
    # filter acceleration data
    accel = filter_data(accel.values.reshape(-1,), filt='low', highcut=6)
    # initial definition of active as > 5m/s^2
    active = accel >= 5.
    # filter out instances of inactive that are too short
    ranges, length = get_ranges(active, 0, True)
    for r, l in zip(ranges, length):
        if l < 50:
            active[r[0]:r[1]] = 1
    # filter out instances of active that are too short
    ranges, length = get_ranges(active, 1, True)
    for r, l in zip(ranges, length):
        if l < 100:
            active[r[0]:r[1]] = 0
    ranges, length = get_ranges(active, 1, True)

    # check for active blocks that have high peak accel, remove the rest
    # TODO: in the next phase flag the peak accel for better division grouping of blocks
    for r, l in zip(ranges, length):
        if l > 100:
            perc_high = len(np.where(accel[r[0]:r[1]] >= 15)[0]) / float(l)
            if perc_high < 0.005:
                active[r[0]:r[1]] = 0

    return active.astype(int).reshape(-1, 1)
