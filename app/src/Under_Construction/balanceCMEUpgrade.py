# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 05:34:54 2016

@author: court
"""
import numpy as np
import coordinateFrameTransformationUpgrade as prep
import quatOps as qo
import quatConvs as qc

"""
#############################################INPUT/OUTPUT####################################################   
Inputs: continuous orientation data, body phase detection, list of states for evaluation, neutral position for
axis, list of thresholds

Outputs: array [time stamp, normalization score, indic of positive or negative, angle difference from neutral]

Datasets: inputs.csv (contains both peak and trough values) -> cont_rot_CME(inputs['EulerX'], inputs['Phase'],
[0,1], neutral_eul[0], cme_dict['prosupl']) -> outputs.csv
#############################################################################################################
"""
def cont_norm_score(mag, quat, cme):
    la = cme[0]
    le = cme[1]
    ua = cme[2] # upper allowable
    ue = cme[3]
    dev = quat-mag
    if 0 < dev <= ua:
        return 1, dev
    elif ua < dev < ue:
        return 1 - ((dev-ua)/(ue-ua)), dev
    elif dev >= ue:
        return 0, dev
    elif la <= dev <= 0:
        return 1, dev
    elif le < dev < la:
        return 1 - ((dev-la)/(le-la)), dev
    elif dev <= le:
        return 0, dev
    
    
def cont_rot_CME(series, states, state, rel, cme):
    out = []
    for i in range(len(series)):
        if states[i] in state:
            ang = (180/np.pi)*series[i]
            comp = (180/np.pi)*rel
            n, raw = cont_norm_score(ang, comp, cme)
            out.append([i, raw, n])
        else:
            out.append([i, np.nan, np.nan])
    return np.array(out)
    
if __name__ == "__main__":
    pos = 'lf'
    lroot = 'C:\\Users\\Brian\\Documents\\GitHub\\PreProcessing\\app\\test\\data\\balanceCME\\input.csv' 
    
    cme_dict = {'prosupl':[-4, -7, 4, 15], 'hiprotl':[-4, -7, 4, 15], 'hipdropl':[-4, -7, 4, 15],
                'prosupr':[-4, -15, 4, 7], 'hiprotr':[-4, -15, 4, 7], 'hipdropr':[-4, -15, 4, 7],
                'hiprotd':[-4, -7, 4, 7]}    
    
    ldata = np.genfromtxt(lroot, dtype=float, delimiter=',', names=True)
    
    #neutral = np.matrix([0.582,0.813,0,0]) # stand-in, will come from anatomical fix module
    hip_bf = hipdata['HqW','HqX','HqY','HqZ']
    neutral = qo.quat_prod(hip_bf,ft_n_transform)    
    
    eulX = ldata['EulerX']
    phase = ldata['Phase']
    neutral_eul = qc.q2eul(neutral)
    
    ###THE GOOD STUFF!!!####
    out = cont_rot_CME(eulX, phase, [0], neutral_eul[0], cme_dict['prosupl'])
    print(out)

    
    
    
