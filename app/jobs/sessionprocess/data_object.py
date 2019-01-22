# -*- coding: utf-8 -*-
"""
Created on Tue Jul 12 11:03:55 2016

@author: Brian
"""
import abc


"""
#############################################INPUT/OUTPUT######################
Inputs: ndarray object to be turned into dataObject, some subclasses allow
passing columns, some subclasses
allow passing of quaternions to be held in dataObject
Outputs: dataObject whose attributes hold ndarrays, some dataObjects also
 hold anatomical quaternions
#############################################################################
"""


class DataObject(object):  # Abstract dataObject class
    """
    Adds columns to object as attributes.
    
    Arg:
        ndarray object
        
    Return:
        dataObject with attributes
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, data=None, columns=None):
        # set attributes using column names
        for i in range(len(columns)):
            setattr(self, columns[i], data[columns[i]].reshape(-1, 1))


class RawFrame(DataObject):
    """
    Allows dataObject to hold quaternions as attributes
    
    Arg:
        dataObject
        
    Return:
        dataObject capable of holding quats as attirbutes
    """
    def __init__(self, data=None, columns=None):
        # make this attribute uninstantiable
        self.columns = columns  # columns are defined from level above
        DataObject.__init__(self, data, self.columns)  # get dataObject
