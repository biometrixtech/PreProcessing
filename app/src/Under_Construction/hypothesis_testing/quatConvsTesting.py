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

    assume ((q == 0).all() == False)
    quat = qo.quat_norm(q.reshape(-1,))
    assume (np.sqrt(quat[0]**2+quat[1]**2+quat[2]**2+quat[3]**2)>0.05)
    comp_eul_phi, comp_eul_theta, comp_eul_psi = qc.quat_to_euler(quat)
    print type(comp_eul_phi)
#    print comp_eul
    comp_quat = qc.euler_to_quat(comp_eul_phi,comp_eul_theta,comp_eul_psi)
#    print type(comp_quat)
    assert type(quat) == np.ndarray
#    assert quat.shape == q.shape
#    print len(comp_eul_phi+comp_eul_theta+comp_eul_psi), len(quat)
#    assert len(comp_eul_phi+comp_eul_theta+comp_eul_psi) == 3
    assert len(quat) == 4
#    assert comp_quat.shape == quat.shape
    print type(comp_eul_phi)
    assert type(comp_eul_phi) == np.ndarray
#    assert type(comp_quat) == np.ndarray
    assert comp_quat == quat

if __name__ == '__main__' :    

    test_quatConvs()