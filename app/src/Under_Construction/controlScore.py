# -*- coding: utf-8 -*-
"""
Created on Mon Oct 10 12:34:44 2016

@author: Gautam
"""
from __future__ import division
#import pandas as pd #need version .19 for time-aware rolling
import numpy as np

def controlScore(LeX, ReX, HeX, msElapsed):
    """Calculates instantaneous control scores
        LeX: left euler X
        ReX: right euler X
        HeX: hip euler x
        msElapsed: time in milliseconds since last sample
    Returns:
        control, hipControl, ankleControl, LControl, RControl scores for each timepoint
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
        for j in range(m):
            if (i-j)<=0: #Check if we're at the start of the list, assign nan and break so times without enough window before don't get calculated
                subset_l.append(np.nan)
                subset_r.append(np.nan)
                subset_h.append(np.nan)
                break
            else:
                prev += msElapsed[i-j]
                if prev<=60: #Append to the list timepoints from history within half the window
                    subset_l.append(LeX[i-j])
                    subset_r.append(ReX[i-j])
                    subset_h.append(HeX[i-j])
                else:
                    break
        for k in range(1,m):
            if (i+j)>=N:
                subset_l.append(np.nan)
                subset_r.append(np.nan)
                subset_h.append(np.nan)
                break
            else:
                forwd += msElapsed[i+j]
                if forwd<=60:#Append to the list timepoints from future within half the window
                    subset_l.append(LeX[i+j])
                    subset_r.append(ReX[i+j])
                    subset_h.append(HeX[i+j])
                else:
                    break
        score_raw_l[i] = np.std(subset_l)
        score_raw_r[i] = np.std(subset_r)
        score_raw_h[i] = np.std(subset_h)

    upper = .25 # upper bound for what sd is considered 0 score
    lower = 0. # lower bound for what sd is considered 100, both of these need to be adjusted based on data
    score_raw_l[score_raw_l>=upper]=upper
    score_raw_l[score_raw_l<=lower]=lower
    LControl = np.abs(score_raw_l-upper)/(upper-lower)*100

    score_raw_r[score_raw_r>=upper]=upper
    score_raw_r[score_raw_r<=lower]=lower
    RControl = np.abs(score_raw_r-upper)/(upper-lower)*100
    
    score_raw_h[score_raw_h>=upper]=upper
    score_raw_h[score_raw_h<=lower]=lower
    hipControl = np.abs(score_raw_h-upper)/(upper-lower)*100
    
    
    ankle_scores = np.vstack([LControl, RControl])
    ankleControl = np.nanmean(ankle_scores,0)
    
    overall_scores = np.vstack([hipControl, ankleControl])
    control = np.nanmean(overall_scores, 0)
        
    return control, hipControl, ankleControl, LControl, RControl
    

    
    
if __name__ == '__main__':
    import time
    path = 'C:\\Users\\dipesh\\Desktop\\biometrix\\indworkout\\'
    data= np.genfromtxt(path+ "Subject3_DblSquat_balCME1.csv",delimiter = ",", dtype =float, names = True)
    pronL = data['pronL']
    pronR = data['pronR']
    distL = pronL
    distR = pronR
    LeX = pronL
    ReX = pronR
    HeX = data['hiprot']
    msElapsed = np.zeros(len(data))+4    
    
    s = time.time()
    control, hipControl, ankleControl, LControl, RControl = controlScore(LeX, ReX, HeX, msElapsed)
    e = time.time()
    elap = e-s
    print elap    
    