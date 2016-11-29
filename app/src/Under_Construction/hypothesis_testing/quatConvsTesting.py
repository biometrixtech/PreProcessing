# -*- coding: utf-8 -*-
"""
Created on Fri Nov 18 07:56:15 2016

@author: court
"""

from hypothesis import given, assume, example
import hypothesis.strategies as st
import random
from hypothesis.extra.numpy import arrays
import numpy as np

import quatConvs as qc
import quatOps as qo

@given(arrays(np.float, (random.randint(5,10),4), elements=st.floats(min_value=-1,
              max_value=1)))
@example(np.array([[1,0,0,0]]))
@example(np.array([[0,0,1,1]]))
def test_quatConvs(q):
    """
    Propert and unit testing for quaternion - euler conversions.
    
    Args:
        q: input array of quaternions
    
    Tests included:
        - quat_to_eul able to pass NaNs
        - normalization of quaternion maintains shape and ndarray type
        - computed euler angles have 3 columns
        - computed quaternions have 4 columns
        - computed quaternions are (nx4) ndarrays
        - computed euler angles are (nx3) ndarrays
        - conversions cancel each other out

    Known limitations:
        - euler_to_quat cannot handle NaNs or infs.
        - quat_to_euler cannot handle "zero" quaternion or very close to zero.
        - quaternion cannot be such that abs(quat_n[:, 1]*quat_n[:, 3] \
            + quat_n[:, 0]*quat_n[:, 2]) = +/-0.5

    Testing weaknesses:
        - assumptions not always registering for tests. Will get failures
            for these cases.

    """
    assume(not (q == 0).all())
    assume(all(np.linalg.norm(q, axis=1) > 0.1))

    # pass data with value through conversions
#    for row in range(len(q)):
#        assume (not (q[row] == 0).all())
#        assume ((np.sqrt(q[row][0]**2 + q[row][1]**2 + q[row][2]**2 \
#            + q[row][3]**2)).all() > 0.05)
    quat_n = qo.quat_norm(q)
    c_mag = np.absolute(quat_n[:, 1]*quat_n[:, 3] + quat_n[:, 0]*quat_n[:, 2])
    assume ((np.absolute(c_mag-0.5)).all() > 0.1)
    quat = quat_n
    comp_eul = qc.quat_to_euler(quat)
    comp_quat = qc.euler_to_quat(comp_eul)
    # test quat_to_eul's passing of NaNs
    nan_in = qc.quat_to_euler(np.array([[np.nan,0,0,0]]))
    nan_out = np.array([[np.nan,np.nan,np.nan]])
    assert ((nan_in == nan_out) | (np.isnan(nan_in) \
        & np.isnan(nan_out))).all() == True
    # check shape and type
    assert type(quat) == np.ndarray
    assert quat.shape == q.shape
    assert len(comp_eul[0]) == 3
    assert len(quat[0]) == 4
    assert len(comp_eul) == len(quat)
    assert comp_quat.shape == quat.shape
    assert type(comp_eul) == np.ndarray
    assert type(comp_quat) == np.ndarray
    # check that conversions cancel each other out.
    for row in range(len(quat_n)):
           assert (np.allclose(quat_n[row], comp_quat[row], atol = 1e-6,
                           equal_nan=True) or np.allclose(quat_n[row], -comp_quat[row],
                           atol = 1e-6, equal_nan=True)) == True

if __name__ == '__main__' :    

    test_quatConvs()