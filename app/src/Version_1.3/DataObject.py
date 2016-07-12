# -*- coding: utf-8 -*-
"""
Created on Tue Jul 12 11:03:55 2016

@author: Brian
"""
import numpy as np
from abc import ABCMeta 

class ColumnMismatchError(ValueError):
    pass

class DataObject(object):
    
    __metaclass__ = ABCMeta
    
    def __init__(self, data=None, columns=None):
        if data is None:
            return {}
        
        if isinstance(data, np.ndarray):
            if columns is None:
                for i in range(len(data.transpose())):
                    setattr(self, 'var_' + str(i), data[:,i])
            if columns is not None:
                if len(columns) != len(data.transpose()):
                    raise ColumnMismatchError
                else:
                    for i in range(len(data.transpose())):
                        setattr(self, columns[i], data[:,i])
        else:
            return None

class InertialFrame(DataObject):
    def __init__(self, data=None):
        DataObject.__init__(self, data, ["qW", "qX", "qY", "qZ", "EulerX", "EulerY", "EulerZ", "AccX", "AccY", "AccZ", "gyrX", "gyrY", "gyrZ", "magX", "magY", "magZ"])
        
