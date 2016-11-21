# -*- coding: utf-8 -*-
"""
Created on Thu Nov 17 17:43:07 2016

@author: court
"""

from hypothesis import given, assume, example
import hypothesis.strategies as st
import random
from hypothesis.extra.numpy import arrays
import numpy as np
import itertools

import placementCheck as pc


@given(arrays(np.int, (3,3), elements=st.floats(min_value=-1500,
              max_value=1500)), arrays(np.int, (3,3), elements
              =st.floats(min_value=-2500,max_value=2500)), arrays(
              np.int,(3,3), elements=st.floats(
              min_value=-1500,max_value=1500)), st.booleans(), st.booleans(),
              st.booleans(), st.booleans())
def test_placement_check(left_acc, hip_acc, right_acc, bad_left,
                         bad_hip, bad_right, handle_nans):

    ind = pc.placement_check(left_acc,hip_acc,right_acc)
    assert type(ind) == np.int
    assert np.in1d(ind, [2,3,4,5,6,7,8,9])
    if bad_left:
        assume (np.nanmean(left_acc[:,0])<200 or np.nanmean(left_acc[:,1])>-200 or np.absolute(np.nanmean(left_acc[:,2])>200))
        assert np.in1d(ind, [2,3,6,7])
    if bad_hip:
        assume (np.absolute(np.nanmean(hip_acc[:,0]))>200 or np.nanmean(hip_acc[:,1])>-800 or np.absolute(np.nanmean(hip_acc[:,2]))>200)
        assert np.in1d(ind, [2,3,4,5])
    if bad_right:
        assume (np.nanmean(right_acc[:,0])>-200 or np.nanmean(right_acc[:,1])>-200 or np.absolute(np.nanmean(right_acc[:,2]))>200)
        assert np.in1d(ind, [2,4,6,8])

#    assert pc.placement_check(np.array([[]]))
#    print left_acc #,hip_acc,right_acc
#    print ind, bad_left, bad_hip, bad_right

if __name__ == '__main__' :

    test_placement_check()