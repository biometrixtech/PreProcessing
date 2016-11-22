# -*- coding: utf-8 -*-
"""
Created on Tue Nov 22 09:18:04 2016

@author: Gautam
"""

import numpy as np
from hypothesis import given, example, assume
import hypothesis.strategies as st
from hypothesis.extra.numpy import arrays

import baseCalibration as bc
import quatOps as qo




length = 5
@given(arrays(np.float, (length, 4), st.floats(min_value = -1000, max_value = 1000)),
       arrays(np.float, (length, 4), st.floats(min_value = -1000, max_value = 1000)),
       st.just(0))
@example(np.array([[1, 0, 0, 0]]*5),np.array([[1, 0, 0, 0]]*5), 1)
def test_baseCalibration(hip_data, feet_data, is_example):
    """Property and unit testing for quat_prod
    Args:
        hip_data: array of quaternions for hip
        foot_data: array of quaternions for foot
        is_example: indicator for examples, auto generated values are always 0
    Tests included:
        --_special_hip_calib
            -output hip_pitch_transform is of shape (4,1)
            -hip_roll_transform is of shape (4,1)
            -with example (unit_quaternion, unit_quaternion, unit_quaternion)
                -hip_aif == hip_bf_transform (broadcasted into app. shape)
                -hip_bf_transform == quat_prod(rot_y, rot_x)
                   where rot_y is rotation of 90 about y
                   rot x is rotation of -90 about x
        --_special_foot_calib
    """
    assume(all(np.linalg.norm(hip_data, axis=1) > .1))
    assume(all(np.linalg.norm(feet_data, axis=1) > .1))
    assume(np.linalg.norm(feet_data > 0.1))
    ## _sensor_to_aif
    hip_pitch_transform, hip_roll_transform = bc._special_hip_calib(hip_data)
    assert hip_pitch_transform.shape == (4, 1)
    assert hip_roll_transform.shape == (4, 1)
#    print hip_aif[0, :]
    
#    if is_example == 1:
#        rot_y = np.array([0.707106781186548,0,0.707106781186548,0])[np.newaxis, :]
#        rot_x = np.array([0.707106781186548,0.707106781186548,0,0])[np.newaxis, :]
#        # FOR NEW SENSORS: 90 deg about y axis, -90 deg about x axis
#        hip_asf_transform = qo.quat_prod(rot_y,rot_x).reshape(-1,1)
#        assert np.allclose(hip_bf_transform, hip_asf_transform, atol=1e-10)
#        assert np.allclose(hip_aif, hip_bf_transform.reshape(1,-1))
    
    ## _feet_transform_calculations
#    print foot_data[0, :]
#    print hip_aif
    
#    lf_bf_transform,lf_yaw_transform,lf_pitch_transform =\
#            ac._feet_transform_calculations(foot_data, hip_aif, foot_roll_transform)
#    assert lf_bf_transform.shape == (4,1)
    
if __name__ == '__main__' :

    test_baseCalibration()