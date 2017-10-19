# -*- coding: utf-8 -*-
"""
Created on Wed Oct 26 12:23:48 2016

@author: ankurmanikandan
"""

import datetime
import logging

import numpy as np

logger = logging.getLogger()


def subset_data(old_data):
    '''
    Subset data when missing type is equal to 2 (done)

    Args:
        old_data: structured array, input data to Data wrangling

    Returns:
        new_data: structured array, subset the input data when missing type=2 
    '''

    # SUBSET DATA
    # enumerated value for done in missing type column
    done = 2

    old_data = old_data[old_data['corrupt_lf'] != done]
    old_data = old_data[old_data['corrupt_lf'] != done]
    new_data = old_data[old_data['corrupt_lf'] != done]

    del old_data  # no use, after assiging it to a new variable

    return new_data


def check_duplicate_epochtime(epoch_time):
    """
    Check if there are duplicate epoch times in the sensor data file.

    Args:
        epoch_time: an array, epoch time from the sensor.

    Returns:
        epoch_time_duplicate: Boolean, if duplicate epoch time exists or not

    """

    # check if there are any duplicate epoch times in the sensor data file
    epoch_time_duplicate = False
    epoch_time_unique, epoch_time_unique_ind = np.unique(epoch_time,
                                                         return_counts=True)
                                                         
    del epoch_time_unique  # not used in further computations

    if np.any(epoch_time_unique_ind>1):
        epoch_time_duplicate = True
        return epoch_time_duplicate
    else:
        return epoch_time_duplicate

        

def convert_epochtime_datetime_mselapsed(epoch_time):

    """
    Converting epochtime from the sensor data to datetime and milli
    seconds elapsed.

    Args:
        epoch_time: epochtime from the sensor data.

    Returns:
        two arrays.
        dummy_time_stamp: date time
        dummy_time_elapsed: milliseconds elapsed
    """

    dummy_time_stamp = []

    dummy_time_elapsed = np.ediff1d(epoch_time, to_begin=0)
    for i in enumerate(epoch_time):
        dummy_time_stamp.append(datetime.datetime.fromtimestamp(np.array(
            epoch_time[i[0]]/1000.)).strftime('%Y-%m-%d %H:%M:%S.%f'))

    return np.array(dummy_time_stamp).reshape(-1, 1), \
    np.array(dummy_time_elapsed).reshape(-1, 1)

