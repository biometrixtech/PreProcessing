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
def calc_norm_score(mag, a, e):        
    for i in mag:
        ang = i[0]
        if 0 < abs(ang) <= a:
            i[0] = 1
        elif a < abs(ang) < e:
            print(abs(ang))
            i[0] = 1 - ((abs(ang)-a)/(e-a))
        elif abs(ang) >= e:
            i[0] = 0
    return mag    

def rot_CME(maxtab, mintab, states, state):
    combine = np.concatenate((maxtab, mintab)) #combine min and max array
    combine = combine[combine[:,0].argsort()] #sort by index to get in chronological order
    mags = [[(180/np.pi)*(combine[i,1]-combine[i-1,1]), combine[i,0], combine[i-1,0]] for i in range(1,len(combine))] #calculate magnitude of change and pass time stamps    
    final = [mags[i] for i in range(1,len(mags)) if states[int(mags[i][1])] in state] #filter out by state
    final = np.array(final)
    print(final)
    out = calc_norm_score(final, 10, 20)
    print(out)
    return final[:,0], final[:,1], final[:,2]
    
    
def rel_rot_CME(maxtab, mintab, states, state, rel):
    combine = np.concatenate((maxtab, mintab))
    combine = combine[combine[:,0].argsort()]
    pos = [[combine[i,1]-rel, combine[i,0]] for i in range(len(combine)) if combine[i,1]-rel > thresh]
    neg = [[combine[i,1]-rel, combine[i,0]] for i in range(len(combine)) if combine[i,1]-rel < -thresh]
    print(pos, neg)       
    return pos,neg

def cont_norm_score(mag, la, le, ua, ue, quat):
    dev = quat-mag
    if 0 < dev <= ua:
        return 1, np.sign(dev)
    elif ua < dev < ue:
        return 1 - ((dev-ua)/(ue-ua)), np.sign(dev)
    elif dev >= ue:
        return 0, np.sign(dev)
    elif la <= dev <= 0:
        return 1, np.sign(dev)
    elif le < dev < la:
        return 1 - ((dev-la)/(le-la)), np.sign(dev)
    elif dev <= le:
        return 0, np.sign(dev)
    
    
def cont_rot_CME(series, states, state, rel):
    out = []
    for i in range(len(series)):
        if states[i] in state:
            ang = (180/np.pi)*series[i]
            comp = (180/np.pi)*rel
            n, indic = cont_norm_score(ang,-4, -7, 4, 15, comp)
            out.append([i, n, indic])
    return np.array(out)
            
    
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
    
    #Peak Detection- Right Foot Pronation
    peak_series = ldata['EulerX'].values
    maxtab, mintab = peak.peakdet(peak_series, .05)
    
    quat = np.array([1.9, 0, 0])
    if len(maxtab) != 0 or len(mintab) != 0:
        #final1, final2, final3 = rot_CME(maxtab, mintab, output, [1,0])
        #pro, sup = rel_rot_CME(maxtab, mintab, output, [2,0], quat)
        out = cont_rot_CME(peak_series, output, [0,1], quat[0])
    
    up = 0
    down = len(peak_series)
    #print(out[1800:2000,:])
    plt.plot(peak_series[up:down])
    plt.plot(out[:,1][up:down])
    plt.plot(out[:,2][up:down])
    plt.show()    