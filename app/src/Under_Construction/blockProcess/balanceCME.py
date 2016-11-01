# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 05:34:54 2016

@author: court
"""
import numpy as np

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
    
    """
    Calculates score comparing body part angle to idealized angle.
    
    Args:
        mag: angle of body part
        quat: idealized angle of "neutral" for comparison
        cme: appropriate dictionary
        
    Returns:
        score: normalized score of difference
        dev: difference between actual position and "neutral" position
    
    """
    
    # set limits from dictionary
    _la = cme[0] # lower allowable
    _le = cme[1] # lower extreme
    _ua = cme[2] # upper allowable
    _ue = cme[3] # upper extreme
    
    # find deviation of actual from "neutral" position
    dev = quat-mag

    # score deviation based on limits
    if 0 < dev <= _ua:
        score = 1
    elif _ua < dev < _ue:
        score = 1 - ((dev-_ua)/(_ue-_ua))
    elif dev >= _ue:
        score = 0
    elif _la <= dev <= 0:
        score = 1
    elif _le < dev < _la:
        score = 1 - ((dev-_la)/(_le-_la))
    elif dev <= _le:
        score = 0
        
    return score, dev
    
    
def cont_rot_CME(data, state, states, neutral, cme):
    
    """
    Calculates the rotation of a body part from its "neutral" position.
    
    Args:
        data: data to compare to neutral position
        state: state of data (usually instantaneous phase)
        states: states during which data should be compared to neutral
        neutral: neutral value to which data should be compared
        cme: appropriate dictionary
    
    Returns:
        comparison: array comparing body position to neutral, consisting of
            [0] sample index
            [1] difference of body position from neutral
            [2] normalized score of difference
    
    """
    
    comparison = []
    for i in range(len(data)):
        
        # if state of body is within relevant states, analyze deviation from 
            # neutral
        if state[i] in states:
            
            # convert body position and neutral position to degrees
            _body_ang = (180/np.pi)*data[i]
            _neutral_ang = (180/np.pi)*neutral[i]
            
            # calculate rotation from neutral
            norm_score, raw = cont_norm_score(_body_ang, _neutral_ang, cme)
            comparison.append([i, raw, norm_score])
            
        else:
            comparison.append([i, np.nan, np.nan])
            
    return np.array(comparison)
    
    
if __name__ == "__main__":
    
    import pandas as pd
    
#    lroot = 'C:\\Users\\Brian\\Documents\\GitHub\\PreProcessing\\app\\test\\data\\balanceCME\\input.csv' 
    datapath = '/home/ankur/Documents/BioMetrix/Data analysis/data exploration/data files/Paul dataset/withPhase_Subject5_LESS_Transformed_Data.csv'
    
    
    cme_dict = {'prosupl':[-4, -7, 4, 15], 'hiprotl':[-4, -7, 4, 15], 'hipdropl':[-4, -7, 4, 15],
                'prosupr':[-4, -15, 4, 7], 'hiprotr':[-4, -15, 4, 7], 'hipdropr':[-4, -15, 4, 7],
                'hiprotd':[-4, -7, 4, 7]}    
    
    ldata = np.genfromtxt(datapath, dtype=float, delimiter=',', names=True)
    
    #neutral = np.matrix([0.582,0.813,0,0]) # stand-in, will come from anatomical fix module
#    hip_bf = hipdata['HqW','HqX','HqY','HqZ']
#    neutral = qo.quat_prod(hip_bf,ft_n_transform)   
    lf_neutral = np.array([-0.3069008549, -0.4869821188, -0.5838032711, -0.572567919])
    hip_neutral = np.array([0.7664549616, 0.0627079623, -0.0409383119, 0.6379173598])
    rf_neutral = np.array([-0.6607139502, -0.1956375453, -0.2694454381, -0.6727422856])

#    eulX = ldata['EulerX']
    phaseL = ldata['phaseL']
    phaseR = ldata['phaseR']
    lf_neutral_eul = qc.q2eul(lf_neutral)
    hip_neutral_eul = qc.q2eul(hip_neutral)
    rf_neutral_eul = qc.q2eul(rf_neutral)
    
    ###THE GOOD STUFF!!!####
    # calculate pronation/supination values
    l_out = cont_rot_CME(ldata['LeX'], phaseL, [0,1], lf_neutral_eul[0], cme_dict['prosupl'])
    r_out = cont_rot_CME(ldata['ReX'], phaseR, [0,2], rf_neutral_eul[0], cme_dict['prosupr'])
    
    # calculate contralateral hip drop values
    l_hipdrop = cont_rot_CME(ldata['HeY'], phaseL, [0,1], hip_neutral_eul[0], cme_dict['hipdropl'])
    r_hipdrop = cont_rot_CME(ldata['HeY'], phaseR, [0,2], hip_neutral_eul[0], cme_dict['hipdropr'])
    
    # calculate hip rotation values
    hiprot = cont_rot_CME(ldata['HeZ'], phaseL, [0], hip_neutral_eul[0], cme_dict['hiprotl'])
    
    df = pd.DataFrame(ldata)
    df['hipDropL'] = pd.Series(l_hipdrop[:,1])
    df['hipDropR'] = pd.Series(r_hipdrop[:,1])
    df['hipRot'] = pd.Series(hiprot[:,1])
    df['ankleRotL'] = pd.Series(l_out[:,1])
    df['ankleRotR'] = pd.Series(r_out[:,1])
    df.to_csv('/home/ankur/Documents/BioMetrix/Data analysis/data exploration/data files/Paul dataset/balacme_Subject5_LESS_Transformed_Data.csv')
    

    

    
    
    
