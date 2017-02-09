# -*- coding: utf-8 -*-
"""
Created on Mon Nov 21 10:05:14 2016

@author: Gautam
"""

import numpy as np
from hypothesis import given, example
import hypothesis.strategies as st
from hypothesis.extra.numpy import arrays

import quatOps as qo

@given(arrays(np.float, length, elements=st.floats(min_value=-np.pi,max_value=np.pi)),
       arrays(np.float, length, elements=st.floats(min_value=-np.pi,max_value=np.pi)),
       arrays(np.float, length, elements=st.floats(min_value=-np.pi,max_value=np.pi)), st.just(0))
@example(np.zeros(length), np.zeros(length), np.zeros(length),1)
@example(np.zeros(length), np.zeros(length), np.random.random(length) , 2)
@example(np.zeros(length), np.random.random(length), np.zeros(length) , 3)
@example(np.random.random(length), np.zeros(length), np.zeros(length) , 4)
def test_quat_prod(q1, q2, example):
    """Property and unit testing for controlScore
    Args:
        q1: quaternions of shape (n,4) or (1,4)
        q2: quaternion to be multiplied by of shape (n,4) or (1,4) i.e. same
            length as q1 or a single quaternion.
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
    prod = qo.quat_prod(q1, q2)
    assert prod.shape == q1.shape
    assert qo.quat_prod(q1, q2) == qo.quat_prod(q2, q1)
    assert prod.shape[1] == 4
    assert qo.quat_prod(q1, qo.quat_conj(q1)) == np.array([[1,0,0,0]])
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