# -*- coding: utf-8 -*-
"""
Created on Thu Jul 07 16:27:47 2016

@author: Ankur
"""

"""
#############################################INPUT/OUTPUT####################################################
Function: combine_phase
Inputs: AccZ right and left feet; sampling rate
Outputs: 2 arrays -> left foot phase & right foot phase
#############################################################################################################
"""

import numpy as np
from phaseID import phase_id

def Phase_Detect(acc, hz):
    
    thresh = 2.0 #setting the threshold to detect balance phase
    bal_win = int(0.08*hz) #setting a sampling window to determine balance phase
    dummy_balphase = [] #dummy variable to store the indexes of balance phase

    for i in range(len(acc) - bal_win):
        count = 0
        for j in range(bal_win):
            if abs(acc[i+j]) <= thresh: #checking whether each data point in the sampling window is lesser than or equal to the thresh
                count = count + 1
        if count == bal_win: #checking if the number of data points that are considered as "balance phase" equal the sampling window (minimum number of data points required for the set of data points to be considered as "balance phase")
            for k in range(bal_win):
                dummy_balphase.append(i+k)       
        
    #determinig the unique indexes in the dummy list
    start_bal = []    
    start_bal = np.unique(dummy_balphase)
    start_bal = start_bal.tolist() #converting from numpy array to a list

    #eliminating false movement phases 
    min_thresh_mov = int(0.024*hz) #a threshold for minimum number of samples required to be classified as a false movement phase

    for i in range(len(start_bal) - 1):
        diff = start_bal[i+1] - start_bal[i]
        if diff > 1 and diff <= min_thresh_mov:
            for j in range(1,diff+1):
                start_bal.insert(i+j, start_bal[i]+j)
    
    #creating the balance phase array
    bal_phase = []
    bal_phase = [1]*len(acc) # 1 = movement phase

    for i in start_bal:
        bal_phase[i] = 0 # 0 = balance phase
    
    return np.array(bal_phase) #return array

def Body_Phase(raz, laz, hz):
    
    r = Phase_Detect(raz, hz) #run phase detect on right foot
    l = Phase_Detect(laz, hz) #run phase detect on left foot
    
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
    
    #determining the starting and ending points of the movement phase for the left foot
    
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
                        
    return start_move, end_move
    
def bound_det_rf(p):
    
    #determining the starting and ending points of the movement phase for the right foot
    
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
            
    return start_move, end_move
    
def impact_detect(start_move, end_move, az, hz):
    
    g = 9.80665 #acceleration due to gravity (constant)
    neg_thresh = -g/2 #negative threshold 
    pos_thresh = g #positive threshold 
    win = int(0.05*hz) #sampling window
    acc = 0
    start_imp = []
    end_imp = []
    
    for i,j in zip(start_move, end_move):
        arr_len = []
        dummy_start_imp = []
        dummy_end_imp = []
        acc = az[i:j] #acceleration values of the corresponding movement phase
        arr_len = range(len(acc)-win)
        numbers = iter(arr_len)
        for k in numbers:
            if acc[k] <= neg_thresh: #checking if AccZ[k] is lesser than the negative thresh
                for l in range(win):
                    if acc[k+l] >= pos_thresh: #checking if AccZ[k+1] is greater or equal than the positive thresh (the trend from a negative acc value to a positive acc value in qick succession is an indication of an impact phase)
                        dummy_start_imp.append(i+k)
                        dummy_end_imp.append(i+k+l)
                        break
        if len(dummy_start_imp) == 1: #if length of the dummy list is 1, then the corresponding value gives us the starting point of the impact phase
            start_imp.append(dummy_start_imp[0]) #appending the starting point of the impact phase
            end_imp.append(j) #appending the ending point of the impact phase
        elif len(dummy_start_imp) > 1: #if the dummy list is greater than 1 then search for the true starting point of the impact phase
            for m, n in zip(range(len(dummy_start_imp)), range(len(dummy_end_imp))):
                if (((j-i)/2)+i) < dummy_start_imp[m] <= j: #search only the second half of a movement phase (generally the first half consitutes the 'foot taking off the ground' phase)
                    pos = np.argmin(az[dummy_start_imp[m]:dummy_end_imp[n]]) #returns the positin of the minimum acceleration value
                    start_imp.append(pos+dummy_start_imp[m]) #appending the starting point of the impact phase
                    end_imp.append(j) #appending the ending point of the impact phase
                    break
                
    imp = []
    imp = [ [i,j] for i,j in zip(start_imp, end_imp) ]
            
    return np.array(imp)

def combine_phase(laccz, raccz, hz):
    
    ph = Body_Phase(raccz, laccz, hz) #balance phase for both the right and left feet  
    
    lf_ph = list(ph)
    rf_ph = list(ph)
    
    lf_sm, lf_em = bound_det_lf(lf_ph) #detecting the start and end points of the left foot movement phase
    rf_sm, rf_em = bound_det_rf(rf_ph) #detecting the start and end points of the right foot movement phase 
    
    lf_imp = impact_detect(lf_sm, lf_em, laccz, hz) #starting and ending point of the impact phase for the left foot
    rf_imp = impact_detect(rf_sm, rf_em, raccz, hz) #starting and ending points of the impact phase for the right foot

    if len(lf_imp) > 0: #condition to check whether impacts exist in the left foot data
        for i,j in zip(lf_imp[:,0], lf_imp[:,1]):
            lf_ph[i:j] = [phase_id.lf_imp.value]*int(j-i) #decide impact phase for the left foot
    
    if len(rf_imp) > 0: #condition to check whether impacts exist in the right foot data
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
    
    datapath = 'C:\\Users\\Ankur\\python\\Biometrix\\Data analysis\\data exploration\\data files\\GRF Data _Abigail\\combined\\combined_bodyframe_sensordata.csv'

    #rdata = np.genfromtxt(rpath, delimiter = ",", dtype = float, names = True)
    #ldata = np.genfromtxt(lpath, delimiter = ",", dtype = float, names = True)
    
    data = np.genfromtxt(datapath, delimiter = ",", dtype = float, names = True)
    
    #rdata = pd.read_csv(rpath)
    #ldata = pd.read_csv(lpath)
    #hdata = pd.read_csv(hpath)
        
    sampl_rate = 250
    #comp = 'AccZ'
    #racc = rdata[comp]
    #lacc = ldata[comp] #input AccZ values!
    #rf_ph = Phase_Detect(racc, sampl_rate)
    #lf_ph = Phase_Detect(lacc, sampl_rate)
    
    lf_phase, rf_phase = combine_phase(data['LAccZ'], data['RAccZ'], sampl_rate)
    
    #Plotting    
    #plt.figure(1)    
    #plt.plot(rf_ph)
    #plt.plot(rdata['AccZ'])
    #plt.title(comp)
    #plt.show()
    
    #plt.figure(2)    
    #plt.plot(lf_ph)
    #plt.plot(ldata['AccZ'])
    #plt.title(comp)
    #plt.show()
    
    plt.figure(3)    
    plt.plot(rf_phase)
    plt.plot(data['RAccZ'])
    #plt.title(comp)
    plt.show()
