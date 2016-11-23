# -*- coding: utf-8 -*-
"""
Created on Mon Nov 21 09:05:12 2016

@author: Gautam
"""

import numpy as np
from hypothesis import given, example, assume
import hypothesis.strategies as st
from hypothesis.extra.numpy import arrays
import random as rand

import accelerationTransformation as at

length = 5
@given(arrays(np.float, (length, 12), elements = st.floats(allow_nan = False, allow_infinity = False)),
       arrays(np.float, (length, 9), elements = st.floats(allow_nan = False, allow_infinity = False)),
       arrays(np.float, (length, 9), elements = st.floats(allow_nan = False, allow_infinity = False)),
       st.just(0))
@example(np.array([[1.,0,0,0]*3]*length), np.array([[0,0,1000.]*3]*length),
         np.array([[0,0,0]*3]*length), 1)
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

    # acceleration magnitude tests
        # gravity is correctly subtracted from z axis in aif, result is in m/s2
    a,b,c = at.acceleration_transform(np.array([[1, 0, 0, 0]]), \
                                     np.array([[1, 0, 0, 0]]), \
                                     np.array([[1, 0, 0, 0]]), \
                                     np.array([[0, 0, 1000]]), \
                                     np.array([[0, 0, 5000]]), \
                                     np.array([[1000, 0, 0]]), \
                                     np.array([[0, 0, 0]]), \
                                     np.array([[0, 0, 0]]), \
                                     np.array([[0, 0, 0]]))
    assert (a == 0).all() and np.array_equal(b, np.array([[0, 0, 39.2266]])) \
        == True and np.array_equal(c, np.array([[9.80665, 0, -9.80665]])) \
        == True
    # rotation tests
        # test that d) matched quat and euler yaw offsets cancel,
            # e) erroneous bf roll and pitch offsets ignored for acc calcs,
            # f) small error in bf yaw offsets still lands us close to perfect
    d,e,f = at.acceleration_transform(np.array([[np.cos(np.pi/4), 0, 0, \
                                     np.sin(np.pi/4)]]), \
                                     np.array([[1, 0, 0, 0]]), \
                                     np.array([[np.cos(np.pi/4), \
                                     np.cos(np.pi/4), 0, 0]]), \
                                     np.array([[0, 0, 1000]]), \
                                     np.array([[0, 0, 1000]]), \
                                     np.array([[0, 0, 1000]]), \
                                     np.array([[0, 0, np.sin(np.pi/4)]]), \
                                     np.array([[rand.randint(-1000,1000), \
                                     rand.randint(-1000,1000), 0]]), \
                                     np.array([[-1.57079633, -0.,  0.0005]]))
    assert (d == 0).all() and (e == 0).all() and np.allclose(f, np.array([[0, \
        -9.80665, -9.80665]]),rtol=1, atol=1e-02, equal_nan=True)
    

if __name__ == '__main__' :

    test_acceleration_transform()
#    print "ALL TESTS SUCCESSFUL"