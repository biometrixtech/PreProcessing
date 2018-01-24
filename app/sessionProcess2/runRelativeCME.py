# -*- coding: utf-8 -*-
"""
Created on Tue Nov 28 15:16:08 2017

@author: court
"""

import numpy as np
import pandas as pd
import copy
from scipy.signal import butter, filtfilt


def run_relative_CMEs(data):
    '''
    Function that takes a (nxm) data frame and returns an (nx(m+p)) data frame
    with p relatively calculated CME values attached.
    
    Arg --
        data: data frame with at least the following (nx1) columns attached -
            - epoch_time - timestamp of data
            - stance - enumerated stance value
            - phase_lf - enumerated left phase value
            - phase_rf - enumerated right phase value
            - LeX - left foot adduction
            - LeY - left foot flexion
            - HeX - hip adduction
            - HeY - hip flexion
            - ReX - right foot adduction
            - ReY - right foot flexion
    
    Return --
        data: data frame with the same columns attached as the input, with
        additional columns of - 
            - adduc_motion_covered_lf - sum of motion in radians covered in
                each phase contacting the ground, normalized by time (rad/sec)
            - adduc_range_of_motion_lf - range of motion in radians covered
                in each phase contacting the ground, normalized by time (rad/sec)
            - flex_motion_covered_lf - sum of motion in radians covered in
                each phase contacting the ground, normalized by time (rad/sec)
            - flex_range_of_motion_lf - range of motion in radians covered
                in each phase contacting the ground, normalized by time (rad/sec)
            - contact_duration_lf - duration of time spent in each phase
                contacting the ground (seconds)
            - adduc_motion_covered_h - sum of motion in radians covered in
                each phase contacting the ground, normalized by time (rad/sec)
            - adduc_range_of_motion_h - range of motion in radians covered
                in each phase contacting the ground, normalized by time (rad/sec)
            - flex_motion_covered_h - sum of motion in radians covered in
                each phase contacting the ground, normalized by time (rad/sec)
            - flex_range_of_motion_h - range of motion in radians covered
                in each phase contacting the ground, normalized by time (rad/sec)
            - contact_duration_h - duration of time spent in each phase
                contacting the ground (seconds)
            - adduc_motion_covered_rf - sum of motion in radians covered in
                each phase contacting the ground, normalized by time (rad/sec)
            - adduc_range_of_motion_rf - range of motion in radians covered
                in each phase contacting the ground, normalized by time (rad/sec)
            - flex_motion_covered_rf - sum of motion in radians covered in
                each phase contacting the ground, normalized by time (rad/sec)
            - flex_range_of_motion_rf - range of motion in radians covered
                in each phase contacting the ground, normalized by time (rad/sec)
            - contact_duration_rf - duration of time spent in each phase
                contacting the ground (seconds)
    '''
    
    length = data.epoch_time
    
    stance = data.stance.reshape(-1, 1)
#    ms_elapsed = np.ediff1d(data.epoch_time)
    ms_elapsed = np.array([10] * len(length)).reshape(-1, 1)

    lphase = copy.deepcopy(data.phase_lf.reshape(-1, 1))
    rphase = copy.deepcopy(data.phase_rf.reshape(-1, 1))

    adduction_L = data.LeX.reshape(-1, 1)
    flexion_L = data.LeY.reshape(-1, 1)
    adduction_H = data.HeX.reshape(-1, 1)
    flexion_H = data.HeY.reshape(-1, 1)
    adduction_R = data.ReX.reshape(-1, 1)
    flexion_R = data.ReY.reshape(-1, 1)

    alnorm_motion_covered = np.empty(len(length)).reshape(-1, 1) * np.nan
    alnorm_range_of_motion = np.empty(len(length)).reshape(-1, 1) * np.nan

    ahnorm_motion_covered = np.empty(len(length)).reshape(-1, 1) * np.nan
    ahnorm_range_of_motion = np.empty(len(length)).reshape(-1, 1) * np.nan

    arnorm_motion_covered = np.empty(len(length)).reshape(-1, 1) * np.nan
    arnorm_range_of_motion = np.empty(len(length)).reshape(-1, 1) * np.nan

    flnorm_motion_covered = np.empty(len(length)).reshape(-1, 1) * np.nan
    flnorm_range_of_motion = np.empty(len(length)).reshape(-1, 1) * np.nan
    flcontact_duration = np.empty(len(length)).reshape(-1, 1) * np.nan

    fhnorm_motion_covered = np.empty(len(length)).reshape(-1, 1) * np.nan
    fhnorm_range_of_motion = np.empty(len(length)).reshape(-1, 1) * np.nan
    fhcontact_duration = np.empty(len(length)).reshape(-1, 1) * np.nan

    frnorm_motion_covered = np.empty(len(length)).reshape(-1, 1) * np.nan
    frnorm_range_of_motion = np.empty(len(length)).reshape(-1, 1) * np.nan
    frcontact_duration = np.empty(len(length)).reshape(-1, 1) * np.nan

    # filter data 
    l0ranges = _num_runs(lphase, 0)
    l1ranges = _num_runs(lphase, 1)
    l4ranges = _num_runs(lphase, 4)
    l6ranges = _num_runs(lphase, 6)

    hl0ranges = _num_runs(lphase, 0)
    hl1ranges = _num_runs(lphase, 1)
    hl2ranges = _num_runs(lphase, 2)
    hl4ranges = _num_runs(lphase, 4)
    hl5ranges = _num_runs(lphase, 5)
    hl6ranges = _num_runs(lphase, 6)
    hl7ranges = _num_runs(lphase, 7)
    hr1ranges = _num_runs(rphase, 1)
    hr2ranges = _num_runs(rphase, 2)
    hr4ranges = _num_runs(rphase, 4)
    hr5ranges = _num_runs(rphase, 5)
    hr6ranges = _num_runs(rphase, 6)
    hr7ranges = _num_runs(rphase, 7)

    r0ranges = _num_runs(rphase, 0)
    r2ranges = _num_runs(rphase, 2)
    r5ranges = _num_runs(rphase, 5)
    r7ranges = _num_runs(rphase, 7)

    # Calculate CMEs agnostic to drift
    flcontact_duration = _drift_agnostic_CMES(flcontact_duration, l0ranges, stance)
    flcontact_duration = _drift_agnostic_CMES(flcontact_duration, l1ranges, stance)
    flcontact_duration = _drift_agnostic_CMES(flcontact_duration, l4ranges, stance)
    flcontact_duration = _drift_agnostic_CMES(flcontact_duration, l6ranges, stance)
    fhcontact_duration = _drift_agnostic_CMES(fhcontact_duration, hl0ranges, stance)
    fhcontact_duration = _drift_agnostic_CMES(fhcontact_duration, hl1ranges, stance)
    fhcontact_duration = _drift_agnostic_CMES(fhcontact_duration, hl2ranges, stance)
    fhcontact_duration = _drift_agnostic_CMES(fhcontact_duration, hl4ranges, stance)
    fhcontact_duration = _drift_agnostic_CMES(fhcontact_duration, hl5ranges, stance)
    fhcontact_duration = _drift_agnostic_CMES(fhcontact_duration, hl6ranges, stance)
    fhcontact_duration = _drift_agnostic_CMES(fhcontact_duration, hl7ranges, stance)
    fhcontact_duration = _drift_agnostic_CMES(fhcontact_duration, hr1ranges, stance)
    fhcontact_duration = _drift_agnostic_CMES(fhcontact_duration, hr2ranges, stance)
    fhcontact_duration = _drift_agnostic_CMES(fhcontact_duration, hr4ranges, stance)
    fhcontact_duration = _drift_agnostic_CMES(fhcontact_duration, hr5ranges, stance)
    fhcontact_duration = _drift_agnostic_CMES(fhcontact_duration, hr6ranges, stance)
    fhcontact_duration = _drift_agnostic_CMES(fhcontact_duration, hr7ranges, stance)
    frcontact_duration = _drift_agnostic_CMES(frcontact_duration, r0ranges, stance)
    frcontact_duration = _drift_agnostic_CMES(frcontact_duration, r2ranges, stance)
    frcontact_duration = _drift_agnostic_CMES(frcontact_duration, r5ranges, stance)
    frcontact_duration = _drift_agnostic_CMES(frcontact_duration, r7ranges, stance)

    # filter out foot data potentially skewed by drift filter and run foot CMEs
    dynamic_range_lf = _detect_long_dynamic(data.corrupt_lf)
    dynamic_range_rf = _detect_long_dynamic(data.corrupt_rf)  
    l0ranges = _remove_filtered_ends(l0ranges, dynamic_range_lf)
    l1ranges = _remove_filtered_ends(l1ranges, dynamic_range_lf)
    l4ranges = _remove_filtered_ends(l4ranges, dynamic_range_lf)
    l6ranges = _remove_filtered_ends(l6ranges, dynamic_range_lf)
    r0ranges = _remove_filtered_ends(r0ranges, dynamic_range_rf)
    r2ranges = _remove_filtered_ends(r2ranges, dynamic_range_rf)
    r5ranges = _remove_filtered_ends(r5ranges, dynamic_range_rf)
    r7ranges = _remove_filtered_ends(r7ranges, dynamic_range_rf)


    alnorm_motion_covered, alnorm_range_of_motion = _driftless_CMES(adduction_L, l0ranges, ms_elapsed, alnorm_motion_covered, alnorm_range_of_motion)
    alnorm_motion_covered, alnorm_range_of_motion = _driftless_CMES(adduction_L, l1ranges, ms_elapsed, alnorm_motion_covered, alnorm_range_of_motion)
    alnorm_motion_covered, alnorm_range_of_motion = _driftless_CMES(adduction_L, l4ranges, ms_elapsed, alnorm_motion_covered, alnorm_range_of_motion)
    alnorm_motion_covered, alnorm_range_of_motion = _driftless_CMES(adduction_L, l6ranges, ms_elapsed, alnorm_motion_covered, alnorm_range_of_motion)
    arnorm_motion_covered, arnorm_range_of_motion = _driftless_CMES(adduction_R, r0ranges, ms_elapsed, arnorm_motion_covered, arnorm_range_of_motion)
    arnorm_motion_covered, arnorm_range_of_motion = _driftless_CMES(adduction_R, r2ranges, ms_elapsed, arnorm_motion_covered, arnorm_range_of_motion)
    arnorm_motion_covered, arnorm_range_of_motion = _driftless_CMES(adduction_R, r5ranges, ms_elapsed, arnorm_motion_covered, arnorm_range_of_motion)
    arnorm_motion_covered, arnorm_range_of_motion = _driftless_CMES(adduction_R, r7ranges, ms_elapsed, arnorm_motion_covered, arnorm_range_of_motion)
    flnorm_motion_covered, flnorm_range_of_motion = _driftless_CMES(flexion_L, l0ranges, ms_elapsed, flnorm_motion_covered, flnorm_range_of_motion)
    flnorm_motion_covered, flnorm_range_of_motion = _driftless_CMES(flexion_L, l1ranges, ms_elapsed, flnorm_motion_covered, flnorm_range_of_motion)
    flnorm_motion_covered, flnorm_range_of_motion = _driftless_CMES(flexion_L, l4ranges, ms_elapsed, flnorm_motion_covered, flnorm_range_of_motion)
    flnorm_motion_covered, flnorm_range_of_motion = _driftless_CMES(flexion_L, l6ranges, ms_elapsed, flnorm_motion_covered, flnorm_range_of_motion)
    frnorm_motion_covered, frnorm_range_of_motion = _driftless_CMES(flexion_R, r0ranges, ms_elapsed, frnorm_motion_covered, frnorm_range_of_motion)
    frnorm_motion_covered, frnorm_range_of_motion = _driftless_CMES(flexion_R, r2ranges, ms_elapsed, frnorm_motion_covered, frnorm_range_of_motion)
    frnorm_motion_covered, frnorm_range_of_motion = _driftless_CMES(flexion_R, r5ranges, ms_elapsed, frnorm_motion_covered, frnorm_range_of_motion)
    frnorm_motion_covered, frnorm_range_of_motion = _driftless_CMES(flexion_R, r7ranges, ms_elapsed, frnorm_motion_covered, frnorm_range_of_motion)

    # filter out hip data potentially skewed by drift filter and run hip CMEs
    hl0ranges = _remove_filtered_ends(hl0ranges, dynamic_range_lf)
    hl0ranges = _remove_filtered_ends(hl0ranges, dynamic_range_rf)
    hl1ranges = _remove_filtered_ends(hl1ranges, dynamic_range_lf)
    hl2ranges = _remove_filtered_ends(hl2ranges, dynamic_range_lf)
    hl4ranges = _remove_filtered_ends(hl4ranges, dynamic_range_lf)
    hl5ranges = _remove_filtered_ends(hl5ranges, dynamic_range_lf)
    hl6ranges = _remove_filtered_ends(hl6ranges, dynamic_range_lf)
    hl7ranges = _remove_filtered_ends(hl7ranges, dynamic_range_lf)
    hr1ranges = _remove_filtered_ends(hr1ranges, dynamic_range_rf)
    hr2ranges = _remove_filtered_ends(hr2ranges, dynamic_range_rf)
    hr4ranges = _remove_filtered_ends(hr4ranges, dynamic_range_rf)
    hr5ranges = _remove_filtered_ends(hr5ranges, dynamic_range_rf)
    hr6ranges = _remove_filtered_ends(hr6ranges, dynamic_range_rf)
    hr7ranges = _remove_filtered_ends(hr7ranges, dynamic_range_rf)

    ahnorm_motion_covered, ahnorm_range_of_motion = _driftless_CMES(adduction_H, hl0ranges, ms_elapsed, ahnorm_motion_covered, ahnorm_range_of_motion)
    ahnorm_motion_covered, ahnorm_range_of_motion = _driftless_CMES(adduction_H, hl1ranges, ms_elapsed, ahnorm_motion_covered, ahnorm_range_of_motion)
    ahnorm_motion_covered, ahnorm_range_of_motion = _driftless_CMES(adduction_H, hl2ranges, ms_elapsed, ahnorm_motion_covered, ahnorm_range_of_motion)
    ahnorm_motion_covered, ahnorm_range_of_motion = _driftless_CMES(adduction_H, hl4ranges, ms_elapsed, ahnorm_motion_covered, ahnorm_range_of_motion)
    ahnorm_motion_covered, ahnorm_range_of_motion = _driftless_CMES(adduction_H, hl5ranges, ms_elapsed, ahnorm_motion_covered, ahnorm_range_of_motion)
    ahnorm_motion_covered, ahnorm_range_of_motion = _driftless_CMES(adduction_H, hl6ranges, ms_elapsed, ahnorm_motion_covered, ahnorm_range_of_motion)
    ahnorm_motion_covered, ahnorm_range_of_motion = _driftless_CMES(adduction_H, hl7ranges, ms_elapsed, ahnorm_motion_covered, ahnorm_range_of_motion)
    ahnorm_motion_covered, ahnorm_range_of_motion = _driftless_CMES(adduction_H, hr1ranges, ms_elapsed, ahnorm_motion_covered, ahnorm_range_of_motion)
    ahnorm_motion_covered, ahnorm_range_of_motion = _driftless_CMES(adduction_H, hr2ranges, ms_elapsed, ahnorm_motion_covered, ahnorm_range_of_motion)
    ahnorm_motion_covered, ahnorm_range_of_motion = _driftless_CMES(adduction_H, hr4ranges, ms_elapsed, ahnorm_motion_covered, ahnorm_range_of_motion)
    ahnorm_motion_covered, ahnorm_range_of_motion = _driftless_CMES(adduction_H, hr5ranges, ms_elapsed, ahnorm_motion_covered, ahnorm_range_of_motion)
    ahnorm_motion_covered, ahnorm_range_of_motion = _driftless_CMES(adduction_H, hr6ranges, ms_elapsed, ahnorm_motion_covered, ahnorm_range_of_motion)
    ahnorm_motion_covered, ahnorm_range_of_motion = _driftless_CMES(adduction_H, hr7ranges, ms_elapsed, ahnorm_motion_covered, ahnorm_range_of_motion)

    fhnorm_motion_covered, fhnorm_range_of_motion = _driftless_CMES(flexion_H, hl0ranges, ms_elapsed, fhnorm_motion_covered, fhnorm_range_of_motion)
    fhnorm_motion_covered, fhnorm_range_of_motion = _driftless_CMES(flexion_H, hl1ranges, ms_elapsed, fhnorm_motion_covered, fhnorm_range_of_motion)
    fhnorm_motion_covered, fhnorm_range_of_motion = _driftless_CMES(flexion_H, hl2ranges, ms_elapsed, fhnorm_motion_covered, fhnorm_range_of_motion)
    fhnorm_motion_covered, fhnorm_range_of_motion = _driftless_CMES(flexion_H, hl4ranges, ms_elapsed, fhnorm_motion_covered, fhnorm_range_of_motion)
    fhnorm_motion_covered, fhnorm_range_of_motion = _driftless_CMES(flexion_H, hl5ranges, ms_elapsed, fhnorm_motion_covered, fhnorm_range_of_motion)
    fhnorm_motion_covered, fhnorm_range_of_motion = _driftless_CMES(flexion_H, hl6ranges, ms_elapsed, fhnorm_motion_covered, fhnorm_range_of_motion)
    fhnorm_motion_covered, fhnorm_range_of_motion = _driftless_CMES(flexion_H, hl7ranges, ms_elapsed, fhnorm_motion_covered, fhnorm_range_of_motion)
    fhnorm_motion_covered, fhnorm_range_of_motion = _driftless_CMES(flexion_H, hr1ranges, ms_elapsed, fhnorm_motion_covered, fhnorm_range_of_motion)
    fhnorm_motion_covered, fhnorm_range_of_motion = _driftless_CMES(flexion_H, hr2ranges, ms_elapsed, fhnorm_motion_covered, fhnorm_range_of_motion)
    fhnorm_motion_covered, fhnorm_range_of_motion = _driftless_CMES(flexion_H, hr4ranges, ms_elapsed, fhnorm_motion_covered, fhnorm_range_of_motion)
    fhnorm_motion_covered, fhnorm_range_of_motion = _driftless_CMES(flexion_H, hr5ranges, ms_elapsed, fhnorm_motion_covered, fhnorm_range_of_motion)
    fhnorm_motion_covered, fhnorm_range_of_motion = _driftless_CMES(flexion_H, hr6ranges, ms_elapsed, fhnorm_motion_covered, fhnorm_range_of_motion)
    fhnorm_motion_covered, fhnorm_range_of_motion = _driftless_CMES(flexion_H, hr7ranges, ms_elapsed, fhnorm_motion_covered, fhnorm_range_of_motion)

    data.adduc_motion_covered_lf = alnorm_motion_covered
    data.adduc_range_of_motion_lf = alnorm_range_of_motion
    data.flex_motion_covered_lf = flnorm_motion_covered
    data.flex_range_of_motion_lf = flnorm_range_of_motion
    data.contact_duration_lf = flcontact_duration
    data.adduc_motion_covered_h = ahnorm_motion_covered
    data.adduc_range_of_motion_h = ahnorm_range_of_motion
    data.flex_motion_covered_h = fhnorm_motion_covered
    data.flex_range_of_motion_h = fhnorm_range_of_motion
    data.contact_duration_h = fhcontact_duration
    data.adduc_motion_covered_rf = arnorm_motion_covered
    data.adduc_range_of_motion_rf = arnorm_range_of_motion
    data.flex_motion_covered_rf = frnorm_motion_covered
    data.flex_range_of_motion_rf = frnorm_range_of_motion
    data.contact_duration_rf = frcontact_duration

    return data


def _drift_agnostic_CMES(CME, data_range, stance):
    '''
    Function that calculates CME values for which drift is deemed to be
    irrelevant.

    Args:
        CME - nx1 CME to be calculated
        data_range - nx2 array in which each row represents a range of indices
            in which the CME should be computed
        stance - column of enumerated stance values
    Returns:
        CME - nx1 array where values of CME have been calculated and added in
            accordance with proper data_range indices
    '''

    for i in range(len(data_range)):

        CMEwin = stance[data_range[i][0]:data_range[i][1]]
        CME[data_range[i][0]:data_range[i][1]] = _rough_contact_duration(CMEwin)

    return CME


def _driftless_CMES(data, ranges, ms_elapsed, mot_cov, range_mot):
    '''
    Function that calculates CME values after drift affects have been removed

    Args:
        data - nx1 array of orientation data (adduction or flexion)
        ranges - mx2 array in which each row represents a range of indices
            in which the CME should be computed
        ms_elapsed - nx1 array of point to point milliseconds elapsed
        mot_cov - nx1 CME describing total motion covered in a period
        range_mot - nx1 CME describing overall ptp range of the motion (max -
            min)
    Returns:
        mot_cov - nx1 CME describing total motion covered in a period where
            values of CME have been calculated and added in accordance with
            proper ranges indices
        range_mot - nx1 CME describing overall ptp range of the motion (max -
            min) where values of CME have been calculated and added in
            accordance with proper ranges indices
    '''

    for i in range(len(ranges)):

        window = data[ranges[i][0]:ranges[i][1]]
        win_time = ms_elapsed[ranges[i][0]:ranges[i][1]]
        mot_cov[ranges[i][0]:ranges[i][1]] = _norm_motion_covered(window, win_time)
        range_mot[ranges[i][0]:ranges[i][1]] = _norm_range_of_motion(window, win_time)

    return mot_cov, range_mot


def _norm_range_of_motion(data, time):
    '''
    Function that returns the range of euler angles moved through in the
    provided data window, normalized by the time it took to do so.
    
    Args --
        data: orientation array stretching across window of interest (phase)
        time: ms_elapsed corresponding to data
    
    Return --
        mot_range: range of Euler angles moved through per second during the
        window of interest
    
    '''

    # create a copy of data so as not to rewrite it
    datac = copy.copy(data)

    # account for corner cases of windows filled with NaNs or of repeat data
    if np.sum(np.isnan(datac)) == len(datac):
        return data.reshape(-1, 1)
    else:
        pass
    if np.ptp(datac) == 0:
        return np.zeros((len(datac), 1))
    else:

        # find the peak to peak range of the data
        ptp = np.nanmax(datac) - np.nanmin(datac)
        datac.fill(ptp)
        mot_range = datac.reshape(-1, 1)

        # normalize by time
        time_elapsed = np.sum(time)
        mot_range = mot_range/time_elapsed

        return mot_range * 1000 # 1000 multiplier puts in units of seconds

def _norm_motion_covered(data, time):
    '''
    Function that returns the total euler angles moved through in the
    provided data window, normalized by the time it took to do so.
    
    Args --
        data: orientation array stretching across window of interest (phase)
        time: ms_elapsed corresponding to data
    
    Return --
        mot_range: sum of motion in Euler angles moved through per second
    '''

    # create a copy of the data so as not to rewrite it
    datac = copy.deepcopy(data)

    # find the difference in position between subsequent  points
    inc = np.ediff1d(datac)

    # account for corner cases where data = NaN
    where_are_NaNs = np.isnan(inc)
    inc[where_are_NaNs] = 0
    if np.sum(inc) == 0:
        return np.zeros((len(datac), 1))
    else:

        # fill the returned value and normalize by time
        datac.fill(np.sum(inc))
        mot = datac.reshape(-1, 1)
        time_elapsed = np.sum(time)
        mot = mot/time_elapsed

        return mot * 1000 # 1000 multiplier puts in units of seconds

def _rough_contact_duration(stance):
    '''
    Function that divides the window of stance into contact vs. non-contact
    phases, and then returns the duration of each contact vs. non-contact phase
    
    Arg --
        stance: (nx1) array of enumerated stance values including
            [0] Not standing
            [1] Feet eliminated
            [2] Single dyn balance
            [3] Single stat balance
            [4] Double dyn balance
            [5] Double stat balance
            [6] Single impact
            [7] Double impact
            [8] Single takeoff
            [9] Double takeoff

    Return --
        contact: (nx1) array where windows of contact are represented by filled
            values of the duration spent in contact with the ground. NaNs
            represent non-contact.
    '''

    # initialize the variable space
    contact = np.zeros((len(stance), 1)) * np.nan

    # create a mask for non-contact stances
    inv_mask = (stance == 0) | (stance ==1)

    # use the mask to define contact phases, then find contact boundary indices
    contact[inv_mask==False] = 1
    cont_ind = _num_runs(contact, 1)

    # where there is contact, report the duration of the contact
    for i in range(int(cont_ind.shape[0])):
        dur = cont_ind[i, 1] - cont_ind[i, 0]
        contact[cont_ind[i, 0]:cont_ind[i, 1]] = dur

    return contact / 1000 # 1000 divisor puts in units of seconds

def _num_runs(arr, num):
    """
    Function that determines the beginning and end indices of stretches of
    of the same value in an array.

    Args:
        arr: array to be analyzed for runs of a value
        num: number to searched for in the array arr

    Returns:
        ranges: nx2 np.array, with each row containing start and stop + 1
            indices of runs of the value num

    Example:
    >> arr = np.array([1, 1, 2, 3, 2, 0, 0, 1, 3, 1, 1, 1, 6])
    >> _num_runs(arr, 1)
    Out:
    array([[ 0,  2],
           [ 7,  8],
           [ 9, 12]], dtype=int64)
    >> _num_runs(arr, 0)
    Out:
    array([[5, 7]], dtype=int64)

    """

    # Create an array that is 1 where a=num, and pad each end with an extra 0.

    iszero = np.concatenate(([0], np.equal(arr.reshape(-1,), num), [0]))
    del arr, num  # not used in further computations
    absdiff = np.abs(np.diff(iszero))
    del iszero  # not used in further computations

    # Runs start and end where absdiff is 1.
    ranges = np.where(absdiff == 1)[0].reshape(-1, 2)

    return ranges

def _detect_long_dynamic(dyn_vs_static):
    """
    Determine if the data is corrupt because of drift or short switch from dynamic to static algorithm
    Data is said to be corrupt if
    1) There are frequent short switches from dynamic to static algorithm within
       short period of time, currently defined as 5 switches with 4 or fewer points within 5 s
    2) Too much drift has accumulated if the algorithm does not switch to static from dynamic for
       extended period of time, currently defined as no static algorithm of 30 points or more for
       more than 10 mins
    
    """
    min_length = 10 * 100
    bad_switch_len = 30
    range_static, length_static = _zero_runs(dyn_vs_static, 0)
    short_static = np.where(length_static <= bad_switch_len)[0]
    short_static_range = range_static[short_static, :]
    if len(short_static_range) > 0:
        for i, j in zip(short_static_range[:, 0], short_static_range[:, 1]):
            dyn_vs_static[i:j] = 8
    range_dyn, length_dyn= _zero_runs(dyn_vs_static, 8)
    long_dynamic = np.where(length_dyn >= min_length)[0]
    long_dyn_range = range_dyn[long_dynamic, :]
    return long_dyn_range


def _zero_runs(col_dat, static):
    """
    Determine the start and end of each impact.
    
    Args:
        col_dat: array, algorithm indicator
        static: int, indicator for static algorithm
    Returns:
        ranges: 2d array, start and end of each static algorithm use
        length: length of 
    """

    # determine where column data is the relevant impact phase value
    isnan = np.array(np.array(col_dat==static).astype(int)).reshape(-1, 1)
    
    if isnan[0] == 1:
        t_b = 1
    else:
        t_b = 0

    # mark where column data changes to and from NaN
    absdiff = np.abs(np.ediff1d(isnan, to_begin=t_b))
    if isnan[-1] == 1:
        absdiff = np.concatenate([absdiff, [1]], 0)
    del isnan  # not used in further computations

    # determine the number of consecutive NaNs
    ranges = np.where(absdiff == 1)[0].reshape((-1, 2))
    length = ranges[:, 1] - ranges[:, 0]

    return ranges, length



def _filter_data(X, filt='band', lowcut=.1, highcut=40, fs=100, order=4):
    """forward-backward bandpass butterworth filter
    defaults:
        lowcut freq: 0.1
        hicut freq: 20
        sampling rage: 100hz
        order: 4"""
    nyq = 0.5 * fs
    low = lowcut/nyq
    high = highcut/nyq
    if filt == 'low':
        b, a = butter(order, high, btype='low', analog=False)
    elif filt == 'band':
        b, a = butter(order, [low, high], btype='band', analog=False)
    X_filt = filtfilt(b, a, X, axis=0)
    return X_filt


def _remove_filtered_ends(data_range, dyn_range):
    '''
    Function that takes in arrays containing ranges of data corresponding
    with a specific filtering, which is to be processed in CMEs, and ranges of
    data for which dynamic motion has been true for a long time, which is
    filtered against drift. Trims data around the end of filters. If the end of
    the filter is near to the end of the data, the range is trimmed. If not, it
    the range is split around the point, with a pad = 1 pt also removed.
    
    Args:
        data_range - nx2 array, where each row contains the start and end
            indices of a data window that has met previous criteria for CME
            calculations
        dyn_range - mx2 array, where each row contains the start and end
            indices of dynamic data filtered for drift, according to the
            function _detect_long_dynamic()

    Returns:
        data_range - (n-p)x2 array, containing rows of the arg data_range which
            do not represent ranges of data overlapping with p ends of
            dyn_range rows

    '''

    # set, intialize  vars
    split_rows = np.array([])
    del_rows = np.array([])
    pad = 1 # pad to be removed around filter ends

    for j in dyn_range[:, 1]:
        for k in range(len(data_range)):

            # find intersections of filter ends and data ranges
            if j in np.arange(data_range[k, 0], data_range[k, 1]):
#                print data_range[k, 0], '|' , j, '|', data_range[k, 1]

                # if range very short, mark for deletion
                if (data_range[k, 1] - data_range[k, 0]) < (2 * pad + 2):
                    data_range[k, 0] = 0
                    data_range[k, 1] = 0
#                    print 'del'

                # if intersection at very beginning, trim the range
                elif (j - data_range[k, 0]) < (pad + 1):
                    data_range[k, 0] = data_range[k, 0] + 2 * pad + 1
#                    print 'trim the start'

                # if intersection at very ending, trim the range
                elif (data_range[k, 1] - j) < (pad + 1):
                    data_range[k, 1] = data_range[k, 1] - (2 * pad) - 1
#                    print 'trim the end'

                # if intersection in middle of range, mark for range splitting
                else:
                    split_rows = np.hstack((split_rows, np.array([j])))
#                    print 'split'

    # where intersection of filter end and data range, split range around it
    for j in split_rows:
        index = 0
        while data_range[index, 1] < j:
            index = index + 1
        beg = data_range[index, 0]
        data_range[index, 0] = j + pad + 1
        data_range = np.insert(data_range, (index), [beg, j - pad - 1], axis=0)

    # delete rows where an intersection occurred but range too short to trim
    for k in range(len(data_range)):
        if (data_range[k, 0] == 0) & (data_range[k, 1] == 0):
            del_rows = np.hstack((del_rows, np.array([k])))
    if len(del_rows) != 0:        
        data_range = np.delete(data_range, (list(map(int, del_rows))), axis=0)
    else:
        pass

    return data_range


if __name__ == '__main__':
    import timeit

    filename = 'stance_phase_a1bf8bad-8fb6-4cfc-865b-3a6271ccf3aa_00_transformed.csv'
    data = pd.read_csv(filename)

    start = timeit.default_timer()

    data = run_relative_CMEs(data)

    stop = timeit.default_timer()    
    print 'RUNTIME: ', stop - start
