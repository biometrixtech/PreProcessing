# -*- coding: utf-8 -*-
"""
Created on Thu Jul 07 16:27:47 2016

@author: Ankur
"""

import numpy as np

from phaseID import phase_id


def combine_phase(laccz, raccz, hz):
    
    """Combines the balance, foot in the air and the impact phases for the
    left and right feet.
    
    Args:
        laccz: left foot vertical acceleration
        raccz: right foot vertical acceleration
        hz: sampling rate
        
    Returns:
        lf_ph: an array of the different phases of the left foot
        rf_ph: an array of the different phases of the right foot
    
    """
    
    ph = _body_phase(raccz, laccz, hz)  # balance phase for both the right
    # and left feet
    
    lf_ph = list(ph)
    rf_ph = list(ph)
    
    lf_sm, lf_em = _bound_det_lf(lf_ph)  # detecting the start and end
    # points of the left foot movement phase
    rf_sm, rf_em = _bound_det_rf(rf_ph)  # detecting the start and end
    # points of the right foot movement phase
    
    lf_imp = _impact_detect(lf_sm, lf_em, laccz, hz)  # starting and ending
    # point of the impact phase for the left foot
    rf_imp = _impact_detect(rf_sm, rf_em, raccz, hz)  # starting and ending
    # points of the impact phase for the right foot

    if len(lf_imp) > 0: #condition to check whether impacts exist in the
    # left foot data
        for i, j in zip(lf_imp[:, 0], lf_imp[:, 1]):
            lf_ph[i:j] = [phase_id.lf_imp.value]*int(j-i) #decide impact
            # phase for the left foot
    
    if len(rf_imp) > 0: #condition to check whether impacts exist in the
    # right foot data
        for x, y in zip(rf_imp[:, 0], rf_imp[:, 1]):
            rf_ph[x:y] = [phase_id.rf_imp.value]*int(y-x) #decide impact
            # phase for the right foot
                        
    return np.array(lf_ph).reshape(-1, 1), np.array(rf_ph).reshape(-1, 1)
    
    
def _body_phase(raz, laz, hz):
    
    """Combining the phases of both the left and right feet.

    Args:
        raz: right foot vertical acceleration
        laz: left foot vertical acceleration
        hz: int, sampling rate of sensor
        
    Returns:
        phase: a numpy array that stores the different phases of both the feet
    
    """
    
    r = _phase_detect(raz, hz)  # run phase detect on right foot
    l = _phase_detect(laz, hz)  # run phase detect on left foot
    
    phase = []  # store body phase decisions
    for i in range(len(r)):
        if r[i] == 0 and l[i] == 0:  # decide in balance phase
            phase.append(phase_id.rflf_ground.value)  # append to list
        elif r[i] == 1 and l[i] == 0:  # decide left foot on the ground
            phase.append(phase_id.lf_ground.value)  # append to list
        elif r[i] == 0 and l[i] == 1:  # decide right foot on the ground
            phase.append(phase_id.rf_ground.value)  # append to list
        elif r[i] == 1 and l[i] == 1:  # decide both feet off ground
            phase.append(phase_id.rflf_offground.value)  # append to list
            
    return np.array(phase)


def _phase_detect(acc, hz):
    
    """Detects when the foot is on the ground vs. when the foot is in the air
    
    Args:
        acc: an array, foot acceleration in the adjusted inertial frame
        hz: an int, sampling rate of sensor
        
    Returns:
        bal_phase: a numpy array that returns 1's and 0's for foot in the air
        and foot on the ground respectively
    
    """
    
    thresh = 2.0  # threshold to detect balance phase
    bal_win = int(0.08*hz)  # sampling window to determine balance phase
    dummy_balphase = []  # dummy variable to store indexes of balance phase

    for i in range(len(acc) - bal_win):
        count = 0
        for j in range(bal_win):
            if abs(acc[i+j]) <= thresh:  # checking whether each data point 
            # in the sampling window is lesser than or equal to the thresh
                count = count + 1
        if count == bal_win:  # checking if the number of data points that 
        # are considered as "balance phase" equal the sampling window 
        # (minimum number of data points required for the set of data points 
        # to be considered as "balance phase")
            for k in range(bal_win):
                dummy_balphase.append(i+k)       
        
    # determine the unique indexes in the dummy list
    start_bal = []    
    start_bal = np.unique(dummy_balphase)
    start_bal = start_bal.tolist()  # convert from numpy array to list

    # eliminate false movement phases 
    min_thresh_mov = int(0.024*hz)  # threshold for minimum number of samples 
    # required to be classified as false movement phase

    for i in range(len(start_bal) - 1):
        diff = start_bal[i+1] - start_bal[i]
        if diff > 1 and diff <= min_thresh_mov:
            for j in range(1, diff+1):
                start_bal.insert(i+j, start_bal[i]+j)
    
    # create balance phase array
    bal_phase = []
    bal_phase = [1]*len(acc)  # 1=movement phase

    for i in start_bal:
        bal_phase[i] = 0  # 0=balance phase
    
    return np.array(bal_phase)
 
   
def _bound_det_lf(p):
    
    """Determines the starting and ending points of the movement phase for
    the left foot
    
    Args:
        p: an array, left foot phase
    
    Returns:
        start_move: an array that stores the indexes when the 'foot in the
        air' phase begins for the left foot
        end_move: an array that stores the indexes when the 'foot in the
        air' phase ends for the left foot
        
    """
    start_move = []
    end_move = []
    
    for i in range(len(p)-1):
        if p[i] == phase_id.rflf_ground.value and \
        p[i+1] == phase_id.rf_ground.value:
            start_move.append(i+1)
        elif p[i] == phase_id.lf_ground.value and \
        p[i+1] == phase_id.rf_ground.value: 
            start_move.append(i+1)
        elif p[i] == phase_id.rflf_ground.value and \
        p[i+1] == phase_id.rflf_offground.value: 
            start_move.append(i+1)
        elif p[i] == phase_id.lf_ground.value and \
        p[i+1] == phase_id.rflf_offground.value: 
            start_move.append(i+1)
        elif p[i] == phase_id.rf_ground.value and \
        p[i+1] == phase_id.rflf_ground.value:
            end_move.append(i)
        elif p[i] == phase_id.rf_ground.value and \
        p[i+1] == phase_id.lf_ground.value:
            end_move.append(i)
        elif p[i] == phase_id.rflf_offground.value and \
        p[i+1] == phase_id.rflf_ground.value: 
            end_move.append(i)
        elif p[i] == phase_id.rflf_offground.value and \
        p[i+1] == phase_id.lf_ground.value:
            end_move.append(i)
                        
    return start_move, end_move
 
   
def _bound_det_rf(p):
    
    """Determines the starting and ending points of the movement phase for
    the right foot
    
    Args:
        p: right foot phase
    
    Returns:
        start_move: an array that stores the indexes when the 'foot in the
        air' phase begins for the right foot
        end_move: an array that stores the indexes when the 'foot in the
        air' phase ends for the right foot
    
    """
    start_move = []
    end_move = []
    
    for i in range(len(p)-1):
        if p[i] == phase_id.rflf_ground.value and \
        p[i+1] == phase_id.lf_ground.value:
            start_move.append(i+1)
        elif p[i] == phase_id.rf_ground.value and \
        p[i+1] == phase_id.lf_ground.value:
            start_move.append(i+1)
        elif p[i] == phase_id.rflf_ground.value and \
        p[i+1] == phase_id.rflf_offground.value:
            start_move.append(i+1)
        elif p[i] == phase_id.rf_ground.value and \
        p[i+1] == phase_id.rflf_offground.value:
            start_move.append(i+1)
        elif p[i] == phase_id.lf_ground.value and \
        p[i+1] == phase_id.rflf_ground.value:
            end_move.append(i)
        elif p[i] == phase_id.lf_ground.value and \
        p[i+1] == phase_id.rf_ground.value:
            end_move.append(i)
        elif p[i] == phase_id.rflf_offground.value and \
        p[i+1] == phase_id.rflf_ground.value:
            end_move.append(i)
        elif p[i] == phase_id.rflf_offground.value and \
        p[i+1] == phase_id.rf_ground.value:
            end_move.append(i)
            
    return start_move, end_move
 
   
def _impact_detect(start_move, end_move, az, hz):
    
    """Detects when impact occurs.
    
    Args:
        start_move: an array of the indexes when the 'foot in the air' phase
        begins for left/right foot
        end_move: an array of the indexes when the 'foot in the air' phase
        ends for left/right foot
        az: vertical acceleration of left/right foot
        hz: an int, sampling rate of sensor
        
    Returns:
        imp: a 2d array that stores the indexes of when the impact phase
        begins and ends for left/right foot
    
    """
    g = 9.80665  # acceleration due to gravity (constant)
    neg_thresh = -g/2  # negative threshold 
    pos_thresh = g  # positive threshold 
    win = int(0.05*hz)  # sampling window
    acc = 0
    start_imp = []
    end_imp = []
    
    for i,j in zip(start_move, end_move):
        arr_len = []
        dummy_start_imp = []
        dummy_end_imp = []
        acc = az[i:j]  # acceleration values of corresponding movement phase
        arr_len = range(len(acc)-win)
        numbers = iter(arr_len)
        for k in numbers:
            if acc[k] <= neg_thresh:  # check if AccZ[k] is lesser than 
            # the negative thresh
                for l in range(win):
                    if acc[k+l] >= pos_thresh:  # checking if AccZ[k+1] is 
                    # greater or equal than the positive thresh (the trend 
                    # from a negative acc value to a positive acc value in 
                    # qick succession is an indication of an impact phase)
                        dummy_start_imp.append(i+k)
                        dummy_end_imp.append(i+k+l)
                        break
        if len(dummy_start_imp) == 1:  # if length of dummy list is 1, then 
        # the corresponding value gives us the starting point of the 
        # impact phase
            start_imp.append(dummy_start_imp[0])  # append start point of 
            # impact phase
            end_imp.append(j)  # append end point of impact phase
        elif len(dummy_start_imp) > 1:  # if dummy list is greater than 1 
        # then search for the true starting point of impact phase
            for m, n in zip(range(len(dummy_start_imp)), 
                                range(len(dummy_end_imp))):
                if (((j-i)/2)+i) < dummy_start_imp[m] <= j:  # search only 
                # second half of movement phase (generally first half 
                # consitutes, 'foot taking off the ground' phase)
                    pos = np.argmin(az[dummy_start_imp[m]:dummy_end_imp[n]]) 
                    # returns positin of the minimum acceleration value
                    start_imp.append(pos+dummy_start_imp[m])  # append start 
                    # point of impact phase
                    end_imp.append(j)  # append end point of impact phase
                    break
                
    imp = []
    imp = [[i,j] for i,j in zip(start_imp, end_imp)]
            
    return np.array(imp)

    
if __name__ == "__main__":
    
    import matplotlib.pyplot as plt
    import time
    
    datapath = '/Users/ankurmanikandan/Documents/BioMetrix/data files/Datasets\
    /bodyframe_Subject5_LESS.csv'
    data = np.genfromtxt(datapath, delimiter=",", dtype=float,
                         names=True)
    
    #rdata = pd.read_csv(rpath)
    #ldata = pd.read_csv(lpath)
    #hdata = pd.read_csv(hpath)
        
    sampl_rate = 250
    #comp = 'AccZ'
    #racc = rdata[comp]
    #lacc = ldata[comp] #input AccZ values!
    #rf_ph = _phase_detect(racc, sampl_rate)
    #lf_ph = _phase_detect(lacc, sampl_rate)
    
    start_time = time.time()
    lf_phase, rf_phase = combine_phase(data['LAccZ'], data['RAccZ'],
                                       data['Timestamp'])
    print time.time() - start_time
    
    #Plotting
    #plt.figure(1)
    #plt.plot(rf_ph)
    #plt.plot(rdata['AccZ'])
    #plt.title(comp)
    #plt.show()
    
    plt.figure(2)
    plt.plot(lf_phase)
    plt.plot(data['LAccZ'])
#    plt.title(comp)
    plt.show()
    
    plt.figure(3)
    plt.plot(rf_phase)
    plt.plot(data['RAccZ'])
    #plt.title(comp)
    plt.show()
#
#    plt.figure(4)
#    plt.plot(data['epoch_time'])
#    plt.show()
