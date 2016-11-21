# -*- coding: utf-8 -*-
"""
Created on Mon Nov 21 09:05:12 2016

@author: Gautam
"""

import numpy as np
from hypothesis import given, example
import hypothesis.strategies as st
from hypothesis.extra.numpy import arrays

from controlScore import control_score

length = 50
@given(arrays(np.float, length, elements=st.floats(min_value=-np.pi,max_value=np.pi)),
       arrays(np.float, length, elements=st.floats(min_value=-np.pi,max_value=np.pi)),
       arrays(np.float, length, elements=st.floats(min_value=-np.pi,max_value=np.pi)), st.just(0))
@example(np.zeros(length), np.zeros(length), np.zeros(length),1)
@example(np.zeros(length), np.zeros(length), np.random.random(length) , 2)
@example(np.zeros(length), np.random.random(length), np.zeros(length) , 3)
@example(np.random.random(length), np.zeros(length), np.zeros(length) , 4)
def test_acceleration_transform(hip_data,lf_data,rf_data,hip_acc,lf_acc,rf_acc,
                                hip_bf_eul,lf_bf_eul,rf_bf_eul):
    """Property and unit testing for controlScore
    Args:
        LeX: Euler X for left ankle
        HeX: Euler X for hip
        ReX: Euler X for right ankle
        example: indicator for examples, auto generated values are always 0
    Tests included:
        -Output data is same as input data
        -Output data is ndarray of size (n,1)
    Tests with Example:
        -args(np.zeros(length), np.zeros(length), np.zeros(length),1)
            --All non-nan scores in all control scores are 100
        -args(np.zeros(length), np.zeros(length), np.random.random(length),2)
            --All non-nan scores are 100 for control_lf, hip_control
            --Assert control_rf == control == ankle_control
        -@args(np.zeros(length), np.random.random(length), np.zeros(length) , 3)
            --All non-nan scores are 100 for control_lf, control_rf and ankle
            --For hip_control, control there are values other than 100
        -@args(np.random.random(length), np.zeros(length), np.zeros(length) , 4)
            --All non-nan scores are 100 for control_rf, hip_control
            --For control_lf, control, ankle_control there are values other than 100  
    """
    ms_elapsed = np.array([4]*len(LeX)).reshape(-1, 1)
    LeX = LeX.reshape(-1, 1)
    HeX = HeX.reshape(-1, 1)
    ReX = ReX.reshape(-1, 1)
    control, hip_control, ankle_control, control_lf,control_rf = control_score(LeX, HeX, ReX, ms_elapsed)

    assert control.shape == LeX.shape
    assert type(control) == np.ndarray
    if example == 1:
        assert all(control[np.isfinite(control)] == 100)
        assert all(hip_control[np.isfinite(hip_control)] == 100)
        assert all(ankle_control[np.isfinite(ankle_control)] == 100)
        assert all(control_lf[np.isfinite(control_lf)] == 100)
        assert all(control_rf[np.isfinite(control_rf)] == 100)
    elif example == 2:
        assert any(control[np.isfinite(control)] != 100)
        assert all(hip_control[np.isfinite(hip_control)] == 100)
        assert any(ankle_control[np.isfinite(ankle_control)] != 100)
        assert all(control_lf[np.isfinite(control_lf)] == 100)
        assert any(control_rf[np.isfinite(control_rf)] != 100)
        print "control_rf", control_rf
    elif example == 3:
        assert any(control[np.isfinite(control)] != 100)
        assert any(hip_control[np.isfinite(hip_control)] != 100)
        assert all(ankle_control[np.isfinite(ankle_control)] == 100)
        assert all(control_lf[np.isfinite(control_lf)] == 100)
        assert all(control_rf[np.isfinite(control_rf)] == 100)
    elif example == 4:
        assert any(control[np.isfinite(control)] != 100)
        assert all(hip_control[np.isfinite(hip_control)] == 100)
        assert any(ankle_control[np.isfinite(ankle_control)] != 100)
        assert any(control_lf[np.isfinite(control_lf)] != 100)
        assert all(control_rf[np.isfinite(control_rf)] == 100)

if __name__ == '__main__' :

#    test__computation_imaginary_quat()
#    print "_computation_imaginary_quat() passed"
#    test_calc_quaternions()
#    print "calc_quaternions() passed"
#    test_check_duplicate_epochtime()
#    print "check_duplicate_epochtime() passed"
    test_control_score()
#    print "ALL TESTS SUCCESSFUL"