# -*- coding: utf-8 -*-
"""
Created on Thu Jun  9 14:48:17 2016

@author: Brian
"""

import numpy as np
import pandas as pd
import phase_exploration as phase
import coordinateFrameTransformation as prep
import impact_phase as impact
import anatomicalCalibration as anatom
import executionScore as exec_score
import balanceCME as cmed
from impactCME import *
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
    
    #yaw offsets for various sensors
    hq0 = np.matrix([hip.ix[0,'qW_raw'], hip.ix[0,'qX_raw'], hip.ix[0,'qY_raw'], hip.ix[0,'qZ_raw']]) #t=0 quaternion
    hyaw_fix = prep.yaw_offset(hq0) #uses yaw offset function above to compute initial heading quaternion
    init_head_h = prep.QuatConj(hyaw_fix) #store quaternion with conjugate of intial heading
    
    lq0 = np.matrix([lfoot.ix[0,'qW_raw'], lfoot.ix[0,'qX_raw'], lfoot.ix[0,'qY_raw'], lfoot.ix[0,'qZ_raw']]) #t=0 quaternion
    lyaw_fix = prep.yaw_offset(lq0) #uses yaw offset function above to compute initial heading quaternion
    init_head_l = prep.QuatConj(lyaw_fix) #store quaternion with conjugate of intial heading
     
    rq0 = np.matrix([rfoot.ix[0,'qW_raw'], rfoot.ix[0,'qX_raw'], rfoot.ix[0,'qY_raw'], rfoot.ix[0,'qZ_raw']]) #t=0 quaternion
    ryaw_fix = prep.yaw_offset(rq0) #uses yaw offset function above to compute initial heading quaternion
    init_head_r = prep.QuatConj(ryaw_fix) #store quaternion with conjugate of intial heading
    
    #set rolling mean windows
    w = int(hz*.08) #set rolling mean windows
    edge = int(.2*hz)
    #initiate lists to hold move decisions
    movhold = [0]*int(1.5*w)
    gmovhold = [0]*int(1.5*w)
    rmovh = [0]*int(1.5*w)
    rgmovh = [0]*int(1.5*w)
    for i in range(len(lfoot)):
        #FRAME TRANSFORM
        #frame transforms for all sensors (returns sensor frame data as well but not very relevant)
        hq0 = np.matrix([hip.ix[i,'qW_raw'], hip.ix[i,'qX_raw'], hip.ix[i,'qY_raw'], hip.ix[i,'qZ_raw']]) #t=0 quaternion
        hyaw_fix = prep.yaw_offset(hq0) #uses yaw offset function above to compute body frame quaternion
        hyfix_c = prep.QuatConj(hyaw_fix) #uses quaternion conjugate function to return body frame quaternion transform
        hyfix_c = prep.QuatProd(prep.QuatConj(hana_yaw_offset), hyfix_c) #align reference frame straight forward
        head_h = prep.QuatProd(init_head_h, hyaw_fix) #heading quaternion (yaw difference from t=0)       
        
        lq0 = np.matrix([lfoot.ix[i,'qW_raw'], lfoot.ix[i,'qX_raw'], lfoot.ix[i,'qY_raw'], lfoot.ix[i,'qZ_raw']]) #t=0 quaternion
        lyaw_fix = prep.yaw_offset(lq0) #uses yaw offset function above to compute body frame quaternion
        lyfix_c = prep.QuatConj(lyaw_fix) #uses quaternion conjugate function to return body frame quaternion transform
        lyfix_c = prep.QuatProd(prep.QuatConj(lana_yaw_offset), lyfix_c) #align reference frame flush with left foot
        head_l = prep.QuatProd(init_head_l, lyaw_fix) #heading quaternion (yaw difference from t=0)
        
        rq0 = np.matrix([rfoot.ix[i,'qW_raw'], rfoot.ix[i,'qX_raw'], rfoot.ix[i,'qY_raw'], rfoot.ix[i,'qZ_raw']]) #t=0 quaternion
        ryaw_fix = prep.yaw_offset(rq0) #uses yaw offset function above to compute body frame quaternion
        ryfix_c = prep.QuatConj(ryaw_fix) #uses quaternion conjugate function to return body frame quaternion transform
        ryfix_c = prep.QuatProd(prep.QuatConj(rana_yaw_offset), ryfix_c) #align reference frame flush with right foot
        head_r = prep.QuatProd(init_head_r, ryaw_fix) #heading quaternion (yaw difference from t=0)
        
        #frame transforms for all sensors (returns sensor frame data as well but not very relevant)
        hipbod, hipsen = prep.FrameTransform(hip.ix[i,:], hyfix_c, head_h, hsens_offset)
        lfbod, lfsen = prep.FrameTransform(lfoot.ix[i,:], lyfix_c, head_l, lsens_offset)
        rfbod, rfsen = prep.FrameTransform(rfoot.ix[i,:], ryfix_c, head_r, rsens_offset)
        
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
        
        #PHASE DETECTION
        #set stickiness of weighted rolling means
        infl = .0001
        inflg = .00015
        if len(lfbf) >= 2*w +1:
            larr = lfbf[i-2*w+1:i+2, 9] #create array holding raw data
            uaZ = pd.rolling_mean(larr, window=w, center=True) #rolling mean of raw data
            stdaZ = pd.rolling_std(larr, window=w, center=True) #rolling std of raw data
            uaZ = uaZ[~np.isnan(uaZ)] #remove nan
            stdaZ = stdaZ[~np.isnan(stdaZ)] #remove nan
            
            if i == 2*w: #set initial means and stds for move functions
                new_u = np.mean(stdaZ)
                new_std = np.std(stdaZ)
                gnew_u = np.mean(uaZ)
                gnew_std = np.std(uaZ)
            else: #update new means and stds for move functions as points roll in
                new_u = (new_u + infl*stdaZ[-1])/(1+infl) #find new mean
                new_std = (new_std + infl*(np.sqrt((stdaZ[-1]-new_u)**2))/(1+infl)) #find new SD
                gnew_u = (gnew_u + inflg*uaZ[-1])/(1+inflg) #find new mean
                gnew_std = (gnew_std + inflg*(np.sqrt((uaZ[-1]-gnew_u)**2))/(1+inflg)) #find new SD
            
            #append move functions decisions
            movhold.append(phase.Move(stdaZ[-1], w, new_u, new_std, lfbf[i, 5]))
            gmovhold.append(phase.Grad_Move(uaZ[-1], w, gnew_u, gnew_std, lfbf[i, 5]))
        
        if len(rfbf) >= 2*w +1:
            rarr = rfbf[i-2*w+1:i+2, 9] #create array holding raw data
            ruaZ = pd.rolling_mean(rarr, window=w, center=True) #rolling mean of raw data
            rstdaZ = pd.rolling_std(rarr, window=w, center=True) #rolling std of raw data
            ruaZ = ruaZ[~np.isnan(ruaZ)] #remove nan
            rstdaZ = rstdaZ[~np.isnan(rstdaZ)] #remove nan
            
            if i == 2*w: #set initial means and stds for move functions
                rnew_u = np.mean(rstdaZ)
                rnew_std = np.std(rstdaZ)
                rgnew_u = np.mean(ruaZ)
                rgnew_std = np.std(ruaZ)
            else: #update new means and stds for move functions as points roll in
                rnew_u = (rnew_u + infl*rstdaZ[-1])/(1+infl) #find new mean
                rnew_std = (rnew_std + infl*(np.sqrt((rstdaZ[-1]-rnew_u)**2))/(1+infl)) #find new SD
                rgnew_u = (rgnew_u + inflg*ruaZ[-1])/(1+inflg) #find new mean
                rgnew_std = (rgnew_std + inflg*(np.sqrt((ruaZ[-1]-rgnew_u)**2))/(1+inflg)) #find new SD
            
            #append move functions decisions
            rmovh.append(phase.Move(rstdaZ[-1], w, rnew_u, rnew_std, rfbf[i, 5]))
            rgmovh.append(phase.Grad_Move(ruaZ[-1], w, rgnew_u, rgnew_std, rfbf[i, 5]))
    
    ###Finalize Phase Detection
    cmove = phase.Comb_Move(movhold, gmovhold)  #combine move fxn results for left foot      
    mscore = pd.rolling_mean(cmove, window=edge) #smooth results
    final = phase.Final(mscore) #mark smoothed results 
    final = phase.Fix_Edges(final, edge) #fix edges of results

    rcmove = phase.Comb_Move(rmovh, rgmovh) #combine move fxn results for rightt foot
    rmscore = pd.rolling_mean(rcmove, window=edge) #smooth results
    rfinal = phase.Final(rmscore) #mark smoothed results
    rfinal = phase.Fix_Edges(rfinal, edge) #fix edges of results
            
    body = phase.Body_Phase(rfinal, final) #create decisions on balance, one foot or no feet
    body = np.append(body, np.zeros(int(.5*w))) #add nan to match body frame data length
    
    #IMPACT PHASE DETECTION- not real time, run for each heel sensor
    limpact = impact.impact_phase(lfbf[:,9],hz)  
    rimpact = impact.impact_phase(rfbf[:,9], hz)
    
    #add decisions to body frame data
    hipbf = pd.DataFrame(hipbf)
    lfbf = pd.DataFrame(hipbf)
    rfbf = pd.DataFrame(hipbf)
    
    hipbf['Phase'] = lfbf['Phase'] = rfbf['Phase'] = body
    lfbf['Impact'] = limpact
    rfbf['Impact'] = rimpact
    
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
    nl_contra = cmed.cont_rot_CME(hipbf['EulerY'], rfbf['Phase'], [1,0], neutral_eulh[1], cme_dict['hipdropl'])
    #Pronation/Supination
    nr_prosup = cmed.cont_rot_CME(rfbf['EulerX'], rfbf['Phase'], [2,0], neutral_eulr[0], cme_dict['prosupr'])
    nl_prosup = cmed.cont_rot_CME(lfbf['EulerX'], rfbf['Phase'], [1,0], neutral_eull[0], cme_dict['prosupl'])
    #Lateral Hip Rotation
    nr_hiprot = cmed.cont_rot_CME(hipbf['EulerZ'], rfbf['Phase'], [2], neutral_eulh[2], cme_dict['hiprotr'])
    nrdbl_hiprot = cmed.cont_rot_CME(hipbf['EulerZ'], rfbf['Phase'], [0], neutral_eulh[2], cme_dict['hiprotd'])
    nl_hiprot = cmed.cont_rot_CME(hipbf['EulerZ'], rfbf['Phase'], [1], neutral_eulh[2], cme_dict['hiprotl'])
    nldbl_hiprot = cmed.cont_rot_CME(hipbf['EulerZ'], rfbf['Phase'], [0], neutral_eulh[2], cme_dict['hiprotd'])
    
    #Landing Time
    n_landtime = sync_time(rfbf['Impact'], lfbf['Impact'], hz, cme_dict_imp['landtime'])
    #Landing Pattern
    if len(n_landtime) != 0:
        n_landpattern = landing_pattern(rfbf['EulerY'], lfbf['EulerY'], n_landtime[:,0], n_landtime[:,1], cme_dict_imp['landpattern'])
    else:
        n_landpattern = np.array([])
        
    #Determining the load            
    load = ldcalc.load_bal_imp(rfbf, lfbf, hipbf, mass, extra_mass)

    #Execution Score
    score = exec_score.weight_load(nr_contra, nl_contra, nr_prosup, nl_prosup, nr_hiprot, nl_hiprot, nrdbl_hiprot, nldbl_hiprot, n_landtime, n_landpattern, load)
