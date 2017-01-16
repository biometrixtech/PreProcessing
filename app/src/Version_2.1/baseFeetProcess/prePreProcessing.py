# -*- coding: utf-8 -*-
"""
Created on Tue Oct 11 16:30:36 2016

@author: ankurmanikandan
"""

import numpy as np
from scipy import interpolate
import pandas as pd

from errors import ErrorId


def check_duplicate_index(index):
    """
    Check if there are duplicate indexes in the sensor data file.
    
    Args:
        index: array, index.
        
    Returns:
        index_duplicate: Boolean, if duplicate index exists or not
    """
    # check if there are any duplicate epoch times in the sensor data file
    index_duplicate = False
    index_unique_ind = np.unique(index, return_counts=True)[1]
    if 2 in index_unique_ind:
        index_duplicate = True
        return index_duplicate
    else:
        return index_duplicate
        
        
def subset_data(old_data, subset_value, missing_or_corrupt='missing'):
    '''
    Subset data
    
    Args:
        old_data: structured array, input data to Data wrangling
        subset_value: an int, enumerated value for corrupt/missing type
        missing_or_corrupt: string, indicates whether subsetting by
        missing/corrupt type
        
    Returns:
        new_data: structured array, subset the input data when missing type=2 
    '''
        
    df_old_data = pd.DataFrame(old_data)  # convert structured array to 
    # data frame
    if 'm' in missing_or_corrupt:
        df_old_data = df_old_data.drop(df_old_data[
        df_old_data.missing_type == subset_value].index) # subset data
        new_data = df_old_data.to_records(index=False)  # convert data frame back
        # to structured array
    else:
        df_old_data = df_old_data.drop(df_old_data[
        df_old_data.corrupt_magn == subset_value].index) # subset data
        new_data = df_old_data.to_records(index=False)  # convert data frame back
        # to structured array
    
    return new_data


def calc_quaternions(quat_array, missing_type):

    """Calculating the real quaternion.

    Args:
        quat_array: an array of the quaternions from the sensor data, qX,
        qY, qZ.
        missing_type: array, indicator for type of missing value

    Returns:
        all_quaternions: An array of real and imaginary quaternions,
        qW, qX, qY, qZ.
        conversion_error: Boolean, error in type conversion of quaternions.
    """

    # assume no error, correct later if necessary
    conversion_error = False

    # determine the imaginary quaternions
    q_i = _computation_imaginary_quat(quat_array[:, 0], False)  # imaginary
                                                                # quaternion
    q_j = _computation_imaginary_quat(quat_array[:, 1], False)  # imaginary
                                                                # quaternion
    q_k = _computation_imaginary_quat(quat_array[:, 2], False)  # imaginary
                                                                # quaternion
    
    # determine the real quaternion
    qi_calc_qw = _computation_imaginary_quat(quat_array[:, 0])
    # imaginary quaternion
    qj_calc_qw = _computation_imaginary_quat(quat_array[:, 1])
    # imaginary quaternion
    qk_calc_qw = _computation_imaginary_quat(quat_array[:, 2])
    # imaginary quaternion
    q_w = np.sqrt(1 - qi_calc_qw - qj_calc_qw - qk_calc_qw)  # real
                                                            # quaternion
    
    # define constant, enumerated value for unintentional value
    unintentional_missing_type = 1

    # check if NaN exists in the real quaternion array
    if np.any(np.isnan(q_w[missing_type != unintentional_missing_type])):
        conversion_error = True

    # appending the real and imaginary quaternions arrays to a single array
    all_quaternions = np.hstack([q_w, q_i, q_j, q_k])
    
    return all_quaternions, conversion_error


def _computation_imaginary_quat(i_quat, check_qw=True):

    """
    Compute the imaginary quaternions to implement in the computation to
    determine the real quaternion.

    Args:
        i_quat: an array, imaginary quaternion
        check_qw: boolean variable to check if the function is used to
        calculate the real quaternion

    Returns:
        if check_qw == True:
            comp_i_quat: an array, computed imaginary quaternion to help
            determine the real quaternion
        else:
            comp_i_quat: an array, computed imaginary quaternion to scale
            it back
    """

    if check_qw:  # check if function is used to calculate real quaternion
        comp_i_quat = (i_quat/32767.0)**2
        return comp_i_quat.reshape(-1, 1)
    else:  # function is used to calculate imaginary quaternion
        comp_i_quat = i_quat/32767.0
        return comp_i_quat.reshape(-1, 1)


def handling_missing_data(index, col_data, corrup_magn, missing_type):

    """
    Checking for missing data. Imputing the values if the number of
    consecutive
    missing values is less than the threshold.

    Args:
        index: array, index
        col_data: an array, each column data from the data file
        corrup_magn: an array, binary values indicating if the
        magnetometer is corrupted or not
        missing_type: array, enumerated values indicating if blank is 
        intentional or unintentional
        
    Returns:
        col_data: an array, column data either with imputed values or data
        as in the data file
        ErrorId.missing.value: an int, if missing data is greater
        than the threshold
        ErrorId.no_error.value: an int, no missing data
        ErrorId.corrupt_magn.value: an int, corrupted data becuase of the
        magnetometer
       
    """

    # threshold for acceptable number of consecutive missing values
    MISSING_DATA_THRESH = 3
    
    # enumerated values of missing type column 
    intentional_missing_data = 1  # indicate unitentional missing data 

    # where magnetometer corrupt, return 'Fail' notification to user
    if 1 in corrup_magn:
        return col_data, ErrorId.corrupt_magn.value

    # where magnetometer not corrupt, correct for missing values
    else:
        ran = _zero_runs(col_data.reshape(-1,), missing_type, 
                         intentional_missing_data)

        # if missing data, check if it is enough to cross error threshold
        if ran.shape[0] != 0:
            index = index.reshape((-1, 1))
            col_data = col_data.reshape((-1, 1))
            non_nan_index = np.isfinite(col_data).reshape(-1,)
            dummy_data = col_data[non_nan_index]
            dummy_index = index[non_nan_index]
            dummy_index = dummy_index.reshape((-1, 1))
            interp = interpolate.splrep(dummy_index,
                                        dummy_data,
                                        k=3,
                                        s=0)  # spline interpolation function

            for i in range(len(ran)):
                if ran[i, 1]-ran[i, 0] <= MISSING_DATA_THRESH:
                    y_new = interpolate.splev(index[ran[i, 0]:ran[i, 1],
                                                         0], interp, der=0)
                    col_data[ran[i, 0]:ran[i, 1], 0] = y_new
            return col_data.reshape((-1, )), ErrorId.no_error.value

        # if no missing data, return values
        else:
            return col_data, ErrorId.no_error.value
            
            
def _zero_runs(col_dat, miss_type, intentional_missing_data):

    """
    Determining the number of consecutive nan's.

    Args:
        col_dat: column data as a numpy array.
        miss_type: array, enumerated values indicating if blank is 
        intentional or unintentional
        intentional_missing_data: int, enumerated value to indicate
        intentioal blank

    Returns:
        ranges: 2D numpy array. 1st column is the starting position of the
        first nan.
        2nd column is the end position + 1 of the last consecutive nan.

    """

    # determine where column data is NaN
    isnan = np.array(np.isnan(col_dat).astype(int)).reshape(-1, 1)
    isnan = isnan[miss_type != intentional_missing_data]  # subsetting for when
    # missing value is not an intentional blank
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
#
#    data = pd.read_csv('Subject4_rawData.csv')
#    data.columns = data.columns.str.replace('Timestamp', 'epochtime')
##    df.columns = df.columns.str.replace('$','')
##    data = np.genfromtxt(data_path, delimiter =',', dtype = float,
##    names = True)
##    new_data = data.as_matrix()
##    new_data1 = data.values
##    lq_xyz = data[:,4:7]
#
#    # DETERMINE THE REAL PART OF THE QUATERNIONS
#
#    # Left foot
#    lq_xyz = np.array(data.ix[:,['LqX','LqY','LqZ']])
#    lq_wxyz = calc_quaternions(lq_xyz)
#    data.insert(4, 'LqW', lq_wxyz[:,0], allow_duplicates=False)  # adding the
#    # real quaternion to the data table
#    data['LqX'] = pd.Series(lq_wxyz[:,1])  # adding the re calculated qX
#    data['LqY'] = pd.Series(lq_wxyz[:,2])  # adding the re calculated qY
#    data['LqZ'] = pd.Series(lq_wxyz[:,3])  # adding the re calculated qZ
###    # Hip
#    hq_xyz = np.array(data.ix[:,['HqX','HqY','HqZ']])
#    hq_wxyz = calc_quaternions(hq_xyz)
#    data.insert(11, 'HqW', hq_wxyz[:,0], allow_duplicates=False)  # adding the
#    # real quaternion to the data table
#    data['HqX'] = pd.Series(hq_wxyz[:,1])  # adding the re calculated qX
#    data['HqY'] = pd.Series(hq_wxyz[:,2])  # adding the re calculated qY
#    data['HqZ'] = pd.Series(hq_wxyz[:,3])  # adding the re calculated qZ
##    #Right foot
#    rq_xyz = np.array(data.ix[:,['RqX','RqY','RqZ']])
#    rq_wxyz = calc_quaternions(rq_xyz)
#    data.insert(18, 'RqW', rq_wxyz[:,0], allow_duplicates=False)  # adding the
#    # real quaternion to the data table
#    data['RqX'] = pd.Series(rq_wxyz[:,1])  # adding the re calculated qX
#    data['RqY'] = pd.Series(rq_wxyz[:,2])  # adding the re calculated qY
#    data['RqZ'] = pd.Series(rq_wxyz[:,3])  # adding the re calculated qZ
##
#    #CONVERT EPOCHTIME TO DATETIME WITH MILLISECOND RESOLUTION AND DETERMINE
#    #TIME ELAPSED IN MILLISECONDS (INT)
#    dummy_time_stamp = []
##    for i in range(data.shape[0]):
##        dummy_time_stamp.append(datetime.datetime.fromtimestamp(
##         np.array(data['epoch_time'].ix[i])).strftime('%Y-%m-%d %H:%M:%S.%f'))
#    e_time, time_elapsed = convert_epochtime_datetime_mselapsed(
#                                                    data['epochtime'])
#    data.insert(0, 'timestamp', e_time, allow_duplicates=False)  # adding the
#    # datetime column to the data table
#    data.insert(2, 'msElapsed', time_elapsed, allow_duplicates=False)
#    # adding the time elapsed column to the data table
#
#    data.to_csv('new_Subject4_Sensor_Data.csv', index=False)
