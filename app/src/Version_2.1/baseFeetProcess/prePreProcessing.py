# -*- coding: utf-8 -*-
"""
Created on Tue Oct 11 16:30:36 2016

@author: ankurmanikandan
"""

import numpy as np
from scipy import interpolate

from errors import ErrorId


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


def calc_quaternions(quat_array):

    """Calculating the real quaternion.

    Args:
        quat_array: an array of the quaternions from the sensor data, qX,
        qY, qZ.

    Returns:
        An array of real and imaginary quaternions, qW, qX, qY, qZ.

    """

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

    # check if NaN exists in the real quaternion array
    if np.any(np.isnan(q_w)):
        raise ValueError('Real quaternion cannot be comupted. Cannot \
        take square root of a negative number.')

    # appending the real and imaginary quaternions arrays to a single array
    all_quaternions = np.hstack([q_w, q_i, q_j, q_k])

    return all_quaternions


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
    abs_diff = np.abs(np.ediff1d(isnan, to_begin=t_b))
    if isnan[-1] == 1:
        abs_diff = np.concatenate([abs_diff, [1]], 0)

    # determine the number of consecutive NaNs
    ranges = np.where(abs_diff == 1)[0].reshape((-1, 2))

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

    # threshold for acceptable number of consecutive missing values
    MISSING_DATA_THRESH = 3

    # where magnetometer corrupt, return 'Fail' notification to user
    if 1 in corrup_magn:
        return col_data, ErrorId.corrupt_magn.value

    # where magnetometer not corrupt, correct for missing values
    else:
        ran = _zero_runs(col_data.reshape(-1,))

        # if missing data, check if it is enough to cross error threshold
        if ran.shape[0] != 0:

            # if missing data crosses threshold, return with error
            if np.any(ran[:, 1].reshape(-1, 1)-ran[:, 0].reshape(-1, 1) \
                > MISSING_DATA_THRESH):

                return col_data, ErrorId.missing.value

            # if missing data below threshold, impute
            elif np.any(ran[:, 1].reshape(-1, 1) - ran[:, 0].reshape(-1, 1) \
                <= MISSING_DATA_THRESH):

                epoch_time = epoch_time.reshape((-1, 1))
                col_data = col_data.reshape((-1, 1))
                dummy_data = col_data[np.isfinite(col_data).reshape((-1,))]
                dummy_epochtime = epoch_time[
                    np.isfinite(col_data).reshape((-1,))]
                dummy_epochtime = dummy_epochtime.reshape((-1, 1))
                interp = interpolate.splrep(dummy_epochtime,
                                            dummy_data,
                                            k=3,
                                            s=0)  # spline interpolation function

                for i in range(len(ran)):
                    y_new = interpolate.splev(epoch_time[ran[i, 0]:ran[i, 1],
                                                         0], interp, der=0)
                    col_data[ran[i, 0]:ran[i, 1], 0] = y_new
                return col_data.reshape((-1, )), ErrorId.no_error.value

        # if no missing data, return values
        else:
            return col_data, ErrorId.no_error.value


#if __name__ == "__main__":
#
#    import pandas as pd
#
#    data = pd.read_csv('team1_session1_trainingset_anatomicalCalibration.csv')
#    data.columns = data.columns.str.replace('Timestamp', 'epochtime')
##    df.columns = df.columns.str.replace('$','')
##    data = np.genfromtxt(data_path, delimiter =',', dtype = float,
##    names = True)
##    new_data = data.as_matrix()
##    new_data1 = data.values
##    lq_xyz = data[:,4:7]
##    print data.shape
#    # DETERMINE THE REAL PART OF THE QUATERNIONS
#
#    # Left foot
#    lq_xyz = np.array(data.ix[:, ['LqX', 'LqY', 'LqZ']])
#    lq_wxyz = calc_quaternions(lq_xyz)
##    lq_wxyz = lq_wxyz.reshape(-1,4)
#    print lq_wxyz[0]
#    data.insert(4, 'LqW', lq_wxyz[:, 0], allow_duplicates=False)  # adding the
#    # real quaternion to the data table
#    data['LqX'] = pd.Series(lq_wxyz[:, 1])  # adding the re calculated qX
#    data['LqY'] = pd.Series(lq_wxyz[:, 2])  # adding the re calculated qY
#    data['LqZ'] = pd.Series(lq_wxyz[:, 3])  # adding the re calculated qZ
###    # Hip
#    hq_xyz = np.array(data.ix[:, ['HqX', 'HqY', 'HqZ']])
#    hq_wxyz = calc_quaternions(hq_xyz)
#    data.insert(11, 'HqW', hq_wxyz[:, 0], allow_duplicates=False)  # adding the
#    # real quaternion to the data table
#    data['HqX'] = pd.Series(hq_wxyz[:, 1])  # adding the re calculated qX
#    data['HqY'] = pd.Series(hq_wxyz[:, 2])  # adding the re calculated qY
#    data['HqZ'] = pd.Series(hq_wxyz[:, 3])  # adding the re calculated qZ
##    #Right foot
#    rq_xyz = np.array(data.ix[:, ['RqX', 'RqY', 'RqZ']])
#    rq_wxyz = calc_quaternions(rq_xyz)
#    data.insert(18, 'RqW', rq_wxyz[:, 0], allow_duplicates=False)  # adding the
#    # real quaternion to the data table
#    data['RqX'] = pd.Series(rq_wxyz[:, 1])  # adding the re calculated qX
#    data['RqY'] = pd.Series(rq_wxyz[:, 2])  # adding the re calculated qY
#    data['RqZ'] = pd.Series(rq_wxyz[:, 3])  # adding the re calculated qZ
#
#    #CONVERT EPOCHTIME TO DATETIME WITH MILLISECOND RESOLUTION AND DETERMINE
#    #TIME ELAPSED IN MILLISECONDS (INT)
#    dummy_time_stamp = []
##    for i in range(data.shape[0]):
##        dummy_time_stamp.append(datetime.datetime.fromtimestamp(
##         np.array(data['epoch_time'].ix[i])).strftime('%Y-%m-%d %H:%M:%S.%f'))
##    e_time, time_elapsed = convert_epochtime_datetime_mselapsed(data['epochtime'])
##    data.insert(0, 'timestamp', e_time, allow_duplicates=False)  # adding the
#    # datetime column to the data table
##    data.insert(2, 'msElapsed', time_elapsed, allow_duplicates=False)
#    # adding the time elapsed column to the data table
#
#    data.to_csv('new_Subject4_Sensor_Data.csv', index=False)
