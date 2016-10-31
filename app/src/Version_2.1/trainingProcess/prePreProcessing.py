# -*- coding: utf-8 -*-
"""
Created on Tue Oct 11 16:30:36 2016

@author: ankurmanikandan
"""

import numpy as np
import datetime
from scipy import interpolate
from errors import ErrorId


def calc_quaternions(q):
    
    """Calculating the real quaternion.
 
    Args:
        q: an array of the quaternions from the sensor data, qX, qY, qZ.
 
    Returns:
        An array of real and imaginary quaternions, qW, qX, qY, qZ.
 
    """
    all_quaternions = []
    for i in range(len(q)):
        if np.isnan(np.sqrt(1-((q[i,0]*16.0/32767)**2)
        -((q[i,1]*16.0/32767)**2)-((q[i,2]*16.0/32767)**2))):  # checking when 
        #the sqrt is not a real number.
            all_quaternions.append([0, q[i,0]*16.0/32767, q[i,1]*16.0/32767, 
                                    q[i,2]*16.0/32767])  # if the sqrt is not 
                                    #a real number then we assign 0 to qW.
        else:
            all_quaternions.append([np.sqrt(1-((q[i,0]*16.0/32767)**2)
            -((q[i,1]*16.0/32767)**2)-((q[i,2]*16.0/32767)**2)), 
            q[i,0]*16.0/32767, q[i,1]*16.0/32767, q[i,2]*16.0/32767])
            
    return np.array(all_quaternions)
    
    
def convert_epochtime_datetime_mselapsed(epoch_time):
   
   """Converting epochtime from the sensor data to datetime and milli 
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
       dummy_time_stamp.append(datetime.datetime.fromtimestamp(
       np.array(epoch_time[i]/1000.)).strftime('%Y-%m-%d %H:%M:%S.%f'))   
       
   return np.array(dummy_time_stamp).reshape(-1,1), \
   np.array(dummy_time_elapsed).reshape(-1,1)
    

def _zero_runs(a):
    
    """Determinging the number of consecutive nan's.
    
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
    abs_diff = np.abs(np.ediff1d(isnan,to_begin=tb))
    if isnan[-1]==1:
        abs_diff = np.concatenate([abs_diff, [1]], 0)
    ranges = np.where(abs_diff == 1)[0].reshape((-1,2))        
    
    return ranges
    

def handling_missing_data(epoch_time, col_data, corrup_magn):
    
    """
    Args:
        epoch_time: Timestamp integer
        col_data: data to check for missing value
        corrup_magn: indicator for corrupt magnetometer
    Returns:
        missing_ind: indocatoer boolean to indicate if missing values were
        imputed(0) or not(1)
        col_data: same as input col_data possibly with missing data imputed

    """  
    
    MISSING_DATA_THRESH = 3  # threshold for acceptable number of consecutive 
                             # missing values
    
    if 1 in corrup_magn:  # if 1 exists then return missing indiactor as 1. 
                            # 'Fail' notification to user.
        return col_data, ErrorId.corrupt_magn.value
    else:
        r = _zero_runs(col_data.reshape(-1,))
        if r.shape[0] != 0:
            if np.any(r[:,1].reshape(-1,1) - r[:,0].reshape(-1,1) \
            > MISSING_DATA_THRESH):
                return col_data, ErrorId.missing.value
            elif np.any(r[:,1].reshape(-1,1) - r[:,0].reshape(-1,1) \
            <= MISSING_DATA_THRESH):
                epoch_time = epoch_time.reshape((-1,1))
                col_data = col_data.reshape((-1,1))
                dummy_data = col_data[np.isfinite(col_data).reshape((-1,))]
                dummy_epochtime = epoch_time[
                np.isfinite(col_data).reshape((-1,))]
                dummy_epochtime = dummy_epochtime.reshape((-1,1))
                f = interpolate.splrep(dummy_epochtime, 
                                       dummy_data, 
                                       k=3, 
                                       s=0)  # spline interpolation function 
                for i in range(len(r)):
                    ynew = interpolate.splev(epoch_time[r[i,0]:r[i,1],0],
                                             f, der=0)
                    col_data[r[i,0]:r[i,1],0] = ynew
                return col_data.reshape((-1,)), ErrorId.no_error.value
        else:  # no missing values 
            return col_data, ErrorId.no_error.value
            

if __name__ == "__main__":
    
    import pandas as pd
    
    data = pd.read_csv('Subject4_rawData.csv')
    data.columns = data.columns.str.replace('Timestamp', 'epochtime')    
#    df.columns = df.columns.str.replace('$','')
#    data = np.genfromtxt(data_path, delimiter =',', dtype = float, 
#    names = True)
#    new_data = data.as_matrix()
#    new_data1 = data.values
#    lq_xyz = data[:,4:7]
    
    # DETERMINE THE REAL PART OF THE QUATERNIONS
    
    # Left foot
    lq_xyz = np.array(data.ix[:,['LqX','LqY','LqZ']])
    lq_wxyz = calc_quaternions(lq_xyz)
    data.insert(4, 'LqW', lq_wxyz[:,0], allow_duplicates=False)  # adding the 
    # real quaternion to the data table
    data['LqX'] = pd.Series(lq_wxyz[:,1])  # adding the re calculated qX
    data['LqY'] = pd.Series(lq_wxyz[:,2])  # adding the re calculated qY
    data['LqZ'] = pd.Series(lq_wxyz[:,3])  # adding the re calculated qZ
##    # Hip
    hq_xyz = np.array(data.ix[:,['HqX','HqY','HqZ']])
    hq_wxyz = calc_quaternions(hq_xyz)
    data.insert(11, 'HqW', hq_wxyz[:,0], allow_duplicates=False)  # adding the 
    # real quaternion to the data table
    data['HqX'] = pd.Series(hq_wxyz[:,1])  # adding the re calculated qX
    data['HqY'] = pd.Series(hq_wxyz[:,2])  # adding the re calculated qY
    data['HqZ'] = pd.Series(hq_wxyz[:,3])  # adding the re calculated qZ
#    #Right foot
    rq_xyz = np.array(data.ix[:,['RqX','RqY','RqZ']])
    rq_wxyz = calc_quaternions(rq_xyz)
    data.insert(18, 'RqW', rq_wxyz[:,0], allow_duplicates=False)  # adding the 
    # real quaternion to the data table
    data['RqX'] = pd.Series(rq_wxyz[:,1])  # adding the re calculated qX
    data['RqY'] = pd.Series(rq_wxyz[:,2])  # adding the re calculated qY
    data['RqZ'] = pd.Series(rq_wxyz[:,3])  # adding the re calculated qZ
#    
    #CONVERT EPOCHTIME TO DATETIME WITH MILLISECOND RESOLUTION AND DETERMINE 
    # TIME ELAPSED IN MILLISECONDS (INT)
    dummy_time_stamp = []
#    for i in range(data.shape[0]):
#        dummy_time_stamp.append(datetime.datetime.fromtimestamp(
#    np.array(data['epoch_time'].ix[i])).strftime('%Y-%m-%d %H:%M:%S.%f'))
    e_time, time_elapsed = convert_epochtime_datetime_mselapsed(
                                                        data['epochtime'])    
    data.insert(0, 'timestamp', e_time, allow_duplicates=False)  # adding the 
    # datetime column to the data table
    data.insert(2, 'msElapsed', time_elapsed, allow_duplicates=False)  
    # adding the time elapsed column to the data table
    
    data.to_csv('new_Subject4_Sensor_Data.csv', index=False)    
    
    



