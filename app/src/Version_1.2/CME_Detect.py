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
#############################################################################################################
"""
def rot_CME(maxtab, mintab, states, state):
    combine = np.concatenate((maxtab, mintab)) #combine min and max array
    combine = combine[combine[:,0].argsort()] #sort by index to get in chronological order
    mags = [[(180/np.pi)*(combine[i,1]-combine[i-1,1]), combine[i,0], combine[i-1,0]] for i in range(1,len(combine))] #calculate magnitude of change and pass time stamps    
    final = [mags[i] for i in range(1,len(mags)) if states[int(mags[i][1])] in state] #filter out by state
    final = np.array(final)
    return final[:,0], final[:,1], final[:,2]
    
if __name__ == "__main__":
    pos = 'lf'
    lroot = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\lfdatabody.csv'
    rroot = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\rfdatabody.csv'
    hroot = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\hipdatabody.csv'
    
#    lroot = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\BodyFrame walking\\Lheel_Gabby_walking_heeltoe_set1.csv'
#    rroot = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\BodyFrame walking\\Rheel_Gabby_walking_heeltoe_set1.csv'
#    hroot = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\BodyFrame walking\\hips_Gabby_walking_heeltoe_set1.csv'    
    
    rdata = pd.read_csv(rroot)
    ldata = pd.read_csv(lroot)
    hdata = pd.read_csv(hroot)
    
    ##Phase Detection
    rseries = rdata['AccZ'].values
    lseries = ldata['AccZ'].values #input AccZ values!
    rpitch = rdata['EulerY'].values
    lpitch = ldata['EulerY'].values
    output = phase.Body_Phase(rseries, lseries, rpitch, lpitch, 250)
    ldata['Phase'] = output
    rdata['Phase'] = output
    hdata['Phase'] = output   
    
    #Peak Detection- Right Foot Pronation
    peak_series = hdata['EulerZ'].values
    maxtab, mintab = peak.peakdet(peak_series, .05)
    
    ###THE GOOD STUFF!!!####
    if len(maxtab) != 0 or len(mintab) != 0:
        rot_mag, upper_lim, lower_lim = rot_CME(maxtab, mintab, output, [1,0])

    
    
    