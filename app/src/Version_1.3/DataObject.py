# -*- coding: utf-8 -*-
"""
Created on Tue Jul 12 11:03:55 2016

@author: Brian
"""
import numpy as np
import abc

class ColumnMismatchError(ValueError):
    pass
    
class DataObject(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self, data=None, columns=None):
        if data is None:
            return {}
        
        if isinstance(data, np.ndarray):
            if columns is None:
                if np.isnan(data[0,:]).any() == True:
                    data = data[1:]
                for i in range(len(data.transpose())):
                    setattr(self, 'var_' + str(i), data[:,i])
            if columns is not None:
                if len(columns) != len(data.transpose()):
                    raise ColumnMismatchError
                elif data.ndim == 1:
                    for i in range(len(data.transpose())):
                        setattr(self, columns[i], data[i])
                else:
                    if np.isnan(data[0,:]).any() == True:
                        data = data[1:]
                    for i in range(len(data.transpose())):
                        setattr(self, columns[i], data[:,i])
        else:
            return None
    
    def row(self, key, columns):
        row = np.array([])
        for i in range(len(columns)):
            row = np.append(row, self.__dict__[columns[i]][key])
        return RowFrame(row, columns)

class InertialFrame(DataObject):
    def __init__(self, data=None):
        self.columns = ["qW", "qX", "qY", "qZ", "EulerX", "EulerY", "EulerZ", "AccX", "AccY", "AccZ"]
        DataObject.__init__(self, data, self.columns)
    
    def row(self, key):
        return DataObject.row(key, self.columns)

class AnatomicalFrame(DataObject):
    def __init__(self, data=None):
        self.columns = ["gX", "gY", "gZ", "EulerZ"]
        DataObject.__init__(self, data, self.columns)
    
    def row(self, key):
        return DataObject.row(key, self.columns)

class RawFrame(DataObject):
    def __init__(self, data=None, columns=None, yaw_q=None, align_q=None, neutral_q=None):
        self.columns = columns
        DataObject.__init__(self, data, self.columns)

        if yaw_q is None:
            self.yaw_q = np.matrix([1,0,0,0])
        else:
            self.yaw_q = yaw_q
        if align_q is None:
            self.align_q = np.matrix([1,0,0,0])
        else:
            self.align_q = align_q
        if neutral_q is None:
            self.neutral_q = np.matrix([0.582,0.813,0,0])
        else:
            self.neutral_q = neutral_q
    
    def row(self, key):
        return DataObject.row(self, key, self.columns)
    
class RowFrame(DataObject):
    def __init__(self, data=None, columns=None):
        DataObject.__init__(self, data, columns)
    
        
