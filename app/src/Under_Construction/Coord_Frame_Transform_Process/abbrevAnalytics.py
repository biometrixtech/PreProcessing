# -*- coding: utf-8 -*-
"""
Created on Tue Dec 06 17:42:32 2016

@author: court
"""

import numpy as np
import analyticsPrePreProcessing as appp
import dataObject as do
#import phaseDetection as phase
#import IAD
#import IED
import coordinateFrameTransformation as coord
import pickle
#from mechStressTraining import prepareData
#import movementAttrib as matrib
#import balanceCME as cmed
import quatConvs as qc
import quatOps as qo
#import impactCME as impact
#from controlScore import controlScore
#from scoring import score
#import matplotlib.pyplot as plt
import createTables as ct
from sklearn import preprocessing
import sys
import re
#from applyOffset import apply_offsets
import pandas as pd

def dynamicName(sdata):
    names = sdata.dtype.names[1:]
    width = len(names)+1
    data = sdata.view((float, width))    
    return data

class abbrev_analytics(object):
    def __init__(self, path, calib_transforms):

        sdata = np.genfromtxt(path, dtype=float, delimiter=',', names=True) #create ndarray from path
#        uuids = pd.read_csv('uuid_list.csv')
        columns = sdata.dtype.names        
        data = dynamicName(sdata)
        self.data = do.RawFrame(data, columns)

        # Save raw values in different attributes to later populate table
        # left
        self.data.raw_LaX = self.data.LaX
        self.data.raw_LaY = self.data.LaY
        self.data.raw_LaZ = self.data.LaZ
        self.data.raw_LqX = self.data.LqX
        self.data.raw_LqY = self.data.LqY
        self.data.raw_LqZ = self.data.LqZ
        # hip
        self.data.raw_HaX = self.data.HaX
        self.data.raw_HaY = self.data.HaY
        self.data.raw_HaZ = self.data.HaZ
        self.data.raw_HqX = self.data.HqX
        self.data.raw_HqY = self.data.HqY
        self.data.raw_HqZ = self.data.HqZ
        # right
        self.data.raw_RaX = self.data.RaX
        self.data.raw_RaY = self.data.RaY
        self.data.raw_RaZ = self.data.RaZ
        self.data.raw_RqX = self.data.RqX
        self.data.raw_RqY = self.data.RqY
        self.data.raw_RqZ = self.data.RqZ
        self.data.obs_master_index = (np.array(range(len(self.data.raw_LaX)))\
                                        +1).reshape(-1, 1)

        # PRE-PRE-PROCESSING

        # Check for duplicate epoch time
        duplicate_epoch_time =\
                            appp.check_duplicate_epochtime(self.data.epoch_time)
#        if duplicate_epoch_time:
#            print 'Duplicate epoch time.'

        # check for missing values
        self.data = appp.handling_missing_data(self.data)
        
        # determine the real quartenion
        # left
        _lq_xyz = np.hstack([self.data.LqX, self.data.LqY, self.data.LqZ])
        _lq_wxyz, self.data.corrupt_type =\
                        appp.calc_quaternions(_lq_xyz,
                                             self.data.missing_data_indicator,
                                             self.data.corrupt_magn)
        #check for type conversion error in left foot quaternion data
#        if 2 in self.data.corrupt_type:
#            print 'Error! Type conversion error: LF quat'
        self.data.LqW = _lq_wxyz[:, 0].reshape(-1, 1)
        self.data.LqX = _lq_wxyz[:, 1].reshape(-1, 1)
        self.data.LqY = _lq_wxyz[:, 2].reshape(-1, 1)
        self.data.LqZ = _lq_wxyz[:, 3].reshape(-1, 1)
        # hip
        _hq_xyz = np.hstack([self.data.HqX, self.data.HqY, self.data.HqZ])
        _hq_wxyz, self.data.corrupt_type =\
                        appp.calc_quaternions(_hq_xyz,
                                             self.data.missing_data_indicator,
                                             self.data.corrupt_magn)
        #check for type conversion error in hip quaternion data
#        if 2 in self.data.corrupt_type:
#            print 'Error! Type conversion error: Hip quat'
        self.data.HqW = _hq_wxyz[:, 0].reshape(-1, 1)
        self.data.HqX = _hq_wxyz[:, 1].reshape(-1, 1)
        self.data.HqY = _hq_wxyz[:, 2].reshape(-1, 1)
        self.data.HqZ = _hq_wxyz[:, 3].reshape(-1, 1)
        # right
        _rq_xyz = np.hstack([self.data.RqX, self.data.RqY, self.data.RqZ])
        _rq_wxyz, self.data.corrupt_type =\
                        appp.calc_quaternions(_rq_xyz,
                                             self.data.missing_data_indicator,
                                             self.data.corrupt_magn)
        #check for type conversion error in right foot quaternion data
#        if 2 in self.data.corrupt_type:
#            print 'Error! Type conversion error: RF quat'
        self.data.RqW = _rq_wxyz[:, 0].reshape(-1, 1)
        self.data.RqX = _rq_wxyz[:, 1].reshape(-1, 1)
        self.data.RqY = _rq_wxyz[:, 2].reshape(-1, 1)
        self.data.RqZ = _rq_wxyz[:, 3].reshape(-1, 1)

        # convert epoch time to date time and determine milliseconds elapsed
        self.data.time_stamp, self.data.ms_elapsed = \
            appp.convert_epochtime_datetime_mselapsed(self.data.epoch_time)

        # COORDINATE FRAME TRANSFORMATION

        hip_bf_transform = calib_transforms[0]
        lf_bf_transform = calib_transforms[1]
        rf_bf_transform = calib_transforms[2]
        lf_n_transform = calib_transforms[4]
        rf_n_transform = calib_transforms[5]
        hip_n_transform = calib_transforms[3]

        d, d_neutral= coord.transform_data(self.data, hip_bf_transform,
                                           lf_bf_transform,rf_bf_transform,
                                           lf_n_transform,rf_n_transform,
                                           hip_n_transform)

        d_neutral = np.array(d_neutral)

#        #Left foot body transformed data        
        self.data.LaX = d[:,1].reshape(-1,1)
        self.data.LaY = d[:,2].reshape(-1,1)  
        self.data.LaZ = d[:,3].reshape(-1,1)  
        self.data.LeX = d[:,4].reshape(-1,1)    
        self.data.LeY = d[:,5].reshape(-1,1)  
        self.data.LeZ = d[:,6].reshape(-1,1)  
        self.data.LqW = d[:,7].reshape(-1,1)    
        self.data.LqX = d[:,8].reshape(-1,1)  
        self.data.LqY = d[:,9].reshape(-1,1)  
        self.data.LqZ = d[:,10].reshape(-1,1)  
        #Hip body transformed data
        self.data.HaX = d[:,11].reshape(-1,1)    
        self.data.HaY = d[:,12].reshape(-1,1)  
        self.data.HaZ = d[:,13].reshape(-1,1)  
        self.data.HeX = d[:,14].reshape(-1,1)    
        self.data.HeY = d[:,15].reshape(-1,1)  
        self.data.HeZ = d[:,16].reshape(-1,1)  
        self.data.HqW = d[:,17].reshape(-1,1)    
        self.data.HqX = d[:,18].reshape(-1,1)  
        self.data.HqY = d[:,19].reshape(-1,1)  
        self.data.HqZ = d[:,20].reshape(-1,1)  
        #Right foot body transformed data
        self.data.RaX = d[:,21].reshape(-1,1)    
        self.data.RaY = d[:,22].reshape(-1,1)  
        self.data.RaZ = d[:,23].reshape(-1,1)  
        self.data.ReX = d[:,24].reshape(-1,1)    
        self.data.ReY = d[:,25].reshape(-1,1)  
        self.data.ReZ = d[:,26].reshape(-1,1)  
        self.data.RqW = d[:,27].reshape(-1,1)    
        self.data.RqX = d[:,28].reshape(-1,1)  
        self.data.RqY = d[:,29].reshape(-1,1)  
        self.data.RqZ = d[:,30].reshape(-1,1)
        
        movement_data = ct.create_movement_data(len(self.data.LaX), self.data)
        movement_data_pd = pd.DataFrame(movement_data)
        movement_data_pd.to_csv("movement_data_" + path, index = False)