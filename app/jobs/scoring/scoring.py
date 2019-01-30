# -*- coding: utf-8 -*-
"""
Created on Wed Oct 12 11:16:55 2016

@author:Dipesh Gautam
"""

from __future__ import division
from aws_xray_sdk.core import xray_recorder
from scipy.interpolate import UnivariateSpline
from sklearn.neighbors.kde import KernelDensity as kde
from sklearn import mixture
import copy
import logging
import numpy as np
import pandas as pd


logger = logging.getLogger()

"""
#############################################INPUT/OUTPUT###################
Inputs: DataFrame with movement quality feature current session
        grf_scale: scaling factor for ground reaction forces
Outputs: Input data frame with Consistency and symmetry scores, destructive multiplier,
        destructive and constructive grf and session_duration
        session_grf_elapsed for each timepoint added
#############################################################################
"""


@xray_recorder.capture('app.jobs.scoring.score')
def score(data, grf_scale):
    """
    Average consistency, symmetry, control scores at sensor level,
    ankle/hip level and then average at body level
    Args:
        data : Pandas dataframe with the movement quality features, total_accel,
               grf, ms_elapsed, control score, session_type attributes
        grf_scale: scaling factor for ground reaction forces
    Returns:
        consistency, hip_consistency, ankle_consistency, consistency_lf,
        consistency_rf, symmetry, hip_symmetry, ankle_symmetry, destr_multiplier,
        dest_mech_stress, const_mech_stress, block_duration, session_duration,
        block_mech_stress_elapsed, session_mech_stress_elapsed

    Note: All symmetry and consistency scores are multiplied by grf
          for calculating weighted average while aggregating
    """
    data = _categorize_data(data)
    grf = np.abs(np.array(data.grf)).reshape(-1, )

    control = copy.copy(data.control.values)

    data['ankle_symmetry'] = np.zeros(data.shape[0]) * np.nan
    data['hip_symmetry'] = np.zeros(data.shape[0]) * np.nan
    data['symmetry'] = np.zeros(data.shape[0]) * np.nan
    data['consistency_lf'] = np.zeros(data.shape[0]) * np.nan
    data['consistency_rf'] = np.zeros(data.shape[0]) * np.nan
    data['ankle_consistency'] = np.zeros(data.shape[0]) * np.nan
    data['hip_consistency'] = np.zeros(data.shape[0]) * np.nan
    data['consistency'] = np.zeros(data.shape[0]) * np.nan

    for stance in np.unique(data.stance):
        if stance == 2 or stance == 3:
            cme_to_use = ['adduc_motion_covered',
                          'adduc_range_of_motion',
                          'flex_motion_covered',
                          'flex_range_of_motion',
                          'contact_duration',
                         ]
            rofa_cats = np.append(data.rofa_lf_cat.values, data.rofa_rf_cat.values)
            rofa_cats = rofa_cats[np.isfinite(rofa_cats)]
            for rofa_cat in np.unique(rofa_cats):
                data_sub = data.loc[(data.stance == stance) & ((data.rofa_lf_cat == rofa_cat) | (data.rofa_rf_cat == rofa_cat)), :]
                if data_sub.shape[0] >= 30:
                    _score_subset(data, data_sub, cme_to_use)

    grf = grf / grf_scale

    # Calculate the destructive mechStress multiplier
    data['destr_multiplier'] = ((1 - data['symmetry'].values/100)**2 + (1 - control/100)**2)/2

    data['dest_grf'] = np.array(grf)*np.array(data['destr_multiplier'].values)
    data['const_grf'] = grf - data['dest_grf'].values

    # Multiply each score by mechStress value for weighting
    data['symmetry'] = data['symmetry'] * grf
    data['hip_symmetry'] = data['hip_symmetry'] * grf
    data['ankle_symmetry'] = data['ankle_symmetry'] * grf

    data['consistency_lf'] = data['consistency_lf'] * grf
    data['consistency_rf'] = data['consistency_rf'] * grf
    data['hip_consistency'] = data['hip_consistency'] * grf
    data['ankle_consistency'] = data['ankle_consistency'] * grf
    data['consistency'] = data['consistency'] * grf

    # Block/Session duration
    ms_elapsed = np.array(data.ms_elapsed)
    data['session_duration'] = np.nan_to_num(ms_elapsed).cumsum()/np.nansum(ms_elapsed)

    #MechStress Elapsed
    data['session_grf_elapsed'] = np.nan_to_num(grf).cumsum()/np.nansum(grf)

    return data


@xray_recorder.capture('app.jobs.scoring._score_subset')
def _score_subset(data, data_sub, cme_to_use):
    """
    Run consistency and symmetry scoring on the subset of data and insert the respective scores
    to relevant parts of main pandas dataframe
    Args:
        data: pandas dataframe to store scores
        data_sub: subset of data which is used in scoring
        (Note: index is preserved between the two and used to reinsert scores at correct place)
    Returns:
        None, dataframe data is updated at relevant locations
    """
    ankle_symm, cons_lf, cons_rf, ankle_cons = _ankle(data_sub, cme_to_use)
    hip_symm, hip_cons = _hip(data_sub, cme_to_use)
    symmetry = np.nanmean(np.append(hip_symm.reshape(-1, 1), ankle_symm.reshape(-1, 1), axis=1), axis=1)
    data.loc[data_sub.index, 'ankle_symmetry'] = ankle_symm
    data.loc[data_sub.index, 'hip_symmetry'] = hip_symm
    data.loc[data_sub.index, 'symmetry'] = symmetry

    consistency = np.nanmean(np.append(hip_cons.reshape(-1, 1), ankle_cons.reshape(-1, 1), axis=1), axis=1)
    data.loc[data_sub.index, 'consistency'] = consistency
    data.loc[data_sub.index, 'hip_consistency'] = hip_cons
    data.loc[data_sub.index, 'ankle_consistency'] = ankle_cons
    data.loc[data_sub.index, 'consistency_lf'] = cons_lf
    data.loc[data_sub.index, 'consistency_rf'] = cons_rf


@xray_recorder.capture('app.jobs.scoring._categorize_data')
def _categorize_data(data):
    """
    Categorize and enumerate data based on phase2 categorization
        to control for motion complexity in scoring.
        CMEs during similar complexity are compared against each other in scoring
    Categorizations:
        1) phase: balance, takeoff, impact, contact, non-contact
        2) stance: single leg, double leg
        3) RoFA
        4) RoFP
        5) GRF during balance phase
    """
    rofa_lf_cat = pd.cut(data.rate_force_absorption_lf.values,
                         bins=[0, 2, 4, 8, 20, 1000],
                         labels=False,
                         include_lowest=False,
                         right=True)
    rofa_rf_cat = pd.cut(data.rate_force_absorption_rf.values,
                         bins=[0, 2, 4, 8, 20, 1000],
                         labels=False,
                         include_lowest=False,
                         right=True)
    rofp_lf_cat = pd.cut(data.rate_force_production_lf.values,
                         bins=[0, 2, 4, 8, 20, 1000],
                         labels=False,
                         include_lowest=False,
                         right=True)
    rofp_rf_cat = pd.cut(data.rate_force_production_rf.values,
                         bins=[0, 2, 4, 8, 20, 1000],
                         labels=False,
                         include_lowest=False,
                         right=True)
    balance_grf_cat = pd.cut(data.grf_bal_phase,
                             bins=[0, .5, 1., 1.4, 1000],
                             labels=False,
                             include_lowest=True,
                             right=True)

    data['rofa_lf_cat'] = rofa_lf_cat
    data['rofa_rf_cat'] = rofa_rf_cat
    data['rofp_lf_cat'] = rofp_lf_cat
    data['rofp_rf_cat'] = rofp_rf_cat
    data['balance_grf_cat'] = balance_grf_cat

    return data


@xray_recorder.capture('app.jobs.scoring._ankle')
def _ankle(data, cme):
    """
    Calculates consistency and symmetry score for each ankle features and
    averages the score for each ankle.
    Args:
        data: subset of data to score on (pandas dataframe)
        cme: CMEs to be used in scoring (string)
    Returns:
        ankle_symmetry: symmetry averaged over ankle features
        consistency_lf: consistency averaged over left ankle features
        consistency_rf: consistency averaged over right ankle features
        ankle_consistency: consistency averaged over right and left ankles
    """
    sub_len = data.shape[0]
    symmetry_scores = np.zeros([sub_len, 1]) * np.nan
    consistency_scores_lf = np.zeros([sub_len, 1]) * np.nan
    consistency_scores_rf = np.zeros([sub_len, 1]) * np.nan
    # Calculate symmetry scores for ankle features
    # If all the rows for either left or right features are blank or we have at
    # most 2 non-empty rows, we cannot score so, nan's are returned as score for
    # all rows
    ## Scoring for ankle rotation
    if 'ankle_rot' in cme:
        # symmetry
        left = copy.copy(data.ankle_rot_lf.values)
        right = copy.copy(data.ankle_rot_rf.values)
        symmetry_scores = _run_symmetry(left, right, symmetry_scores)

        # consistency
        consistency_scores_lf = _run_consistency(left, consistency_scores_lf)
        consistency_scores_rf = _run_consistency(right, consistency_scores_rf)

    if 'land_pattern' in cme:
        # symmetry
        left = copy.copy(data.land_pattern_lf.values)
        right = copy.copy(data.land_pattern_rf.values)
        symmetry_scores = _run_symmetry(left, right, symmetry_scores)

        # consistency
        consistency_scores_lf = _run_consistency(left, consistency_scores_lf)
        consistency_scores_rf = _run_consistency(right, consistency_scores_rf)

    # Scoring for for landing time
    # subset landing time data to create two distributions to compare
    # change negative values to positive so both dist are in same range
    if 'land_time' in cme:
        # symmetry
        land_time = copy.copy(data.land_time.values).reshape(-1,)
        left = copy.copy(land_time)
        right = copy.copy(land_time)
        left[left > 0] = np.nan
        left = np.abs(left)
        right[right < 0] = np.nan
        symmetry_scores = _run_symmetry(left, right, symmetry_scores)

        # consistency
        consistency_scores_lf = _run_consistency(left, consistency_scores_lf)
        consistency_scores_rf = _run_consistency(right, consistency_scores_rf)

    ## Scoring for adduction motion covered
    if 'adduc_motion_covered' in cme:
        left = copy.copy(data.adduc_motion_covered_abs_lf.values)
        right = copy.copy(data.adduc_motion_covered_abs_rf.values)
        symmetry_scores = _run_symmetry(left, right, symmetry_scores)

        # consistency
        consistency_scores_lf = _run_consistency(left, consistency_scores_lf)
        consistency_scores_rf = _run_consistency(right, consistency_scores_rf)

    ## Scoring for adduction range of motion
    if 'adduc_range_of_motion' in cme:
        left = copy.copy(data.adduc_range_of_motion_lf.values)
        right = copy.copy(data.adduc_range_of_motion_rf.values)
        symmetry_scores = _run_symmetry(left, right, symmetry_scores)

        # consistency
        consistency_scores_lf = _run_consistency(left, consistency_scores_lf)
        consistency_scores_rf = _run_consistency(right, consistency_scores_rf)

    ## Scoring for flexion motion covered
    if 'flex_motion_covered' in cme:
        left = copy.copy(data.flex_motion_covered_abs_lf.values)
        right = copy.copy(data.flex_motion_covered_abs_rf.values)
        symmetry_scores = _run_symmetry(left, right, symmetry_scores)

        # consistency
        consistency_scores_lf = _run_consistency(left, consistency_scores_lf)
        consistency_scores_rf = _run_consistency(right, consistency_scores_rf)

    ## Scoring for flexion range of moton
    if 'flex_range_of_motion' in cme:
        left = copy.copy(data.flex_range_of_motion_lf.values)
        right = copy.copy(data.flex_range_of_motion_rf.values)
        symmetry_scores = _run_symmetry(left, right, symmetry_scores)

        # consistency
        consistency_scores_lf = _run_consistency(left, consistency_scores_lf)
        consistency_scores_rf = _run_consistency(right, consistency_scores_rf)


    ## Scoring for contact duration
    if 'contact_duration' in cme:
        left = copy.copy(data.contact_duration_lf.values)
        right = copy.copy(data.contact_duration_rf.values)
        symmetry_scores = _run_symmetry(left, right, symmetry_scores)

        # consistency
        consistency_scores_lf = _run_consistency(left, consistency_scores_lf)
        consistency_scores_rf = _run_consistency(right, consistency_scores_rf)

    # Average the scores from all the different CMEs
    consistency_lf = np.nanmean(consistency_scores_lf, axis=1).reshape(-1, 1)
    consistency_rf = np.nanmean(consistency_scores_rf, axis=1).reshape(-1, 1)
    ankle_cons = np.append(consistency_lf, consistency_rf, axis=1)
    ankle_consistency = np.nanmean(ankle_cons, axis=1)

    ankle_symmetry = np.nanmean(symmetry_scores, axis=1)

    return ankle_symmetry, consistency_lf, consistency_rf, ankle_consistency


@xray_recorder.capture('app.jobs.scoring._hip')
def _hip(data, cme):
    """
    Calculates consistency and symmetry score for each hip features and averages the score
    Args:
        data: subset of data to score on (pandas dataframe)
        cme: CMEs to be used in scoring (string)
    Returns:
        hip_symmetry: symmetry averaged over all hip features (num 0-100)
        hip_consistency: consistency averaged over all hip features (num 0-100)
    """
#    sub_len = data.shape[0]
    symmetry_scores = np.zeros([data.shape[0], 1]) * np.nan
    consistency_scores = np.zeros([data.shape[0], 1]) * np.nan

    #Calculate symmetry scores for hip features
    #If all the rows for either left or right features are blank or we have at
    #most 2 non-empty rows, we cannot score so, nan's are returned as score for
    #all rows
#    ground_lf = [0, 1, 4, 6]
#    ground_rf = [0, 2, 5, 7]
    ground_lf = [0, 2, 3]
    ground_rf = [0, 2, 3]
    if 'hip_drop' in cme:
        # symmetry
        left = copy.copy(data.contra_hip_drop_lf.values)
        right = copy.copy(data.contra_hip_drop_rf.values)
        symmetry_scores = _run_symmetry(left, right, symmetry_scores)

        # consistency
        consistency_scores = _run_consistency(left, consistency_scores)
        consistency_scores = _run_consistency(right, consistency_scores)

    if 'adduc_motion_covered' in cme:
        # symmetry
        adduc_motion = copy.copy(data.adduc_motion_covered_abs_h.values)
        left = copy.copy(adduc_motion)
        right = copy.copy(adduc_motion)
        left[np.array([i not in ground_lf for i in data.phase_lf])] = np.nan
        right[np.array([i not in ground_rf for i in data.phase_rf])] = np.nan
        symmetry_scores = _run_symmetry(left, right, symmetry_scores)

        # consistency
        consistency_scores = _run_consistency(adduc_motion, consistency_scores)

    if 'adduc_range_of_motion' in cme:
        # symmetry
        adduc_rom = copy.copy(data.adduc_range_of_motion_h.values)
        left = copy.copy(adduc_rom)
        right = copy.copy(adduc_rom)
        left[np.array([i not in ground_lf for i in data.phase_lf])] = np.nan
        right[np.array([i not in ground_rf for i in data.phase_rf])] = np.nan
        symmetry_scores = _run_symmetry(left, right, symmetry_scores)

        # consistency
        consistency_scores = _run_consistency(adduc_rom, consistency_scores)

    if 'flex_motion_covered' in cme:
        # symmetry
        flex_motion = copy.copy(data.flex_motion_covered_abs_h.values)
        left = copy.copy(flex_motion)
        right = copy.copy(flex_motion)
        left[np.array([i not in ground_lf for i in data.phase_lf])] = np.nan
        right[np.array([i not in ground_rf for i in data.phase_rf])] = np.nan
        symmetry_scores = _run_symmetry(left, right, symmetry_scores)

        # consistency
        consistency_scores = _run_consistency(flex_motion, consistency_scores)

    if 'flex_range_of_motion' in cme:
        # symmetry
        flex_rom = copy.copy(data.flex_range_of_motion_h.values)
        left = copy.copy(flex_rom)
        right = copy.copy(flex_rom)
        left[np.array([i not in ground_lf for i in data.phase_lf])] = np.nan
        right[np.array([i not in ground_rf for i in data.phase_rf])] = np.nan
        symmetry_scores = _run_symmetry(left, right, symmetry_scores)

        # consistency
        consistency_scores = _run_consistency(flex_rom, consistency_scores)

    # Average the scores from all the different CMEs
    hip_consistency = np.nanmean(consistency_scores, axis=1)

    hip_symmetry = np.nanmean(symmetry_scores, axis=1)

    return hip_symmetry, hip_consistency


@xray_recorder.capture('app.jobs.scoring._run_symmetry')
def _run_symmetry(left, right, symmetry_scores):
    """
    Compute symmetry score for the given left, right CME pair and append to the numpy array
    Args:
        left: left CME
        right: right CME
        symmetry_scores: numpy array with symmetry scores for CMEs already scored
    Returns:
        symmetry_scores: same as input with scores for current CME appended
    """
    size = left.shape[0]
    if all(np.isnan(left)) or all(np.isnan(right)):
        scores = np.zeros(size) * np.nan
    elif len(left[np.isfinite(left)]) < 5 or len(right[np.isfinite(right)]) < 5:
        scores = np.zeros(size) * np.nan
    elif np.nanstd(left) < 1e-4 or np.nanstd(right) < 1e-4:
        scores = np.zeros(size) * np.nan
    else:
        try:
            l_fn, r_fn = _symmetry_score(left, right, kernel='gaussian')
            score_l = l_fn(left)
            score_r = r_fn(right)
            scores = np.vstack([score_l, score_r])
            scores = np.nanmean(scores, 0)
            scores[scores > 100] = 100
            scores[scores <= 0] = 0
        except ValueError:
            scores = np.zeros(size) * np.nan

    symmetry_scores = np.append(symmetry_scores, scores.reshape(-1, 1), axis=1)

    return symmetry_scores


@xray_recorder.capture('app.jobs.scoring._run_consistency')
def _run_consistency(dist, consistency_scores, double=False):
    """
    Compute symmetry score for the given left, right CME pair and append to the numpy array
    Args:
        dist: CME to be scored
        consistency_scores: numpy array with consistency scores for CMEs already scored
    Returns:
        consistency_scores: same as input with scores for current CME appended
    """
    cons_fn = _con_fun(dist, double)
    cons = np.array(cons_fn(dist))
    cons[cons > 100] = 100
    cons[cons < 0] = 0

    consistency_scores = np.append(consistency_scores, cons.reshape(-1, 1), axis=1)

    return consistency_scores


@xray_recorder.capture('app.jobs.scoring._symmetry_score')
def _symmetry_score(dist_l, dist_r, kernel):
    """
    Calculates symmetry score for each point of the two distribution
    Args:
        dist_l : MQ feature values for left side already controled
        dist_r : MQ feature values for right side already controled
    Returns:
        left_score_fn: interpolation function for left
        right_score_fn: interpolation function for right
    """
    kernel = 'gaussian'
    dist_left = np.sort(dist_l[np.isfinite(dist_l)])
    dist_right = np.sort(dist_r[np.isfinite(dist_r)])

    # Use sample of points in scoring if above threshold
    np.random.seed(0115)
    sample_size = min([len(dist_left), len(dist_right), 10000])
    dist_l1 = np.random.choice(dist_left, size=sample_size,
                               replace=False).reshape(-1, 1)
    dist_r1 = np.random.choice(dist_right, size=sample_size,
                               replace=False).reshape(-1, 1)
    #Bandwith needs to be adjusted with the data length and sd of data
    #using constant for now
    band_left = 1.06*np.std(dist_l1)*(len(dist_l1))**(-.2)
    band_right = 1.06*np.std(dist_r1)*(len(dist_r1))**(-.2)

    kernel_density_l = kde(kernel=kernel, bandwidth=band_left, rtol=1E-3,
                           atol=1E-3).fit(dist_l1)
    kernel_density_r = kde(kernel=kernel, bandwidth=band_right, rtol=1E-3,
                           atol=1E-3).fit(dist_r1)
    #Calculate density estimate for left data under both distribution
    #and calculate score based on difference and create a dictionary for
    #mapping
    len_l = min(len(dist_l1), 1000)
    sample_left = np.linspace(min(dist_l1), max(dist_l1), len_l).reshape(-1, 1)
    den_dist_l_kde_l = np.exp(kernel_density_l.score_samples(sample_left))
    den_dist_l_kde_r = np.exp(kernel_density_r.score_samples(sample_left))
    dens_left = np.vstack([den_dist_l_kde_l, den_dist_l_kde_r])
    max_den_left = np.max(dens_left)
    score_left = (1 - np.abs(den_dist_l_kde_l - den_dist_l_kde_r)/max_den_left)*100
    left_score_fn = UnivariateSpline(sample_left, score_left)

    # Calculate density estimate for right data under both distribution
    # and calculate score based on difference and create a dictionary for
    # mapping
    len_r = min(len(dist_r1), 1000)
    sample_right = np.linspace(min(dist_r1), max(dist_r1), len_r).reshape(-1, 1)
    den_dist_r_kde_l = np.exp(kernel_density_l.score_samples(sample_right))
    den_dist_r_kde_r = np.exp(kernel_density_r.score_samples(sample_right))
    dens_right = np.vstack([den_dist_r_kde_l, den_dist_r_kde_r])
    max_den_right = np.max(dens_right)
    score_right = (1 - np.abs(den_dist_r_kde_l-den_dist_r_kde_r)/max_den_right)*100
    right_score_fn = UnivariateSpline(sample_right, score_right)

    return left_score_fn, right_score_fn


@xray_recorder.capture('app.jobs.scoring._con_fun')
def _con_fun(dist, double=False):
    """
    Creates consistency score for individual points and create an
    interpolation object for mapping

    Args:
        dist : distribution to create the mapping function for
        double: Indicator for if the given distribution might have double peaks

    Returns:
        function: Interpolation mapping function for the given distribution
    """
    # get rid of missing values in the provided distribution
    dist = dist[np.isfinite(dist)]

    #Limit historical data to 1.5M for memory issue (Will get rid later)
    sample_size = min([len(dist), 50000])
    try:
        if len(dist) < 5:
            logger.info('Not enough data to create mapping function')
            dist_sorted = np.array([-1, -.5, 0, .5, 1])
            consistency_score = np.array([np.nan, np.nan, np.nan, np.nan, np.nan])
            func = UnivariateSpline(dist_sorted, consistency_score)
        elif double is False:
            dist = np.random.choice(dist, size=sample_size, replace=False)
            dist_sorted = np.sort(dist)
            var = np.var(dist_sorted)
            sq_dev = (dist_sorted-np.mean(dist_sorted))**2
            # TODO(Dipesh): adjust limits with more data
            ## 95th perc sq_dev is 0, 5th perc sq_dev is 100 and is scaled accordingly
            ratio = sq_dev/(len(dist)*var)
            max_ratio = np.percentile(ratio, 95)
            min_ratio = np.percentile(ratio, 5)
            consistency_score = (1-(ratio-min_ratio)/(max_ratio-min_ratio))*100
            #extrapolation is done for values outside the range
            dist_sorted = dist_sorted.reshape(-1, 1)
            consistency_score = consistency_score.reshape(-1, 1)
            func = UnivariateSpline(dist_sorted, consistency_score)
        elif double is True:
            dist = np.random.choice(dist, size=sample_size, replace=False)
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
            ## 95th perc sq_dev is 0, 5th perc sq_dev is 100 and is scaled accordingly
                ratio = sq_dev/(len(dist)*var)
                max_ratio = np.percentile(ratio, 95)
                min_ratio = np.percentile(ratio, 5)
                consistency_score = (1-(ratio-min_ratio)/(max_ratio-min_ratio))*100
                #extrapolation is done for values outside the range
                func = UnivariateSpline(dist_sorted, consistency_score)
            else:
                sq_dev1 = (sample1 - np.mean(sample1))**2
                ratio1 = sq_dev1/(len(sample1)*np.var(sample1))
                sq_dev2 = (sample2 - np.mean(sample2))**2
                ratio2 = sq_dev2/(len(sample2)*np.var(sample2))
                max_ratio = np.percentile(ratio1, 95)
                min_ratio = np.percentile(ratio1, 5)
                score1 = (1-(ratio1-min_ratio)/(max_ratio-min_ratio))*100
                max_ratio = np.percentile(ratio2, 95)
                min_ratio = np.percentile(ratio2, 5)
                score2 = (1-(ratio2-min_ratio)/(max_ratio-min_ratio))*100
                # score1 = (1 - (ratio1 - min(ratio1))/(max(ratio1) - min(ratio1)))*100
                # score2 = (1 - (ratio2 - min(ratio2))/(max(ratio2) - min(ratio2)))*100
                scores = np.hstack([score1, score2])
                dist_comb = np.hstack([sample1, sample2])
                dict_scores = dict(zip(dist_comb, scores))
                dist_sorted = np.sort(dist_comb)
                scores_sorted = [dict_scores.get(k, 0) for k in dist_sorted]
                func = UnivariateSpline(dist_sorted, scores_sorted)
    except:
        dist_sorted = np.array([-1, -.5, 0, .5, 1])
        consistency_score = np.array([np.nan, np.nan, np.nan, np.nan, np.nan])
        func = UnivariateSpline(dist_sorted, consistency_score)

    return func


if __name__ == '__main__':
    pass
