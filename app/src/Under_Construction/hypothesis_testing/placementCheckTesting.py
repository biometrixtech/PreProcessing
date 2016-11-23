# -*- coding: utf-8 -*-
"""
Created on Wed Nov 23 09:24:37 2016

@author: court
"""

from hypothesis import given, assume
import hypothesis.strategies as st
from hypothesis.extra.numpy import arrays
import numpy as np
import random

import placementCheck as pc


@given(st.booleans(), st.booleans(), st.booleans())
def test_placement_check(bad_left, bad_hip, bad_right):
    length = random.randint(1, 15)
    less_200 = arrays(np.int, (length, 1), elements=st.floats(min_value=-1500,
                      max_value=200)).example()
    great_200 = arrays(np.int, (length, 1), elements=st.floats(min_value=200,
                      max_value=1500)).example()
    less_n200 = arrays(np.int, (length, 1), elements=st.floats(min_value=-1500,
                      max_value=-200)).example()
    great_n200 = arrays(np.int, (length, 1), elements=st.floats(min_value=-200,
                      max_value=1500)).example()
    less_n800 = arrays(np.int, (length, 1), elements=st.floats(min_value=-1500,
                      max_value=-800)).example()
    great_n800 = arrays(np.int, (length, 1), elements=st.floats(min_value=-800,
                      max_value=1500)).example()
    betw_200 = arrays(np.int, (length, 1), elements=st.floats(min_value=-200,
                      max_value=200)).example()

    if bad_left:
        left_acc = np.hstack((less_200, great_n200,
                    st.sampled_from([less_n200, great_200]).example()))
    else:
        left_acc = np.hstack((great_200, less_n200, betw_200))
    if bad_hip:
        hip_acc = np.hstack((st.sampled_from([less_n200,
                             great_200]).example(), great_n800,
                             st.sampled_from([less_n200,
                                              great_200]).example()))
    else:
        hip_acc = np.hstack((betw_200, less_n800, betw_200))
    if bad_right:
        right_acc = np.hstack((great_n200, great_n200,
                               st.sampled_from([less_n200,
                               great_200]).example()))
    else:
        right_acc = np.hstack((less_n200, less_n200, betw_200))
    ind = pc.placement_check(left_acc, hip_acc, right_acc)
    assert type(ind) == np.int
    assert np.in1d(ind, [0, 2, 3, 4, 5, 6, 7, 8, 9])
    if bad_left:
        assert np.in1d(ind, [2, 3, 6, 7])
    if bad_hip:
        assert np.in1d(ind, [2, 3, 4, 5])
    if bad_right:
        assert np.in1d(ind, [2, 4, 6, 8])
    good_left = np.array([[500,-500,0],[500,-500,0]])
    nan_left = np.array([[500,-500,0],[500,np.nan,0]])
    good_hip = np.array([[0,-1000,0],[0,-1000,0]])
    good_right = np.array([[-500,-500,0]])
    assert pc.placement_check(good_left,good_hip,good_right) == 0
    assert pc.placement_check(nan_left,good_hip,good_right) == 0


if __name__ == '__main__' :
    test_placement_check()