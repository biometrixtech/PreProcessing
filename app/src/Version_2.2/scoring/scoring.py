# -*- coding: utf-8 -*-
"""
Created on Wed Oct 12 11:16:55 2016

@author:Dipesh Gautam
"""

from __future__ import division
import logging
import sys

import numpy as np
import pandas as pd
from scipy.interpolate import UnivariateSpline
from sklearn.neighbors.kde import KernelDensity as kde
from sklearn import mixture

logger = logging.getLogger()

"""
#############################################INPUT/OUTPUT###################
Inputs: Two RawFrame object with movement quality features
    --current session/block,
    --historical user data
Outputs: Consistency and symmetry scores, destructive multiplier,
        destructive and constructive grf and block/session_duration
        block/session_mech_stress_elapsed for each timepoint
#############################################################################
"""


def score(data, user_hist, grf_scale):
    """Average consistency, symmetry, control scores at sensor level,
    ankle/hip level and then average at body level
    Args:
        data : RawFrame object with the movement quality features, total_accel,
               grf, ms_elapsed, control score, session_type attributes
        user_hist : RawFrame object/pandas dataframe with historical(5 days)
                    MQ features, total_accel and grf for the user
        grf_scale: scaling factor for mechanical stress
        Returns:
        consistency, hip_consistency, ankle_consistency, consistency_lf,
        consistency_rf, symmetry, hip_symmetry, ankle_symmetry, destr_multiplier,
        dest_mech_stress, const_mech_stress, block_duration, session_duration,
        block_mech_stress_elapsed, session_mech_stress_elapsed

        Note: All symmetry and consistency scores are multiplied by grf
                for calculating weighted average while aggregating

        For session_type = 1, block_mech_stress_elapsed and block_duration will
        be nan's
        For session_type =2,3, session_mech_stress_elapsed and session_duration
        will be nan's.
    """
    global GRF_SCALE
    GRF_SCALE = grf_scale
    mS = np.abs(np.array(data.grf)).reshape(-1, )
    mS_norm = np.array(mS/np.nanmean(mS))
    tA = np.abs(np.array(data.total_accel)).reshape(-1, )
    tA_norm = np.array(tA/np.nanmean(tA))

    #divide each feature value by (totalAccel*mechStress) to control
    #for these performance variables
    # TODO (Dipesh) need to find better control
#    scale = mS_norm*tA
    scale = np.sqrt(tA_norm*mS_norm)
    hDL = np.array(data.contra_hip_drop_lf).reshape(-1, )/(scale)
    hDR = np.array(data.contra_hip_drop_rf).reshape(-1, )/(scale)
#    hR = np.array(data.hip_rot).reshape(-1, )/(mS*tA)
    aRL = np.array(data.ankle_rot_lf).reshape(-1, )/(scale)
    aRR = np.array(data.ankle_rot_rf).reshape(-1, )/(scale)
    lPL = np.array(data.land_pattern_lf).reshape(-1, )/(scale)
    lPR = np.array(data.land_pattern_rf).reshape(-1, )/(scale)
    lT = np.array(data.land_time).reshape(-1, )/(scale)
    fPL = np.array(data.foot_position_lf).reshape(-1,)/(scale)
    fPR = np.array(data.foot_position_rf).reshape(-1,)/(scale)

    control = np.array(data.control).reshape(-1, )
    #Create mapping functions for consistency using historical user data
    fn_hDL, fn_hDR, fn_aRL, fn_aRR, fn_lPL, fn_lPR, fn_lT,\
                                fn_fPL, fn_fPR = _create_distribution(user_hist)
    logger.info("Distributions for consistency created")
    consistency_lf, consistency_rf, ankle_consistency, ankle_symmetry =\
                                                   _ankle(aRL, aRR, lPL, lPR,
                                                          lT, fPL, fPR,
                                                          fn_aRL, fn_aRR,
                                                          fn_lPL, fn_lPR, fn_lT,
                                                          fn_fPL, fn_fPR)
    logger.info("Ankle scoring completed")
    hip_consistency, hip_symmetry = _hip(hDL, hDR, fn_hDL, fn_hDR)
    logger.info("Hip scoring completed")
    #Aggregate consistency scores
    overall_consistency_scores = np.vstack([ankle_consistency, hip_consistency])
    consistency = np.nanmean(overall_consistency_scores, 0)

    mS = mS/GRF_SCALE

    #multiply each score by mechStress value for weighting
    consistency_lf = consistency_lf*mS
    consistency_rf = consistency_rf*mS
    hip_consistency = hip_consistency*mS
    ankle_consistency = ankle_consistency*mS
    consistency = consistency*mS

    #Aggregate symmetry scores
    overall_symmetry_scores = np.vstack([hip_symmetry, ankle_symmetry])
    symmetry = np.nanmean(overall_symmetry_scores, 0)

    ##Calculate the destructive mechStress multiplier
    destr_multiplier = ((1 - symmetry/100)**2 + (1 - control/100)**2)/2

    dest_grf = np.array(mS)*np.array(destr_multiplier)
    const_grf = mS - dest_grf

    #multiply each score by mechStress value for weighting
    symmetry = symmetry*mS
    hip_symmetry = hip_symmetry*mS
    ankle_symmetry = ankle_symmetry*mS

#    Block/Session duration
    ms_elapsed = np.array(data.ms_elapsed)
    session_duration = np.nan_to_num(ms_elapsed).cumsum()/np.nansum(ms_elapsed)

    #MechStress Elapsed
    session_grf_elapsed = np.nan_to_num(mS).cumsum()/np.nansum(mS)


    return consistency.reshape(-1, 1), hip_consistency.reshape(-1, 1),\
        ankle_consistency.reshape(-1, 1), consistency_lf.reshape(-1, 1),\
        consistency_rf.reshape(-1, 1), symmetry.reshape(-1, 1),\
        hip_symmetry.reshape(-1, 1), ankle_symmetry.reshape(-1, 1),\
        destr_multiplier.reshape(-1, 1), dest_grf.reshape(-1, 1),\
        const_grf.reshape(-1, 1), session_duration.reshape(-1, 1),\
        session_grf_elapsed.reshape(-1, 1)


def _create_distribution(data):
    """Creates mapping interpolation functions to file for each Movement
    Quality feature

    Args:
        data : data table with historical(7 days) MQ features,
        total_accel and grf for the user

    Returns:
        Interpolation mapping function for each Movement Quality feature
    """
    mS = np.abs(np.array(data.grf))
    mS_norm = np.array(mS/np.nanmean(mS))
    tA = np.abs(np.array(data.total_accel))
    tA_norm = np.array(tA/np.nanmean(tA))
    scale = np.sqrt(tA_norm*mS_norm)
    fn_hDL = _con_fun(np.array(data.contra_hip_drop_lf/(scale)))
    fn_hDR = _con_fun(np.array(data.contra_hip_drop_rf/(scale)))
#    fn_hR = _con_fun(np.array(data.hip_rot/(tA*mS)))
    fn_aRL = _con_fun(np.array(data.ankle_rot_lf/(scale)), True)
    fn_aRR = _con_fun(np.array(data.ankle_rot_rf/(scale)), True)
    fn_lPL = _con_fun(np.array(data.land_pattern_lf/(scale)))
    fn_lPR = _con_fun(np.array(data.land_pattern_rf/(scale)))
    fn_lT = _con_fun(np.array(data.land_time/(scale)))
    fn_fPL = _con_fun(np.array(data.foot_position_lf/(scale)))
    fn_fPR = _con_fun(np.array(data.foot_position_rf/(scale)))
#    fn_lTR = _con_fun(np.array(data.land_time_r/(tA*mS)))

    return fn_hDL, fn_hDR, fn_aRL, fn_aRR, fn_lPL, fn_lPR, fn_lT, fn_fPL, fn_fPR


def _con_fun(dist, double=False):
    """Creates consistency score for individual points and create an
    interpolation object for mapping

    Args:
        dist : distribution to create the mapping function for
        double: Indicator for if the given distribution might have double peaks

    Returns:
        fn: Interpolation mapping function for the given distribution
    """
    # get rid of missing values in the provided distribution
    dist = dist[np.isfinite(dist)]

    #Limit historical data to 1.5M for memory issue (Will get rid later)
    sample_size = min([len(dist), 1500000])
    dist = np.random.choice(dist, size=sample_size, replace=False)
    if len(dist) < 5:
        logger.info('Not enough data to create mapping function')
        dist_sorted = np.array([-1, -.5, 0, .5, 1])
        consistency_score = np.array([np.nan, np.nan, np.nan, np.nan, np.nan])
        fn = UnivariateSpline(dist_sorted, consistency_score)
    elif double is False:
        dist_sorted = np.sort(dist)
        var = np.var(dist_sorted)
        sq_dev = (dist_sorted-np.mean(dist_sorted))**2
        # TODO(Dipesh): adjust limits with more data
        ##max sq_dev is 0, min sq_dev is 100 and is scaled accordingly
        ratio = sq_dev/(len(dist)*var)
        consistency_score = (1-(ratio-min(ratio))/(max(ratio)-min(ratio)))*100
        #extrapolation is done for values outside the range
        fn = UnivariateSpline(dist_sorted, consistency_score)
    elif double is True:
        # If we expect the feature to have multiple modes, it's split into two
        # separate distribution using gaussian mixture model and scored
        # separately and combined
        mix = mixture.GMM(n_components=2)
        comps = mix.fit_predict(dist.reshape(-1, 1))
        sample1 = np.sort(dist[comps == 0], 0)
        sample2 = np.sort(dist[comps == 1], 0)

        if len(sample1) == 0 or len(sample2) == 0:
            dist_sorted = np.sort(dist)
            var = np.var(dist_sorted)
            sq_dev = (dist_sorted-np.mean(dist_sorted))**2
            # TODO(Dipesh): adjust limits with more data
            ##max sq_dev is 0, min sq_dev is 100 and is scaled accordingly
            ratio = sq_dev/(len(dist)*var)
            consistency_score = (1-(ratio-min(ratio))/(max(ratio)-min(ratio)))*100
            #extrapolation is done for values outside the range
            fn = UnivariateSpline(dist_sorted, consistency_score)
        else:
            sq_dev1 = (sample1 - np.mean(sample1))**2
            ratio1 = sq_dev1/(len(sample1)*np.var(sample1))
            sq_dev2 = (sample2 - np.mean(sample2))**2
            ratio2 = sq_dev2/(len(sample2)*np.var(sample2))
            score1 = (1 - (ratio1 - min(ratio1))/(max(ratio1) - min(ratio1)))*100
            score2 = (1 - (ratio2 - min(ratio2))/(max(ratio2) - min(ratio2)))*100
            scores = np.hstack([score1, score2])
            dist_comb = np.hstack([sample1, sample2])
            dict_scores = dict(zip(dist_comb, scores))
            dist_sorted = np.sort(dist_comb)
            scores_sorted = [dict_scores.get(k, 0) for k in dist_sorted]
            fn = UnivariateSpline(dist_sorted, scores_sorted)
    return fn


def _ankle(aRL, aRR, lPL, lPR, lT, fPL, fPR,
           fn_aRL, fn_aRR, fn_lPL, fn_lPR, fn_lT, fn_fPL, fn_fPR):
    """Calculates consistency and symmetry score for each ankle features and
    averages the score for each ankle.
    Args:
        aRL : ankle_rot_l
        aRR : ankle_rot_r
        lPL : land_pattern_l
        lPR : land_pattern_r
        lTL : land_time
        fn_aRL,fn_aRR,fn_lPL,fn_lPR,fn_lT : mapping functions
    Returns:
        consistency_lf: consistency averaged over left ankle features
        consistency_rf: consistency averaged over right ankle features
        ankle_symmetry: symmetry averaged over ankle features
    """
    ##Consistency
    #Call individual interpolation function for each feature
    score_aRL = fn_aRL(aRL)
    score_aRR = fn_aRR(aRR)

    score_lPL = fn_lPL(lPL)
    score_lPR = fn_lPR(lPR)

    score_fPL = fn_fPL(fPL)
    score_fPR = fn_fPR(fPR)

    score_lT = fn_lT(lT)

    #Combine scores for left ankle
    cons_scores_l = np.vstack([score_aRL, score_lPL, score_fPL])
    #interpolation function is set to extrapolate which might
    #result in negative scores.
    cons_scores_l[cons_scores_l > 100] = 100 #set scores higher than 100 to 100
    cons_scores_l[cons_scores_l <= 0] = 0 #set negative scores to 0

    #Combine score for right ankle
    cons_scores_r = np.vstack([score_aRR, score_lPR, score_fPR])
    cons_scores_r[cons_scores_r > 100] = 100
    cons_scores_r[cons_scores_r <= 0] = 0

    #MQ features with missing values will return 'nan' scores.
    #ignore those features when averaging
    consistency_lf = np.nanmean(cons_scores_l, 0)
    consistency_rf = np.nanmean(cons_scores_r, 0)
    ankle_cons_scores = np.vstack([cons_scores_l, cons_scores_r, score_lT])
    ankle_consistency = np.nanmean(ankle_cons_scores, 0)
    logger.info("ankle consistency completed")
    #Calculate symmetry scores for ankle features
    #If all the rows for either left or right features are blank or we have at
    #most 2 non-empty rows, we cannot score so, nan's are returned as score for
    #all rows
    ##Symmetry for ankle rotation
    if all(np.isnan(aRL)) or all(np.isnan(aRR)):
        ankle_rot_score = np.zeros(len(aRL))*np.nan
    elif len(aRL[np.isfinite(aRL)]) < 5 or len(aRR[np.isfinite(aRR)]) < 5:
        ankle_rot_score = np.zeros(len(aRL))*np.nan
    else:
        l_fn_rot, r_fn_rot = _symmetry_score(aRL, aRR)
        score_rot_l = l_fn_rot(aRL)
        score_rot_r = r_fn_rot(aRR)
        scores_rot = np.vstack([score_rot_l, score_rot_r])
        ankle_rot_score = np.nanmean(scores_rot, 0)
        ankle_rot_score[ankle_rot_score > 100] = 100
        ankle_rot_score[ankle_rot_score <= 0] = 0
    logger.info("ankle rotation symmetry complete")
    ##Symmetry for foot position
    if all(np.isnan(fPL)) or all(np.isnan(fPR)):
        foot_pos_score = np.zeros(len(fPL))*np.nan
    elif len(fPL[np.isfinite(fPL)]) < 5 or len(fPR[np.isfinite(fPR)]) < 5:
        foot_pos_score = np.zeros(len(fPL))*np.nan
    else:
        l_fn_pos, r_fn_pos = _symmetry_score(fPL, fPR)
        score_pos_l = l_fn_pos(fPL)
        score_pos_r = r_fn_pos(fPR)
        scores_pos = np.vstack([score_pos_l, score_pos_r])
        foot_pos_score = np.nanmean(scores_pos, 0)
        foot_pos_score[foot_pos_score > 100] = 100
        foot_pos_score[foot_pos_score <= 0] = 0
    logger.info("foot position symmetry complete")
    # Symmetry score for landing pattern
    if all(np.isnan(lPL)) or all(np.isnan(lPR)):
        ankle_pat_score = np.zeros(len(lPL))*np.nan
    elif len(lPL[np.isfinite(lPL)]) < 5 or len(lPR[np.isfinite(lPR)]) < 5:
        ankle_pat_score = np.zeros(len(lPL))*np.nan
    else:
        l_fn_pat, r_fn_pat = _symmetry_score(lPL, lPR)
        score_pat_l = l_fn_pat(lPL)
        score_pat_r = r_fn_pat(lPR)
        scores_pat = np.vstack([score_pat_l, score_pat_r])
        ankle_pat_score = np.nanmean(scores_pat, 0)
        ankle_pat_score[ankle_pat_score > 100] = 100
        ankle_pat_score[ankle_pat_score <= 0] = 0
    logger.info("landing pattern symmetry complete")
    # symmetry score for landing time
    #subset landing time data to create two distributions to compare
    #change negative values to positive so both dist are in same range
    lTL = np.array(np.abs(lT[lT <= 0]))
    lTR = np.array(lT[lT >= 0])

    if all(np.isnan(lT)):
        ankle_tim_score = np.zeros(len(lT))*np.nan
    elif len(lTL[np.isfinite(lTL)]) < 5 or len(lTR[np.isfinite(lTR)]) < 5:
        ankle_tim_score = np.zeros(len(lT))*np.nan
    else:
        l_fn_tim, r_fn_tim = _symmetry_score(lTL, lTR)
        left = np.array(lT)
        left[left > 0] = np.nan
        score_tim_l = l_fn_tim(left)
        right = np.array(lT)
        right[right < 0] = np.nan
        score_tim_r = r_fn_tim(right)
        scores_tim = np.vstack([score_tim_l, score_tim_r])
        ankle_tim_score = np.nanmean(scores_tim, 0)
        ankle_tim_score[ankle_tim_score > 100] = 100
        ankle_tim_score[ankle_tim_score <= 0] = 0
    logger.info("landing time symmetry complete")
    # Aggregate symmetry scores for all four movement features
    ankle_scores = np.vstack([ankle_rot_score, foot_pos_score,
                              ankle_pat_score, ankle_tim_score])
    ankle_symmetry = np.nanmean(ankle_scores, 0)

    return consistency_lf, consistency_rf, ankle_consistency, ankle_symmetry

def _hip(hDL, hDR, fn_hDL, fn_hDR):
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
#    con_score_hR = fn_hR(hR)

    con_scores = np.vstack([con_score_hDL, con_score_hDR])
    #interpolation function is set to extrapolate which might result in
    #negative scores.
    con_scores[con_scores > 100] = 100 #set scores higher than 100 to 100
    con_scores[con_scores <= 0] = 0 #set negative scores to 0
    #MQ features with missing values will return 'nan' scores.
    #ignore those features when averaging
    hip_consistency = np.nanmean(con_scores, 0)
    #Calculate symmetry scores for hip features
    #If all the rows for either left or right features are blank or we have at
    #most 2 non-empty rows, we cannot score so, nan's are returned as score for
    #all rows
    if all(np.isnan(hDL)) or all(np.isnan(hDR)):
        hip_drop_score = np.zeros(len(hDR))*np.nan
    elif len(hDL[np.isfinite(hDL)]) < 5 or len(hDR[np.isfinite(hDR)]) < 5:
        hip_drop_score = np.zeros(len(hDL))*np.nan
    else:
        l_fn_drop, r_fn_drop = _symmetry_score(hDL, hDR)
        score_drop_l = l_fn_drop(hDL)
        score_drop_r = r_fn_drop(hDR)
        scores_drop = np.vstack([score_drop_l, score_drop_r])
        hip_drop_score = np.nanmean(scores_drop, 0)
        hip_drop_score[hip_drop_score > 100] = 100
        hip_drop_score[hip_drop_score <= 0] = 0

    hip_symmetry = hip_drop_score
    return hip_consistency, hip_symmetry


def _symmetry_score(dist_l, dist_r):
    """Calculates symmetry score for each point of the two distribution
    Args:
        dist_l : MQ feature values for left side already controled
        dist_r : MQ feature values for right side already controled
    Returns:

    """
    dist_left = np.sort(dist_l[np.isfinite(dist_l)])
    dist_right = np.sort(dist_r[np.isfinite(dist_r)])

    # Use sample of points in scoring if above threshold
    sample_size = min([len(dist_left), len(dist_right), 100000])
    dist_l1 = np.random.choice(dist_left, size=sample_size,
                               replace=False).reshape(-1, 1)
    dist_r1 = np.random.choice(dist_right, size=sample_size,
                               replace=False).reshape(-1, 1)
    #Bandwith needs to be adjusted with the data length and sd of data
    #using constant for now
    band_left = 1.06*np.std(dist_l1)*(len(dist_l1))**(-.2)
    band_right = 1.06*np.std(dist_r1)*(len(dist_r1))**(-.2)
#    band_left = .05
#    band_right = .05
    kernel_density_l = kde(kernel='gaussian', bandwidth=band_left, rtol=1E-3,
                           atol=1E-3).fit(dist_l1)
    kernel_density_r = kde(kernel='gaussian', bandwidth=band_right, rtol=1E-3,
                           atol=1E-3).fit(dist_r1)
    #Calculate density estimate for left data under both distribution
    #and calculate score based on difference and create a dictionary for
    #mapping
    len_l = min(len(dist_l1), 2000)
    sample_left = np.linspace(min(dist_l1), max(dist_l1), len_l).reshape(-1, 1)
    den_distL_kdeL = np.exp(kernel_density_l.score_samples(sample_left))
    den_distL_kdeR = np.exp(kernel_density_r.score_samples(sample_left))
    dens_left = np.vstack([den_distL_kdeL, den_distL_kdeR])
    max_den_left = np.max(dens_left, 0)
    score_left = (1 - np.abs(den_distL_kdeL - den_distL_kdeR)/max_den_left)*100
    left_score_fn = UnivariateSpline(sample_left, score_left)

    #Calculate density estimate for right data under both distribution
    #and calculate score based on difference and create a dictionary for
    #mapping
    len_r = min(len(dist_r1), 2000)
    sample_right = np.linspace(min(dist_r1), max(dist_r1), len_r).reshape(-1, 1)
    den_distR_kdeL = np.exp(kernel_density_l.score_samples(sample_right))
    den_distR_kdeR = np.exp(kernel_density_r.score_samples(sample_right))
    dens_right = np.vstack([den_distR_kdeL, den_distR_kdeR])
    max_den_right = np.max(dens_right, 0)
    score_right = (1 - np.abs(den_distR_kdeL-den_distR_kdeR)/max_den_right)*100
    right_score_fn = UnivariateSpline(sample_right, score_right)

    return left_score_fn, right_score_fn


if __name__ == '__main__':
    pass
