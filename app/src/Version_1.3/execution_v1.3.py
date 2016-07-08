# -*- coding: utf-8 -*-
"""
Created on Thu Jul  7 12:34:12 2016

@author: Brian
"""

import numpy as np
import pandas as pd
import phaseDetection as phase
import coordinateFrameTransformation as prep
import anatomicalCalibration as anatom
import executionScore as exec_score
import balanceCME as cmed
import impactCME as impact
import loadCalc as ldcalc

"""
#############################################INPUT/OUTPUT####################################################   
Inputs: data object that must contain raw accel, gyr, mag, and quat values for hip, left heel, and right heel
sensors; (9) quaternions from the anatomical fix module representing 2 different transforms and 1 "neutral"
orientation per sensor
Outputs: hipbf, lfbf, rfbf (sensor-body frames with phases appended; 3 objects); raw dataframes with gravity
removed; execution score (0-100)
#############################################################################################################
"""

if __name__ == "__main__":
    root = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\' #root path for data folder...reset to your own path
    exercise = "LESS" #Look at file name to find equiv for single squat, double, and LESS
    subject = "Subject3" #Subject you want to look at
    num = 0 #which set you want to evaluate
    sens_loc = ["hips", "rightheel", "leftheel"] #list holding sensor location
    hz = 250 #smapling rate
    
    #concatenated paths for all sensors
    pathip = root + subject + '_' + sens_loc[0] + '_42116_' + exercise + '.csv'
    pathrf = root + subject + '_' + sens_loc[1] + '_42116_' + exercise + '.csv'
    pathlf = root + subject + '_' + sens_loc[2] + '_42116_' + exercise + '.csv'
    
    #output path...I just keep it in the same folder with a generic name...you could always run through all of them and place in new folder.
    #Might be worth it instead of having to run this everytime you change the dataset
    outhipp = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\hipdatabody.csv'
    outrfp = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\rfdatabody.csv'
    outlfp = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\lfdatabody.csv'    
    
    #read all datasets in
    hip = pd.read_csv(pathip)
    lfoot = pd.read_csv(pathlf)
    rfoot = pd.read_csv(pathrf)
    
    ###Reference Quaternions from Anatomical Fix module
    #aligning along foot axis
    hana_yaw_offset = anatom.hfx_q   
    lana_yaw_offset = anatom.yaw_alignl_q   
    rana_yaw_offset = anatom.yaw_alignr_q
    
    #correcting sensor-body frame for sensor placement
    hsens_offset = anatom.alignh_q  
    lsens_offset = anatom.alignl_q  
    rsens_offset = anatom.alignr_q   
    
    #set body weight and any extra mass variables
    mass = 75
    extra_mass = 0
    
    #make sure all datasets are off same length
    if len(hip) != len(lfoot) or len(hip) != len(rfoot):
        lens = [len(hip), len(lfoot), len(rfoot)] #list of dataset lengths
        lenmin = np.min(lens) #find min length of datasets
        #find diff between min and dataset size. If no diff do nothing, if there is take off end of dataset        
        hdiff = len(hip) - lenmin
        if hdiff > 0:
            hip = hip[:-hdiff]
        ldiff = len(lfoot) - lenmin
        if ldiff > 0:
            lfoot = lfoot[:-ldiff]
        rdiff = len(rfoot) - lenmin
        if rdiff > 0:
            rfoot = rfoot[:-rdiff]
    
    hipbf, rfbf, lfbf, hipfinal, rffinal, lffinal = [np.zeros((1,16)) for i in range(6)]
    hipsf, rfsf, lfsf = [np.empty((1,9)) for i in range(3)]
    iters = len(hip) #find how many data vectors

    for i in range(len(lfoot)):
        #FRAME TRANSFORM
        #frame transforms for all sensors (returns sensor frame data as well but not very relevant)
        hq0 = np.matrix([hip.ix[i,'qW_raw'], hip.ix[i,'qX_raw'], hip.ix[i,'qY_raw'], hip.ix[i,'qZ_raw']]) #t=0 quaternion
        hyaw_fix = prep.yaw_offset(hq0) #uses yaw offset function above to compute body frame quaternion
        hyfix_c = prep.QuatConj(hyaw_fix) #uses quaternion conjugate function to return body frame quaternion transform
        hyfix_c = prep.QuatProd(prep.QuatConj(hana_yaw_offset), hyfix_c) #align reference frame straight forward      
        
        lq0 = np.matrix([lfoot.ix[i,'qW_raw'], lfoot.ix[i,'qX_raw'], lfoot.ix[i,'qY_raw'], lfoot.ix[i,'qZ_raw']]) #t=0 quaternion
        lyaw_fix = prep.yaw_offset(lq0) #uses yaw offset function above to compute body frame quaternion
        lyfix_c = prep.QuatConj(lyaw_fix) #uses quaternion conjugate function to return body frame quaternion transform
        lyfix_c = prep.QuatProd(prep.QuatConj(lana_yaw_offset), lyfix_c) #align reference frame flush with left foot
        
        rq0 = np.matrix([rfoot.ix[i,'qW_raw'], rfoot.ix[i,'qX_raw'], rfoot.ix[i,'qY_raw'], rfoot.ix[i,'qZ_raw']]) #t=0 quaternion
        ryaw_fix = prep.yaw_offset(rq0) #uses yaw offset function above to compute body frame quaternion
        ryfix_c = prep.QuatConj(ryaw_fix) #uses quaternion conjugate function to return body frame quaternion transform
        ryfix_c = prep.QuatProd(prep.QuatConj(rana_yaw_offset), ryfix_c) #align reference frame flush with right foot
        
        #frame transforms for all sensors (returns sensor frame data as well but not very relevant)
        hipbod, hipsen = prep.FrameTransform(hip.ix[i,:], hyfix_c, hsens_offset)
        lfbod, lfsen = prep.FrameTransform(lfoot.ix[i,:], lyfix_c, lsens_offset)
        rfbod, rfsen = prep.FrameTransform(rfoot.ix[i,:], ryfix_c, rsens_offset)
        
        hipbf = np.vstack([hipbf, hipbod[0,:]]) #body frame hip
        hipsf = np.vstack([hipsf, hipsen[0,:]]) #sensor frame hip
        lfbf = np.vstack([lfbf, lfbod[0,:]]) #body frame left
        lfsf = np.vstack([lfsf, lfsen[0,:]]) #sensor frame left
        rfbf = np.vstack([rfbf, rfbod[0,:]]) #body frame right
        rfsf = np.vstack([rfsf, rfsen[0,:]]) #sensor frame right
        if i == 0:
            hipbf = np.delete(hipbf, 0, axis=0)
            lfbf = np.delete(lfbf, 0, axis=0)
            rfbf = np.delete(rfbf, 0, axis=0)
    
    #create dataframes of adjusted data
    hipbf = pd.DataFrame(hipbf, columns=["qW", "qX", "qY", "qZ", "EulerX", "EulerY", "EulerZ", "AccX", "AccY", "AccZ", "gyrX", "gyrY", "gyrZ", "magX", "magY", "magZ"])
    lfbf = pd.DataFrame(lfbf, columns=["qW", "qX", "qY", "qZ", "EulerX", "EulerY", "EulerZ", "AccX", "AccY", "AccZ", "gyrX", "gyrY", "gyrZ", "magX", "magY", "magZ"])
    rfbf = pd.DataFrame(rfbf, columns=["qW", "qX", "qY", "qZ", "EulerX", "EulerY", "EulerZ", "AccX", "AccY", "AccZ", "gyrX", "gyrY", "gyrZ", "magX", "magY", "magZ"])
    
    ##PHASE DETECTION
    lf_phase, rf_phase = phase.combine_phase(lfbf['AccZ'].values, rfbf['AccZ'].values, rfbf['EulerY'].values, lfbf['EulerY'].values, hz)
    
    lfbf['Phase'] =  lf_phase
    rfbf['Phase'] = rf_phase
    
    #Mass and extra mass to test the load function    
    mass = 75
    extra_mass = 0
    
    #Balance CME thresdholds
    cme_dict = {'prosupl':[-1, -4, 2, 8], 'hiprotl':[-1, -4, 2, 8], 'hipdropl':[-1, -4, 2, 8],
                'prosupr':[-1, -4, 2, 8], 'hiprotr':[-1, -4, 2, 8], 'hipdropr':[-1, -4, 2, 8],
                'hiprotd':[-1, -4, 2, 8]}
    #Impact CME thresholds
    cme_dict_imp = {'landtime':[0.2, 0.25], 'landpattern':[12, -50]}

    neutral_h = np.matrix([0.582,0.813,0,0]) # will come from anatomical_fix module as such anatom.neutral_hq
    neutral_l = np.matrix([0.582,0.813,0,0]) # will come from anatomical_fix module as such anatom.neutral_lq
    neutral_r = np.matrix([0.582,0.813,0,0]) # will come from anatomical_fix module as such anatom.neutral_rq
    #get "neutral" euler angles from quaternions    
    neutral_eulh = prep.Calc_Euler(neutral_h)
    neutral_eull = prep.Calc_Euler(neutral_l)
    neutral_eulr = prep.Calc_Euler(neutral_r)
    
    #Contralateral Hip Drop
    nr_contra = cmed.cont_rot_CME(hipbf['EulerY'], rfbf['Phase'], [2,0], neutral_eulh[1], cme_dict['hipdropr'])
    nl_contra = cmed.cont_rot_CME(hipbf['EulerY'], lfbf['Phase'], [1,0], neutral_eulh[1], cme_dict['hipdropl'])
    #Pronation/Supination
    nr_prosup = cmed.cont_rot_CME(rfbf['EulerX'], rfbf['Phase'], [2,0], neutral_eulr[0], cme_dict['prosupr'])
    nl_prosup = cmed.cont_rot_CME(lfbf['EulerX'], lfbf['Phase'], [1,0], neutral_eull[0], cme_dict['prosupl'])
    #Lateral Hip Rotation
    nr_hiprot = cmed.cont_rot_CME(hipbf['EulerZ'], rfbf['Phase'], [2], neutral_eulh[2], cme_dict['hiprotr'])
    nrdbl_hiprot = cmed.cont_rot_CME(hipbf['EulerZ'], rfbf['Phase'], [0], neutral_eulh[2], cme_dict['hiprotd'])
    nl_hiprot = cmed.cont_rot_CME(hipbf['EulerZ'], lfbf['Phase'], [1], neutral_eulh[2], cme_dict['hiprotl'])
    nldbl_hiprot = cmed.cont_rot_CME(hipbf['EulerZ'], rfbf['Phase'], [0], neutral_eulh[2], cme_dict['hiprotd'])
    
    #Landing Time
    n_landtime = impact.sync_time(rfbf['Phase'], lfbf['Phase'], hz, cme_dict_imp['landtime'])
    #Landing Pattern
    if len(n_landtime) != 0:
        n_landpattern = impact.landing_pattern(rfbf['EulerY'], lfbf['EulerY'], n_landtime[:,0], n_landtime[:,1], cme_dict_imp['landpattern'])
    else:
        n_landpattern = np.array([])
        
    #Determining the load            
    load = ldcalc.load_bal_imp(rfbf, lfbf, hipbf, mass, extra_mass)

    #Execution Score
    score = exec_score.weight_load(nr_contra, nl_contra, nr_prosup, nl_prosup, nr_hiprot, nl_hiprot, nrdbl_hiprot, nldbl_hiprot, n_landtime, n_landpattern, load)
