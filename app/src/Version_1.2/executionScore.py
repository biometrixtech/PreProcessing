# -*- coding: utf-8 -*-
"""
Created on Fri Jun 24 09:47:48 2016

@author: Ankur
"""

import numpy as np

"""
#############################################INPUT/OUTPUT####################################################
Function: weight_load
Inputs: normalized scores for, contralateral hip drop (right and left feet); pronation/supination (right and
        left feet); lateral hip rotation (right and left feet, both single and double); landing time; landing
        pattern; load array (output of the load_bal_imp function)
Outputs: THE EXECUTION SCORE!
#############################################################################################################
"""

def weight_load(nrf_contra, nlf_contra, nrf_prosup, nlf_prosup, nrf_hiprot, nlf_hiprot, nrfdbl_hiprot, nlfdbl_hiprot, nlndtme, nlndptn, load):
    
    #ASSIGNING THE POINTS TO EACH CME
    #Contralateral Hip Drop
    lambda_contra = 10.0
    #Pronation/Supination
    lambda_prosup = 15.0
    #Lateral Hip Drop
    lambda_hiprot = 5.0
    #Landing Time
    lambda_landtime = 2.5
    #Landing Pattern
    lambda_landpattern = 2.5
  
    #DETERMINING THE LOAD ON THE RIGHT AND LEFT FEET FOR EACH CME    
    #Contralateral Hip Drop   
    pos = loadrf_sum = loadlf_sum = br = bl = 0
    #Right foot
    for i in range(len(nrf_contra)):
        a = b = 0
        pos = int(nrf_contra[i,0])
        if load[pos,2] == 0 or load[pos,2] == 2:
            a = nrf_contra[i,1] * load[pos,0] * lambda_contra
            b = load[pos,0]
            br = br + a
            loadrf_sum = loadrf_sum + b
    #Left foot
    for i in range(len(nlf_contra)):
        a = b = 0
        pos = int(nlf_contra[i,0])
        if load[pos,3] == 0 or load[pos,3] == 1:
            a = nlf_contra[i,1]*load[pos,1] * lambda_contra
            b = load[pos,1]
            bl = bl + a
            loadlf_sum = loadlf_sum + b
    #P_contra       
    pcontra = (br/(loadrf_sum + loadlf_sum)) + (bl/(loadrf_sum + loadlf_sum))
    
    #Pronation/Supination    
    pos = loadrf_sum = loadlf_sum = br = bl = 0
    #Right foot
    for i in range(len(nrf_prosup)):
        a = b = 0
        pos = int(nrf_prosup[i,0])
        if load[pos,2] == 0 or load[pos,2] == 2:
            a = nrf_prosup[i,1] * load[pos,0] * lambda_prosup
            b = load[pos,0]
            br = br + a
            loadrf_sum = loadrf_sum + b
    #Left foot
    for i in range(len(nlf_prosup)):
        a = b = 0
        pos = int(nlf_prosup[i,0])
        if load[pos,3] == 0 or load[pos,3] == 1:
            a = nlf_prosup[i,1]*load[pos,1] * lambda_prosup
            b = load[pos,1]
            bl = bl + a
            loadlf_sum = loadlf_sum + b
    #P_pro/sup       
    pprosup = (br/(loadrf_sum + loadlf_sum)) + (bl/(loadrf_sum + loadlf_sum))
    
    #Lateral Hip Rotation
    pos = loadrf_sum = loadlf_sum = br = bl = loadrfdbl_sum = loadlfdbl_sum = brdbl = bldbl = 0
    #Right foot (Single and double)
    for i in range(len(nrf_hiprot)):
        a = b = 0
        pos = int(nrf_hiprot[i,0])
        if load[pos,2] == 2:
            a = nrf_hiprot[i,1] * load[pos,0] * lambda_hiprot
            b = load[pos,0]
            br = br + a
            loadrf_sum = loadrf_sum + b
    for i in range(len(nrfdbl_hiprot)):
        a = b = 0
        pos = int(nrfdbl_hiprot[i,0])
        if load[pos,2] == 0:
            a = nrfdbl_hiprot[i,1] * load[pos,0] * lambda_hiprot
            b = load[pos,0]
            brdbl = brdbl + a
            loadrfdbl_sum = loadrfdbl_sum + b
    #Left foot (Single and Double)
    for i in range(len(nlf_hiprot)):
        a = b = 0
        pos = int(nlf_hiprot[i,0])
        if load[pos,3] == 1:
            a = nlf_hiprot[i,1]*load[pos,1] * lambda_hiprot
            b = load[pos,1]
            bl = bl + a
            loadlf_sum = loadlf_sum + b
    for i in range(len(nlfdbl_hiprot)):
        a = b = 0
        pos = int(nlfdbl_hiprot[i,0])
        if load[pos,3] == 0:
            a = nlfdbl_hiprot[i,1]*load[pos,1] * lambda_hiprot
            b = load[pos,1]
            bldbl = bldbl + a
            loadlfdbl_sum = loadlfdbl_sum + b
    #P_hiprot
    phiprot = (br/(loadrf_sum + loadlf_sum + loadrfdbl_sum + loadlfdbl_sum)) + (bl/(loadrf_sum + loadlf_sum  + loadrfdbl_sum + loadlfdbl_sum)) + (brdbl/(loadrf_sum + loadlf_sum + loadrfdbl_sum + loadlfdbl_sum)) + (bldbl/(loadrf_sum + loadlf_sum  + loadrfdbl_sum + loadlfdbl_sum))
        
    #Impact CMEs
    if len(nlndtme) != 0:
        #Landing Time (Double leg only)
        pos = loadrfdbl_sum = loadlfdbl_sum = brdbl = bldbl = total_loadrfdbl_sum = total_loadlfdbl_sum = 0
        #Right foot
        for i in range(len(nlndtme)):
            pos = int(nlndtme[i,0])
            for j,k in zip(load[pos:,0], load[pos:,2]):
                if k == 4:
                    loadrfdbl_sum = loadrfdbl_sum + j
                elif k != 4:
                    break
            brdbl = loadrfdbl_sum * nlndtme[i,2] * lambda_landtime + brdbl
            total_loadrfdbl_sum = loadrfdbl_sum + total_loadrfdbl_sum
        #Left foot
        for i in range(len(nlndtme)):
            pos = int(nlndtme[i,1])
            for j,k in zip(load[pos:,1], load[pos:,3]):
                if k == 4:
                    loadlfdbl_sum = loadlfdbl_sum + j
                elif k != 4:
                    break
            bldbl = loadlfdbl_sum * nlndtme[i,3] * lambda_landtime + bldbl
            total_loadlfdbl_sum = total_loadlfdbl_sum + loadlfdbl_sum
        #P_landtime
        plandtime = (brdbl/(total_loadrfdbl_sum + total_loadlfdbl_sum)) + (bldbl/(total_loadrfdbl_sum + total_loadlfdbl_sum))
    
        #Landing Pattern (Double only)
        pos = loadrfdbl_sum = loadlfdbl_sum = brdbl = bldbl = total_loadrfdbl_sum = total_loadlfdbl_sum = 0
        #Right foot
        for i in range(len(nlndptn)):
            pos = int(nlndptn[i,0])
            for j,k in zip(load[pos:,0], load[pos:,2]):
                if k == 4:
                    loadrfdbl_sum = loadrfdbl_sum + j
                elif k != 4:
                    break
            brdbl = loadrfdbl_sum * nlndptn[i,2] + brdbl
            total_loadrfdbl_sum = loadrfdbl_sum + total_loadrfdbl_sum
        #Left foot
        for i in range(len(nlndptn)):
            pos = int(nlndptn[i,1])
            for j,k in zip(load[pos:,1], load[pos:,3]):
                if k == 4:
                    loadlfdbl_sum = loadlfdbl_sum + j
                elif k != 4:
                    break
            bldbl = loadlfdbl_sum * nlndptn[i,3] + bldbl
            total_loadlfdbl_sum = total_loadlfdbl_sum + loadlfdbl_sum
        #P_landpattern
        plandpattern = (brdbl/(total_loadrfdbl_sum + total_loadlfdbl_sum)) + (bldbl/(total_loadrfdbl_sum + total_loadlfdbl_sum))
    else:
        plandtime = plandpattern = 0
        
    #DETERMINING THE EXECUTION SCORE
    s = (pcontra + pprosup + phiprot + plandtime + plandpattern)/(lambda_contra + lambda_prosup + lambda_hiprot + lambda_landtime + lambda_landpattern)    
    
    #print pcontra, pprosup, phiprot, plandtime, plandpattern
    
    return s*100
    
if __name__ == "__main__":
    
    import pandas as pd
    from impact_phase import impact_phase
    from phase_exploration import *
    import CME_Detect as cmed
    import Data_Processing as prep
    from load_calc import load_bal_imp
    from impact_cme import *
    
    rpath = 'C:\\Users\\Ankur\\python\\Biometrix\\Data analysis\\data exploration\\data files\\Subject5\\Subject5_rfdatabody_LESS.csv'
    #rpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_rfdatabody_snglsquat_set1.csv'
    lpath = 'C:\\Users\\Ankur\\python\\Biometrix\\Data analysis\\data exploration\\data files\\Subject5\\Subject5_lfdatabody_LESS.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_lfdatabody_snglsquat_set1.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Stomp\Lheel_Gabby_stomp_set1.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\ChangeDirection\Lheel_Gabby_changedirection_set1.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Jump\Lheel_Gabby_jumping_explosive_set2.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Walking\Lheel_Gabby_walking_heeltoe_set1.csv'
    hpath = 'C:\\Users\\Ankur\\python\\Biometrix\\Data analysis\\data exploration\\data files\\Subject5\\Subject5_hipdatabody_LESS.csv'
    #hpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_hipdatabody_snglsquat_set1.csv'

    rdata = pd.read_csv(rpath)
    ldata = pd.read_csv(lpath)
    hdata = pd.read_csv(hpath)
    
    #print len(rdata), len(ldata)
    
    #acc = ['AccX', 'AccY', 'AccZ']
    #rdata = rdata[acc]
    #ldata = ldata[acc]
    #hdata = hdata[acc]
    
    sampl_rate = 250
    
    comp = 'AccZ'
    ptch = 'EulerY'
    racc = rdata[comp].values
    lacc = ldata[comp].values #input AccZ values!
    rpitch = rdata[ptch].values
    lpitch = ldata[ptch].values
    ph = Body_Phase(racc, lacc, rpitch, lpitch,  sampl_rate)
    
    #ph = pe_v1.Body_Phase(rdata['AccZ'], ldata['AccZ'], sampl_rate) #array containing the full body moving decisions
    rdata['Phase'] = ph
    ldata['Phase'] = ph
    hdata['Phase'] = ph
        
    lf_impact = impact_phase(ldata['AccZ'], sampl_rate)
    rf_impact = impact_phase(rdata['AccZ'], sampl_rate)
    rdata['Impact'] = rf_impact
    ldata['Impact'] = lf_impact
        
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
    nr_contra = cmed.cont_rot_CME(hdata['EulerY'], rdata['Phase'], [2,0], neutral_eulh[1], cme_dict['hipdropr'])
    nl_contra = cmed.cont_rot_CME(hdata['EulerY'], rdata['Phase'], [1,0], neutral_eulh[1], cme_dict['hipdropl'])
    #Pronation/Supination
    nr_prosup = cmed.cont_rot_CME(rdata['EulerX'], rdata['Phase'], [2,0], neutral_eulr[0], cme_dict['prosupr'])
    nl_prosup = cmed.cont_rot_CME(ldata['EulerX'], rdata['Phase'], [1,0], neutral_eull[0], cme_dict['prosupl'])
    #Lateral Hip Rotation
    nr_hiprot = cmed.cont_rot_CME(hdata['EulerZ'], rdata['Phase'], [2], neutral_eulh[2], cme_dict['hiprotr'])
    nrdbl_hiprot = cmed.cont_rot_CME(hdata['EulerZ'], rdata['Phase'], [0], neutral_eulh[2], cme_dict['hiprotd'])
    nl_hiprot = cmed.cont_rot_CME(hdata['EulerZ'], rdata['Phase'], [1], neutral_eulh[2], cme_dict['hiprotl'])
    nldbl_hiprot = cmed.cont_rot_CME(hdata['EulerZ'], rdata['Phase'], [0], neutral_eulh[2], cme_dict['hiprotd'])
    
    #Landing Time
    n_landtime = sync_time(rdata['Impact'], ldata['Impact'], sampl_rate, cme_dict_imp['landtime'])
    #Landing Pattern
    if len(n_landtime) != 0:
        n_landpattern = landing_pattern(rdata['EulerY'], ldata['EulerY'], n_landtime[:,0], n_landtime[:,1], cme_dict_imp['landpattern'])
    else:
        n_landpattern = np.array([])
            
    ldd = load_bal_imp(rdata, ldata, hdata, mass, extra_mass)

    score = weight_load(nr_contra, nl_contra, nr_prosup, nl_prosup, nr_hiprot, nl_hiprot, nrdbl_hiprot, nldbl_hiprot,n_landtime, n_landpattern, ldd)

    #the_score = exec_score_mechanism(rdata, ldata, hdata, mass, extra_mass, sampl_rate)  
    
    print score
