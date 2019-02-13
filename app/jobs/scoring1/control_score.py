# -*- coding: utf-8 -*-
"""
Created on Mon Oct 10 12:34:44 2016

@author: Gautam
"""
from __future__ import division
import numpy as np


def control_score(euler_x):
    """Calculates instantaneous control scores
    Scoring is based on standard deviation of euler angle (x) within a certian
    window.
    Current window is set to 120ms
    Args:
        euler_x: euler x
    Returns:
        control scores for
        each timepoint all these should be (n,1) numpy arrays
    """
    window = int(120/10.) + 1
    min_period = 5

    score_raw = euler_x.rolling(min_periods=min_period, window=window, center=True).std()
    score_raw[np.isnan(euler_x)] = np.nan

    # TODO(Dipesh) Need to update the bounds based on data
    upper = .20  # upper bound for what sd is considered 0 score
    lower = 0.  # lower bound for what sd is considered 100,

    score_raw[score_raw >= upper] = upper
    score_raw[score_raw <= lower] = lower
    control = np.abs(score_raw-upper)/(upper-lower)*100

    return control
