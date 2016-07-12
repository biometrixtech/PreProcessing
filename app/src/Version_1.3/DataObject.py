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
                for i in range(len(data.transpose())):
                    setattr(self, 'var_' + str(i), data[:,i])
            if columns is not None:
                if len(columns) != len(data.transpose()):
                    raise ColumnMismatchError
                elif data.ndim == 1:
                    for i in range(len(data.transpose())):
                        setattr(self, columns[i], data[i])
                else:
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
        self.columns = ["qW", "qX", "qY", "qZ", "EulerX", "EulerY", "EulerZ", "AccX", "AccY", "AccZ", "gyrX", "gyrY", "gyrZ", "magX", "magY", "magZ"]
        DataObject.__init__(self, data, self.columns)
    
    def row(self, key):
        return DataObject.row(key, self.columns)

class SensorFrame(DataObject):
    def __init__(self, data=None):
        self.columns = ["accX", "accY", "accZ", "gyrX", "gyrY", "gyrZ", "magX", "magY", "magZ"]
        DataObject.__init__(self, data, self.columns)
    
    def row(self, key):
        return DataObject.row(key, self.columns)

class AnatomicalFrame(DataObject):
    def __init__(self, data=None):
        self.columns = ["gyrX", "gyrY", "gyrZ", "EulerZ"]
        DataObject.__init__(self, data, self.columns)
    
    def row(self, key):
        return DataObject.row(key, self.columns)

class RawFrame(DataObject):
    #self.columns = columns = ['regimenAcitivityId', 'sensorId', 'sensorLocationId', 'logMode', 'logFreg', 'timestamp', 'accX_raw', 'accY_raw', 'accZ_raw', 'gyrX_raw', 'gyrY_raw', 'gyrZ_raw', 'magX_raw', 'magY_raw', 'magZ_raw', 'qW_raw', 'qX_raw', 'qY_raw', 'qZ_raw', 'set']
    
    def __init__(self, data=None):
        self.columns = ['regimenAcitivityId', 'sensorId', 'sensorLocationId', 'logMode', 'logFreg', 'timestamp', 'accX_raw', 'accY_raw', 'accZ_raw', 'gyrX_raw', 'gyrY_raw', 'gyrZ_raw', 'magX_raw', 'magY_raw', 'magZ_raw', 'qW_raw', 'qX_raw', 'qY_raw', 'qZ_raw', 'set']
        DataObject.__init__(self, data, self.columns)
    
    def row(self, key):
        return DataObject.row(self, key, self.columns)

class RowFrame(DataObject):
    def __init__(self, data=None, columns=None):
        DataObject.__init__(self, data, columns)
    
        
