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
#        print ind, 'index'
#        print np.where(epoch_time_subset - \
#        epoch_time_subset[0] == MS_WIN_SIZE)[0], 'np.where'
        subset_data = data[ind:ind + np.where(epoch_time_subset - \
        epoch_time_subset[0] <= MS_WIN_SIZE)[0][-1]]
        return subset_data
   
   
                            