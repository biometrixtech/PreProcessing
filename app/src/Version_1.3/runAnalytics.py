# -*- coding: utf-8 -*-
"""
Created on Wed Jul 13 20:19:05 2016

@author: Brian
"""

import numpy as np
import setUp as su
import phaseDetection as phase
import coordinateFrameTransformation as prep
import balanceCME as cmed
import impactCME as impact
import loadCalc as ldcalc

class RunAnalytics(object):
    def __init__(self, path, mass, extra_mass, hz, anatom=None):
        #Set up objects that hold raw datasets 
        data = su.Analytics(path, mass, extra_mass, hz, anatom)
        
        #Create Inertial Frame objects transformed data
        hipbf = prep.TransformData(data.hipdataset)
        rfbf = prep.TransformData(data.rfdataset)
        lfbf = prep.TransformData(data.lfdataset)
        
        ##PHASE DETECTION
        lf_phase, rf_phase = phase.combine_phase(lfbf.AccZ, rfbf.AccZ, rfbf.EulerY, lfbf.EulerY, data.hz)
        
        lfbf.phase =  lf_phase
        rfbf.phase = rf_phase
        
        #Determining the load            
        self.load = ldcalc.load_bal_imp(rfbf.phase, lfbf.phase, hipbf.AccX, hipbf.AccY, hipbf.AccZ, data.mass, data.extra_mass)
        
        #Contralateral Hip Drop
        self.nr_contra = cmed.cont_rot_CME(hipbf.EulerY, rfbf.phase, [2,0], prep.Calc_Euler(data.hipdataset.neutral_q)[1], data.cme_dict['hipdropr'])
        self.nl_contra = cmed.cont_rot_CME(hipbf.EulerY, lfbf.phase, [1,0], prep.Calc_Euler(data.hipdataset.neutral_q)[1], data.cme_dict['hipdropl'])
        #Pronation/Supination
        self.nr_prosup = cmed.cont_rot_CME(rfbf.EulerX, rfbf.phase, [2,0], prep.Calc_Euler(data.rfdataset.neutral_q)[0], data.cme_dict['prosupr'])
        self.nl_prosup = cmed.cont_rot_CME(lfbf.EulerX, lfbf.phase, [1,0], prep.Calc_Euler(data.lfdataset.neutral_q)[0], data.cme_dict['prosupl'])
        #Lateral Hip Rotation
        self.nr_hiprot = cmed.cont_rot_CME(hipbf.EulerZ, rfbf.phase, [2], prep.Calc_Euler(data.hipdataset.neutral_q)[2], data.cme_dict['hiprotr'])
        self.nrdbl_hiprot = cmed.cont_rot_CME(hipbf.EulerZ, rfbf.phase, [0], prep.Calc_Euler(data.hipdataset.neutral_q)[2], data.cme_dict['hiprotd'])
        self.nl_hiprot = cmed.cont_rot_CME(hipbf.EulerZ, lfbf.phase, [1], prep.Calc_Euler(data.hipdataset.neutral_q)[2], data.cme_dict['hiprotl'])
        self.nldbl_hiprot = cmed.cont_rot_CME(hipbf.EulerZ, rfbf.phase, [0], prep.Calc_Euler(data.hipdataset.neutral_q)[2], data.cme_dict['hiprotd'])
        
        #Landing Time
        self.n_landtime = impact.sync_time(rfbf.phase, lfbf.phase, data.hz, data.cme_dict_imp['landtime'])
        #Landing Pattern
        if len(self.n_landtime) != 0:
            self.n_landpattern = impact.landing_pattern(rfbf.EulerY, lfbf.EulerY, self.n_landtime[:,0], self.n_landtime[:,1], data.cme_dict_imp['landpattern'])
        else:
            self.n_landpattern = np.array([])
