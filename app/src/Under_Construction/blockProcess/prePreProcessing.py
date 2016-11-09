# -*- coding: utf-8 -*-
"""
Created on Wed Oct 26 12:23:48 2016

@author: ankurmanikandan
"""

import numpy as np
import datetime
from scipy import interpolate


def _computation_imaginary_quat(i_quat):
    """
    Compute the imaginary quaternions to implement in the computation to
    determine the real quaternion.
    
    Args: 
        i_quat: imaginary quaternion
        
    Returns:
        comp_i_quat: computed imaginary quaternion to help determine the 
        real quaternion
    """
    comp_i_quat = (i_quat/32767.0)**2
    
    return comp_i_quat
    
    
def calc_quaternions(q):
    
    """Calculating the real quaternion.
 
    Args:
        q: an array of the quaternions from the sensor data, qX, qY, qZ.
 
    Returns:
        An array of real and imaginary quaternions, qW, qX, qY, qZ.
 
    """
        
    # determine the real and imaginary quaternions and the magnitude
    qi = _computation_imaginary_quat(q[:,0])  # imaginary quaternion
    qj = _computation_imaginary_quat(q[:,1])  # imaginary quaternion
    qk = _computation_imaginary_quat(q[:,2])  # imaginary quaternion
    qw =  np.sqrt(1 - qi - qj - qk)  # real quaternion
    
    # check if NaN exists in the real quaternion array
    if np.any(np.isnan(qw)):
        raise ValueError('Real quaternion cannot be comupted. Cannot \
        take square root of a negative number.')
    
    all_quaternions = np.hstack([qw, qi, qj, qk])  # appending the real
    # and imaginary quaternions arrays to a single array
            
    return np.array(all_quaternions)
 
   
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
    
    dummy_time_elapsed = np.ediff1d(epoch_time, to_begin = 0)        
    for i in range(len(epoch_time)):
        dummy_time_stamp.append(datetime.datetime.fromtimestamp(np.array(
        epoch_time[i]/1000.)).strftime('%Y-%m-%d %H:%M:%S.%f'))   
        
    return np.array(dummy_time_stamp).reshape(-1,1), \
    np.array(dummy_time_elapsed).reshape(-1,1)
   
   
def _zero_runs (a):
    
    """
    Determining the number of consecutive nan's.
    
    Args:
        a - column data as a numpy array.
        
    Returns:
        ranges - 2D numpy array. 1st column is the starting position of the 
        first nan.
        2nd column is the end position + 1 of the last consecutive nan.
        
    """
    
    isnan = np.isnan(a).astype(int)
    if isnan[0]==1:
        tb = 1
    else:
        tb = 0
    absdiff = np.abs(np.ediff1d(isnan,to_begin=tb))
    if isnan[-1]==1:
        absdiff = np.concatenate([absdiff, [1]], 0)
    ranges = np.where(absdiff == 1)[0].reshape((-1,2))        
    
    return ranges

    
def handling_missing_data(obj_data):
    
    """Checking for missing data. Imputing the values if the number of 
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
    
    # Initializing values
    MISSING_DATA_THRESH = 3  # threshold for acceptable number of consecutive 
    # missing values
    missing_data_indicator_L = np.array(['N']*len(obj_data.LaX))  # numpy array to 
    # check for missing data in the left foot sensor
    missing_data_indicator_H = np.array(['N']*len(obj_data.LaX))  # numpy array to 
    # check for missing data in the hip sensor
    missing_data_indicator_R = np.array(['N']*len(obj_data.LaX))  # numpy array to 
    # check for missing data in the right foot sensor

    # Checking if the number of consecutive missing values for the left foot 
    # sensor data is greater than the threshold
    r_L = _zero_runs(obj_data.LaX)
    if r_L.shape[0] != 0:
        for i in range(len(r_L[np.where(r_L[:,1]-r_L[:,0] \
        > MISSING_DATA_THRESH)[0],1])):
            missing_data_indicator_L[r_L[np.where(r_L[:,1]-r_L[:,0] \
            > MISSING_DATA_THRESH)[0][i],0]:r_L[np.where(r_L[:,1]-r_L[:,0] \
            > MISSING_DATA_THRESH)[0][i],1]] = 'L'  # adding 'L' if the 
            # threshold is surpassed
    
    # Checking if the number of consecutive missing values for the hip sensor 
    # data is greater than the threshold
    r_H = _zero_runs(obj_data.HaX)
    if r_H.shape[0] != 0:
        for i in range(len(r_H[np.where(r_H[:,1]-r_H[:,0] \
        > MISSING_DATA_THRESH)[0],1])):
            missing_data_indicator_H[r_H[np.where(r_H[:,1]-r_H[:,0] \
            > MISSING_DATA_THRESH)[0][i],0]:r_H[np.where(r_H[:,1]-r_H[:,0] \
            > MISSING_DATA_THRESH)[0][i],1]] = 'H'  # adding 'H' if the 
            # threshold is surpassed

    # Checking if the number of consecutive missing values for the right foot 
    # sensor data is greater than the threshold
    r_R = _zero_runs(obj_data.RaX)
    if r_R.shape[0] != 0:
        for i in range(len(r_R[np.where(r_R[:,1]-r_R[:,0] \
        > MISSING_DATA_THRESH)[0],1])):
            missing_data_indicator_R[r_R[np.where(r_R[:,1]-r_R[:,0] \
            > MISSING_DATA_THRESH)[0][i],0]:r_R[np.where(r_R[:,1]-r_R[:,0] \
            > MISSING_DATA_THRESH)[0][i],1]] = 'R'  # adding 'R' if the 
            # threshold is surpassed

    # all columns from the sensor data
    var = ['LaX', 'LaY', 'LaZ', 'LqX', 'LqY', 'LqZ',
           'HaX', 'HaY', 'HaZ', 'HqX', 'HqY', 'HqZ',
           'RaX', 'RaY', 'RaZ', 'RqX', 'RqY', 'RqZ']
    
    # Imputing the values if the number of consecutive missing values is less 
    # than the threshold       
    epoch_time = obj_data.epoch_time
    for i in var:
        col_data = getattr(obj_data, i)
        r = _zero_runs(col_data.reshape(-1,))
        dummy_data = col_data[np.isfinite(col_data).reshape((-1,))]
        dummy_epochtime = epoch_time[np.isfinite(col_data).reshape((-1,))]
        f = interpolate.splrep(dummy_epochtime, dummy_data, k=3, s=0)  
        # spline interpolation function
        if r.shape[0] != 0:
            for j in range(len(r)):
                if r[j,1] - r[j,0] <= MISSING_DATA_THRESH:
                    ynew = interpolate.splev(epoch_time[r[j,0]:r[j,1]], 
                                             f, 
                                             der=0)  # Imputing missing values
                    col_data[r[j,0]:r[j,1]] = ynew
        setattr(obj_data, i, col_data)
    
    # Creating the missing data indicator column
    missing_data_indicator = []
    for i in range(len(missing_data_indicator_L)):
        if missing_data_indicator_L[i] == 'N' \
        and missing_data_indicator_H[i] == 'N' \
        and missing_data_indicator_R[i] == 'N':
            missing_data_indicator.append('N')
        elif missing_data_indicator_L[i] == 'L' \
        and missing_data_indicator_H[i] == 'N' \
        and missing_data_indicator_R[i] == 'N':
            missing_data_indicator.append('L')
        elif missing_data_indicator_L[i] == 'N' \
        and missing_data_indicator_H[i] == 'H' \
        and missing_data_indicator_R[i] == 'N':
            missing_data_indicator.append('H')
        elif missing_data_indicator_L[i] == 'N' \
        and missing_data_indicator_H[i] == 'N' \
        and missing_data_indicator_R[i] == 'R':
            missing_data_indicator.append('R')
        elif missing_data_indicator_L[i] == 'L' \
        and missing_data_indicator_H[i] == 'H' \
        and missing_data_indicator_R[i] == 'N':
            missing_data_indicator.append('LH')
        elif missing_data_indicator_L[i] == 'N' \
        and missing_data_indicator_H[i] == 'H' \
        and missing_data_indicator_R[i] == 'R':
            missing_data_indicator.append('HR')
        elif missing_data_indicator_L[i] == 'L' \
        and missing_data_indicator_H[i] == 'N' \
        and missing_data_indicator_R[i] == 'R':
            missing_data_indicator.append('LR')
        elif missing_data_indicator_L[i] == 'L' \
        and missing_data_indicator_H[i] == 'H' \
        and missing_data_indicator_R[i] == 'R':
            missing_data_indicator.append('LHR')
    
    # Adding the final missing data indicator column to the data object        
    obj_data.missing_data_indicator = np.array(missing_data_indicator)

    return obj_data

    
if __name__ == "__main__":
    
    import pandas as pd
    import sys
    
    datapath = 'prePreProcessing_qa_testing.csv'
    data = np.genfromtxt(datapath, delimiter=',', names=True, dtype=float)
    object_data = data.view(np.recarray)
    checked_data = handling_missing_data(object_data)
    
    df = pd.DataFrame()
    df['epoch_time'] = pd.Series(checked_data.epoch_time)
    df['LaX'] = pd.Series(checked_data.LaX)
    df['LaY'] = pd.Series(checked_data.LaY)
    df['LaZ'] = pd.Series(checked_data.LaZ)
    df['LqX'] = pd.Series(checked_data.LqX)
    df['LqY'] = pd.Series(checked_data.LqY)
    df['LqZ'] = pd.Series(checked_data.LqZ)
    df['HaX'] = pd.Series(checked_data.HaX)
    df['HaY'] = pd.Series(checked_data.HaY)
    df['HaZ'] = pd.Series(checked_data.HaZ)
    df['HqX'] = pd.Series(checked_data.HqX)
    df['HqY'] = pd.Series(checked_data.HqY)
    df['HqZ'] = pd.Series(checked_data.HqZ)
    df['RaX'] = pd.Series(checked_data.RaX)
    df['RaY'] = pd.Series(checked_data.RaY)
    df['RaZ'] = pd.Series(checked_data.RaZ)
    df['RqX'] = pd.Series(checked_data.RqX)
    df['RqY'] = pd.Series(checked_data.RqY)
    df['RqZ'] = pd.Series(checked_data.RqZ)
    df['missing_indicator'] = pd.Series(checked_data.missing_data_indicator)
    
    df.to_csv('checked_prePreProcessing_qa_testing.csv', index=False)
    