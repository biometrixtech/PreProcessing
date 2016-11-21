# -*- coding: utf-8 -*-
"""
Created on Wed Nov 16 13:17:16 2016

@author: ankurmanikandan
"""

import numpy as np


def handle_dynamic_sampling(data, epoch_time_subset, MS_WIN_SIZE, ind):
    """
    Handle dynamic sampling rates. 
   
    Args:
        data: an array, data from which window size data packets need to 
        be returned
        epoch_time_subset: an array, a subset of epoch time from the sensor
        MS_WIN_SIZE: int, size of sampling window in milliseconds
        nmsec_jump: int, number of milliseconds to jump the sampling window by
       
    Returns:
        subset_data: an array, a subset of the data coming in, size equals
        that of the sampling window
       
    """
   
    # determine the smallest sampling window size
    LOWEST_HZ = 100
    len_thresh_epoch_time = int(MS_WIN_SIZE/1000.0 * LOWEST_HZ)
   
    # obtain data equivalent to sampling window size
    if len(epoch_time_subset) < len_thresh_epoch_time:
        subset_data = data[ind:]
        return subset_data
    else:
        subset_data = data[ind:ind + np.where(epoch_time_subset - \
        epoch_time_subset[0] <= MS_WIN_SIZE)[0][-1]]
        return subset_data
       

def handle_dynamic_sampling_create_features(data, epoch_time_subset, 
                                            MS_WIN_SIZE, ind):
    """
    Handle dynamic sampling rates. This function is specfically designed for
    IAD and IED.
   
    Args:
        data: an array, data from which window size data packets need to 
        be returned
        epoch_time_subset: an array, a subset of epoch time from the sensor
        MS_WIN_SIZE: int, size of sampling window in milliseconds
        nmsec_jump: int, number of milliseconds to jump the sampling window by
       
    Returns:
        subset_data: an array, a subset of the data coming in, size equals
        that of the sampling window
        avg_hz: an int, mean of the sampling rate in a window
       
    """
   
    # determine the smallest sampling window size
    LOWEST_HZ = 100
    len_thresh_epoch_time = int(MS_WIN_SIZE/1000.0 * LOWEST_HZ)
   
    # obtain data equivalent to sampling window size
    if len(epoch_time_subset) < len_thresh_epoch_time:
        subset_data = data[ind:]
        return subset_data
    else:
        subset_data = data[ind:ind + np.where(epoch_time_subset - \
        epoch_time_subset[0] <= MS_WIN_SIZE)[0][-1]]
       
        epoch_time_win = epoch_time_subset[ind:ind + np.where(
            epoch_time_subset - epoch_time_subset[0] <= MS_WIN_SIZE)[0][-1]]
         
        avg_hz = avg_sampl_rate_win(epoch_time_win)

        return subset_data, avg_hz


def avg_sampl_rate_win(epoch_time_subset):
    """
    Determine avergae sampling rate in a given window.
    
    Args:
        epoch_time_subset: an array, a subset of the epoch time 
        
    Returns:
        avg_hz: an int, mean of sampling rate in a window
    """
   
    dummy_time_elapsed = np.ediff1d(epoch_time_subset, to_begin=0)
       
    hz = [int(1000/dummy_time_elapsed[1])]
   
    for i in dummy_time_elapsed[1:]:
        hz.append(int(1000/i))
     
    avg_hz = int(np.mean(hz))

    return avg_hz 
                           