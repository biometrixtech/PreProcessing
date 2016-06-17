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

"""
#############################################INPUT/OUTPUT####################################################   
Inputs: peak detection for each sensor on each axis, body phase detection

Outputs: lists with angular displacement changes for pronation/supination on each foot(2) and for each balance
phase(3), lists with angular displacement changes for Lateral Hip Rotation for each balance phase (3), lists
with angular displacement changes for Contralateral Hip Drop for each balance phase (3)

Datasets: phase_inputs.csv, peak_inputs.csv (contains both peak and trough values) ->
rot_CME(maxtab, mintab, output, .1, 1, 250) -> outputs.csv 
#############################################################################################################
"""

def rot_CME(maxtab, mintab, states, thresh, state, hz):
    combine = np.concatenate((maxtab, mintab)) #combine min and max arrays
    combine = combine[combine[:,0].argsort()] #sort by index to get in chronological order
    mags = [[(180/np.pi)*(combine[i,1]-combine[i-1,1]), combine[i,0]] for i in range(1,len(combine)) if abs(combine[i,1]-combine[i-1,1]) > thresh] #convert peak to trough diff to degrees filtered by threshold 
    tdiff = [combine[i,0] for i in range(1,len(combine)) if (combine[i,0]-combine[i-1,0]) < 1.6*hz] #make sure time the critical value is time relevant (i.e. peak doesn't happen 5 seconds after trough)
    mdiff = [combine[i] for i in range(1,len(combine)) if abs(combine[i,1]-combine[i-1,1]) > thresh] #filter list by threshold 
    if len(tdiff) > 0 and len(mdiff) > 0: 
        diff = [mdiff[i] for i in range(len(mdiff)) if mdiff[i][0] in tdiff] #make list of points that satisfy time and threshold conditions
        diff = np.array([diff[i] for i in range(len(diff)) if states[int(diff[i][0])] == state]) #refine list by removing points not in relevant phase
        if len(diff) > 0:
            final = [mags[i][0] for i in range(len(mags)) if mags[i][1] in diff[:,0]] #create list of degree values of movements
            return final
    return [], [] #if no peaks meet requirement return empty list
    
if __name__ == "__main__":
    pos = 'lf'
    lroot = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\lfdatabody.csv'
    rroot = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\rfdatabody.csv'
    hroot = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\hipdatabody.csv'
    
    rdata = pd.read_csv(rroot)
    ldata = pd.read_csv(lroot)
    hdata = pd.read_csv(hroot)
    
    ##Phase Detection
    rseries = rdata['AccZ'].values
    lseries = ldata['AccZ'].values #input AccZ values!
    rpitch = rdata['EulerY'].values
    lpitch = ldata['EulerY'].values
    output = phase.Body_Phase(rseries, lseries, rpitch, lpitch, 250)    
    
    #Peak Detection- Right Foot Pronation
    peak_series = hdata['EulerZ'].values
    maxtab, mintab = peak.peakdet(peak_series, .05)
    
    ###THE GOOD STUFF!!!####
    if len(maxtab) != 0 or len(mintab) != 0:
        out= rot_CME(maxtab, mintab, output, .1, 1, 250)
    
    
    
    