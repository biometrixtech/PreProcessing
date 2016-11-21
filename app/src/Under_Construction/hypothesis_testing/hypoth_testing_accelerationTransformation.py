# -*- coding: utf-8 -*-
"""
Created on Mon Nov 21 09:05:12 2016

@author: Gautam
"""

import numpy as np
from hypothesis import given, example, assume
import hypothesis.strategies as st
from hypothesis.extra.numpy import arrays

import accelerationTransformation as at

length = 5
@given(arrays(np.float, (length, 12), elements = st.floats(allow_nan = False, allow_infinity = False)),
       arrays(np.float, (length, 9), elements = st.floats(allow_nan = False, allow_infinity = False)),
       arrays(np.float, (length, 9), elements = st.floats(allow_nan = False, allow_infinity = False)),
       st.just(0))
@example(np.array([[1.,0,0,0]*3]*length), np.array([[0,0,1.]*3]*length),
         np.array([[np.pi/2,0,0]*3]*length), 1)
def test_acceleration_transform(data, acc, euler, is_example):
    """Property and unit testing for controlScore
    Args:
        data: quaternion values for left, hip and right respcetively
        acc: acceleration values for left, hip and right respectively
        euler: body frames in terms of euler angles
        is_example: indicator for examples, auto generated values are always 0
    Tests included:
        -Output data is same as input data
    """
    hip_quat = data[:, 4:8]
    assume(not (hip_quat == 0).all())
    lf_quat = data[:, 0:4]
    assume(not (lf_quat == 0).all())
    rf_quat = data[:, 8:]
    assume(not (rf_quat == 0).all())
    hip_acc = acc[:, 3:6]
    lf_acc = acc[:, 0:3]
    rf_acc = acc[:, 6:]
    hip_bf_eul = euler[:, 3:6]
    lf_bf_eul = euler[:, 0:3]
    rf_bf_eul = euler[:, 6:]
    hip_aif_acc, lf_aif_acc, rf_aif_acc=\
            at.acceleration_transform(hip_quat, lf_quat, rf_quat, hip_acc,
                                      lf_acc, rf_acc, hip_bf_eul, lf_bf_eul,
                                      rf_bf_eul)
    assert hip_aif_acc.shape == hip_acc.shape
    assert lf_aif_acc.shape == lf_acc.shape
    assert rf_aif_acc.shape == rf_acc.shape

if __name__ == '__main__' :

    test_acceleration_transform()
#    print "ALL TESTS SUCCESSFUL"