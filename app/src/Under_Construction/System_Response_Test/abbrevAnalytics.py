# -*- coding: utf-8 -*-
"""
Created on Tue Dec 06 17:42:32 2016

@author: court
"""

import numpy as np
import analyticsPrePreProcessing as appp
import dataObject as do
import phaseDetection as phase
#import IAD
#import IED
import coordinateFrameTransformation as coord
import pickle
#from mechStressTraining import prepareData
import movementAttrib as matrib
import balanceCME as cmed
import quatConvs as qc
import quatOps as qo
import impactCME as impact
#from controlScore import controlScore
#from scoring import score
import matplotlib.pyplot as plt
import createTables as ct
from sklearn import preprocessing
import sys
import re
from applyOffset import apply_offsets
import pandas as pd

def dynamicName(sdata):
    names = sdata.dtype.names[1:]
    width = len(names)+1
    data = sdata.view((float, width))    
    return data

class abbrev_analytics(object):
    def __init__(self, path, calib_transforms, session_bool, left_bool,
                 hip_bool, right_bool, offset):

        left_offset = np.zeros(())
        hip_offset = np.zeros(())
        right_offset = np.zeros(())

#        split = re.split("/", path)[1]
#        split_path = re.split('_', split)
#        calib_ = split_path[0]+"_"+split_path[1]+'_'#+split_path[2]+'_'
#        split_path1 = re.split('\.',split)
#        path_ = "output/"+split_path1[0]
        
        sdata = np.genfromtxt(path, dtype=float, delimiter=',', names=True) #create ndarray from path
#        uuids = pd.read_csv('uuid_list.csv')
        columns = sdata.dtype.names        
        data = dynamicName(sdata)
        self.data = do.RawFrame(data, columns)
        
        ##dummy values for now
#        self.data.team_id = np.array([uuids.team_id[uuids.filename==split].values]*len(sdata)).reshape(-1,1)
#        self.data.user_id = np.array([uuids.user_id[uuids.filename==split].values]*len(sdata)).reshape(-1,1)
#        self.data.team_regimen_id = np.array([uuids.team_regimen_id[uuids.filename==split].values]*len(sdata)).reshape(-1,1)
#        self.data.block_id = np.array([uuids.block_id[uuids.filename==split].values]*len(sdata)).reshape(-1,1)
#        self.data.block_event_id = np.array([uuids.block_event_id[uuids.filename==split].values]*len(sdata)).reshape(-1,1)
#        self.data.training_session_log_id = np.array([uuids.training_session_log_id[uuids.filename==split].values]*len(sdata)).reshape(-1,1)
#        self.data.session_event_id = np.array(['']*len(sdata)).reshape(-1,1)
#        self.data.exercise_id = np.array(['']*len(sdata)).reshape(-1,1)
#        self.data.session_type = np.array([uuids.session_type[uuids.filename==split].values]*len(sdata)).reshape(-1,1)
        
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
#        plt.figure(2)
#        plt.plot(self.data.raw_LaY)

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
        
        # APPLY ERROR OFFSET
        if session_bool:
            if left_bool:
                left_offset = offset
                self.data.LqW, self.data.LqX, self.data.LqY, self.data.LqZ, \
                    self.data.LaX, self.data.LaY, self.data.LaZ \
                    = apply_offsets(self.data.LqW, self.data.LqX,
                                    self.data.LqY, self.data.LqZ,
                                    self.data.LaX, self.data.LaY,
                                    self.data.LaZ, left_offset)
            if hip_bool:
                hip_offset = offset
                self.data.HqW, self.data.HqX, self.data.HqY, self.data.HqZ, \
                    self.data.HaX, self.data.HaY, self.data.HaZ \
                    = apply_offsets(self.data.HqW, self.data.HqX,
                                    self.data.HqY, self.data.HqZ,
                                    self.data.HaX, self.data.HaY,
                                    self.data.HaZ, hip_offset)
            if right_bool:
                right_offset = offset
                self.data.RqW, self.data.RqX, self.data.RqY, self.data.RqZ, \
                    self.data.RaX, self.data.RaY, self.data.RaZ \
                    = apply_offsets(self.data.RqW, self.data.RqX,
                                    self.data.RqY, self.data.RqZ,
                                    self.data.RaX, self.data.RaY,
                                    self.data.RaZ, right_offset)
        
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

        #Left foot body transformed data        
        self.data.LaX = d[:,1].reshape(-1,1)
        self.data.LaY = d[:,2].reshape(-1,1)  
        self.data.LaZ = d[:,3].reshape(-1,1)  
        plt.figure(4)
        plt.plot(self.data.LaX)
        plt.figure(5)
        plt.plot(self.data.LaY)
        plt.figure(6)
        plt.plot(self.data.LaZ)
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
        
        # PLOT NEUTRAL DATA
        #Left foot body transformed data        
 
        self.data.LqW_neutral = d_neutral[:,0].reshape(-1,1)    
        self.data.LqX_neutral = d_neutral[:,1].reshape(-1,1)  
        self.data.LqY_neutral = d_neutral[:,2].reshape(-1,1)  
        self.data.LqZ_neutral = d_neutral[:,3].reshape(-1,1)  
        #Hip body transformed data
        
        self.data.HqW_neutral = d_neutral[:,4].reshape(-1,1)    
        self.data.HqX_neutral = d_neutral[:,5].reshape(-1,1)  
        self.data.HqY_neutral = d_neutral[:,6].reshape(-1,1)  
        self.data.HqZ_neutral = d_neutral[:,7].reshape(-1,1)  
        #Right foot body transformed data
        
        self.data.RqW_neutral = d_neutral[:,8].reshape(-1,1)    
        self.data.RqX_neutral = d_neutral[:,9].reshape(-1,1)  
        self.data.RqY_neutral = d_neutral[:,10].reshape(-1,1)  
        self.data.RqZ_neutral = d_neutral[:,11].reshape(-1,1)
        
        # PHASE DETECTION
        sampl_freq = 100
        
        self.data.phase_lf, self.data.phase_rf = phase.combine_phase(self.data.LaZ,
                                                                     self.data.RaZ,
                                                                    sampl_freq)
        
        # MOVEMENT ATTRIBUTES AND PERFORMANCE VARIABLES
        # isolate hip acceleration and euler angle data
        hip_acc = np.hstack([self.data.HaX, self.data.HaY, self.data.HaZ])
        hip_eul = np.hstack([self.data.HeX, self.data.HeY, self.data.HeZ])
    
        # analyze planes of movement
        self.data.lat, self.data.vert, self.data.horz, self.data.rot,\
            self.data.lat_binary, self.data.vert_binary, \
            self.data.horz_binary, self.data.rot_binary, \
            self.data.stationary_binary, self.data.total_accel \
            = matrib.plane_analysis(hip_acc, hip_eul, self.data.ms_elapsed)
    
        # analyze stance
        self.data.standing, self.data.not_standing \
            = matrib.standing_or_not(hip_eul, sampl_freq)
        self.data.double_leg, self.data.single_leg, self.data.feet_eliminated \
            = matrib.double_or_single_leg(self.data.phase_lf,
                                          self.data.phase_rf,
                                          self.data.standing, sampl_freq)
        self.data.single_leg_stationary, self.data.single_leg_dynamic \
            = matrib.stationary_or_dynamic(self.data.phase_lf,
                                           self.data.phase_rf,
                                           self.data.single_leg, sampl_freq)
        
        # MOVEMENT QUALITY FEATURES
        # isolate neutral quaternions
        lf_neutral = d_neutral[:, :4]
        hip_neutral = d_neutral[:, 4:8]
        rf_neutral = d_neutral[:, 8:]
    
        # isolate actual euler angles
        hip_euler = qc.quat_to_euler(hip_neutral)
        lf_euler = qc.quat_to_euler(lf_neutral)
        rf_euler = qc.quat_to_euler(rf_neutral)
    
        # define balance CME dictionary
    
        # contralateral hip drop attributes
        nl_contra = cmed.cont_rot_CME(self.data.HeX, self.data.phase_lf, [1], hip_euler[:, 0])
        nr_contra = cmed.cont_rot_CME(self.data.HeX, self.data.phase_rf, [2], hip_euler[:, 0])
        self.data.contra_hip_drop_lf = nl_contra[:, 1].reshape(-1, 1)
        # fix so superior > 0
        self.data.contra_hip_drop_lf = self.data.contra_hip_drop_lf* - 1
        self.data.contra_hip_drop_rf = nr_contra[:, 1].reshape(-1, 1)
    
        # pronation/supination attributes
        nl_prosup = cmed.cont_rot_CME(self.data.LeX, self.data.phase_lf, [0, 1],
                                      lf_euler[:, 0])
        nr_prosup = cmed.cont_rot_CME(self.data.ReX, self.data.phase_rf, [0, 2],
                                      rf_euler[:, 0])
        self.data.ankle_rot_lf = nl_prosup[:, 1].reshape(-1, 1)
        self.data.ankle_rot_lf = self.data.ankle_rot_lf*-1 # fix so superior > 0
        self.data.ankle_rot_rf = nr_prosup[:, 1].reshape(-1, 1)
    
        # lateral hip rotation attributes
        cont_hiprot = cmed.cont_rot_CME(self.data.HeZ, self.data.phase_lf, [0, 1, 2, 3, 4, 5],
                                        hip_euler[:, 2])
        self.data.hip_rot = cont_hiprot[:, 1].reshape(-1, 1)
        self.data.hip_rot = self.data.hip_rot*-1 # fix so clockwise > 0


        # IMPACT CME
        # define dictionary for msElapsed

        # landing time attributes
        n_landtime, ltime_index, lf_rf_imp_indicator = impact.sync_time(self.data.phase_rf, self.data.phase_lf,
                                                   sampl_freq)
        # landing pattern attributes
        if len(n_landtime) != 0:
            n_landpattern = impact.landing_pattern(self.data.ReY, self.data.LeY,
                                                   land_time_index=ltime_index,
                                                   l_r_imp_ind=lf_rf_imp_indicator,
                                                   sampl_rate=sampl_freq,
                                                   land_time=n_landtime)
            land_time, land_pattern =\
                impact.continuous_values(n_landpattern, n_landtime,
                                         len(self.data.LaX), ltime_index)
            self.data.land_time = land_time.reshape(-1, 1)
            self.data.land_pattern_rf = land_pattern[:, 0].reshape(-1, 1)
            self.data.land_pattern_lf = land_pattern[:, 1].reshape(-1, 1)
        else:
            self.data.land_time = np.zeros((len(self.data.LaX), 1))*np.nan
            self.data.land_pattern_lf = np.zeros((len(self.data.LaX), 1))*np.nan
            self.data.land_pattern_rf = np.zeros((len(self.data.LaX), 1))*np.nan
        
        movement_data = ct.create_movement_data(len(self.data.LaX), self.data)
        movement_data_pd = pd.DataFrame(movement_data)
        movement_data_pd.to_csv(str(offset) + "_movement_data.csv", index = False)

