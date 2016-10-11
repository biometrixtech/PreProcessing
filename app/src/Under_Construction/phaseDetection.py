# -*- coding: utf-8 -*-
"""
Created on Thu Jul 07 16:27:47 2016

@author: Ankur
"""

import numpy as np
from phaseID import phase_id

def phase_detect(acc, hz):
    
    """Detecting balance and foot in the air phases.
 
    Args:
        acc: vertical acceleration of right/left foot.
        hz: sampling rate of the data.
 
    Returns:
        A numpy array of balance phase and foot in the air phase.
        For example:
 
        array([0,0,0,1,1,0,...,0,1,1,0,0,0])
 
    """
    
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
    bal_phase = [phase_id.IN_AIR.value]*len(acc) # 1 = foot in the air phase

    for i in start_bal:
        bal_phase[i] = phase_id.GROUND.value # 0 = balance phase
        
    bal_phase[-1] = phase_id.GROUND.value # correcting for a false negative (false foot in the air phase)
    
    return np.array(bal_phase) #return array
    
def bound_det_lf(lp):
    
    """Determining the starting and ending points of, foot in the air phase for the left foot.
 
    Args:
        lp: left foot phase.
 
    Returns:
        Two lists, start_move and end_move. 
        start_move: index number of data point, when movement (foot in the air) phase begins.
        end_move: index number of data point, when movement (foot in the air) phase ends.
        For example:
 
        start_move: [5,68,...,468,678]
        end_move: [12,77,...,500,700]
 
    """
    
    start_move = []
    end_move = []
    
    for i in range(len(lp)-1):
        if lp[i] == phase_id.GROUND.value and lp[i+1] == phase_id.IN_AIR.value:
            start_move.append(i+1)
        elif lp[i] == phase_id.IN_AIR.value and lp[i+1] == phase_id.GROUND.value:
            end_move.append(i)
                        
    return start_move, end_move
    
def bound_det_rf(rp):
    
    
    """Determining the starting and ending points of, foot in the air phase for the right foot.
 
    Args:
        rp: right foot phase.
 
    Returns:
        Two lists, start_move and end_move. 
        start_move: index number of data point, when movement (foot in the air) phase begins.
        end_move: index number of data point, when movement (foot in the air) phase ends.
        For example:
 
        start_move: [5,68,...,468,678]
        end_move: [12,77,...,500,700]
 
    """
    
    start_move = []
    end_move = [] 
    
    for i in range(len(rp)-1):
        if rp[i] == phase_id.GROUND.value and rp[i+1] == phase_id.IN_AIR.value:
            start_move.append(i+1)
        elif rp[i] == phase_id.IN_AIR.value and rp[i+1] == phase_id.GROUND.value:
            end_move.append(i)
            
    return start_move, end_move
    
def impact_detect(start_move, end_move, az, hz):
    
    
    """Detecting the index values, when an impact begins and ends.
 
    Args:
        start_move: index when movement (foot in the air) phase begins.
        end_move: index when movement (foot in the aor) phase ends.
        az: vertical acceleration (right/left foot).
        hz: sampling rate of the data.
 
    Returns:
        A 2-D numpy array. 
        1st column: index values, when impact begins.
        2nd column: index values, when impact ends.
        For example:
 
        array([[23,27], [78,86], ..., [567,578]])
 
    """
    
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
    imp = [ [i,j] for i,j in zip(start_imp, end_imp) ]  # start and end of impact phase
            
    return np.array(imp)

def combine_phase(laccz, raccz, hz):
    
    """Combining the balance, foot in the air and impact phases into a single
    array independently for each foot.
 
    Args:
        laccz: vertical acceleration, left foot.
        raccz: vertical acceleration, right foot.
        hz: sampling rate.
 
    Returns:
        Two 1-D numpy arrays.
        lf_ph: continuous phase values, left foot.
        rf_ph: continuous phase values, right foot.
        For example:
 
        lf_ph = array([0,0,0,1,1,1,...,2,2,2,2,2,0,0,0])
        rf_ph = array([1,1,0,0,0,1,...,1,1,2,2,2,0,0,0])
 
    """
    
    rf_ph = list(phase_detect(raccz, hz)) #run phase detect on right foot
    lf_ph = list(phase_detect(laccz, hz)) #run phase detect on left foot
    
    lf_sm, lf_em = bound_det_lf(lf_ph) #detecting the start and end points of the left foot movement phase
    rf_sm, rf_em = bound_det_rf(rf_ph) #detecting the start and end points of the right foot movement phase 
    
    lf_imp = impact_detect(lf_sm, lf_em, laccz, hz) #starting and ending point of the impact phase for the left foot
    rf_imp = impact_detect(rf_sm, rf_em, raccz, hz) #starting and ending points of the impact phase for the right foot

    if len(lf_imp) > 0: #condition to check whether impacts exist in the left foot data
        for i,j in zip(lf_imp[:,0], lf_imp[:,1]):
            lf_ph[i:j] = [phase_id.IMPACT.value]*int(j-i) #decide impact phase for the left foot
    
    if len(rf_imp) > 0: #condition to check whether impacts exist in the right foot data
        for x,y in zip(rf_imp[:,0], rf_imp[:,1]):
            rf_ph[x:y] = [phase_id.IMPACT.value]*int(y-x) #decide impact phase for the right foot  
            
    return np.array(lf_ph), np.array(rf_ph)  # return left foot phase array, right foot phae array
    
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
    
    datapath = '/home/ankur/Documents/BioMetrix/Data analysis/data exploration/data files/GRF Data _Abigail/combined/combined_bodyframe_sensordata.csv'

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
    
    plt.figure(1)    
    plt.plot(rf_phase*10)
    plt.plot(data['RAccZ'])
    #plt.title(comp)
    plt.show()
    
    plt.figure(2)    
    plt.plot(lf_phase*10)
    plt.plot(data['LAccZ'])
    #plt.title(comp)
    plt.show()
