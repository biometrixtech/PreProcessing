# -*- coding: utf-8 -*-
"""
Created on Wed Jul 13 13:16:42 2016

@author: Brian
"""

import numpy as np
import abc
import dataObject as do

class Set_Up(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self, path, columns, hz, anatom=None):
        data = np.genfromtxt(path, dtype=float, delimiter=',')
        self.timestamp = data[:,0]
        if anatom is None:
            self.hipdataset = do.RawFrame(data[:,1:8], columns)
            self.lfdataset = do.RawFrame(data[:,8:15], columns)
            self.rfdataset = do.RawFrame(data[:,15:22], columns)
        else:
            self.hipdataset = do.RawFrame(data[:,1:8], columns, anatom.yaw_alignh_q, anatom.alignh_q, anatom.neutral_hq)
            self.lfdataset = do.RawFrame(data[:,8:15], columns, anatom.yaw_alignl_q, anatom.alignl_q, anatom.neutral_lq)
            self.rfdataset = do.RawFrame(data[:,15:22], columns, anatom.yaw_alignr_q, anatom.alignr_q, anatom.neutral_rq)
            
        self.hz = hz

class Analytics(object):
    def __init__(self, path, mass, extra_mass, hz, anatom=None):
        columns = ['aX', 'aY', 'aZ', 'qW', 'qX', 'qY', 'qZ']
        Set_Up.__init__(self, path, columns, hz, anatom)
        self.mass = mass
        self.extra_mass = extra_mass
        
        self.cme_dict = {'prosupl':[-1, -4, 2, 8], 'hiprotl':[-1, -4, 2, 8], 'hipdropl':[-1, -4, 2, 8],
                         'prosupr':[-1, -4, 2, 8], 'hiprotr':[-1, -4, 2, 8], 'hipdropr':[-1, -4, 2, 8],
                         'hiprotd':[-1, -4, 2, 8]}
        self.cme_dict_imp = {'landtime':[0.2, 0.25], 'landpattern':[12, -50]}

class Anatomical(object):
    def __init__(self, path, hz):
        columns = ['gX', 'gY', 'gZ', 'qW', 'qX', 'qY', 'qZ']
        Set_Up.__init__(self, path, columns, hz)
        
        