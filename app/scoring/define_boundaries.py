"""
Group data into active blocks
"""
from collections import OrderedDict

import numpy as np


def define_bounds(active):
    """Get boundaries for chunking data for block aggregation using definition
    Uses definition of active blocks so that data is not chunked in the middle of
    active block
    Each chunk is kept as close to 100000 lines as possible
    """
    unit_block_ranges, unit_block_lengths = _zero_runs(active, 1)
    active_blocks = OrderedDict()
    block = 0
    if len(unit_block_ranges) > 0:
        active_blocks[str(block)] = [unit_block_ranges[0]]
        for i in range(len(unit_block_ranges)-1):
            if unit_block_ranges[i+1][0] - unit_block_ranges[i][1] < 6000:
                active_blocks[str(block)].append(unit_block_ranges[i+1])
            else:
                block += 1
                active_blocks[str(block)] = [unit_block_ranges[i+1]]

    block_ends = []
    for block in active_blocks:
        block_ends.append(active_blocks[block][-1][1])

    boundaries = []
    prev_end = 0
    for counter, value in enumerate(block_ends):
        if value - prev_end < 80000:
            continue
        elif value - prev_end > 130000:
            if i == 0:
                bound = value + 1000
                boundaries.append(bound)
                prev_end = bound
            else:
                bound = block_ends[counter - 1] + 1000
                boundaries.append(bound)
                prev_end = bound
        else:
            bound = value + 1000
            boundaries.append(bound)
            prev_end = bound
    return boundaries


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
