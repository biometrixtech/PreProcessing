# -*- coding: utf-8 -*-
"""
Created on Mon Nov 21 10:05:14 2016

@author: Gautam
"""

import numpy as np
from hypothesis import given, example, assume
import hypothesis.strategies as st
from hypothesis.extra.numpy import arrays

import quatOps as qo


length = 5
@given(arrays(np.float, (length, 4),
              elements=st.floats(min_value=-np.pi, max_value=np.pi)),
       arrays(np.float, (length, 4),
              elements=st.floats(min_value=-np.pi, max_value=np.pi)),
       st.just(0))
@example(np.ones(4).reshape(1, -1),
         np.array([[np.cos(np.deg2rad(45)), np.sin(np.deg2rad(45)),0,0]]),
         1)
def test_quatOps(q1, q2, example):
    """Property and unit testing for quat_prod
    Args:
        q1: quaternions of shape (n,4) or (1,4)
        q2: quaternion to be multiplied by of shape (n,4) or (1,4) i.e. same
            length as q1 or a single quaternion.
        example: indicator for examples, auto generated values are always 0
    Tests included:
        --quat_prod
            -Output data is same type and shape as q1
            -Product of a quaternion with its conjugate is unit quaternion
            -Multiplying by unit quaternion returns input
        --quat_norm
            -Output data is same type and shape as q1
            -Magnitude of all quaternions is 1 after normalizing
        --find_rot
            -Output data is same type and shape as q1
            -Rotation between self is [1,0,0,0]
            -Rotation between q1 and -q1 os [-1,0,0,0]
            -Rotation between [1,0,0,0] and q1 is quat_norm(q1)
        --quat_conj
            -Output data is same type and shape as q1
            -quat_conj(quat_cont(q1)) is quat_norm(q1)
        --vect_rot
            -Output data is same type and shape as v
            -Rotating by unit vector returns v
            -Rotating 4 times about x-axis returns v
    Tests with Example:
        -(array([[1,1,1,1]]), array([[ 0.70710678,  0.70710678, 0., 0.]]), 1)
            --Rotating 4 times about x-axis returns -q1
            --Rotating 8 times about x-axis returns q1
    """
    assume(not (q1 == 0).all())
    assume(not (q2 == 0).all())
    assume(all(np.linalg.norm(q1, axis=1) > 0.1))
    assume(all(np.linalg.norm(q2, axis=1) > 0.1))
    
    ## quat_prod
    assert type(qo.quat_prod(q1, q2)) == type(q1)
    assert qo.quat_prod(q1, q2).shape == q1.shape
    assert np.allclose(qo.quat_prod(qo.quat_norm(q1), qo.quat_conj(q1)),
                       np.array([[1, 0, 0, 0]]), atol=1e-10)
    q_unit = np.array([[1, 0, 0, 0]])
    assert np.allclose(q1, qo.quat_prod(q1, q_unit))
    if example == 1:
        p1 = qo.quat_prod(q1, q2)
        p2 = qo.quat_prod(p1, q2)
        p3 = qo.quat_prod(p2, q2)
        p4 = qo.quat_prod(p3, q2)
        assert np.allclose(p4, -q1, atol=1e-10)
        p5 = qo.quat_prod(p4, q2)
        p6 = qo.quat_prod(p5, q2)
        p7 = qo.quat_prod(p6, q2)
        p8 = qo.quat_prod(p7, q2)
        assert np.allclose(p8, q1, atol=1e-10)
    
    ## quat_norm
    assert type(qo.quat_norm(q1)) == type(q1)
    assert qo.quat_norm(q1).shape == q1.shape
    assert np.allclose(np.linalg.norm(qo.quat_norm(q1), axis=1), 1)
    
    ## find_rot
    assert type(qo.find_rot(q1, q2)) == type(q1)
    assert qo.find_rot(q1, q2).shape == q1.shape 
    assert np.allclose(qo.find_rot(q1,q1), np.array([[1, 0, 0, 0]]))
    assert np.allclose(qo.find_rot(q1,-q1), np.array([[-1, 0, 0, 0]]))
    assert np.allclose(qo.find_rot(np.array([[1, 0, 0, 0]]*len(q1)), q1),
                       qo.quat_norm(q1))

    ## quat_conj
    assert type(qo.quat_conj(q1)) == type(q1)
    assert qo.quat_conj(q1).shape == q1.shape
    assert np.allclose(qo.quat_conj(qo.quat_conj(q1)),
                       qo.quat_norm(q1), atol=1e-10)
    
    ## vect_rot
    v = q1[:,0:3]
    q_unit = np.array([[1, 0, 0, 0]]*len(v))
    assert type(qo.vect_rot(v,q1)) == type(v)
    assert qo.vect_rot(v, q1).shape == v.shape
    assert np.allclose(qo.vect_rot(v, q_unit), v, atol=1e-10)
    q_45_x = np.array([[np.cos(np.deg2rad(45)),
                        np.sin(np.deg2rad(45)), 0, 0]]*len(v))
    v1 = qo.vect_rot(v, q_45_x)
    v2 = qo.vect_rot(v1, q_45_x)
    v3 = qo.vect_rot(v2, q_45_x)
    v4 = qo.vect_rot(v3, q_45_x)
    assert np.allclose(v4, v, atol=1e-10)

if __name__ == '__main__' :
    test_quatOps()
    print "ALL TESTS SUCCESSFUL"