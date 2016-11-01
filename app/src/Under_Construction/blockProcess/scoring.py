# -*- coding: utf-8 -*-
"""
Created on Wed Oct 12 11:16:55 2016

@author:Dipesh Gautam
"""

from __future__ import division
import numpy as np
import time
from scipy.interpolate import UnivariateSpline
from sklearn.neighbors.kde import KernelDensity as kde
from sklearn import mixture


"""
#############################################INPUT/OUTPUT###################
Inputs: Two RawFrame object with movement quality features
    --current session/block,
    --historical user data
Outputs: Consistency and symmetry scores, destructive multiplier, 
        destructive and constructive mech_stress and block/session_duration
        block/session_mech_stress_elapsed for each timepoint
#############################################################################
"""


def _con_fun(dist, double = False):
    """Creates consistency score for individual points and create an 
    interpolation object for mapping

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
        # TODO(Dipesh): adjust limits with more data
        ##max sq_dev is 0, min sq_dev is 100 and is scaled accordingly
        ratio = sq_dev/(len(dist)*var)
        score = (1-(ratio-min(ratio))/(max(ratio)-min(ratio)))*100
        fn = UnivariateSpline(dist_sorted, score, ext = 0, check_finite = True)#extrapolation is done for values outside the range
    elif double ==True:
        #If the feature has multiple modes, it's split into two separate
        #distribution using gaussian mixture model and scored separately
        #and combined
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


def _create_distribution(data):
    """Creates mapping interpolation functions to file for each Movement
    Quality feature

    Args:
        data : data table with historical(7 days) MQ features, 
        total_accel and mech_stress for the user 

    Returns:
        Interpolation mapping function for each Movement Quality feature        
    """
    mS = np.array(np.abs(data.mech_stress))
    tA = np.array(np.abs(data.total_accel))
    fn_hDL = _con_fun(np.array(data.hip_drop_l/(tA*mS)))
    fn_hDR = _con_fun(np.array(data.hip_drop_r/(tA*mS)))
    fn_hR = _con_fun(np.array(data.hip_rot/(tA*mS)))
    fn_aRL = _con_fun(np.array(data.ankle_rot_l/(tA*mS)))
    fn_aRR = _con_fun(np.array(data.ankle_rot_r/(tA*mS)))
    fn_lPL = _con_fun(np.array(data.land_pattern_l/(tA*mS)))
    fn_lPR = _con_fun(np.array(data.land_pattern_r/(tA*mS)))
    fn_lTL = _con_fun(np.array(data.land_time_l/(tA*mS)))
    fn_lTR = _con_fun(np.array(data.land_time_r/(tA*mS)))
    
    return fn_hDL, fn_hDR, fn_hR, fn_aRL, fn_aRR, fn_lPL, fn_lPR, fn_lTL, fn_lTR
                    

def _symmetry_score(dist_l,dist_r):
    """Calculates symmetry score for each point of the two distribution
    Args:
        dist_l : MQ feature values for left side already controled
        dist_r : MQ feature values for right side already controled
    Returns:            

    """
    dist_l = np.sort(dist_l[np.isfinite(dist_l)])
    dist_r = np.sort(dist_r[np.isfinite(dist_r)])
    dist_l1 = dist_l[:,np.newaxis]
    dist_r1 = dist_r[:,np.newaxis]
    #Bandwith needs to be adjusted with the data length and sd of data
    #using constant for now
#    band_l = 1.06*np.std(dist_l)*(len(dist_l))**(-.2)
#    band_r = 1.06*np.std(dist_r)*(len(dist_r))**(-.2)
    band_l = .05
    band_r = .05
    kernel_density_l = kde(kernel= 'gaussian', bandwidth = band_l, rtol = 1E-3,
                           atol = 1E-3).fit(dist_l1)
    kernel_density_r = kde(kernel= 'gaussian', bandwidth = band_r, rtol = 1E-3,
                           atol = 1E-3).fit(dist_r1)
    
    #Calculate density estimate for left data under both distribution
    #and calculate score based on difference and create a dictionary for
    #mapping
    den_distL_kdeL = np.exp(kernel_density_l.score_samples(dist_l1))
    den_distL_kdeR = np.exp(kernel_density_r.score_samples(dist_l1))
    dens_l = np.vstack([den_distL_kdeL,den_distL_kdeR])
    max_den_l = np.max(dens_l,0)
    score_l = (1-np.abs(den_distL_kdeL-den_distL_kdeR)/max_den_l)*100
    left_score_dict = dict(zip(dist_l,score_l))
    
    #Calculate density estimate for right data under both distribution
    #and calculate score based on difference and create a dictionary for
    #mapping
    den_distR_kdeL = np.exp(kernel_density_l.score_samples(dist_r1))
    den_distR_kdeR = np.exp(kernel_density_r.score_samples(dist_r1))
    dens_r = np.vstack([den_distR_kdeL,den_distR_kdeR])
    max_den_r = np.max(dens_r,0)
    score_r = (1-np.abs(den_distR_kdeL-den_distR_kdeR)/max_den_r)*100
    right_score_dict = dict(zip(dist_r,score_r))
      
    return left_score_dict, right_score_dict
 
 
def _hip(hDL, hDR, hR, fn_hDL,fn_hDR,fn_hR):
    """Calculates consistency and symmetry score for each hip features and 
    averages the score
    Args:
        hDL : hip_drop_l
        hDR : hip_drop_r
        hR : hip_rot
        fn_hDL,fn_hDR,fn_hR : mapping functions for hDL, hDR and hR
    Returns:
        hip_consistency: consistency averaged over all hip features (num 0-100)
        hip_symmetry: symmetry averaged over all hip features (num 0-100)
    """   
    #Call individual interpolation function for each feature
    con_score_hDL = fn_hDL(hDL)
    con_score_hDR = fn_hDR(hDR)
    con_score_hR= fn_hR(hR)
    
    con_scores = np.vstack([con_score_hDL, con_score_hDR, con_score_hR])
    #interpolation function is set to extrapolate which might result in negative scores.    
    con_scores[con_scores>100]=100 #set scores higher than 100(should not happen) to 100
    con_scores[con_scores<=0]=0 #set negative scores to 0
    #MQ features with missing values will return 'nan' scores.
    #ignore those features when averaging
    hip_consistency = np.nanmean(con_scores,0)
    
    #Calculate symmetry scores for hip features
    #If all the rows for either left or right features are blank or we have at
    #most 2 non-empty rows, we cannot score so, nan's are returned as score for 
    #all rows    
    if (all(np.isnan(hDL)) or all(np.isnan(hDR))):
        hip_drop_score = np.zeros(len(hDR))*np.nan
    else:
        l_dict_drop, r_dict_drop = _symmetry_score(hDL, hDR)
        score_drop_l = [l_dict_drop.get(k, np.nan) for k in hDL]
        score_drop_r = [r_dict_drop.get(k, np.nan) for k in hDR]
        scores_drop = np.vstack([score_drop_l, score_drop_r])
        hip_drop_score = np.nanmean(scores_drop,0)
        
    #subset hip rotation data to create two distributions to compare
    hRL = np.abs(hR[hR<=0]) #change negative values to positive so both dist are in same range
    hRR = hR[hR>=0]
    if all(np.isnan(hR)):
        hip_rot_score = np.zeros(len(hR))*np.nan
    elif (len(hRL)==0 or len(hRR)==0):
        hip_rot_score = np.zeros(len(hR))*np.nan
    else:
        l_dict_rot, r_dict_rot = _symmetry_score(hRL, hRR)
        score_rot_l = [l_dict_rot.get(k, np.nan) for k in -hR]
        score_rot_r = [r_dict_rot.get(k, np.nan) for k in hR]
        scores_rot = np.vstack([score_rot_l, score_rot_r])
        hip_rot_score = np.nanmean(scores_rot,0)
        
    hip_scores = np.vstack([hip_drop_score, hip_rot_score])
    hip_symmetry = np.nanmean(hip_scores,0)
    
    return hip_consistency, hip_symmetry
    
    
def _ankle(aRL,aRR,lPL,lPR,lTL,lTR,fn_aRL,fn_aRR,fn_lPL,fn_lPR,fn_lTL,fn_lTR):
    """Calculates consistency and symmetry score for each ankle features and 
    averages the score for each ankle.
    Args:
        aRL : ankle_rot_l
        aRR : ankle_rot_r
        lPL : land_pattern_l
        lPR : land_pattern_r
        lTL : land_time_l
        lTR : land_time_r
        fn_aRL,fn_aRR,fn_lPL,fn_lPR,fn_lTL,fn_lTR : mapping functions
    Returns:
        l_consistency: consistency averaged over left ankle features
        r_consistency: consistency averaged over right ankle features
        ankle_symmetry: symmetry averaged over ankle features       
    """    
    ##Consistency
    #Call individual interpolation function for each feature
    score_aRL = fn_aRL(aRL)
    score_aRR = fn_aRR(aRR)
    
    score_lPL = fn_lPL(lPL)
    score_lPR = fn_lPR(lPR)
    
    score_lTL = fn_lTL(lTL)
    score_lTR = fn_lTR(lTR)
    
    #Combine scores for left ankle
    cons_scores_l = np.vstack([score_aRL,score_lPL,score_lTL])
    #interpolation function is set to extrapolate which might result in negative scores.
    cons_scores_l[cons_scores_l>100]=100 #set scores higher than 100(should not happen) to 100
    cons_scores_l[cons_scores_l<=0]=0 #set negative scores to 0
    
    #Combine score for right ankle
    cons_scores_r = np.vstack([score_aRR,score_lPR,score_lTR])
    cons_scores_r[cons_scores_r>100]=100
    cons_scores_r[cons_scores_r<=0]=0
    
    #MQ features with missing values will return 'nan' scores.
    #ignore those features when averaging
    l_consistency = np.nanmean(cons_scores_l,0)    
    r_consistency = np.nanmean(cons_scores_r,0)

    #Calculate symmetry scores for ankle features
    #If all the rows for either left or right features are blank or we have at
    #most 2 non-empty rows, we cannot score so, nan's are returned as score for 
    #all rows
    if (all(np.isnan(aRL)) or all(np.isnan(aRR))):
        ankle_rot_score = np.zeros(len(aRL))*np.nan
    elif ((len(aRL[np.isfinite(aRL)])<=2) or (len(aRL[np.isfinite(aRL)])<=2)):
        ankle_rot_score = np.zeros(len(aRL))*np.nan
    else:
        l_dict_rot, r_dict_rot = _symmetry_score(aRL, aRR)
        score_rot_l = [l_dict_rot.get(k, np.nan) for k in aRL]
        score_rot_r = [r_dict_rot.get(k, np.nan) for k in aRR]
        scores_rot = np.vstack([score_rot_l, score_rot_r])
        ankle_rot_score = np.nanmean(scores_rot,0)

    if (all(np.isnan(lPL)) or all(np.isnan(lPR))):
        ankle_pat_score = np.zeros(len(lPL))*np.nan
    elif ((len(lPL[np.isfinite(lPL)])<=2) or (len(lPR[np.isfinite(lPR)])<=2)):
        ankle_pat_score = np.zeros(len(lPL))*np.nan
    else:        
        l_dict_pat, r_dict_pat = _symmetry_score(lPL, lPR)
        score_pat_l = [l_dict_pat.get(k, np.nan) for k in lPL]
        score_pat_r = [r_dict_pat.get(k, np.nan) for k in lPR]
        scores_pat = np.vstack([score_pat_l, score_pat_r])
        ankle_pat_score = np.nanmean(scores_pat,0)
 
    if (all(np.isnan(lTL)) or all(np.isnan(lTR))):
        ankle_tim_score = np.zeros(len(lTL))*np.nan
    elif ((len(lTL[np.isfinite(lTL)])<=2) or (len(lTR[np.isfinite(lTR)])<=2)):
        ankle_tim_score = np.zeros(len(lTL))*np.nan
    else:         
        l_dict_tim, r_dict_tim = _symmetry_score(lTL, lTR)
        score_tim_l = [l_dict_tim.get(k, np.nan) for k in lTL]
        score_tim_r = [r_dict_tim.get(k, np.nan) for k in lTR]
        scores_tim = np.vstack([score_tim_l, score_tim_r])
        ankle_tim_score = np.nanmean(scores_tim,0)
                            
    ankle_scores = np.vstack([ankle_rot_score,ankle_pat_score,
                              ankle_tim_score])
    ankle_symmetry = np.nanmean(ankle_scores,0)
    
    return l_consistency, r_consistency, ankle_symmetry


def score(data,userDB):
    """Average consistency, symmetry, control scores at sensor level, 
    ankle/hip level and then average at body level
    Args:
        data : RawFrame object with the movement quality features, total_accel,
                mech_stress, ms_elapsed, control score, session_type attributes
        userDB : RawFrame object with historical(7 days) MQ features,
                total_accel and mech_stress for the user 
    Returns:
        consistency, hip_consistency, ankle_consistency, l_consistency,
        r_consistency, symmetry, hip_symmetry, ankle_symmetry, destr_multiplier,
        dest_mech_stress, const_mech_stress, block_duration, session_duration,
        block_mech_stress_elapsed, session_mech_stress_elapsed
        
        Note: All symmetry and consistency scores are multiplied by mech_stress
                for calculating weighted average while aggregating        
        
        For session_type = 1, block_mech_stress_elapsed and block_duration will
        be nan's
        For session_type =2,3, session_mech_stress_elapsed and session_duration
        will be nan's.
        
    """
    mS = np.abs(np.array(data.mech_stress)).reshape(-1,)
    tA = np.abs(np.array(data.total_accel)).reshape(-1,)
    
    #divide each feature value by (totalAccel*mechStress) to control
    #for these performance variables
    # TODO (Dipesh) need to find better control
    hDL = np.array(data.hip_drop_l).reshape(-1,)/(mS*tA)
    hDR = np.array(data.hip_drop_r).reshape(-1,)/(mS*tA)
    hR = np.array(data.hip_rot).reshape(-1,)/(mS*tA)
    aRL = np.array(data.ankle_rot_l).reshape(-1,)/(mS*tA)
    aRR = np.array(data.ankle_rot_r).reshape(-1,)/(mS*tA)
    lPL = np.array(data.land_pattern_l).reshape(-1,)/(mS*tA)
    lPR = np.array(data.land_pattern_r).reshape(-1,)/(mS*tA)
    lTL = np.array(data.land_time_l).reshape(-1,)/(mS*tA)
    lTR = np.array(data.land_time_r).reshape(-1,)/(mS*tA)
    
    control = np.array(data.control).reshape(-1,)
    
    #Create mapping functions for consistency using historical user data
    fn_hDL,fn_hDR,fn_hR,fn_aRL,fn_aRR,fn_lPL,fn_lPR,fn_lTL,fn_lTR = _create_distribution(userDB)
    
    l_consistency, r_consistency, ankle_symmetry = _ankle(aRL,aRR,lPL, lPR, lTL,
                                                          lTR,fn_aRL,fn_aRR,
                                                          fn_lPL,fn_lPR,fn_lTL,
                                                          fn_lTR)
    hip_consistency, hip_symmetry = _hip(hDL, hDR, hR, fn_hDL,fn_hDR,fn_hR)

    #Aggregate Ankle scores
    ankle_scores = np.vstack([l_consistency, r_consistency])
    ankle_consistency = np.nanmean(ankle_scores,0)
    overall_consistency_scores = np.vstack([ankle_consistency, hip_consistency])
    consistency = np.nanmean(overall_consistency_scores,0)
    
    #multiply each score by mechStress value for weighting
    l_consistency = l_consistency*mS
    r_consistency = r_consistency*mS
    hip_consistency = hip_consistency*mS
    ankle_consistency = ankle_consistency*mS
    consistency = consistency*mS
    
    #Aggregate symmetry scores
    overall_symmetry_scores = np.vstack([hip_symmetry, ankle_symmetry])
    symmetry = np.nanmean(overall_symmetry_scores,0)
    
    ##Calculate the destructive mechStress multiplier
    destr_multiplier = (1-symmetry/100)**2+(1-control/100)**2
    
    dest_mech_stress = np.array(mS)*np.array(destr_multiplier)
    const_mech_stress = mS - dest_mech_stress    
    
    #multiply each score by mechStress value for weighting
    symmetry = symmetry*mS
    hip_symmetry = hip_symmetry*mS
    ankle_symmetry = ankle_symmetry*mS
    
    #Block/Session duration
    ms_elapsed = np.array(data.ms_elapsed)
    session_type = np.array(data.session_type)
    duration = np.cumsum(ms_elapsed)/np.sum(ms_elapsed)

    #MechStress Elapsed
    mech_stress_elapsed = np.cumsum(mS)/np.sum(mS)
    
    if session_type[0] in (2,3): #2:strength_training, 3: return to play
        block_duration = duration
        session_duration = np.zeros(len(duration))*np.nan
        
        block_mech_stress_elapsed = mech_stress_elapsed
        session_mech_stress_elapsed = np.zeros(len(duration))*np.nan
        
    elif session_type[0]==1: #1: practice
        block_duration = np.zeros(len(duration))*np.nan
        session_duration = duration
        
        block_mech_stress_elapsed = np.zeros(len(duration))*np.nan
        session_mech_stress_elapsed = mech_stress_elapsed
    
    return consistency.reshape(-1,1), hip_consistency.reshape(-1,1), ankle_consistency.reshape(-1,1), l_consistency.reshape(-1,1), r_consistency.reshape(-1,1), symmetry.reshape(-1,1), hip_symmetry.reshape(-1,1), ankle_symmetry.reshape(-1,1), destr_multiplier.reshape(-1,1), dest_mech_stress.reshape(-1,1), const_mech_stress.reshape(-1,1), block_duration.reshape(-1,1), session_duration.reshape(-1,1), block_mech_stress_elapsed.reshape(-1,1), session_mech_stress_elapsed.reshape(-1,1)

    
if __name__ == '__main__':
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np
    import time
    path = 'C:\\Users\\dipesh\\Desktop\\biometrix\\indworkout\\'
    data= np.genfromtxt(path+ "Subject3_LESS_Transformed_Data.csv",delimiter = ",", dtype =float, names = True)
    
    
    ms_ta = np.genfromtxt(path+ "ms_ta.csv",delimiter = ",", dtype =float, names = True)
    data1 = pd.DataFrame()                 
#    data1['msElapsed'] = np.zeros(len(data))+4
    data1['epochTime'] = data['Timestamp']
    data1['hip_drop_l'] = data['hipDropL']
    data1['hip_drop_r'] = data['hipDropR']
    data1['hip_rot'] = data['hipRot']-90
    data1['ankle_rot_l'] = data['ankleRotL']
    data1['ankle_rot_r'] = data['ankleRotR']
#    data1['foot_position_l'] = data['ankleRotL']  
#    data1['foot_position_r'] = data['ankleRotR'] 
    data1['land_pattern_l'] = np.zeros(len(data))*np.nan
    data1['land_pattern_r'] = np.zeros(len(data))*np.nan
    data1['land_time_l'] = np.zeros(len(data))*np.nan
    data1['land_time_r'] = np.zeros(len(data))*np.nan
    data1['control'] = data['control']
    data1['mech_stress'] = ms_ta['mechStress'][range(len(data))]
    data1['total_accel'] = ms_ta['totalAccel'][range(len(data))]
    
    userDB = pd.DataFrame(data)
    userDB['mech_stress'] = ms_ta['mechStress'][range(len(data))]
    userDB['total_accel'] = ms_ta['totalAccel'][range(len(data))]
    userDB['land_pattern_l'] = np.random.rand(len(data))
    userDB['land_pattern_r'] = np.random.rand(len(data))
    userDB['land_time_l'] = np.random.rand(len(data))
    userDB['land_time_r'] = np.random.rand(len(data))
    
    userDB.to_csv(path+"subject3_DblSquat_hist.csv")
    
#    userDB['epochTime'] = data['Timestamp']
#    userDB['hip_drop_l'] = data['hipDropL']
#    userDB['hip_drop_r'] = data['hipDropR']
#    userDB['hip_rot'] = data['hipRot']-90
#    userDB['ankle_rot_l'] = data['ankleRotL']
#    userDB['ankle_rot_r'] = data['ankleRotR']
##    data1['foot_position_l'] = data['ankleRotL']  
##    data1['foot_position_r'] = data['ankleRotR'] 
#    userDB['land_pattern_l'] = np.random.rand(len(data))
#    userDB['land_pattern_r'] = np.random.rand(len(data))
#    userDB['land_time_l'] = np.random.rand(len(data))
#    userDB['land_time_r'] = np.random.rand(len(data))
#    userDB['control'] = data['control']
#    userDB['mech_stress'] = ms_ta['mechStress'][range(len(data))]
#    userDB['total_accel'] = ms_ta['totalAccel'][range(len(data))]
#    userDB['land_pattern_l'] = data['ankleRotL']
    
    s= time.time()
    consistency, hip_consistency, ankle_consistency, l_consistency, r_consistency, symmetry, hip_symmetry, ankle_symmetry, destr_multiplier, dest_mech_stress, const_mech_stress, block_duration, session_duration, block_mech_stress_elapsed, session_mech_stress_elapsed = score(data1, userDB)
    e = time.time()
    elap = e-s
    print elap
    
    data_pd = pd.DataFrame(data)
    data_pd['consistency'] = consistency
    data_pd['hip_consistency'] = hip_consistency
    data_pd['ankle_consistency'] = ankle_consistency
    data_pd['l_consistency'] = l_consistency
    data_pd['r_consistency'] = r_consistency
    data_pd['symmetry'] = symmetry
    data_pd['hip_symmetry'] = hip_symmetry
    data_pd['ankle_symmetry'] = ankle_symmetry
    data_pd['destr_multiplier'] = destr_multiplier
    data_pd['dest_mech_stress'] = dest_mech_stress
    data_pd['const_mech_stress'] = const_mech_stress
    data_pd['block_duration'] = block_duration
    data_pd['session_duration'] = session_duration
    data_pd['block_mech_stress_elapsed'] = block_mech_stress_elapsed
    data_pd['session_mech_stress_elapsed'] = session_mech_stress_elapsed
#    data_pd.to_csv(path+"Subject3_DblSquat_Transformed_scoring.csv")
    
    
    
    