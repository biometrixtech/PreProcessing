# -*- coding: utf-8 -*-
"""
Created on Wed Jul 13 13:16:42 2016

@author: Brian
"""

import numpy as np
import abc
import dataObject as do

"""
#############################################INPUT/OUTPUT####################################################   
Inputs: ndarray object to be turned into dataObject, column names/attributes for dataObject, sampling rate, 
allow the passing of anatomical correction object, some classes require passing of mass and extra_mass vars
Outputs: setUp object with dataObject (including anatom quaternions) for each sensor location, Analytics subclass
also hold mass and extra mass attributes as well as dictionaries of CME thresholds
#############################################################################################################
"""
def dynamicName(sdata):
    names = sdata.dtype.names[1:]
    width = len(names)+1
    data = sdata.view((float, width))
    
    prefix = []
    for i in range(len(names)):
        name = names[i]
        name = name[:-2]
        if name not in prefix:
            prefix.append(name)
    return data, prefix

class Set_Up(object, metaclass=abc.ABCMeta): #Abstract setUp class
    @abc.abstractmethod
    def __init__(self, path, columns, hz, anatom=None):
        sdata = np.genfromtxt(path, dtype=float, delimiter=',', names=True) #create ndarray from path
        data, self.prefix= dynamicName(sdata)
        self.timestamp = data[:,0] #declare timestamp attribute
        if anatom is None: #if no previous anatomical calibration create dataObject with default quaternions (mainly used in runAnatomical)
            self.hipdataset = do.RawFrame(data[:,8:15], columns)
            self.lfdataset = do.RawFrame(data[:,1:8], columns)
            self.rfdataset = do.RawFrame(data[:,15:22], columns)
        else: #create dataObject that includes custom anatomical calibration quaternions (used mainly for runAnalytics)
            self.hipdataset = do.RawFrame(data[:,8:15], columns, anatom.yaw_alignh_q, anatom.alignh_q, anatom.neutral_hq)
            self.lfdataset = do.RawFrame(data[:,1:8], columns, anatom.yaw_alignl_q, anatom.alignl_q, anatom.neutral_lq)
            self.rfdataset = do.RawFrame(data[:,15:22], columns, anatom.yaw_alignr_q, anatom.alignr_q, anatom.neutral_rq)
        
        #declare sampling rate attribute
        self.hz = hz

class Analytics(object):
    def __init__(self, path, mass, extra_mass, hz, anatom=None):
        columns = ['aX', 'aY', 'aZ', 'qW', 'qX', 'qY', 'qZ'] #declare columns to be passed
        Set_Up.__init__(self, path, columns, hz, anatom) #create setUp object
        #create attributes of mass inputs
        self.mass = mass
        self.extra_mass = extra_mass
        
        #attributes with dictionaries of CME thresholds
        self.cme_dict = {'prosupl':[-1, -4, 2, 8], 'hiprotl':[-1, -4, 2, 8], 'hipdropl':[-1, -4, 2, 8],
                         'prosupr':[-1, -4, 2, 8], 'hiprotr':[-1, -4, 2, 8], 'hipdropr':[-1, -4, 2, 8],
                         'hiprotd':[-1, -4, 2, 8]}
        self.cme_dict_imp = {'landtime':[0.2, 0.25], 'landpattern':[12, -50]}

class Anatomical(object):
    def __init__(self, path, hz):
        columns = ['gX', 'gY', 'gZ', 'qW', 'qX', 'qY', 'qZ'] #declare columns to be passed
        Set_Up.__init__(self, path, columns, hz) #create setUp object
        
class SensPlace(object):
    def __init__(self, path, hz):
        columns = ['aX', 'aY', 'aZ', 'qW', 'qX', 'qY', 'qZ'] #declare columns to be passed
        Set_Up.__init__(self, path, columns, hz) #create setUp object    
        
        