# -*- coding: utf-8 -*-
"""
Created on Mon Oct 10 12:34:44 2016

@author: Gautam
"""
from __future__ import division
import numpy as np
import pandas as pd


def control_score(LeX, HeX, ReX, phase_lf, phase_rf):
    """Calculates instantaneous control scores
    Scoring is based on standard deviation of euler angle (x) within a certian
    window.
    Current window is set to 120ms
    Args:
        LeX: left euler X
        ReX: right euler X
        HeX: hip euler x
        phase_lf: left foot phase
        phase_rf: right foot phase
    Returns:
        control, hip_control, ankle_control, control_lf, control_rf scores for
        each timepoint all these should be (n,1) numpy arrays
    """
    N = int(120/10.) + 1
    M = 5
    LeX_copy = np.array(LeX)
    ReX_copy = np.array(ReX)
    HeX_copy = np.array(HeX)
    LeX_copy[np.array([i not in [0, 1, 4] for i in phase_lf])] = np.nan
    ReX_copy[np.array([i not in [0, 2, 5] for i in phase_rf])] = np.nan
    HeX_copy[np.array([i==3 for i in phase_lf])] = np.nan

    #TODO(Dipesh) Handle weird jumps in euler angles/ possibly add handling of missing data)    
    LeX_pd = pd.Series(LeX_copy.reshape(-1,))
    HeX_pd = pd.Series(HeX_copy.reshape(-1,))
    ReX_pd = pd.Series(ReX_copy.reshape(-1,))

    score_raw_l = LeX_pd.rolling(min_periods=M, window=N, center=True).std()
    score_raw_h = HeX_pd.rolling(min_periods=M, window=N, center=True).std()
    score_raw_r = ReX_pd.rolling(min_periods=M, window=N, center=True).std()
    score_raw_l[np.isnan(LeX_pd)] = np.nan
    score_raw_h[np.isnan(HeX_pd)] = np.nan
    score_raw_r[np.isnan(ReX_pd)] = np.nan
    #TODO(Dipesh) Need to update the bounds based on data
    upper = .20 # upper bound for what sd is considered 0 score
    lower = 0. # lower bound for what sd is considered 100,
    score_raw_l[score_raw_l >= upper] = upper
    score_raw_l[score_raw_l <= lower] = lower
    control_lf = np.abs(score_raw_l-upper)/(upper-lower)*100

    score_raw_r[score_raw_r >= upper] = upper
    score_raw_r[score_raw_r <= lower] = lower
    control_rf = np.abs(score_raw_r-upper)/(upper-lower)*100

    score_raw_h[score_raw_h >= upper] = upper
    score_raw_h[score_raw_h <= lower] = lower
    hip_control = np.abs(score_raw_h-upper)/(upper-lower)*100

    #combine l and r ankle scores to get overall ankle score
    ankle_scores = np.vstack([control_lf, control_rf])
    ankle_control = np.nanmean(ankle_scores, 0)

    overall_scores = np.vstack([hip_control, ankle_control])
    control = np.nanmean(overall_scores, 0)

    return control.reshape(-1, 1), hip_control.reshape(-1, 1),\
    ankle_control.reshape(-1, 1), control_lf.reshape(-1, 1),\
    control_rf.reshape(-1, 1)


if __name__ == '__main__':
    import time
    file_name = 'subject3_DblSquat_hist.csv'
    data = pd.read_csv(file_name)
    start = time.time()
    control, hip_control, ankle_control, control_lf,\
            control_rf = control_score(data.LeX, data.ReX, data.HeX,
                                       data.ms_elapsed, data.phase_lf,
                                       data.phase_rf)
    print time.time() - start
    pass

