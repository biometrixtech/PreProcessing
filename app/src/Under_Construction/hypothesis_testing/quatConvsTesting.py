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
import itertools

import quatConvs as qc
import quatOps as qo

@given(arrays(np.float, (1,4), elements=st.floats(min_value=-1,
              max_value=2)))
def test_quatConvs(q):

    assume (not (q == 0).all())
    assume (np.sqrt(q[0][0]**2+q[0][1]**2+q[0][2]**2+q[0][3]**2)>0.05)
    print q.shape
    quat = qo.quat_norm(q)
    print "quat",quat
    print "quat shape",quat.shape
    comp_eul = qc.quat_to_euler(quat)
    print "EUL",comp_eul
#    print type(comp_eul)
#    print comp_eul
    comp_quat = qc.euler_to_quat(comp_eul)
#    print type(comp_quat)
    assert type(quat) == np.ndarray
    assert quat.shape == q.shape
#    print len(comp_eul_phi+comp_eul_theta+comp_eul_psi), len(quat)
    assert len(comp_eul[0]) == 3
    assert len(quat[0]) == 4
    assert len(comp_eul) == len(quat)
    assert comp_quat.shape == quat.shape
    print "comp",comp_quat
    print "orig",quat
    assert type(comp_eul) == np.ndarray
    assert type(comp_quat) == np.ndarray
    assert (np.allclose(quat, comp_quat, rtol=1e-05, atol=1e-08, equal_nan=True) or np.allclose(quat, -comp_quat, rtol=1e-05, atol=1e-08, equal_nan=True)) == True

if __name__ == '__main__' :    

    test_quatConvs()