# -*- coding: utf-8 -*-
"""
Created on Mon Nov 21 17:11:40 2016

@author: Gautam
"""

import numpy as np
from hypothesis import given, example, assume
import hypothesis.strategies as st
from hypothesis.extra.numpy import arrays

import anatomicalCalibration as ac
import quatOps as qo




length = 5
@given(arrays(np.float, (length, 4), elements=st.floats(min_value=-np.pi,
              max_value=np.pi)),
       arrays(np.float, (length, 4), elements=st.floats(min_value=-np.pi,
              max_value=np.pi)),
       arrays(np.float, (4, 1), elements=st.floats(min_value=-np.pi,
              max_value=np.pi)),
       arrays(np.float, (4, 1), elements=st.floats(min_value=-np.pi,
              max_value=np.pi)),
       arrays(np.float, (4, 1), elements=st.floats(min_value=-np.pi,
              max_value=np.pi)),
       st.just(0))
@example(np.array([[1, 0, 0, 0]]*5), np.array([[1, 0, 0, 0]]*5),
         np.array([1, 0, 0, 0]).reshape(-1, 1),
         np.array([1, 0, 0, 0]).reshape(-1, 1),
         np.array([1, 0, 0, 0]).reshape(-1, 1), 1)
def test_anatomicalCalibration(hip_data, foot_data, hip_pitch_transform,
                               hip_roll_transform, foot_roll_transform,
                               is_example):
    """Property and unit testing for quat_prod
    Args:
        hip_data: array of quaternions for hip
        foot_data: array of quaternions for foot
        hip_pitch_transform: hip_pitch transform shape(4,1)
        hip_roll_transform: hip_roll_transform_values shape(4,1)
        is_example: indicator for examples, auto generated values are always 0
    Tests included:
        --_sensor_to_aif
            -output hip_aif is numpu ndarrat of same shape as hip_data
            -body_frame transform result is of shape (4,1)
            -with example (unit_quaternions, unit_quaternions, unit_quaternions
                            unit_quaternions, unit_quaternions)
                -hip_aif == hip_bf_transform (broadcasted into app. shape)
                -hip_bf_transform == quat_prod(rot_y, rot_x)
                   where rot_y is rotation of 90 about y
                   rot x is rotation of -90 about x
        --_feet_transform_calculations
            - lf_bf_transform is numpy ndarray of shape (4, 1)
            - lf_yaw_transform is numpy ndarray of shape (4, 1)
            - lf_pitch_transform is numpy ndarray of shape (4, 1)
    """
    assume(not (hip_data == 0).all())
    assume(all(np.linalg.norm(hip_data, axis=1) > .1))
    assume(not (foot_data == 0).all())
    assume(all(np.linalg.norm(foot_data, axis=1) > .1))
    assume(not (hip_pitch_transform == 0).all())
    assume(np.linalg.norm(hip_pitch_transform) > 0.1)
    assume(not (hip_roll_transform == 0).all())
    assume(np.linalg.norm(hip_roll_transform) > 0.1)
    assume(not (foot_roll_transform == 0).all())
    assume(np.linalg.norm(foot_roll_transform) > 0.1)
    ## _sensor_to_aif
    hip_aif, hip_bf_transform = ac._sensor_to_aif(hip_data, hip_pitch_transform,
                                                  hip_roll_transform)
    assert type(hip_aif) == np.ndarray
    assert hip_aif.shape == hip_data.shape
    assert type(hip_bf_transform) == np.ndarray
    assert hip_bf_transform.shape == (4, 1)
    
    if is_example == 1:
        rot_y = np.array([np.sqrt(.5), 0, np.sqrt(.5), 0])[np.newaxis, :]
        rot_x = np.array([np.sqrt(.5), np.sqrt(.5), 0, 0])[np.newaxis, :]
        # FOR NEW SENSORS: 90 deg about y axis, -90 deg about x axis
        hip_asf_transform = qo.quat_prod(rot_y,rot_x).reshape(-1, 1)
        assert np.allclose(hip_bf_transform, hip_asf_transform, atol=1e-10)
        assert np.allclose(hip_aif, hip_bf_transform.reshape(1, -1))
    ## _feet_transform_calculations    
    lf_bf_transform, lf_yaw_transform, lf_pitch_transform =\
            ac._feet_transform_calculations(foot_data, hip_aif,
                                            foot_roll_transform)
    assert type(lf_bf_transform) == np.ndarray
    assert lf_bf_transform.shape == (4, 1)
    assert type(lf_yaw_transform) == np.ndarray
    assert lf_yaw_transform.shape == (4, 1)
    assert type(lf_pitch_transform) == np.ndarray
    assert lf_pitch_transform.shape == (4, 1)


if __name__ == '__main__' :
    test_anatomicalCalibration()