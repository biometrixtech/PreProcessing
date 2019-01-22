# -*- coding: utf-8 -*-
"""
Created on Tue Feb  7 16:14:03 2017

@author: ankurmanikandan
"""

import numpy as np


def detect_start_end_impact_phase(lph, rph):
    """
    Detect impact phase for left and right foot.

    Args:
        lph = array, left foot phase
        rph = array, right foot phase

    Returns:
        lf_imp_start_stop: array, marker when impact phase for left foot
        starts and ends
        rf_imp_start_stop: array, marker when impact phase for right foot
        starts and ends
        lf_range_imp: 2d array, start and end indices of left foot impact
        rf_range_imp: 2d array, start and end indices of right foot impact
    """
    
    # start and end indices of impact phase for left and right foot
#    rf_range_imp = _zero_runs(col_dat=rph, imp_value=phase_id.rf_imp.value)
#    lf_range_imp = _zero_runs(col_dat=lph, imp_value=phase_id.lf_imp.value)
    rf_range_imp = _zero_runs(col_dat=rph, imp_value=2)
    lf_range_imp = _zero_runs(col_dat=lph, imp_value=2)
    
    # declaring variable to store the start and end of impact phase
    lf_imp_start_stop = np.zeros(len(lph))*np.nan
    rf_imp_start_stop = np.zeros(len(rph))*np.nan
    
    # assigning True when an impact phase appears
    for i in range(len(lf_range_imp)):
        lf_imp_start_stop[lf_range_imp[i, 0]:lf_range_imp[i, 1]] = i+1
    for j in range(len(rf_range_imp)):
        rf_imp_start_stop[rf_range_imp[j, 0]:rf_range_imp[j, 1]] = j+1
    
    return lf_imp_start_stop.reshape(-1, 1), rf_imp_start_stop.reshape(-1, 1), lf_range_imp, rf_range_imp

    
def _zero_runs(col_dat, imp_value):
    """
    Determine the start and end of each impact.
    
    Args:
        col_dat: array, right/left foot phase
        imp_value: int, indicator for right/left foot impact phase
    Returns:
        ranges: 2d array, start and end of each impact for right/left foot
    """

    # determine where column data is the relevant impact phase value
    isnan = np.array(np.array(col_dat == imp_value).astype(int)).reshape(-1, 1)
    
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

    return ranges
