"""
Aggregate unit blocks into active blocks
"""
from collections import OrderedDict

import numpy as np


def define_blocks(active):
    """
    Aggregate unit blocks into active blocks
    """
    # get ranges for unit blocks
    unit_block_ranges, unit_block_lengths = _get_ranges(active, 1)
    active_blocks = OrderedDict()
    block = 0
    if len(unit_block_ranges) > 0:  # make sure there's at least one unit block
        active_blocks[str(block)] = [unit_block_ranges[0]]
        for i in range(len(unit_block_ranges)-1):
            # if distance between unit blocks is less than 1m, combine them into single block
            if unit_block_ranges[i+1][0] - unit_block_ranges[i][1] < 6000:
                active_blocks[str(block)].append(unit_block_ranges[i+1])
            else:
                block += 1
                active_blocks[str(block)] = [unit_block_ranges[i+1]]
    return active_blocks


def _get_ranges(col_data, value):
    """
    For a given categorical data, determine start and end index for the given value
    start: index where it first occurs
    end: index after the last occurence

    Args:
        col_data
        value: int, value to get ranges for
    Returns:
        ranges: 2d array, start and end index for each occurance of value
    """

    # determine where column data is the relevant value
    is_value = np.array(np.array(col_data == value).astype(int)).reshape(-1, 1)

    # if data starts with given value, range starts with index 0
    if is_value[0] == 1:
        t_b = 1
    else:
        t_b = 0

    # mark where column data changes to and from the given value
    absdiff = np.abs(np.ediff1d(is_value, to_begin=t_b))

    # handle the closing edge
    # if the data ends with the given value, if it was the only point, ignore the range,
    # else assign the last index as end of range
    if is_value[-1] == 1:
        if absdiff[-1] == 0:
            absdiff[-1] = 1
        else:
            absdiff[-1] = 0
    # determine the number of consecutive NaNs
    ranges = np.where(absdiff == 1)[0].reshape((-1, 2))

    length = ranges[:, 1] - ranges[:, 0]

    return ranges, length
