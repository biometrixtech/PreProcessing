# -*- coding: utf-8 -*-
"""
Created on Fri Jun 24 09:47:48 2016

@author: Ankur
"""

import numpy as np
import peak_det as peak
import CME_Detect as cmed
#from load_calc import load_cme

def weight_load(nrf_contra, nlf_contra, nrf_prosup, nlf_prosup, nrf_hiprot, nlf_hiprot, nrfdbl_hiprot, nlfdbl_hiprot, lf_prosup_ut, lf_prosup_lt, rf_prosup_ut, rf_prosup_lt, lf_contra_ut, lf_contra_lt, rf_contra_ut, rf_contra_lt, rfdbl_hiprot_ut, rfdbl_hiprot_lt, lfdbl_hiprot_ut, lfdbl_hiprot_lt, lf_hiprot_ut, lf_hiprot_lt, rf_hiprot_ut, rf_hiprot_lt, m, em, hip):
    
    #DETERMINING THE LOAD FOR EACH CME
    
    #Under development   

def calc_norm_score(mag, a, e):
    
    n = [] 
    
    for i in mag:
        if i <= a:
            n.append(1)
        elif a < i < e:
            n.append((-(i-a)/(e - a))+1)
        elif i>= e or i == 0:
            n.append(0)
    
    return np.array(n)
        
def normalize_good(lsin_mag_prosup, rsin_mag_prosup, lsin_mag_contra, rsin_mag_contra, rdbl_mag_hiprot, ldbl_mag_hiprot, lsin_mag_hiprot, rsin_mag_hiprot):
    
    rnorm_contra = lnorm_contra = rnorm_prosup = lnorm_prosup = rnorm_hiprot = lnorm_hiprot = rdblnorm_hiprot = ldblnorm_hiprot = [] #initializing lists of all the normalized scores of "goodness"
    
    #DEFINING THE ALLOWABLE AND EXTREME THRESHOLDS
    #Contralateral Hip Drop
    rallowthresh_contra, rextmthresh_contra = 7.0,11.0
    lallowthresh_contra, lextmthresh_contra = 7.0,11.0
    #Pronation/Supination
    rallowthresh_prosup, rextmthresh_prosup = 7.0,11.0
    lallowthresh_prosup, lextmthresh_prosup = 7.0,11.0
    #Lateral Hip Rotation
    rallowthresh_hiprot, rextmthresh_hiprot = 7.0,11.0
    lallowthresh_hiprot, lextmthresh_hiprot = 7.0,11.0
    rdbl_allowthresh_hiprot, rdbl_extmthresh_hiprot = 7.0,11.0
    ldbl_allowthresh_hiprot, ldbl_extmthresh_hiprot = 7.0,11.0
    
    #CALCULATING THE NORMALIZED SCORE
    #Contralateral Hip Drop
    rnorm_contra = calc_norm_score(rsin_mag_contra, rallowthresh_contra, rextmthresh_contra)
    lnorm_contra = calc_norm_score(lsin_mag_contra, lallowthresh_contra, lextmthresh_contra)
    #Pronation/Supination
    rnorm_prosup = calc_norm_score(rsin_mag_prosup, rallowthresh_prosup, rextmthresh_prosup)
    lnorm_prosup = calc_norm_score(lsin_mag_prosup, lallowthresh_prosup, lextmthresh_prosup)
    #Laterl Hip Rotation
    rnorm_hiprot = calc_norm_score(rsin_mag_hiprot, rallowthresh_hiprot, rextmthresh_hiprot)
    lnorm_hiprot = calc_norm_score(lsin_mag_hiprot, lallowthresh_hiprot, lextmthresh_hiprot)
    rdblnorm_hiprot = calc_norm_score(rdbl_mag_hiprot, rdbl_allowthresh_hiprot, rdbl_extmthresh_hiprot)
    ldblnorm_hiprot = calc_norm_score(ldbl_mag_hiprot, ldbl_allowthresh_hiprot, ldbl_extmthresh_hiprot)
    
    return rnorm_contra, lnorm_contra, rnorm_prosup, lnorm_prosup, rnorm_hiprot, lnorm_hiprot, rdblnorm_hiprot, ldblnorm_hiprot      

def exec_score(ph, rdata, ldata, hdata, mass, extra_mass):
    
    #XXXXXXXXXXXXXXXXXXXXXXXXXXXX STEP I - DETERMINING CME VALUES XXXXXXXXXXXXXXXXXXXXXXXXXXX 
    
    #Set peak detection parameters and initiate objects    
    rxmaxtab, rymaxtab, rzmaxtab, lxmaxtab, lymaxtab, lzmaxtab, hxmaxtab, hymaxtab, hzmaxtab = [[] for i in range(9)]
    rxmintab, rymintab, rzmintab, lxmintab, lymintab, lzmintab, hxmintab, hymintab, hzmintab = [[] for i in range(9)]
    rxmn, rymn, rzmn, lxmn, lymn, lzmn, hxmn, hymn, hzmn = [np.Inf for i in range(9)] # initiate min, max value variable
    rxmx, rymx, rzmx, lxmx, lymx, lzmx, hxmx, hymx, hzmx = [-np.Inf for i in range(9)]
    rxmnpos, rymnpos, rzmnpos, lxmnpos, lymnpos, lzmnpos, hxmnpos, hymnpos, hzmnpos = [np.NaN for i in range(9)] #initiate min, max index variable
    rxmxpos, rymxpos, rzmxpos, lxmxpos, lymxpos, lzmxpos, hxmxpos, hymxpos, hzmxpos = [np.NaN for i in range(9)]
    
    #PEAK DETECTION - run for each sensor and each euler rotation (9 times)
    for i in range(len(ldata)):
        rxmaxtab, rxmintab, rxmx, rxmn, rxmxpos, rxmnpos = peak.peak_det(rdata[0,4], i, .05, rxmx, rxmn, rxmxpos, rxmnpos, rxmaxtab, rxmintab)
        rymaxtab, rymintab, rymx, rymn, rymxpos, rymnpos = peak.peak_det(rdata[0,5], i, .05, rymx, rymn, rymxpos, rymnpos, rymaxtab, rymintab)
        rzmaxtab, rzmintab, rzmx, rzmn, rzmxpos, rzmnpos = peak.peak_det(rdata[0,6], i, .05, rzmx, rzmn, rzmxpos, rzmnpos, rzmaxtab, rzmintab)

        lxmaxtab, lxmintab, lxmx, lxmn, lxmxpos, lxmnpos = peak.peak_det(ldata[0,4], i, .05, lxmx, lxmn, lxmxpos, lxmnpos, lxmaxtab, lxmintab)
        lymaxtab, lymintab, lymx, lymn, lymxpos, lymnpos = peak.peak_det(ldata[0,5], i, .05, lymx, lymn, lymxpos, lymnpos, lymaxtab, lymintab)
        lzmaxtab, lzmintab, lzmx, lzmn, lzmxpos, lzmnpos = peak.peak_det(ldata[0,6], i, .05, lzmx, lzmn, lzmxpos, lzmnpos, lzmaxtab, lzmintab)

        hxmaxtab, hxmintab, hxmx, hxmn, hxmxpos, hxmnpos = peak.peak_det(hdata[0,4], i, .05, hxmx, hxmn, hxmxpos, hxmnpos, hxmaxtab, hxmintab)
        hymaxtab, hymintab, hymx, hymn, hymxpos, hymnpos = peak.peak_det(hdata[0,5], i, .05, hymx, hymn, hymxpos, hymnpos, hymaxtab, hymintab)
        hzmaxtab, hzmintab, hzmx, hzmn, hzmxpos, hzmnpos = peak.peak_det(hdata[0,6], i, .05, hzmx, hzmn, hzmxpos, hzmnpos, hzmaxtab, hzmintab)
    
    #DETERMINING THE ROTATIONAL MAGNITUDE AND, UPPER AND LOWER TIME INTERVALS FOR EACH CME
    #Pronation/Supination
    if len(lxmaxtab) != 0 and len(lxmintab) != 0:
        lsin_prosup_mag, lsin_lprosup_uppert, lsin_lprosup_lowert = cmed.rot_CME(lxmaxtab, lxmintab, ph, [0,1]) #peak detect left foot x-axis single and double leg left balance
    else:
        lsin_prosup_mag = [0] #if error doesn't exist, then initialize magnitude to zero

    if len(rxmaxtab) != 0 and len(rxmintab) != 0:
        rsin_prosup_mag, rsin_rprosup_uppert, rsin_rprosup_lowert = cmed.rot_CME(rxmaxtab, rxmintab, ph,[0,2]) #peak detect right foot x-axis single and double leg right balance
    else:
        rsin_prosup_mag = [0] #if error doesn't exist, then initialize magnitude to zero
        
    #Contralateral Hip Drop
    if len(hymaxtab) != 0 and len(hymintab) != 0:
        lsin_contra_mag, lsin_contra_uppert, lsin_contra_lowert = cmed.rot_CME(hymaxtab, hymintab, ph, [0,1]) #peak detect hips y-axis single and double leg left
        rsin_contra_mag, rsin_contra_uppert, rsin_contra_lowert = cmed.rot_CME(hymaxtab, hymintab, ph, [0,2]) #peak detect hips y-axis single and double leg right
    else:
        lsin_contra_mag = rsin_contra_mag = [0] #if error doesn't exist, then initialize magnitude to zero         
        
    #Lateral Hip Rotation
    if len(hzmaxtab) != 0 and len(hzmintab) != 0:
        rdbl_hiprot_mag, rdbl_hiprot_uppert, rdbl_hiprot_lowert = ldbl_hiprot_mag, ldbl_hiprot_uppert, ldbl_hiprot_lowert = cmed.rot_CME(hzmaxtab, hzmintab, ph, 0) #peak detect hips z-axis double leg balance (right and left feet)
        lsin_hiprot_mag, lsin_hiprot_uppert, lsin_hiprot_lowert = cmed.rot_CME(hzmaxtab, hzmintab, ph, 1) #peak detect hips z-axis single leg left
        rsin_hiprot_mag, rsin_hiprot_uppert, rsin_hiprot_lowert = cmed.rot_CME(hzmaxtab, hzmintab, ph, 2) #peak detect hips z-axis single leg right
    else:
        rdbl_hiprot_mag = lsin_hiprot_mag = rsin_hiprot_mag = [0] #if error doesn't exist, then initialize magnitude to zero
        
    #XXXXXXXXXXXXXXXXXXXXXXXXXXXX STEP II - NORMALIZATION OF CME "GOODNESS" XXXXXXXXXXXXXXXXXXXXXXXXXXX
    
    #DETERMINING THE NORMALIZED SCORES OF "GOODNESS"    
    #nr_contra = nl_contra = nr_prosup = nl_prosup = nr_hiprot = nl_hiprot = nrdbl_hiprot = nldbl_hiprot = [0] #initializing all the normalized scores of "goodness"
    nr_contra, nl_contra, nr_prosup, nl_prosup, nr_hiprot, nl_hiprot, nrdbl_hiprot, nldbl_hiprot = normalize_good (lsin_prosup_mag, rsin_prosup_mag, lsin_contra_mag, rsin_contra_mag, rdbl_hiprot_mag, ldbl_hiprot_mag, lsin_hiprot_mag, rsin_hiprot_mag) #normalizing the "goodness" of each movement made by the user
    
    #XXXXXXXXXXXXXXXXXXXXXXXXXXXX STEP III - WEIGHTING BY LOAD XXXXXXXXXXXXXXXXXXXXXXXXXXX
    
    p_contra, p_prosup, p_hiprot = weight_load(nr_contra, nl_contra, nr_prosup, nl_prosup, nr_hiprot, nl_hiprot, nrdbl_hiprot, nldbl_hiprot, lsin_lprosup_uppert, lsin_lprosup_lowert, rsin_rprosup_uppert, rsin_rprosup_lowert, lsin_contra_uppert, lsin_contra_lowert, rsin_contra_uppert, rsin_contra_lowert, rdbl_hiprot_uppert, rdbl_hiprot_lowert, ldbl_hiprot_uppert, ldbl_hiprot_lowert, lsin_hiprot_uppert, lsin_hiprot_lowert, rsin_hiprot_uppert, rsin_hiprot_lowert, mass, extra_mass, hdata)
    
