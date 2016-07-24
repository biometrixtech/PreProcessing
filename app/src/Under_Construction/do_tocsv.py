# -*- coding: utf-8 -*-
"""
Created on Sun Jul 24 12:57:57 2016

@author: Brian
"""

import numpy as np

def stack_data(data):
    output = np.zeros((len(data.qX),1))
    output = np.hstack((output, data.qW))
    output = np.hstack((output, data.qX))
    output = np.hstack((output, data.qY))
    output = np.hstack((output, data.AccX))
    output = np.hstack((output, data.AccY))
    output = np.hstack((output, data.AccZ))
    output = np.hstack((output, data.EulerX))
    output = np.hstack((output, data.EulerY))
    output = np.hstack((output, data.EulerZ))