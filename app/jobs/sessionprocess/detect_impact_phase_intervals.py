# -*- coding: utf-8 -*-
"""
Created on Tue Feb  7 16:14:03 2017

@author: ankurmanikandan
"""
from aws_xray_sdk.core import xray_recorder
import numpy as np

from utils import get_ranges


@xray_recorder.capture('app.jobs.sessionprocess.detect_impact_phase_intervals.detect_start_end_impact_phase')
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
    rf_range_imp = get_ranges(col_data=rph, value=2)
    lf_range_imp = get_ranges(col_data=lph, value=2)
    
    # declaring variable to store the start and end of impact phase
    lf_imp_start_stop = np.zeros(len(lph))*np.nan
    rf_imp_start_stop = np.zeros(len(rph))*np.nan
    
    # assigning True when an impact phase appears
    for i in range(len(lf_range_imp)):
        lf_imp_start_stop[lf_range_imp[i, 0]:lf_range_imp[i, 1]] = i+1
    for j in range(len(rf_range_imp)):
        rf_imp_start_stop[rf_range_imp[j, 0]:rf_range_imp[j, 1]] = j+1
    
    return lf_imp_start_stop.reshape(-1, 1), rf_imp_start_stop.reshape(-1, 1), lf_range_imp, rf_range_imp
