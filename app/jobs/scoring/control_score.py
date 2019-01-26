# -*- coding: utf-8 -*-
"""
Created on Mon Oct 10 12:34:44 2016

@author: Gautam
"""
from __future__ import division
import numpy as np
import pandas as pd


def control_score(eul_lf_x, eul_hip_x, eul_rf_x, phase_lf, phase_rf):
    """Calculates instantaneous control scores
    Scoring is based on standard deviation of euler angle (x) within a certian
    window.
    Current window is set to 120ms
    Args:
        eul_lf_x: left euler X
        eul_rf_x: right euler X
        eul_hip_x: hip euler x
        phase_lf: left foot phase
        phase_rf: right foot phase
    Returns:
        control, hip_control, ankle_control, control_lf, control_rf scores for
        each timepoint all these should be (n,1) numpy arrays
    """
    n = int(120/10.) + 1
    m = 5
    eul_lf_x_copy = np.array(eul_lf_x)
    eul_rf_x_copy = np.array(eul_rf_x)
    eul_hip_x_copy = np.array(eul_hip_x)
    eul_lf_x_copy[np.array([i == 1 for i in phase_lf])] = np.nan
    eul_rf_x_copy[np.array([i == 1 for i in phase_rf])] = np.nan
    eul_hip_x_copy[np.array([i == 1 for i in phase_lf]) & np.array([i == 1 for i in phase_rf])] = np.nan

    # TODO(Dipesh) Handle weird jumps in euler angles/ possibly add handling of missing data)
    eul_lf_x_pd = pd.Series(eul_lf_x_copy.reshape(-1,))
    eul_hip_x_pd = pd.Series(eul_hip_x_copy.reshape(-1,))
    eul_rf_x_pd = pd.Series(eul_rf_x_copy.reshape(-1,))

    score_raw_l = eul_lf_x_pd.rolling(min_periods=m, window=n, center=True).std()
    score_raw_h = eul_hip_x_pd.rolling(min_periods=m, window=n, center=True).std()
    score_raw_r = eul_rf_x_pd.rolling(min_periods=m, window=n, center=True).std()
    score_raw_l[np.isnan(eul_lf_x_pd)] = np.nan
    score_raw_h[np.isnan(eul_hip_x_pd)] = np.nan
    score_raw_r[np.isnan(eul_rf_x_pd)] = np.nan
    # TODO(Dipesh) Need to update the bounds based on data
    upper = .35  # upper bound for what sd is considered 0 score
    lower = 0.  # lower bound for what sd is considered 100,
    score_raw_l[score_raw_l >= upper] = upper
    score_raw_l[score_raw_l <= lower] = lower
    control_lf = np.abs(score_raw_l-upper) / (upper-lower) * 100

    score_raw_r[score_raw_r >= upper] = upper
    score_raw_r[score_raw_r <= lower] = lower
    control_rf = np.abs(score_raw_r-upper) / (upper-lower) * 100

    score_raw_h[score_raw_h >= upper] = upper
    score_raw_h[score_raw_h <= lower] = lower
    hip_control = np.abs(score_raw_h-upper) / (upper-lower) * 100

    # Combine l and r ankle scores to get overall ankle score
    ankle_scores = np.vstack([control_lf, control_rf])
    ankle_control = np.nanmean(ankle_scores, 0)

    overall_scores = np.vstack([hip_control, ankle_control])
    control = np.nanmean(overall_scores, 0)

    return (
        control.reshape(-1, 1),
        hip_control.values.reshape(-1, 1),
        ankle_control.reshape(-1, 1),
        control_lf.values.reshape(-1, 1),
        control_rf.values.reshape(-1, 1)
    )
