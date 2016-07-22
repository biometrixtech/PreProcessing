# -*- coding: utf-8 -*-
"""
Created on Tue Jul 12 11:03:55 2016

@author: Brian
"""
import numpy as np
import abc

"""
#############################################INPUT/OUTPUT####################################################   
Inputs: ndarray object to be turned into dataObject, some subclasses allow passing columns, some subclasses
allow passing of quaternions to be held in dataObject
Outputs: dataObject whose attributes hold ndarrays, some dataObjects also hold anatomical quaternions
#############################################################################################################
"""

class ColumnMismatchError(ValueError):
    pass
    
class DataObject(object, metaclass=abc.ABCMeta): #Abstract dataObject class
    @abc.abstractmethod
    def __init__(self, data=None, columns=None):
        if data is None: #return empty dictionary if no data
            return {}
        
        if isinstance(data, np.ndarray): #make sure data is an ndarray
            if columns is None: 
                if np.isnan(data[0,:]).any() == True: #if first line is full of nan delete it
                    data = data[1:]
                for i in range(len(data.transpose())):
                    setattr(self, 'var_' + str(i), data[:,i]) #set attributes of object with general names
            if columns is not None:
                if len(columns) != len(data.transpose()): #throw error if len(data.columns) != len(columns)
                    raise ColumnMismatchError
                elif data.ndim == 1: #handle 1 dim ndarrays
                    for i in range(len(data.transpose())):
                        setattr(self, columns[i], data[i]) #set attributes using associated column names
                else:
                    if np.isnan(data[0,:]).any() == True: #if first line is full of nan delete it
                        data = data[1:]
                    for i in range(len(data.transpose())): #set attributes using column names
                        setattr(self, columns[i], data[:,i])
        else:
            return None #return None if empty dictionary
    
    def row(self, key, columns): #use in case you are trying to evaluate a "row" within an object
        row = np.array([])
        for i in range(len(columns)):
            row = np.append(row, self.__dict__[columns[i]][key]) #create array and append element at row number in each attribute
        return RowFrame(row, columns)

class InertialFrame(DataObject):
    def __init__(self, data=None):
        #define columns needed in InertialFrame
        self.columns = ["qW", "qX", "qY", "qZ", "EulerX", "EulerY", "EulerZ", "AccX", "AccY", "AccZ"]
        DataObject.__init__(self, data, self.columns) #create object
    
    def row(self, key): #use row function on Inertial Frame object
        return DataObject.row(key, self.columns)

class AnatomicalFrame(DataObject):
    def __init__(self, data=None):
        #define columns needed for AnatomicalFrame
        self.columns = ["gX", "gY", "gZ", "EulerZ"]
        DataObject.__init__(self, data, self.columns) #create object
    
    def row(self, key): #use row function on Anatomical Frame object
        return DataObject.row(key, self.columns)

class RawFrame(DataObject):
    def __init__(self, data=None, columns=None, yaw_q=None, align_q=None, neutral_q=None):
        #make this attribute uninstantiable
        self.columns = columns #columns are defined from level above
        DataObject.__init__(self, data, self.columns) #get dataObject
        #create attributes for anatomical calibration quaternions
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
    
    def row(self, key): #use row function on Raw Frame object
        return DataObject.row(self, key, self.columns)
    
class RowFrame(DataObject):
    def __init__(self, data=None, columns=None):
        DataObject.__init__(self, data, columns)
    
        
