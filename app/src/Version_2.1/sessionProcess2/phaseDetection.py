# -*- coding: utf-8 -*-
"""
Created on Mon Dec 12 10:02:11 2016

@author: ankurmanikandan
"""

import logging

import numpy as np

from phaseID import phase_id


logger = logging.getLogger()


def combine_phase(laccz, raccz, hz):
    """
    Combines balance, foot in the air and impact phases for left and 
    right feet.
    
    Args:
        laccz: an array, left foot vertical acceleration
        raccz: an array, right foot vertical acceleration
        hz: an int, sampling rate
        
    Returns:
        lf_ph: an array, different phases of left foot
        rf_ph: an array, different phases of right foot
    """
    
    ph = _body_phase(raz=raccz, laz=laccz, hz=hz)  # balance phase for 
    # both right and left feet
    
    lf_ph = list(ph)
    rf_ph = list(ph)
    
    lf_sm, lf_em = _bound_det_lf(p=lf_ph)  # detecting the start and end
    # points of the left foot movement phase
    rf_sm, rf_em = _bound_det_rf(p=rf_ph)  # detecting the start and end
    # points of the right foot movement phase
    
    lf_imp = _impact_detect(start_move=lf_sm, end_move=lf_em, 
                            az=laccz, hz=hz)  # starting and ending
    # point of the impact phase for the left foot
    del lf_sm, lf_em, laccz  # no use in further computations
    rf_imp = _impact_detect(start_move=rf_sm, end_move=rf_em, 
                            az=raccz, hz=hz)  # starting and ending
    # points of the impact phase for the right foot
    del rf_sm, rf_em, raccz  # no use in further computations

    if len(lf_imp) > 0:  # condition to check whether impacts exist in the
    # left foot data
        for i, j in zip(lf_imp[:, 0], lf_imp[:, 1]):
            lf_ph[i:j+1] = [phase_id.lf_imp.value]*int(j-i+1)  # decide impact
            # phase for the left foot
    del lf_imp  # no use in further computation
    
    if len(rf_imp) > 0:  # condition to check whether impacts exist in the
    # right foot data
        for x, y in zip(rf_imp[:, 0], rf_imp[:, 1]):
            rf_ph[x:y+1] = [phase_id.rf_imp.value]*int(y-x+1)  # decide impact
            # phase for the right foot
    del rf_imp  # no use in further computation
            
    rf_ph = np.array(rf_ph)
    lf_ph = np.array(lf_ph)
            
    lf_ph, rf_ph = _final_phases(rf_ph, lf_ph)
    
    lf_imp_start_end, rf_imp_start_end,\
    lf_imp_range, rf_imp_range = _detect_start_end_imp_phase(lph=lf_ph,
                                                             rph=rf_ph)
                        
    return lf_ph.reshape(-1, 1), rf_ph.reshape(-1, 1),\
            lf_imp_start_end, rf_imp_start_end,\
            lf_imp_range, rf_imp_range
    
    
def _body_phase(raz, laz, hz):
    """
    Combining phases of both left and right feet.

    Args:
        raz: an array, right foot vertical acceleration
        laz: an array, left foot vertical acceleration
        hz: an int, sampling rate of sensor
        
    Returns:
        phase: an array, different phases of both feet
    """
    
    r = _phase_detect(acc=raz, hz=hz)  # run phase detect on right foot
    del raz  # delete raz, no use in further computations
    l = _phase_detect(acc=laz, hz=hz)  # run phase detect on left foot
    del laz  # delete laz, no use in further computations
    
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
    """
    Detect when foot is on the ground vs. when foot is in the air
    
    Args:
        acc: an array, foot acceleration in the adjusted inertial frame
        hz: an int, sampling rate of sensor
        
    Returns:
        bal_phase: an array, returns 1's and 0's for foot in the air
        and foot on the ground respectively
    """
    
    thresh = 2.0  # threshold to detect balance phase
    bal_win = int(0.08*hz)  # sampling window to determine balance phase
    dummy_balphase = []  # dummy variable to store indexes of balance phase
    
    abs_acc = abs(acc)  # creating an array of absolute acceleration values
    len_acc = len(acc)  # length of acceleration value
    
#    dummy_balphase1 = [range(i, i+bal_win) for i in range(len_acc-bal_win) \
#    if len(np.where(abs_acc[i:i+bal_win] <= thresh)[0]) == bal_win]
#    dummy_balphase = [val for sublist in dummy_balphase1 for val in sublist]

    for i in range(len_acc-bal_win):
#        count = 0
#        for j in range(bal_win):
#            if abs(acc[i+j]) <= thresh:  # checking whether each data point 
#            # in the sampling window is lesser than or equal to the thresh
#                count = count + 1
        if len(np.where(abs_acc[i:i+bal_win] <= thresh)[0]) == bal_win:  
#        if count == bal_win:
        # checking if the number of data points that 
        # are considered as "balance phase" equal the sampling window 
        # (minimum number of data points required for the set of data points 
        # to be considered as "balance phase")
#            for k in range(bal_win):
#                dummy_balphase.append(i+k) 
            dummy_balphase += range(i, i+bal_win)
                                
    # delete variables that are of no use in further compuations
    del acc, abs_acc
                        
    # determine the unique indexes in the dummy list
    start_bal = []    
    start_bal = np.unique(dummy_balphase)
    start_bal = start_bal.tolist()  # convert from numpy array to list
    
    # delete variables that are of no use in further compuations
    del dummy_balphase

    # eliminate false movement phases 
    min_thresh_mov = int(0.024*hz)  # threshold for minimum number of samples 
    # required to be classified as false movement phase

    for i in range(len(start_bal) - 1):
        diff = start_bal[i+1] - start_bal[i]
        if 1 < diff <= min_thresh_mov:
            for j in range(1, diff+1):
                start_bal.insert(i+j, start_bal[i]+j)
    
    # create balance phase array
#    bal_phase = []
    bal_phase = np.ones(len_acc)  # 1=movement phase
    bal_phase[start_bal] = 0  # 0=balance phase
    
#    for i in start_bal:
#        bal_phase[i] = 0  # 0=balance phase
    
    return bal_phase
 
   
def _bound_det_lf(p):
    """
    Determine starting and ending points of movement phase for left foot
    
    Args:
        p: an array, left foot phase
    
    Returns:
        start_move: an array, indexes when 'foot in the air' phase begins for 
        left foot
        end_move: an array, indexes when 'foot in the air' phase ends for 
        left foot
    """
    
    start_move = []
    end_move = []
    
    for i in range(len(p)-1):
        if i == 0:
            if p[i] == phase_id.rflf_offground.value or \
            p[i] == phase_id.rf_ground.value:
                start_move.append(i)
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
            
    if len(start_move) != len(end_move):
        end_move.append(start_move[-1])
        
    if len(start_move) == len(end_move):
        logger.info('Lengths of start move and end move are not equal! LF-phase')
                        
    return start_move, end_move
 
   
def _bound_det_rf(p):
    """
    Determine starting and ending points of movement phase for right foot
    
    Args:
        p: an array, right foot phase
    
    Returns:
        start_move: an array, indexes when 'foot in the air' phase begins for 
        right foot
        end_move: an array, indexes when 'foot in the air' phase ends for 
        right foot
    """
    
    start_move = []
    end_move = []
    
    for i in range(len(p)-1):
        if i == 0:
            if p[i] == phase_id.rflf_offground.value or \
            p[i] == phase_id.lf_ground.value:
                start_move.append(i)
        elif p[i] == phase_id.rflf_ground.value and \
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
            
    if len(start_move) != len(end_move):
        end_move.append(start_move[-1])
        
    if len(start_move) == len(end_move):
        logger.info('Lengths of start move and end move are not equal! RF-phase')
            
    return start_move, end_move
 
   
def _impact_detect(start_move, end_move, az, hz):
    """
    Detect when impact occurs.
    
    Args:
        start_move: an array, indexes when 'foot in the air' phase begins for 
        left/right foot
        end_move: an array, indexes when 'foot in the air' phase ends for 
        left/right foot
        az: an array, vertical acceleration of left/right foot
        hz: an int, sampling rate of sensor
        
    Returns:
        imp: 2d array,indexes of impact phase for left/right foot
    """
    
    g = 9.80665  # acceleration due to gravity (constant)
    neg_thresh = -g/2  # negative threshold 
    pos_thresh = g  # positive threshold 
    win = int(0.05*hz)  # sampling window
    end_imp_thresh = int(0.500*hz)
    acc = 0
    start_imp = []
    end_imp = []
    
    for i,j in zip(start_move, end_move):
        arr_len = []
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
                        start_imp_ind = i+k+np.argmin(acc[k:k+l])
                        end_imp_ind = start_imp_ind + win
                        if j-end_imp_ind <= end_imp_thresh:
                            start_imp.append(start_imp_ind)
                            end_imp.append(j)
                        else:
                            start_imp.append(start_imp_ind)
                            end_imp.append(end_imp_ind)
    
    imp = [[i,j] for i,j in zip(start_imp, end_imp)]
            
    return np.array(imp)    
    
    
def _final_phases(rf_ph, lf_ph):
    """
    Determine the final phases of right and left feet.
    
    Args:
        rf_ph: a list, right foot phase
        lf_ph: a list, left foot phase
        
    Returns:
        lf_ph: a list, left foot final phase
        rf_ph: a list, right foot final phase
    """
    
    if len(rf_ph) != len(lf_ph):
        logger.warning("Rf phase and lf phase array lengths are different!")
    else:
        for i in enumerate(rf_ph):
            if rf_ph[i[0]] == phase_id.rf_imp.value and \
            lf_ph[i[0]] == phase_id.rflf_offground.value:
                lf_ph[i[0]] = phase_id.rf_ground.value
            elif lf_ph[i[0]] == phase_id.lf_imp.value and \
            rf_ph[i[0]] == phase_id.rflf_offground.value:
                rf_ph[i[0]] = phase_id.lf_ground.value
                
    return lf_ph, rf_ph
    
    
def _detect_start_end_imp_phase(lph, rph):
    '''
    Detect impact phase for left and right foot.
    
    Args:
        lph = array, left foot phase
        rph = array, right foot phase
        
    Returns:
        lf_imp_start_stop: array, marker when impact phase for left foot
        starts and ends
        rf_imp_start_stop: array, marker when impact phase for right foot
        starts and ends
    '''
    
    # start and end indices of impact phase for left and right foot
    rf_range_imp = _zero_runs(col_dat=rph, imp_value=phase_id.rf_imp.value)
    lf_range_imp = _zero_runs(col_dat=lph, imp_value=phase_id.lf_imp.value)
    
    # declaring variable to store the start and end of impact phase
    lf_imp_start_stop = np.zeros(len(lph))*False
    rf_imp_start_stop = np.zeros(len(rph))*False
    
    # assigning True when an impact phase appears
    for i in range(len(lf_range_imp)):
        lf_imp_start_stop[lf_range_imp[i, 0]:lf_range_imp[i, 1]] = True
    for j in range(len(rf_range_imp)):
        rf_imp_start_stop[rf_range_imp[j, 0]:rf_range_imp[j, 1]] = True
    
    return lf_imp_start_stop.reshape(-1, 1), rf_imp_start_stop.reshape(-1, 1),\
            lf_range_imp, rf_range_imp

    
def _zero_runs(col_dat, imp_value):
    """
    Determine the start and end of each impact.
    
    Args:
        col_dat: array, right/left foot phase
        imp_value: int, indicator for right/left foot impact phase
    Returns:
        ranges: 2d array, start and end of each impact for right/left foot
    """

    # determine where column data is NaN
    isnan = np.array(np.array(col_dat==imp_value).astype(int)).reshape(-1, 1)
    
    if isnan[0] == 1:
        t_b = 1
    else:
        t_b = 0

    # mark where column data changes to and from NaN
    absdiff = np.abs(np.ediff1d(isnan, to_begin=t_b))
    if isnan[-1] == 1:
        absdiff = np.concatenate([absdiff, [1]], 0)
    del isnan  # not used in further computations

    # determine the number of consecutive NaNs
    ranges = np.where(absdiff == 1)[0].reshape((-1, 2))

    return ranges

    
if __name__ == "__main__":
    
    import matplotlib.pyplot as plt
    import time
    
    file_name = '250to125_Ivonna_Combined_Sensor_Transformed_Data.csv'
    
#    datapath = '/Users/ankurmanikandan/Documents/BioMetrix/data files/Datasets/' + file_name
#    datapath = '/Users/ankurmanikandan/Documents/BioMetrix/data files/Datasets/250to125/' + file_name
#    file_name = 'movement_data_ankur_IV_combined.csv'
#    datapath = '/Users/ankurmanikandan/Documents/BioMetrix/data files/12132016/Calibration/' + file_name

    data = np.genfromtxt(file_name, names=True, delimiter=',', dtype=float)
            
    sampl_rate = 125
    
    start_time = time.time()
    lf_phase, rf_phase = combine_phase(laccz = data['LaZ'], 
                                       raccz = data['RaZ'], 
                                       hz = sampl_rate)
#    lf_phase = _phase_detect(data['LaZ'], sampl_rate)
    print time.time() - start_time
        
    #Plotting
    
#    plt.figure(1)
#    plt.title('with Phases: Left foot')
#    plt.plot(lf_phase)
#    plt.plot(data['LaZ'])
#    plt.show()
#    
#    plt.figure(2)
#    plt.title('with Phases: Right foot')
#    plt.plot(rf_phase)
#    plt.plot(data['RaZ'])
#    plt.show()
