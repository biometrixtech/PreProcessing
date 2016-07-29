# -*- coding: utf-8 -*-
"""
Created on Thu Jul 07 16:27:47 2016

@author: Ankur
"""

"""
#############################################INPUT/OUTPUT####################################################
Function: combine_phase
Inputs: AccX, AccZ right and left feet; EulerY angles for right and left feet; sampling rate
Outputs: 2 arrays; left foot phase; right foot phase
#############################################################################################################
"""

import numpy as np
import pandas as pd
from phaseID import phase_id

def Phase_Detect(series, pitch, hz):
    
    acc = 0
    acc = abs(series['AccX']) #absolute value of AccX
    orient = abs(pitch) #absolute value of EulerY
    accdiff = abs(series['AccZ']-acc) #absolute value of the difference between AccZ and AccX
    std_acc = 0    
    
    #setting the rolling window based on the sampling rate
    if hz == 250:
        win = int(0.4*hz) #rolling window
    elif hz == 100:
        win = int(0.2*hz) #rolling window
        
    consec_pnts = int(0.02*hz) #number of consecutive points to be considered to test for balance phase condition
    mean_accdiff = pd.rolling_mean(accdiff, window=win, center=True) #rolling mean of the difference between AccZ and AccX
    std_acc = pd.rolling_std(acc, window = win, center=True) #rolling std of absolute values of AccX
    std_orient = pd.rolling_std(orient, window=win, center=True) #rolling std of absolute values of EulerY
    
    dummy_start_bal = []
    start_bal = []

    for i in range(len(std_acc)-consec_pnts):
        count = 0
        for j in range(consec_pnts): 
            if 0 < std_acc[i+j] <= 1.1: #determine if t=i+j is not moving
                count = count + 1
        if count == consec_pnts: #if count satisfies the minimum number of consecutive data points required to satisfy the balance phase conditions
            for k in range(consec_pnts):
                if std_orient[i+k] < .07 and orient[i+k] < .9: #eliminate curled foot and fast change of orientation
                    dummy_start_bal.append(i+k)
                if orient[i+k] > .3 and mean_accdiff[i+k] > 2 and i+k in dummy_start_bal: #elim slow change in orient
                    dummy_start_bal.remove(i+k)
            
    start_bal = np.unique(dummy_start_bal)
    
    bal_phase = []
    bal_phase = [1]*len(acc)

    for i in start_bal:
        bal_phase[i] = 0
    
    return np.array(bal_phase) #return array

def Body_Phase(right, left, rpitch, lpitch, hz):
    
    r = Phase_Detect(right, rpitch, hz) #run phase detect on right foot
    l = Phase_Detect(left, lpitch, hz) #run phase detect on left foot
    
    phase = [] #store body phase decisions
    for i in range(len(r)):
        if r[i] == 0 and l[i] == 0: #decide in balance phase
            phase.append(phase_id.rflf_ground.value) #append to list
        elif r[i] == 1 and l[i] == 0: #decide left foot on the ground
            phase.append(phase_id.lf_ground.value) #append to list
        elif r[i] == 0 and l[i] == 1: #decide right foot on the ground
            phase.append(phase_id.rf_ground.value) #append to list
        elif r[i] == 1 and l[i] == 1: #decide both feet off ground
            phase.append(phase_id.rflf_offground.value) #append to list
    return np.array(phase)
    
def bound_det_lf(p):
    
    start_move = []
    end_move = []
    
    for i in range(len(p)-1):
        if p[i] == phase_id.rflf_ground.value and p[i+1] == phase_id.rf_ground.value:
            start_move.append(i+1)
        elif p[i] == phase_id.lf_ground.value and p[i+1] == phase_id.rf_ground.value:
            start_move.append(i+1)
        elif p[i] == phase_id.rflf_ground.value and p[i+1] == phase_id.rflf_offground.value:
            start_move.append(i+1)
        elif p[i] == phase_id.lf_ground.value and p[i+1] == phase_id.rflf_offground.value:
            start_move.append(i+1)
        elif p[i] == phase_id.rf_ground.value and p[i+1] == phase_id.rflf_ground.value:
            end_move.append(i)
        elif p[i] == phase_id.rf_ground.value and p[i+1] == phase_id.lf_ground.value:
            end_move.append(i)
        elif p[i] == phase_id.rflf_offground.value and p[i+1] == phase_id.rflf_ground.value:
            end_move.append(i)
        elif p[i] == phase_id.rflf_offground.value and p[i+1] == phase_id.lf_ground.value:
            end_move.append(i)
            
    start_move = np.delete(start_move, [len(start_move)-1])
    end_move = np.delete(end_move, [0])
                        
    return start_move, end_move
    
def bound_det_rf(p):
    
    start_move = []
    end_move = [] 
    
    for i in range(len(p)-1):
        if p[i] == phase_id.rflf_ground.value and p[i+1] == phase_id.lf_ground.value:
            start_move.append(i+1)
        elif p[i] == phase_id.rf_ground.value and p[i+1] == phase_id.lf_ground.value:
            start_move.append(i+1)
        elif p[i] == phase_id.rflf_ground.value and p[i+1] == phase_id.rflf_offground.value:
            start_move.append(i+1)
        elif p[i] == phase_id.rf_ground.value and p[i+1] == phase_id.rflf_offground.value:
            start_move.append(i+1)
        elif p[i] == phase_id.lf_ground.value and p[i+1] == phase_id.rflf_ground.value:
            end_move.append(i)
        elif p[i] == phase_id.lf_ground.value and p[i+1] == phase_id.rf_ground.value:
            end_move.append(i)
        elif p[i] == phase_id.rflf_offground.value and p[i+1] == phase_id.rflf_ground.value:
            end_move.append(i)
        elif p[i] == phase_id.rflf_offground.value and p[i+1] == phase_id.rf_ground.value:
            end_move.append(i)
            
    start_move = np.delete(start_move, [len(start_move)-1])
    end_move = np.delete(end_move, [0])
            
    return start_move, end_move
    
def impact_detect(start_move, end_move, az, hz):
    
    g = 9.80665 
    neg_thresh = -g/2 #negative threshold 
    pos_thresh = g #positive threshold 
    win = int(0.05*hz) #sampling window
    acc = 0
    start_imp = []
    end_imp = []
    
    print(start_move, end_move)
        
    for i,j in zip(start_move, end_move):
        arr_len = []
        dummy_start_imp = []
        dummy_end_imp = []
        acc = az[i:j]
        arr_len = range(len(acc)-win)
        numbers = iter(arr_len)
        for k in numbers:
            if acc[k] <= neg_thresh:
                for l in range(win):
                    if acc[k+l] >= pos_thresh:
                        dummy_start_imp.append(i+k)
                        dummy_end_imp.append(i+k+l)
                        break
        if len(dummy_start_imp) == 1:
            start_imp.append(dummy_start_imp[0])
            end_imp.append(j)
        elif len(dummy_start_imp) > 1:
            for m, n in zip(range(len(dummy_start_imp)), range(len(dummy_end_imp))):
                if (((j-i)/2)+i) < dummy_start_imp[m] <= j:
                    pos = np.argmin(az[dummy_start_imp[m]:dummy_end_imp[n]]) #returns the positin of the minimum acceleration value
                    start_imp.append(pos+dummy_start_imp[m])
                    end_imp.append(j)
                    break
                
    imp = []
    imp = [ [i,j] for i,j in zip(start_imp, end_imp) ]
            
    return np.array(imp)

def combine_phase(lacc, racc, rpitch, lpitch, hz):
    
    ph = Body_Phase(racc, lacc, rpitch, lpitch, hz) #balance phase for both the right and left feet  
    
    lf_ph = list(ph)
    rf_ph = list(ph)
    
    lf_sm, lf_em = bound_det_lf(lf_ph) #detecting the start and end points of the left foot movement phase
    rf_sm, rf_em = bound_det_rf(rf_ph) #detecting the start and end points of the right foot movement phase
    
    lf_imp = impact_detect(lf_sm, lf_em, lacc['AccZ'], hz) #starting and ending point of the impact phase for the left foot
    rf_imp = impact_detect(rf_sm, rf_em, racc['AccZ'], hz) #starting and ending points of the impact phase for the right foot

    for i,j in zip(lf_imp[:,0], lf_imp[:,1]):
        lf_ph[i:j] = [phase_id.lf_imp.value]*int(j-i) #decide impact phase for the left foot
    
    for x,y in zip(rf_imp[:,0], rf_imp[:,1]):
        rf_ph[x:y] = [phase_id.rf_imp.value]*int(y-x) #decide impact phase for the right foot            
            
    return np.array(lf_ph), np.array(rf_ph)
    
if __name__ == "__main__": 
    
    import matplotlib.pyplot as plt
    
    rpath = 'C:\\Users\\Ankur\\python\\Biometrix\\Data analysis\\data exploration\\data files\\Subject5\\Subject5_rfdatabody_LESS.csv'
    #rpath = 'C:\\Users\\Ankur\\python\\Biometrix\\Data analysis\\data exploration\\data files\\ChangeDirection\\Rheel_Gabby_changedirection_set1.csv'
    #rpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Walking\Rheel_Gabby_walking_heeltoe_set1.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Walking\Lheel_Gabby_walking_heeltoe_set1.csv'   
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_lfdatabody_set1.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Stomp\Lheel_Gabby_stomp_set1.csv'
    #lpath = 'C:\\Users\\Ankur\\python\\Biometrix\\Data analysis\\data exploration\\data files\\ChangeDirection\\Lheel_Gabby_changedirection_set1.csv'
    lpath = 'C:\\Users\\Ankur\\python\\Biometrix\\Data analysis\\data exploration\\data files\\Subject5\Subject5_lfdatabody_LESS.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Jump\Lheel_Gabby_jumping_explosive_set2.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Walking\Lheel_Gabby_walking_heeltoe_set1.csv'
    #hpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_hipdatabody_set1.csv'
    hpath = 'C:\\Users\\Ankur\\python\\Biometrix\\Data analysis\\data exploration\\data files\\Subject5\\Subject5_hipdatabody_LESS.csv'

    rdata = np.genfromtxt(rpath, delimiter = ",", dtype = float, names = True)
    ldata = np.genfromtxt(lpath, delimiter = ",", dtype = float, names = True)
    
    #rdata = pd.read_csv(rpath)
    #ldata = pd.read_csv(lpath)
    #hdata = pd.read_csv(hpath)
        
    sampl_rate = 250
    comp = 'AccZ'
    ptch = 'EulerY'
    racc = rdata[comp]
    lacc = ldata[comp] #input AccZ values!
    rpitch = rdata[ptch]
    lpitch = ldata[ptch]
    #ph = Body_Phase(racc, lacc, rpitch, lpitch, sampl_rate)

    lf_phase, rf_phase = combine_phase(ldata[['AccX', 'AccZ']], rdata[['AccX', 'AccZ']], rpitch, lpitch, sampl_rate)
    
    #Plotting
    
    plt.figure(1)    
    plt.plot(rf_phase)
    plt.plot(rdata['AccZ'])
    #plt.title(comp)
    plt.show()
