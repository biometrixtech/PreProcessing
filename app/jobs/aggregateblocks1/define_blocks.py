"""
Aggregate unit blocks into active blocks
"""
from collections import OrderedDict

import numpy as np
from utils import get_ranges

def define_blocks(active):
    """
    Aggregate unit blocks into active blocks
    """
    # get ranges for unit blocks
    unit_block_ranges, unit_block_lengths = get_ranges(active, 1, True)
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
