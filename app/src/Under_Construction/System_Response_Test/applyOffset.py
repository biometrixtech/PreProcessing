# -*- coding: utf-8 -*-
"""
Created on Tue Dec 06 18:01:56 2016

@author: court
"""

import quatOps as qo
import quatConvs as qc
import numpy as np
import sys

def apply_offsets(qW, qX, qY, qZ, aX, aY, aZ, off):
    quat = np.hstack([qW, qX, qY, qZ])
    acc = np.hstack([aX, aY, aZ])
    offset = qc.euler_to_quat(np.array([[0, 0, off]]))
    quat_offset = qo.quat_prod(quat, offset)
    acc_offset = qo.vect_rot(acc, offset)
    qlen = len(qW)
    
    return quat_offset[:,0].reshape(qlen, 1), \
        quat_offset[:,1].reshape(qlen, 1), \
        quat_offset[:,2].reshape(qlen, 1), \
        quat_offset[:,3].reshape(qlen, 1), \
        acc_offset[:,0].reshape(qlen, 1), \
        acc_offset[:,1].reshape(qlen, 1), \
        acc_offset[:,2].reshape(qlen, 1)

def get_acc(aX, aY, aZ):

    acc = np.hstack([aX, aY, aZ]).reshape(-1, 3)
    return acc