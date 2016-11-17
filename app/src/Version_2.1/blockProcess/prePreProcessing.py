# -*- coding: utf-8 -*-
"""
Created on Wed Oct 26 12:23:48 2016

@author: ankurmanikandan
"""

import datetime
import logging

import numpy as np
from scipy import interpolate

logger = logging.getLogger()


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
    if 2 in epoch_time_unique_ind:
        epoch_time_duplicate = True
        return epoch_time_duplicate
    else:
        return epoch_time_duplicate                                                           
        
        
def calc_quaternions(quat_array, indicator_col, corrupt_magn):

    """Calculating the real quaternion.

    Args:
        quat_array: an array of the quaternions from the sensor data, qX,
        qY, qZ.
        indicator_col: an array, values indicate missing data. 
        corrupt_magn: an array, binary values indicating data is 
        corrupted due to uncalibrated magnetometer.

    Returns:
        all_quaternions: An array of real and imaginary quaternions, 
        qW, qX, qY, qZ.
        corrupt_type: an array, indicator for corrupted data

    """

    # determine the imaginary quaternions
    q_i = _computation_imaginary_quat(quat_array[:, 0], False)  # imaginary 
                                                                # quaternion
    q_j = _computation_imaginary_quat(quat_array[:, 1], False)  # imaginary 
                                                                # quaternion
    q_k = _computation_imaginary_quat(quat_array[:, 2], False)  # imaginary 
                                                                # quaternion
    
    # determine the real quaternion
    qi_calc_qw = _computation_imaginary_quat(quat_array[:, 0])  # imaginary 
                                                                # quaternion
    qj_calc_qw = _computation_imaginary_quat(quat_array[:, 1])  # imaginary 
                                                                # quaternion
    qk_calc_qw = _computation_imaginary_quat(quat_array[:, 2])  # imaginary 
                                                                # quaternion
    q_w = np.sqrt(1 - qi_calc_qw - qj_calc_qw - qk_calc_qw)  # real quaternion

    # check if NaN exists in the real quaternion array
    indicator_col = indicator_col.reshape(-1,)
    if len(indicator_col) == len(corrupt_magn) == len(q_w):
        corrupt_type = [2 if np.isnan(q_w[i]) and indicator_col[i] == 'N' else\
        corrupt_magn[i] for i in range(len(q_w))]
    else:
        logger.warning('Error when creating corrupt type column.')
#    if 'N' in indicator_col[np.where(np.isnan(q_w))[0]]:
#        raise ValueError('Real quaternion cannot be comupted. Cannot \
#        take square root of a negative number.')

    # appending the real and imaginary quaternions arrays to a single array
    all_quaternions = np.hstack([q_w, q_i, q_j, q_k])

    return all_quaternions, corrupt_type
    
    
def _computation_imaginary_quat(i_quat, check_qw=True):

    """
    Compute the imaginary quaternions to implement in the computation to
    determine the real quaternion.

    Args:
        i_quat: imaginary quaternion
        check_qw: boolean variable to check if the function is used to 
        calculate the real quaternion

    Returns:
        if check_qw == True:
            comp_i_quat: computed imaginary quaternion to help determine the
            real quaternion
        else:
            comp_i_quat: computed imaginary quaternion to scale it back
    """

    if check_qw:  # check if function is used to calculate real quaternion
        comp_i_quat = (i_quat/32767.0)**2
        return comp_i_quat.reshape(-1, 1)
    else:  # function is used to calculate imaginary quaternion
        comp_i_quat = i_quat/32767.0
        return comp_i_quat.reshape(-1, 1)


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
    for i in range(len(epoch_time)):
        dummy_time_stamp.append(datetime.datetime.fromtimestamp(np.array(
            epoch_time[i]/1000.)).strftime('%Y-%m-%d %H:%M:%S.%f'))

    return np.array(dummy_time_stamp).reshape(-1, 1), \
    np.array(dummy_time_elapsed).reshape(-1, 1)


def handling_missing_data(obj_data):

    """
    Checking for missing data. Imputing the values if the number of
    consecutive
    missing values is less than the threshold.

    Args:
        obj_data - an object with the raw data from the sensor. Does not
        include the
        missing data indicator column.

    Returns:
        obj_data - an object with all the relevant data along with the missing
        data indicator column.

    """

    # INITIALIZING VALUES
    # threshold for acceptable number of consecutive missing values
    MISSING_DATA_THRESH = 3
    # arrays to check for missing data in left, hip, and right sensors
    missing_data_indicator_l = np.array(['N']*len(obj_data.LaX))
    missing_data_indicator_h = np.array(['N']*len(obj_data.LaX))
    missing_data_indicator_r = np.array(['N']*len(obj_data.LaX))

    # ADD INDICATORS FOR MISSING VALUES
    # Checking if the number of consecutive missing values for the left foot
    # sensor data is greater than the threshold
    r_l = _zero_runs(obj_data.LaX)
    if r_l.shape[0] != 0:
        for i in range(len(r_l[np.where(r_l[:, 1]-r_l[:, 0] \
        > MISSING_DATA_THRESH)[0], 1])):
            missing_data_indicator_l[r_l[np.where(r_l[:, 1]-r_l[:, 0] \
            > MISSING_DATA_THRESH)[0][i], 0]:r_l[np.where(r_l[:, 1]-r_l[:, 0] \
            > MISSING_DATA_THRESH)[0][i], 1]] = 'L'  # adding 'L' if the
            # threshold is surpassed

    # Checking if the number of consecutive missing values for the hip sensor
    # data is greater than the threshold
    r_h = _zero_runs(obj_data.HaX)
    if r_h.shape[0] != 0:
        for i in range(len(r_h[np.where(r_h[:, 1]-r_h[:, 0] \
        > MISSING_DATA_THRESH)[0], 1])):
            missing_data_indicator_h[r_h[np.where(r_h[:, 1]-r_h[:, 0] \
            > MISSING_DATA_THRESH)[0][i], 0]:r_h[np.where(r_h[:, 1]-r_h[:, 0] \
            > MISSING_DATA_THRESH)[0][i], 1]] = 'H'  # adding 'H' if the
            # threshold is surpassed

    # Checking if the number of consecutive missing values for the right foot
    # sensor data is greater than the threshold
    r_r = _zero_runs(obj_data.RaX)
    if r_r.shape[0] != 0:
        for i in range(len(r_r[np.where(r_r[:, 1]-r_r[:, 0] \
        > MISSING_DATA_THRESH)[0], 1])):
            missing_data_indicator_r[r_r[np.where(r_r[:, 1]-r_r[:, 0] \
            > MISSING_DATA_THRESH)[0][i], 0]:r_r[np.where(r_r[:, 1]-r_r[:, 0] \
            > MISSING_DATA_THRESH)[0][i], 1]] = 'R'  # adding 'R' if the
            # threshold is surpassed

    # all columns from the sensor data
    var = ['LaX', 'LaY', 'LaZ', 'LqX', 'LqY', 'LqZ',
           'HaX', 'HaY', 'HaZ', 'HqX', 'HqY', 'HqZ',
           'RaX', 'RaY', 'RaZ', 'RqX', 'RqY', 'RqZ']

    # Impute if number of consecutive missing vals is less than threshold
    epoch_time = obj_data.epoch_time
    for i in var:
        col_data = getattr(obj_data, i)
        ran = _zero_runs(col_data.reshape(-1, ))
        dummy_data = col_data[np.isfinite(col_data).reshape((-1, ))]
        dummy_epochtime = epoch_time[np.isfinite(col_data).reshape((-1, ))]
        interp = interpolate.splrep(dummy_epochtime, dummy_data, k=3, s=0)

        # spline interpolation function
        if ran.shape[0] != 0:

            for j in range(len(ran)):

                if ran[j, 1] - ran[j, 0] <= MISSING_DATA_THRESH:
                    y_new = interpolate.splev(epoch_time[ran[j, 0]:ran[j, 1]],
                                              interp,
                                              der=0)  # Imputing missing values
                    col_data[ran[j, 0]:ran[j, 1]] = y_new

        setattr(obj_data, i, col_data)

    # Creating the missing data indicator column
    missing_data_indicator = []
    for i in range(len(missing_data_indicator_l)):
        if missing_data_indicator_l[i] == 'N' \
        and missing_data_indicator_h[i] == 'N' \
        and missing_data_indicator_r[i] == 'N':
            missing_data_indicator.append('N')
        elif missing_data_indicator_l[i] == 'L' \
        and missing_data_indicator_h[i] == 'N' \
        and missing_data_indicator_r[i] == 'N':
            missing_data_indicator.append('L')
        elif missing_data_indicator_l[i] == 'N' \
        and missing_data_indicator_h[i] == 'H' \
        and missing_data_indicator_r[i] == 'N':
            missing_data_indicator.append('H')
        elif missing_data_indicator_l[i] == 'N' \
        and missing_data_indicator_h[i] == 'N' \
        and missing_data_indicator_r[i] == 'R':
            missing_data_indicator.append('R')
        elif missing_data_indicator_l[i] == 'L' \
        and missing_data_indicator_h[i] == 'H' \
        and missing_data_indicator_r[i] == 'N':
            missing_data_indicator.append('LH')
        elif missing_data_indicator_l[i] == 'N' \
        and missing_data_indicator_h[i] == 'H' \
        and missing_data_indicator_r[i] == 'R':
            missing_data_indicator.append('HR')
        elif missing_data_indicator_l[i] == 'L' \
        and missing_data_indicator_h[i] == 'N' \
        and missing_data_indicator_r[i] == 'R':
            missing_data_indicator.append('LR')
        elif missing_data_indicator_l[i] == 'L' \
        and missing_data_indicator_h[i] == 'H' \
        and missing_data_indicator_r[i] == 'R':
            missing_data_indicator.append('LHR')

    # Adding the final missing data indicator column to the data object
    obj_data.missing_data_indicator = np.array(missing_data_indicator)

    return obj_data
    
    
def _zero_runs(col_dat):

    """
    Determining the number of consecutive nan's.

    Args:
        col_dat - column data as a numpy array.

    Returns:
        ranges - 2D numpy array. 1st column is the starting position of the
        first nan.
        2nd column is the end position + 1 of the last consecutive nan.

    """

    # determine where column data is NaN
    isnan = np.isnan(col_dat).astype(int)
    if isnan[0] == 1:
        t_b = 1
    else:
        t_b = 0

    # mark where column data changes to and from NaN
    absdiff = np.abs(np.ediff1d(isnan, to_begin=t_b))
    if isnan[-1] == 1:
        absdiff = np.concatenate([absdiff, [1]], 0)

    # determine the number of consecutive NaNs
    ranges = np.where(absdiff == 1)[0].reshape((-1, 2))

    return ranges


#if __name__ == "__main__":
#
#    import pandas as pd
#    import sys
#
#    datapath = 'prePreProcessing_qa_testing.csv'
#    data = np.genfromtxt(datapath, delimiter=',', names=True, dtype=float)
#    object_data = data.view(np.recarray)
#    checked_data = handling_missing_data(object_data)
#
#    df = pd.DataFrame()
#    df['epoch_time'] = pd.Series(checked_data.epoch_time)
#    df['LaX'] = pd.Series(checked_data.LaX)
#    df['LaY'] = pd.Series(checked_data.LaY)
#    df['LaZ'] = pd.Series(checked_data.LaZ)
#    df['LqX'] = pd.Series(checked_data.LqX)
#    df['LqY'] = pd.Series(checked_data.LqY)
#    df['LqZ'] = pd.Series(checked_data.LqZ)
#    df['HaX'] = pd.Series(checked_data.HaX)
#    df['HaY'] = pd.Series(checked_data.HaY)
#    df['HaZ'] = pd.Series(checked_data.HaZ)
#    df['HqX'] = pd.Series(checked_data.HqX)
#    df['HqY'] = pd.Series(checked_data.HqY)
#    df['HqZ'] = pd.Series(checked_data.HqZ)
#    df['RaX'] = pd.Series(checked_data.RaX)
#    df['RaY'] = pd.Series(checked_data.RaY)
#    df['RaZ'] = pd.Series(checked_data.RaZ)
#    df['RqX'] = pd.Series(checked_data.RqX)
#    df['RqY'] = pd.Series(checked_data.RqY)
#    df['RqZ'] = pd.Series(checked_data.RqZ)
#    df['missing_indicator'] = pd.Series(checked_data.missing_data_indicator)
#
#    df.to_csv('checked_prePreProcessing_qa_testing.csv', index=False)
