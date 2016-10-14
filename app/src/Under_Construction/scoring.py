# -*- coding: utf-8 -*-
"""
Created on Wed Oct 12 11:16:55 2016

@author:Dipesh Gautam
"""

from __future__ import division
import numpy as np
from scipy.interpolate import UnivariateSpline
from sklearn.neighbors.kde import KernelDensity as kde
#import pandas as pd
from sklearn import mixture


"""
#############################################INPUT/OUTPUT####################################################   
Inputs: data table with movement quality features and historical(7 days) user data
Outputs: Consistency and symmetry scores, destructive multiplier, destructive and constructive mechStress and blockDuration for each timepoint
#############################################################################################################
"""
  
def conFun(dist, double = False):
    """Creates consistency score for individual points and create an interpolation object for mapping
    Args:
        dist : distribution to create the mapping function for
        double: Indicator for if the given distribution might have double peaks
    Returns:
        fn: Interpolation mapping function for the given distribution        
    """
    dist = dist[np.isfinite(dist)]# get rid of missing values in the provided distribution
    if double == False:
        dist_sorted = np.sort(dist)
        var = np.var(dist_sorted)    
        sq_dev = (dist_sorted-np.mean(dist_sorted))**2
        ##max sq_dev is 0, min sq_dev is 100 and is scaled accordingly
        ratio = sq_dev/(len(dist)*var)
        score = (1-(ratio-min(ratio))/(max(ratio)-min(ratio)))*100
        fn = UnivariateSpline(dist_sorted, score, ext = 0, check_finite = True)#extrapolation is done for values outside the range
    elif double ==True:
        #If the feature has multiple modes, it's split into two separate distribution using gaussian mixture model and scored separately and combined
        mix = mixture.GMM(n_components = 2)
        comps = mix.fit_predict(dist.reshape(-1,1))
        s1 = np.sort(dist[comps==0],0)
        s2 = np.sort(dist[comps==1],0)
        if max(s1)<=min(s2): #contition to verify the combined samples are sorted
            sample1 = s1
            sample2 = s2
        else:
            sample1 = s2
            sample2 = s1
        
        sq_dev1 = (sample1-np.mean(sample1))**2
        ratio1 = sq_dev1/(len(sample1)*np.var(sample1))
        sq_dev2 = (sample2-np.mean(sample2))**2
        ratio2 = sq_dev2/(len(sample2)*np.var(sample2))
        score1 = ( 1- (ratio1-min(ratio1))/(max(ratio1)-min(ratio1)) )*100
        score2 = (1-(ratio2-min(ratio2))/(max(ratio2)-min(ratio2)))*100
        scores = np.hstack([score1,score2])
        dist_comb = np.hstack([sample1,sample2])
        fn = UnivariateSpline(dist_comb, scores, ext = 0, check_finite = True)
    return fn

def createDistribution(data):
    """Creates mapping interpolation functions to file for each Movement Quality feature
    Args:
        data : data table with historical(7 days) MQ features, total Accel and mechStress for the user 
    Returns:
        Interpolation mapping function for each Movement Quality feature        
    """
#    data = np.genfromtxt(data_path, dtype=float, delimiter=',', names=True)
    mS = np.array(np.abs(data['mechStress']))
    tA = np.array(np.abs(data['totalAccel']))
    fn_hDL = conFun(np.array(data['hipDropL']/(tA*mS)))
    fn_hDR = conFun(np.array(data['hipDropR']/(tA*mS)))
    fn_hR = conFun(np.array(data['hipRot']/(tA*mS)))
    fn_aRL = conFun(np.array(data['ankleRotL']/(tA*mS)),True)
    fn_aRR = conFun(np.array(data['ankleRotR']/(tA*mS)), True)
    fn_fPL = conFun(np.array(data['footPositionL']/(tA*mS)))
    fn_fPR = conFun(np.array(data['footPositionR']/(tA*mS)))
    fn_lPL = conFun(np.array(data['landPatternL']/(tA*mS)))
    fn_lPR = conFun(np.array(data['landPatternR']/(tA*mS)))
    fn_lTL = conFun(np.array(data['landTimeL']/(tA*mS)))
    fn_lTR = conFun(np.array(data['landTimeR']/(tA*mS)))
    
    return fn_hDL, fn_hDR, fn_hR, fn_aRL, fn_aRR, fn_fPL, fn_fPR, fn_lPL, fn_lPR, fn_lTL, fn_lTR
                    

def symmetryScore(distL,distR):
    """Calculates symmetry score for each point of the two distribution
    Args:
        distL : MQ feature values for left side already controled
        distR : MQ feature values for right side
    Returns:            

    """
    distL = np.sort(distL[np.isfinite(distL)])
    distR = np.sort(distR[np.isfinite(distR)])
    distL1 = distL[:,np.newaxis]
    distR1 = distR[:,np.newaxis]
#    bL = 1.06*np.std(distL)*(len(distL))**(-.2)
#    bR = 1.06*np.std(distR)*(len(distR))**(-.2)
    kernel_densityL = kde(kernel= 'gaussian', bandwidth = .05, rtol = 1E-3, atol = 1E-3).fit(distL1)
    kernel_densityR = kde(kernel= 'gaussian', bandwidth = .05, rtol = 1E-3, atol = 1E-3).fit(distR1)
    den_distL_kdeL = np.exp(kernel_densityL.score_samples(distL1))
    den_distL_kdeR = np.exp(kernel_densityR.score_samples(distL1))
    dens_l = np.vstack([den_distL_kdeL,den_distL_kdeR])
    max_den_l = np.max(dens_l,0)
    scoreL = (1-np.abs(den_distL_kdeL-den_distL_kdeR)/max_den_l)*100
    den_distR_kdeL = np.exp(kernel_densityL.score_samples(distR1))
    den_distR_kdeR = np.exp(kernel_densityR.score_samples(distR1))
    dens_r = np.vstack([den_distR_kdeL,den_distR_kdeR])
    max_den_r = np.max(dens_r,0)
    scoreR = (1-np.abs(den_distR_kdeL-den_distR_kdeR)/max_den_r)*100
#    plt.subplot(221);plt.hist(distL)
#    plt.subplot(222);plt.plot(distL, scoreL)
#    plt.subplot(223);plt.hist(distR)
#    plt.subplot(224);plt.plot(distR, scoreR)
    left_score_dict = dict(zip(distL,scoreL))
    right_score_dict = dict(zip(distR,scoreR))
    return left_score_dict, right_score_dict
 
 
def hip(hDL, hDR, hR, fn_hDL,fn_hDR,fn_hR):
    """Calculates consistency and symmetry score for each hip features and averages the score
    Scaled with the assumption that the ranges are [-90,90] for all values, need to be tuned better.
    Args:
        hDL : hipDropL
        hDR : hipDropR
        hR : hipRot
        fn_hDL,fn_hDR,fn_hR : mapping functions
    Returns:
        hipConsistency: hip consistency averaged over all hip features (num 0-100)
        hipSymmetry: hip symmetry averaged over all hip features (num 0-100)
    """   
    #Call individual interpolation function for each feature
    con_score_hDL = fn_hDL(hDL)
    con_score_hDR = fn_hDR(hDR)
    con_score_hR= fn_hR(hR)
    con_scores = np.vstack([con_score_hDL, con_score_hDR, con_score_hR])
    #interpolation function is set to extrapolate which might result in negative scores.    
    con_scores[con_scores>100]=100 #set scores higher than 100(should not happen) to 100
    con_scores[con_scores<=0]=0 #set negative scores to 0
    #MQ features with missing values will return 'nan' scores. ignore those features when averaging
    hipConsistency = np.nanmean(con_scores,0)
    
    
    l_dict_drop, r_dict_drop = symmetryScore(hDL, hDR) 
    #subset hip rotation data to create two distributions to compare
    hRL = np.abs(hR[hR<=0]) #change negative values to positive so both dist are in same range
    hRR = hR[hR>=0]    
    
    l_dict_rot, r_dict_rot = symmetryScore(hRL, hRR)

    score_drop_l = [l_dict_drop.get(k, np.nan) for k in hDL]
    score_drop_r = [r_dict_drop.get(k, np.nan) for k in hDR]
    scores_drop = np.vstack([score_drop_l, score_drop_r])
    hip_drop_score = np.nanmean(scores_drop,0)
    
    score_drop_l = [l_dict_drop.get(k, np.nan) for k in hDL]
    score_drop_r = [r_dict_drop.get(k, np.nan) for k in hDR]
    scores_drop = np.vstack([score_drop_l, score_drop_r])
    hip_drop_score = np.nanmean(scores_drop,0)

    score_rot_l = [l_dict_rot.get(k, np.nan) for k in -hR]
    score_rot_r = [r_dict_rot.get(k, np.nan) for k in hR]
    scores_rot = np.vstack([score_rot_l, score_rot_r])
    hip_rot_score = np.nanmean(scores_rot,0)
    
    hip_scores = np.vstack([hip_drop_score, hip_rot_score])
    hipSymmetry = np.nanmean(hip_scores,0)
    
    return hipConsistency, hipSymmetry
    
    
def ankle(aRL,aRR,fPL,fPR,lPL,lPR,lTL,lTR,fn_aRL,fn_aRR,fn_fPL,fn_fPR,fn_lPL,fn_lPR,fn_lTL,fn_lTR):
    """Calculates consistency and symmetry score for each ankle features and averages the score for each ankle.
    Args:
        aRL : ankleRotL
        aRR : ankleRotR
        fPL : footPositionL
        fPR : footPositionR
        lPL : landPatternL
        lPR : landPatternR
        lTL : landTimeL
        lTR : landTimeR
        fn_aRL,fn_aRR,fn_fPL,fn_fPR,fn_lPL,fn_lPR,fn_lTL,fn_lTR : mapping functions
    Returns:
        ankleConsistencyL: Ankle consistency averaged over left ankle features
        ankleConsistencyR: Ankle consistency averaged over right ankle features
        ankleSymmetry: Ankle symmetry averaged over ankle features       
    """       
    #Call individual interpolation function for each feature
    score_aRL = fn_aRL(aRL)
    score_aRR = fn_aRR(aRR)
    
    score_fPL = fn_fPL(fPL)
    score_fPR = fn_fPR(fPR)
    
    score_lPL = fn_lPL(lPL)
    score_lPR = fn_lPR(lPR)
    
    score_lTL = fn_lTL(lTL)
    score_lTR = fn_lTR(lTR)
    
    scoresL = np.vstack([score_aRL,score_fPL,score_lPL,score_lTL])
    #interpolation function is set to extrapolate which might result in negative scores.
    scoresL[scoresL>100]=100 #set scores higher than 100(should not happen) to 100
    scoresL[scoresL<=0]=0 #set negative scores to 0
    scoresR = np.vstack([score_aRR,score_fPR,score_lPR,score_lTR])
    scoresR[scoresR>100]=100
    scoresR[scoresR<=0]=0
    #MQ features with missing values will return 'nan' scores. ignore those features when averaging
    ankleConsistencyL = np.nanmean(scoresL,0)    
    ankleConsistencyR = np.nanmean(scoresR,0)
    
    
    #Calculate symmetry scores for ankle features
    l_dict_rot, r_dict_rot = symmetryScore(aRL, aRR)
    l_dict_pos, r_dict_pos = symmetryScore(fPL, fPR)
    l_dict_pat, r_dict_pat = symmetryScore(lPL, lPR)
    l_dict_tim, r_dict_tim = symmetryScore(lTL, lTR)
    
    score_rot_l = [l_dict_rot.get(k, np.nan) for k in aRL]
    score_rot_r = [r_dict_rot.get(k, np.nan) for k in aRR]
    scores_rot = np.vstack([score_rot_l, score_rot_r])
    ankle_rot_score = np.nanmean(scores_rot,0)
    
    score_pos_l = [l_dict_pos.get(k, np.nan) for k in fPL]
    score_pos_r = [r_dict_pos.get(k, np.nan) for k in fPR]
    scores_pos = np.vstack([score_pos_l, score_pos_r])
    ankle_pos_score = np.nanmean(scores_pos,0)

    score_pat_l = [l_dict_pat.get(k, np.nan) for k in lPL]
    score_pat_r = [r_dict_pat.get(k, np.nan) for k in lPR]
    scores_pat = np.vstack([score_pat_l, score_pat_r])
    ankle_pat_score = np.nanmean(scores_pat,0)
    
    score_tim_l = [l_dict_tim.get(k, np.nan) for k in lTL]
    score_tim_r = [r_dict_tim.get(k, np.nan) for k in lTR]
    scores_tim = np.vstack([score_tim_l, score_tim_r])
    ankle_tim_score = np.nanmean(scores_tim,0)
    
    ankle_scores = np.vstack([ankle_rot_score, ankle_pos_score, ankle_pat_score,
                              ankle_tim_score])
                        
    ankleSymmetry = np.nanmean(ankle_scores,0)
    
    return ankleConsistencyL, ankleConsistencyR, ankleSymmetry


def score(data,userDB):
    """Average consistency, symmetry, control scores at sensor level, ankle/hip level and then average at body level
    Args:
        data : data table with the movement quality features, totalAccel, mechStress, epochTime for the block
        userDB : data table with historical(7 days) MQ features, total Accel and mechStress for the user 
    Returns:
        bodyConsistency, hipConsistency, ankleConsistency, LConsistency, RConsistency scores
        bodySymmetry, hipSymmetry, ankleSymmetry
        destrMultiplier, destrMechStress, constrMechStress
        
    """
    mS = np.abs(np.array(data['mechStress']))
    tA = np.abs(np.array(data['totalAccel']))
    #divide each feature value by (totalAccel*mechStress) to control for these performance variables
    hDL = np.array(data['hipDropL'])/(mS*tA)
    hDR = np.array(data['hipDropR'])/(mS*tA)
    hR = np.array(data['hipRot'])/(mS*tA)
    aRL = np.array(data['ankleRotL'])/(mS*tA)
    aRR = np.array(data['ankleRotR'])/(mS*tA)
    fPL = np.array(data['footPositionL'])/(mS*tA)
    fPR = np.array(data['footPositionR'])/(mS*tA)
    lPL = np.array(data['landPatternL'])/(mS*tA)
    lPR = np.array(data['landPatternR'])/(mS*tA)
    lTL = np.array(data['landTimeL'])/(mS*tA)
    lTR = np.array(data['landTimeR'])/(mS*tA)
    
    Control = np.array(data['control'])
    
    #Create mapping functions for consistency using historical user data
    fn_hDL,fn_hDR,fn_hR,fn_aRL,fn_aRR,fn_fPL,fn_fPR,fn_lPL,fn_lPR,fn_lTL,fn_lTR = createDistribution(userDB)
    
    
    LConsistency, RConsistency, ankleSymmetry = ankle(aRL,aRR,fPL, fPR, lPL, lPR, lTL,lTR,fn_aRL,fn_aRR,fn_fPL,fn_fPR,fn_lPL,fn_lPR,fn_lTL,fn_lTR)
    hipConsistency, hipSymmetry = hip(hDL, hDR, hR, fn_hDL,fn_hDR,fn_hR)

    #Aggregate Ankle scores
    ankle_scores = np.vstack([LConsistency, RConsistency])
    ankleConsistency = np.nanmean(ankle_scores,0)
    overall_consistency_scores = np.vstack([ankleConsistency, hipConsistency])
    consistency = np.nanmean(overall_consistency_scores,0)
    #multiply each score by mechStress value for weighting
    LConsistency = LConsistency*mS
    RConsistency = RConsistency*mS
    hipConsistency = hipConsistency*mS
    ankleConsistency = ankleConsistency*mS
    consistency = consistency*mS
    
    #Aggregate symmetry scores
    overall_symmetry_scores = np.vstack([hipSymmetry, ankleSymmetry])
    symmetry = np.nanmean(overall_symmetry_scores,0)
    
    ##Calculate the destructive mechStress multiplier
    destrMultiplier = (1-symmetry/100)**2+(1-Control/100)**2
    
    destrMechStress = np.array(mS)*np.array(destrMultiplier)
    constrMechStress = mS - destrMechStress    
    
    #multiply each score by mechStress value for weighting
    symmetry = symmetry*mS
    hipSymmetry = hipSymmetry*mS
    ankleSymmetry = ankleSymmetry*mS
    
    #Block duration
    epochTime = np.array(data['epochTime'])
    start = epochTime[0]
    end = epochTime[-1]
    blockDuration = (epochTime - start)/(end-start)
    
    return consistency, hipConsistency, ankleConsistency, LConsistency, RConsistency, symmetry, hipSymmetry, ankleSymmetry, destrMultiplier, destrMechStress, constrMechStress, blockDuration
    
if __name__ == '__main__':
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np
    import time
    path = 'C:\\Users\\dipesh\\Desktop\\biometrix\\indworkout\\'
    data = np.genfromtxt(path+ "Subject3_DblSquat_balCME1.csv",delimiter = ",", dtype =float, names = True)
    data1 = pd.DataFrame()                 
    data1['msElapsed'] = np.zeros(len(data))+4
    data1['epochTime'] = np.cumsum(data1['msElapsed'])-4
    data1['hipDropL'] = data['pronL']
    data1['hipDropR'] = data['pronR']
    data1['hipRot'] = data['pronR']
    data1['ankleRotL'] = data['pronR']
    data1['ankleRotR'] = data['pronR']
    data1['footPositionL'] = data['pronR']
    data1['footPositionR'] = data['pronR']
    data1['landPatternL'] = data['pronR']
    data1['landPatternR'] = data['pronR']
    data1['landTimeL'] = data['pronR']
    data1['landTimeR'] = data['pronR']
    data1['control'] = np.random.rand(len(data))*100
    data1['mechStress'] = np.ones(len(data))*25
    data1['totalAccel'] = np.ones(len(data))
    userDB = data1
    
    s= time.time()
    consistency, hipConsistency, ankleConsistency, LConsistency, RConsistency, symmetry, hipSymmetry, ankleSymmetry, destrMultiplier, destrMechStress, constrMechStress,blockDuration = score(data1, userDB)
    e = time.time()
    elap = e-s
    print elap
    