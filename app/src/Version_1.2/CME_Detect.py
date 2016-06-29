# -*- coding: utf-8 -*-
"""
Created on Sun Jun 12 11:41:49 2016

@author: Brian
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import peak_det as peak
import phase_exploration as phase
import Data_Processing as prep

"""
#############################################INPUT/OUTPUT####################################################   
Inputs: continuous orientation data, body phase detection, list of states for evaluation, neutral position for
axis, list of thresholds

Outputs: array [time stamp, normalization score, indic of positive or negative, angle difference from neutral]

Datasets: phase_inputs.csv, peak_inputs.csv (contains both peak and trough values) ->
rot_CME(maxtab, mintab, output, [0,1]) -> outputs.csv
#############################################################################################################
"""
def cont_norm_score(mag, quat, cme):
    la = cme[0]
    le = cme[1]
    ua = cme[2]
    ue = cme[3]
    dev = quat-mag
    if 0 < dev <= ua:
        return 1, np.sign(dev), dev
    elif ua < dev < ue:
        return 1 - ((dev-ua)/(ue-ua)), np.sign(dev), dev
    elif dev >= ue:
        return 0, np.sign(dev), dev
    elif la <= dev <= 0:
        return 1, np.sign(dev), dev
    elif le < dev < la:
        return 1 - ((dev-la)/(le-la)), np.sign(dev), dev
    elif dev <= le:
        return 0, np.sign(dev), dev
    
    
def cont_rot_CME(series, states, state, rel, cme):
    out = []
    for i in range(len(series)):
        if states[i] in state:
            ang = (180/np.pi)*series[i]
            comp = (180/np.pi)*rel
            n, indic, raw = cont_norm_score(ang, comp, cme)
            out.append([i, n, indic, raw])
    return np.array(out)
    
if __name__ == "__main__":
    pos = 'lf'
    lroot = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\lfdatabody.csv'
    rroot = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\rfdatabody.csv'
    hroot = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\hipdatabody.csv'
    
#    lroot = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\BodyFrame walking\\Lheel_Gabby_walking_heeltoe_set1.csv'
#    rroot = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\BodyFrame walking\\Rheel_Gabby_walking_heeltoe_set1.csv'
#    hroot = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\BodyFrame walking\\hips_Gabby_walking_heeltoe_set1.csv'    
    
    cme_dict = {'prosupl':[-4, -7, 4, 15], 'hiprotl':[-4, -7, 4, 15], 'hipdropl':[-4, -7, 4, 15],
                'prosupr':[-4, -15, 4, 7], 'hiprotr':[-4, -15, 4, 7], 'hipdropr':[-4, -15, 4, 7]}    
    
    rdata = pd.read_csv(rroot)
    ldata = pd.read_csv(lroot)
    hdata = pd.read_csv(hroot)
    
    neutral = np.matrix([1,0,0,0]) # stand-in, will come from anatomical fix module    
    
    ##Phase Detection
    rseries = rdata['AccZ'].values
    lseries = ldata['AccZ'].values #input AccZ values!
    rpitch = rdata['EulerY'].values
    lpitch = ldata['EulerY'].values
    output = phase.Body_Phase(rseries, lseries, rpitch, lpitch, 250)
    ldata['Phase'] = output
    rdata['Phase'] = output
    hdata['Phase'] = output 
    
    peak_series = ldata['EulerX'].values
    neutral_eul = prep.Calc_Euler(neutral)
    
    ###THE GOOD STUFF!!!####
    out = cont_rot_CME(peak_series, output, [0,1], neutral_eul[0], cme_dict['prosupl'])

    
    
    