# -*- coding: utf-8 -*-
"""
Created on Thu Nov 10 16:39:22 2016

@author: court
"""

from hypothesis import given, assume, example
import hypothesis.strategies as st
import random
from hypothesis.extra.numpy import arrays
import numpy as np
import itertools

import prePreProcessing as ppp
#from errors import ErrorID


"""
PrePreProcessing Property Testing
"""

#def _generate_epoch_times(j, dup_ind==False):
#    epoch_times = np.zeros(j)
#    for i in range(len(epoch_times)+1):
#        epoch_times[i] = random.randint(100,10**13-1)
#        if i>0:
#            assume (epoch_times[i] > epoch_times[i-1])
#            if dup_ind == True:
#                dup_ind = random.randrange(1,i+2)-1
#                epoch_times[dup_ind] = epoch_times[dup_ind-1]
##                print epoch_times
#    return epoch_times.reshape(-1,1)

##length = random.randint(0, )
@given(st.integers(0,25), st.booleans())
def test__computation_imaginary_quat(i_quat_len, qw_calc):

    for i in range(i_quat_len):
        i_quat = arrays(np.int16, (i,1), elements=st.floats(min_value=-32767,
                  max_value=32767)).example()
        comp_i_quat = ppp._computation_imaginary_quat(i_quat, qw_calc)
        assert len(comp_i_quat) == len(i_quat)
        assert type(comp_i_quat) == np.ndarray
        for i in range(len(i_quat)):
            assert comp_i_quat[i] >= -1
            assert comp_i_quat[i] <= 1
            if qw_calc == True:
                assert comp_i_quat[i] >= 0
            else:
                pass

#    print "input array length: ", i_quat_len
#
@given(st.integers(1,25))
def test_calc_quaternions(quat_array_len):

    assume (quat_array_len != 0)
    for i in range(1,quat_array_len+1):
        quat_array = arrays(np.float, (i,3), elements=st.floats(min_value=-1,
                            max_value=1)).example()
#        print quat_array.shape
        assume (np.sqrt(quat_array[i-1,0]**2+quat_array[i-1,1]**2+quat_array[i-1,2]**2) <=1)
        quat_result, conversion_error = ppp.calc_quaternions(quat_array)
#        print len(quat_result), i
        assert len(quat_result) == i
        assert type(quat_result) == np.ndarray
        assert conversion_error == False
        for i in range(len(quat_result)):
            assert np.sqrt(quat_result[i,0]**2+quat_result[i,1]**2
            +quat_result[i,2]**2+quat_result[i,3]**2) <=1

#@given(st.integers(0,25))
#def test_convert_epochtime_datetime_mselapsed(epoch_time_len):
#    for i in range(epoch_time_len):
#        epoch_time = arrays(np.int16, (i,1))
#        for j in range(epoch_time):
#            assume (len(str(epoch_time[j])==13)
#        time_stamp, ms_elapsed = ppp.convert_epochtime_datetime_mselapsed(epoch_time)

#@given(st.integers(1,8), st.booleans())
#def test_check_duplicate_epochtime(epoch_time_len, duplicates):
#
#    epoch_time = _generate_epoch_times(epoch_time_len, duplicates)
#    print epoch_time_len
#    epoch_time_duplicate = ppp.check_duplicate_epochtime(epoch_time)
#    assert type(epoch_time_duplicate) == bool
#    print epoch_time
#    print epoch_time_duplicate, duplicates
##    assume (epoch_time != np.zeros(epoch_time_len))
#    assert epoch_time_duplicate == duplicates

@given(arrays(np.float, 100, elements=st.floats(min_value=0,max_value=1000)), st.booleans(), st.booleans())
@example(np.array([[0],[np.nan],[9],[3], [3], [5],[3], [5],[3], [5]]), True, False)
@example(np.array([[0],[np.nan],[np.nan],[3],[5],[3], [5],[3], [5]]), True, False)
@example(np.array([[0],[np.nan],[np.nan],[np.nan],[8],[8],[np.nan],[5],[3], [5],[3], [5]]), True, False)
@example(np.array([[0],[np.nan],[np.nan],[np.nan],[np.nan],[8],[np.nan],[5],[3], [5],[3], [5]]), True, False)

def test_handling_missing_data(array, intent_blank, corrup_magn_bool):
    """
    test corrupt magn error is triggered when there's a 1
    test no NaNs in data after correction of intentional blanks
    test output data is proper length
    test output data is proper type (data_col = ndarray, error_id = int)
    test error id is correct
    
    """
    col_len = len(array)
    array[np.random.randint(0,col_len,int(np.random.random()*col_len*.3))] = np.nan
    epoch_time = np.zeros(col_len)
#    for i in range(col_len):
#        epoch_time[i] = 1111111111111+(30000*i)
    epoch_time = np.array(range(col_len))
#    print epoch_time
#    col_data = arrays(np.float, (col_len,1), elements=st.floats(min_value=0,
#                            max_value=1000)).example()
    corrupt_magn = np.zeros(col_len)
    if corrup_magn_bool:
        corrupt_val = random.randint(0,col_len-1)
        corrupt_magn[corrupt_val] = 1
    else:
        pass
#    ppp._zero_runs(col_dat)
    too_many_nan = False
    check_nan = np.isnan(array)
    if any(check_nan):
        nan_counts = [ sum( 1 for _ in group ) for key, group in itertools.groupby(check_nan) if key]
#        print nan_counts
        max_nan_counts = max(nan_counts)
        too_many_nan =  max_nan_counts > 3
    
    corrupt_magn = corrupt_magn.reshape(-1,1)

    calc_col_data, error_id = ppp.handling_missing_data(epoch_time, array, corrupt_magn)

    assert len(calc_col_data) == col_len
    assert type(calc_col_data) == np.ndarray
    assert type(error_id) == np.int
    if corrup_magn_bool:
        assert error_id == 1
    elif intent_blank and not too_many_nan:
        assert any(np.isnan(calc_col_data)) == False
        assert error_id == 0
    elif too_many_nan:
        assert any(np.isnan(calc_col_data)) == True
        assert error_id == 10


if __name__ == '__main__' :

#    test__computation_imaginary_quat()
#    print "_computation_imaginary_quat() passed"
#    test_calc_quaternions()
#    print "calc_quaternions() passed"
#    test_check_duplicate_epochtime()
#    print "check_duplicate_epochtime() passed"
    test_handling_missing_data()
#    print "ALL TESTS SUCCESSFUL"