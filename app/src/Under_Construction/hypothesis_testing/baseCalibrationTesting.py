# -*- coding: utf-8 -*-
"""
Created on Tue Nov 22 09:18:04 2016

@author: Gautam
"""

import numpy as np
from hypothesis import given, assume
import hypothesis.strategies as st
from hypothesis.extra.numpy import arrays

import baseCalibration as bc


length = 10
@given(arrays(np.float, (length, 4),
              st.floats(min_value = -2000, max_value = 2000)),
       arrays(np.float, (length, 4),
              st.floats(min_value = -2000, max_value = 2000)),
       st.just(0))
def test_baseCalibration(hip_data, feet_data, is_example):
    """Property and unit testing for quat_prod
    Args:
        hip_data: array of quaternions for hip
        feet_data: array of quaternions for foot
        is_example: indicator for examples, auto generated values are always 0
    Tests included:
        --_special_hip_calib
            -output hip_pitch_transform is numpy ndarray of shape (4,1)
            -hip_roll_transform is numpy ndarray of shape (4,1)
        --_special_foot_calib
           - foot_roll_transform is numpy ndarray of shape (4,1)
    """
    assume(all(np.linalg.norm(hip_data, axis=1) > .1))
    assume(all(np.linalg.norm(feet_data, axis=1) > .1))

    ## _sensor_to_aif
    hip_pitch_transform, hip_roll_transform = bc._special_hip_calib(hip_data)
    assert type(hip_pitch_transform) == np.ndarray
    assert hip_pitch_transform.shape == (4, 1)
    assert type(hip_roll_transform) == np.ndarray
    assert hip_roll_transform.shape == (4, 1)
    
    ## _special_foot_calib
    foot_roll_transform = bc._special_foot_calib(feet_data, hip_data,
                                                 hip_pitch_transform)
    assert type(foot_roll_transform) == np.ndarray
    assert foot_roll_transform.shape == (4, 1)


if __name__ == '__main__' :
    test_baseCalibration()