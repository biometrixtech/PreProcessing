# -*- coding: utf-8 -*-
"""
Created on Thu Jun  9 14:48:17 2016

@author: Brian
"""

import numpy as np
import pandas as pd
import phase_exploration as phase
import Data_Processing as prep
import peak_det as peak

"""
#############################################INPUT/OUTPUT####################################################   
Inputs: data object that must contain raw accel, gyr, mag, and quat values for hip, left heel, and right heel
sensors.

Outputs: hipbf, lfbf, rfbf (body frames with phases appended; 3 objects); min AND max arrays for each sensor
and euler angle (18 total objects; 3 sensors x 3 Euler Angles X 2 min/max arrays each)
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
    
#    #filter out non-set data
#    hip = hip[hip['set'] == num]
#    lfoot = lfoot[lfoot['set'] == num]
#    rfoot = rfoot[rfoot['set'] == num]
    
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
    hyaw_fix = prep.yaw_offset(hq0) #uses yaw offset function above to compute yaw offset quaternion
    hyfix_c = prep.QuatConj(hyaw_fix) #uses quaternion conjugate function to return conjugate of yaw offset
    
    lq0 = np.matrix([lfoot.ix[0,'qW_raw'], lfoot.ix[0,'qX_raw'], lfoot.ix[0,'qY_raw'], lfoot.ix[0,'qZ_raw']]) #t=0 quaternion
    lyaw_fix = prep.yaw_offset(lq0) #uses yaw offset function above to compute yaw offset quaternion
    lyfix_c = prep.QuatConj(lyaw_fix) #uses quaternion conjugate function to return conjugate of yaw offset
        
    rq0 = np.matrix([rfoot.ix[0,'qW_raw'], rfoot.ix[0,'qX_raw'], rfoot.ix[0,'qY_raw'], rfoot.ix[0,'qZ_raw']]) #t=0 quaternion
    ryaw_fix = prep.yaw_offset(rq0) #uses yaw offset function above to compute yaw offset quaternion
    ryfix_c = prep.QuatConj(ryaw_fix) #uses quaternion conjugate function to return conjugate of yaw offset
    
    #Set peak detection parameters and initiate objects    
    delta = .1
    rxmaxtab, rymaxtab, rzmaxtab, lxmaxtab, lymaxtab, lzmaxtab, hxmaxtab, hymaxtab, hzmaxtab = [[] for i in range(9)]
    rxmintab, rymintab, rzmintab, lxmintab, lymintab, lzmintab, hxmintab, hymintab, hzmintab = [[] for i in range(9)]
    rxmn, rymn, rzmn, lxmn, lymn, lzmn, hxmn, hymn, hzmn = [np.Inf for i in range(9)] # initiate min, max value variable
    rxmx, rymx, rzmx, lxmx, lymx, lzmx, hxmx, hymx, hzmx = [-np.Inf for i in range(9)]
    rxmnpos, rymnpos, rzmnpos, lxmnpos, lymnpos, lzmnpos, hxmnpos, hymnpos, hzmnpos = [np.NaN for i in range(9)] #initiate min, max index variable
    rxmxpos, rymxpos, rzmxpos, lxmxpos, lymxpos, lzmxpos, hxmxpos, hymxpos, hzmxpos = [np.NaN for i in range(9)]
    
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
        hipbod, hipsen = prep.FrameTransform(hip.ix[i,:], hyfix_c)
        lfbod, lfsen = prep.FrameTransform(lfoot.ix[i,:], lyfix_c)
        rfbod, rfsen = prep.FrameTransform(rfoot.ix[i,:], ryfix_c)
        
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
            movhold.append(phase.Move(stdaZ[-1], w, new_u, new_std))
            gmovhold.append(phase.Grad_Move(uaZ[-1], w, gnew_u, gnew_std))
        
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
            rmovh.append(phase.Move(rstdaZ[-1], w, rnew_u, rnew_std))
            rgmovh.append(phase.Grad_Move(ruaZ[-1], w, rgnew_u, rgnew_std))
        
        #PEAK DETECTION- run for each sensor and each euler rotation (9 times)
        rxmaxtab, rxmintab, rxmx, rxmn, rxmxpos, rxmnpos = peak.peak_det(rfbod[0,4], i, .1, rxmx, rxmn, rxmxpos, rxmnpos, rxmaxtab, rxmintab)
        rymaxtab, rymintab, rymx, rymn, rymxpos, rymnpos = peak.peak_det(rfbod[0,5], i, .1, rymx, rymn, rymxpos, rymnpos, rymaxtab, rymintab)
        rzmaxtab, rzmintab, rzmx, rzmn, rzmxpos, rzmnpos = peak.peak_det(rfbod[0,6], i, .1, rzmx, rzmn, rzmxpos, rzmnpos, rzmaxtab, rzmintab)

        lxmaxtab, lxmintab, lxmx, lxmn, lxmxpos, lxmnpos = peak.peak_det(lfbod[0,4], i, .1, lxmx, lxmn, lxmxpos, lxmnpos, lxmaxtab, lxmintab)
        lymaxtab, lymintab, lymx, lymn, lymxpos, lymnpos = peak.peak_det(lfbod[0,5], i, .1, lymx, lymn, lymxpos, lymnpos, lymaxtab, lymintab)
        lzmaxtab, lzmintab, lzmx, lzmn, lzmxpos, lzmnpos = peak.peak_det(lfbod[0,6], i, .1, lzmx, lzmn, lzmxpos, lzmnpos, lzmaxtab, lzmintab)

        hxmaxtab, hxmintab, hxmx, hxmn, hxmxpos, hxmnpos = peak.peak_det(hipbod[0,4], i, .1, hxmx, hxmn, hxmxpos, hxmnpos, hxmaxtab, hxmintab)
        hymaxtab, hymintab, hymx, hymn, hymxpos, hymnpos = peak.peak_det(hipbod[0,5], i, .1, hymx, hymn, hymxpos, hymnpos, hymaxtab, hymintab)
        hzmaxtab, hzmintab, hzmx, hzmn, hzmxpos, hzmnpos = peak.peak_det(hipbod[0,6], i, .1, hzmx, hzmn, hzmxpos, hzmnpos, hzmaxtab, hzmintab)
    
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
    
    #add decisions to body frame data
    hipbf = pd.DataFrame(hipbf)
    lfbf = pd.DataFrame(hipbf)
    rfbf = pd.DataFrame(hipbf)
    
    hipbf['Phase'] = lfbf['Phase'] = rfbf['Phase'] = body
            