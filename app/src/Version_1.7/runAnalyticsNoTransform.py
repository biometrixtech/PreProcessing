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
import dataChecks as dc

"""
#############################################INPUT/OUTPUT####################################################   
Inputs: filepath to analytics dataset, sampling rate, mass, and extra mass
Outputs: object with attributes for each CME
#############################################################################################################
"""

class RunAnalytics(object):
    def __init__(self, path, mass, extra_mass, hz, anatom=None):
        #Set up objects that hold raw datasets 
        data = su.Analytics(path, mass, extra_mass, hz, anatom)
        
        #Check quaternions to make sure they are good
        hipbf = dc.quatCheck(data.hipdataset)
        rfbf = dc.quatCheck(data.hipdataset)
        lfbf = dc.quatCheck(data.hipdataset)
        
        #Create add Euler Angle outputs to data object
        hipbf = dc.angleArrays(hipbf)
        rfbf = dc.angleArrays(rfbf)
        lfbf = dc.angleArrays(lfbf)
        
        ##PHASE DETECTION
        self.lf_phase, self.rf_phase = phase.combine_phase(lfbf.AccX, lfbf.AccZ, rfbf.AccX, rfbf.AccZ, rfbf.EulerY, lfbf.EulerY, data.hz)
        
        lfbf.phase =  self.lf_phase
        rfbf.phase = self.rf_phase
        
        #Determining the load attributes           
        self.load = ldcalc.load_bal_imp(rfbf.phase, lfbf.phase, hipbf.AccX, hipbf.AccY, hipbf.AccZ, data.mass, data.extra_mass)
        
        #Contralateral Hip Drop attributes
        self.nr_contra = cmed.cont_rot_CME(hipbf.EulerY, rfbf.phase, [2,0], prep.Calc_Euler(data.hipdataset.neutral_q)[1], data.cme_dict['hipdropr'])
        self.nl_contra = cmed.cont_rot_CME(hipbf.EulerY, lfbf.phase, [1,0], prep.Calc_Euler(data.hipdataset.neutral_q)[1], data.cme_dict['hipdropl'])
        self.cont_contra = cmed.cont_rot_CME(hipbf.EulerY, lfbf.phase, [0,1,2,3,4,5], prep.Calc_Euler(data.hipdataset.neutral_q)[1], data.cme_dict['hipdropl'])
        #Pronation/Supination attributes
        self.nr_prosup = cmed.cont_rot_CME(rfbf.EulerX, rfbf.phase, [2,0], prep.Calc_Euler(data.rfdataset.neutral_q)[0], data.cme_dict['prosupr'])
        self.nl_prosup = cmed.cont_rot_CME(lfbf.EulerX, lfbf.phase, [1,0], prep.Calc_Euler(data.lfdataset.neutral_q)[0], data.cme_dict['prosupl'])
        self.contr_prosup = cmed.cont_rot_CME(rfbf.EulerX, rfbf.phase, [0,1,2,3,4,5], prep.Calc_Euler(data.rfdataset.neutral_q)[0], data.cme_dict['prosupr'])
        self.contl_prosup = cmed.cont_rot_CME(lfbf.EulerX, lfbf.phase, [0,1,2,3,4,5], prep.Calc_Euler(data.lfdataset.neutral_q)[0], data.cme_dict['prosupl'])
        #Lateral Hip Rotation attributes
        self.nr_hiprot = cmed.cont_rot_CME(hipbf.EulerZ, rfbf.phase, [2], prep.Calc_Euler(data.hipdataset.neutral_q)[2], data.cme_dict['hiprotr'])
        self.nrdbl_hiprot = cmed.cont_rot_CME(hipbf.EulerZ, rfbf.phase, [0], prep.Calc_Euler(data.hipdataset.neutral_q)[2], data.cme_dict['hiprotd'])
        self.nl_hiprot = cmed.cont_rot_CME(hipbf.EulerZ, lfbf.phase, [1], prep.Calc_Euler(data.hipdataset.neutral_q)[2], data.cme_dict['hiprotl'])
        self.nldbl_hiprot = cmed.cont_rot_CME(hipbf.EulerZ, rfbf.phase, [0], prep.Calc_Euler(data.hipdataset.neutral_q)[2], data.cme_dict['hiprotd'])
        self.cont_hiprot = cmed.cont_rot_CME(hipbf.EulerZ, lfbf.phase, [0,1,2,3,4,5], prep.Calc_Euler(data.hipdataset.neutral_q)[2], data.cme_dict['hiprotd'])
        #Landing Time attributes
        self.n_landtime = impact.sync_time(rfbf.phase, lfbf.phase, data.hz, data.cme_dict_imp['landtime'])
        #Landing Pattern attributes
        if len(self.n_landtime) != 0:
            self.n_landpattern = impact.landing_pattern(rfbf.EulerY, lfbf.EulerY, self.n_landtime[:,0], self.n_landtime[:,1], data.cme_dict_imp['landpattern'])
        else:
            self.n_landpattern = np.array([])
        
        self.timestamp = data.timestamp
