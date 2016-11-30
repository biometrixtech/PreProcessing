# -*- coding: utf-8 -*-
"""
Created on Mon Oct 10 12:34:44 2016

@author: Gautam
"""
from __future__ import division
import numpy as np


def control_score(LeX, HeX, ReX, ms_elapsed):
    """Calculates instantaneous control scores
    Scoring is based on standard deviation of euler angle (x) within a certian
    window.
    Current window is set to 120ms
    Args:
        LeX: left euler X
        ReX: right euler X
        HeX: hip euler x
        ms_elapsed: time in milliseconds since last sample
    Returns:
        control, hip_control, ankle_control, control_lf, control_rf scores for
        each timepoint all these should be (n,1) numpy arrays

    Note:
    Pandas 0.19 has a feature to get rolling calculation based on time window
    rather than number of points which will make calculations more efficient.
    """
    N = len(LeX)
    m = 15
    score_raw_l = np.zeros(N)
    score_raw_r = np.zeros(N)
    score_raw_h = np.zeros(N)
    for i in range(N):
        subset_l = []
        subset_r = []
        subset_h = []
        prev = 0
        forwd = 0
        #get data for window/2 time from past timepoints
        for j in range(m):
            #Check if we're at the start of the list, assign nan and break so
            #rows without enough data in the past don't get calculated
            if (i-j) <= 0:
                subset_l.append(np.nan)
                subset_r.append(np.nan)
                subset_h.append(np.nan)
                break
            else:
                prev += ms_elapsed[i-j]
                if prev <= 60: #Append to the list timepoints from past within half the window
                    subset_l.append(LeX[i-j])
                    subset_r.append(ReX[i-j])
                    subset_h.append(HeX[i-j])
                else:
                    break
        #get data for window/2 from future timepoints
        for k in range(1, m):
            #Check if we're at the end of the list, assign nan and break so
            #rows without enough data in the future don't get calculated
            if (i+k) >= N:
                subset_l.append(np.nan)
                subset_r.append(np.nan)
                subset_h.append(np.nan)
                break
            else:
                forwd += ms_elapsed[i+k]
                if forwd <= 60:#Append to the list timepoints from future within half the window
                    subset_l.append(LeX[i+k])
                    subset_r.append(ReX[i+k])
                    subset_h.append(HeX[i+k])
                else:
                    break
        #raw score is the rolling standard deviation
        score_raw_l[i] = np.std(subset_l)
        score_raw_r[i] = np.std(subset_r)
        score_raw_h[i] = np.std(subset_h)

    #TODO(Dipesh) Need to update the bounds based on data
    upper = .25 # upper bound for what sd is considered 0 score
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
#    import time
#    import numpy as np
#    path = 'C:\\Users\\dipesh\\Desktop\\biometrix\\indworkout\\'
#    data= np.genfromtxt(path+ "Subject3_DblSquat_Transformed_Data.csv",
#                        delimiter = ",", dtype =float, names = True)
#    pronL = data['pronL']
#    pronR = data['pronR']
#    distL = pronL
#    distR = pronR
#    LeX = pronL
#    ReX = pronR
#    HeX = data['hiprot']
#    ms_elapsed = np.zeros(len(data))+4
#
#    s = time.time()
#    control, hip_control, ankle_control, control_lf, control_rf = control_score([], [], [], [])
#    e = time.time()
#    elap = e-s
#    print elap
    pass
