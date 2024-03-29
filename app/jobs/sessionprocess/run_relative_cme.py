# -*- coding: utf-8 -*-
"""
Created on Tue Nov 28 15:16:08 2017

@author: court
"""
from aws_xray_sdk.core import xray_recorder
import numpy as np
import copy

from utils import get_ranges


@xray_recorder.capture('app.jobs.sessionprocess.run_relative_cmes.run_relative_cmes')
def run_relative_cmes(data):
    """
    Function that takes a (nxm) data frame and returns an (nx(m+p)) data frame
    with p relatively calculated CME values attached.

    Arg --
        data: data frame with at least the following (nx1) columns attached -
            - epoch_time - timestamp of data
            - stance - enumerated stance value
            - phase_lf - enumerated left phase value
            - phase_rf - enumerated right phase value
            - euler_lf_x - left foot adduction
            - euler_lf_y - left foot flexion
            - euler_hip_x - hip adduction
            - euler_hip_y - hip flexion
            - euler_rf_x - right foot adduction
            - euler_rf_y - right foot flexion

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
    """

    length = data.epoch_time

    stance = data.stance.values.reshape(-1, 1)
    ms_elapsed = np.array([10] * len(length)).reshape(-1, 1)

    lphase = copy.deepcopy(data.phase_lf.values.reshape(-1, 1))
    rphase = copy.deepcopy(data.phase_rf.values.reshape(-1, 1))

    adduction_l = data.euler_lf_x.values.reshape(-1, 1)
    flexion_l = data.euler_lf_y.values.reshape(-1, 1)
    adduction_h = data.euler_hip_x.values.reshape(-1, 1)
    flexion_h = data.euler_hip_y.values.reshape(-1, 1)
    adduction_r = data.euler_rf_x.values.reshape(-1, 1)
    flexion_r = data.euler_rf_y.values.reshape(-1, 1)

    alnorm_motion_covered_abs = np.empty(len(length)).reshape(-1, 1) * np.nan
    alnorm_motion_covered_pos = np.empty(len(length)).reshape(-1, 1) * np.nan
    alnorm_motion_covered_neg = np.empty(len(length)).reshape(-1, 1) * np.nan
    alnorm_range_of_motion = np.empty(len(length)).reshape(-1, 1) * np.nan

    ahnorm_motion_covered_abs = np.empty(len(length)).reshape(-1, 1) * np.nan
    ahnorm_motion_covered_pos = np.empty(len(length)).reshape(-1, 1) * np.nan
    ahnorm_motion_covered_neg = np.empty(len(length)).reshape(-1, 1) * np.nan
    ahnorm_range_of_motion = np.empty(len(length)).reshape(-1, 1) * np.nan

    arnorm_motion_covered_abs = np.empty(len(length)).reshape(-1, 1) * np.nan
    arnorm_motion_covered_pos = np.empty(len(length)).reshape(-1, 1) * np.nan
    arnorm_motion_covered_neg = np.empty(len(length)).reshape(-1, 1) * np.nan
    arnorm_range_of_motion = np.empty(len(length)).reshape(-1, 1) * np.nan

    flnorm_motion_covered_abs = np.empty(len(length)).reshape(-1, 1) * np.nan
    flnorm_motion_covered_pos = np.empty(len(length)).reshape(-1, 1) * np.nan
    flnorm_motion_covered_neg = np.empty(len(length)).reshape(-1, 1) * np.nan
    flnorm_range_of_motion = np.empty(len(length)).reshape(-1, 1) * np.nan
    flcontact_duration = np.empty(len(length)).reshape(-1, 1) * np.nan

    fhnorm_motion_covered_abs = np.empty(len(length)).reshape(-1, 1) * np.nan
    fhnorm_motion_covered_pos = np.empty(len(length)).reshape(-1, 1) * np.nan
    fhnorm_motion_covered_neg = np.empty(len(length)).reshape(-1, 1) * np.nan
    fhnorm_range_of_motion = np.empty(len(length)).reshape(-1, 1) * np.nan
    fhcontact_duration = np.empty(len(length)).reshape(-1, 1) * np.nan

    frnorm_motion_covered_abs = np.empty(len(length)).reshape(-1, 1) * np.nan
    frnorm_motion_covered_pos = np.empty(len(length)).reshape(-1, 1) * np.nan
    frnorm_motion_covered_neg = np.empty(len(length)).reshape(-1, 1) * np.nan
    frnorm_range_of_motion = np.empty(len(length)).reshape(-1, 1) * np.nan
    frcontact_duration = np.empty(len(length)).reshape(-1, 1) * np.nan

    # filter data
    l0ranges = get_ranges(lphase, 0)
    l2ranges = get_ranges(lphase, 2)
    l3ranges = get_ranges(lphase, 3)

    hl0ranges = get_ranges(lphase, 0)
    hl2ranges = get_ranges(lphase, 2)
    hl3ranges = get_ranges(lphase, 3)

    hr0ranges = get_ranges(rphase, 0)
    hr2ranges = get_ranges(rphase, 2)
    hr3ranges = get_ranges(rphase, 3)

    r0ranges = get_ranges(rphase, 0)
    r2ranges = get_ranges(rphase, 2)
    r3ranges = get_ranges(rphase, 3)

    ranges = {'l0ranges': l0ranges,
              'l2ranges': l2ranges,
              'l3ranges': l3ranges,
              'hl0ranges': hl0ranges,
              'hl2ranges': hl2ranges,
              'hl3ranges': hl3ranges,
              'hr0ranges': hr0ranges,
              'hr2ranges': hr2ranges,
              'hr3ranges': hr3ranges,
              'r0ranges': r0ranges,
              'r2ranges': r2ranges,
              'r3ranges': r3ranges}

    # Calculate CMEs agnostic to drift
    for i in ['0', '2', '3']:
        left_range = ranges.get('l' + i + 'ranges')
        right_range = ranges.get('r' + i + 'ranges')
        hip_left_range = ranges.get('hl' + i + 'ranges')
        hip_right_range = ranges.get('hr' + i + 'ranges')

        flcontact_duration = _drift_agnostic_cmes(flcontact_duration, left_range, stance)
        frcontact_duration = _drift_agnostic_cmes(frcontact_duration, right_range, stance)
        fhcontact_duration = _drift_agnostic_cmes(fhcontact_duration, hip_left_range, stance)
        fhcontact_duration = _drift_agnostic_cmes(fhcontact_duration, hip_right_range, stance)

    # get the start and end point of long dynamic alogorithm where filter is applied
    # dynamic_range_lf = _detect_long_dynamic(data.static_lf.values)
    # dynamic_range_rf = _detect_long_dynamic(data.static_rf.values)

    for i in ['0', '2', '3']:
        # get the ranges for given phase
        left_range = ranges.get('l' + i + 'ranges')
        right_range = ranges.get('r' + i + 'ranges')
        hip_left_range = ranges.get('hl' + i + 'ranges')
        hip_right_range = ranges.get('hr' + i + 'ranges')

        # filter out hip data potentially skewed by drift filter
        # left_range = _remove_filtered_ends(left_range, dynamic_range_lf)
        # right_range = _remove_filtered_ends(right_range, dynamic_range_rf)
        # hip_left_range = _remove_filtered_ends(hip_left_range, dynamic_range_lf)
        # hip_right_range = _remove_filtered_ends(hip_right_range, dynamic_range_rf)

        (
            alnorm_motion_covered_abs,
            alnorm_motion_covered_pos,
            alnorm_motion_covered_neg,
            alnorm_range_of_motion
        ) = _driftless_cmes(adduction_l, left_range, ms_elapsed,
                            alnorm_motion_covered_abs, alnorm_motion_covered_pos, alnorm_motion_covered_neg,
                            alnorm_range_of_motion)

        (
            flnorm_motion_covered_abs,
            flnorm_motion_covered_pos,
            flnorm_motion_covered_neg,
            flnorm_range_of_motion
        ) = _driftless_cmes(flexion_l, left_range, ms_elapsed,
                            flnorm_motion_covered_abs, flnorm_motion_covered_pos, flnorm_motion_covered_neg,
                            flnorm_range_of_motion)

        (
            arnorm_motion_covered_abs,
            arnorm_motion_covered_pos,
            arnorm_motion_covered_neg,
            arnorm_range_of_motion
        ) = _driftless_cmes(adduction_r, right_range, ms_elapsed,
                            arnorm_motion_covered_abs, arnorm_motion_covered_pos, arnorm_motion_covered_neg,
                            arnorm_range_of_motion)

        (
            frnorm_motion_covered_abs,
            frnorm_motion_covered_pos,
            frnorm_motion_covered_neg,
            frnorm_range_of_motion
        ) = _driftless_cmes(flexion_r, right_range, ms_elapsed,
                            frnorm_motion_covered_abs, frnorm_motion_covered_pos, frnorm_motion_covered_neg,
                            frnorm_range_of_motion)

        (
            ahnorm_motion_covered_abs,
            ahnorm_motion_covered_pos,
            ahnorm_motion_covered_neg,
            ahnorm_range_of_motion
        ) = _driftless_cmes(adduction_h, hip_left_range, ms_elapsed,
                            ahnorm_motion_covered_abs, ahnorm_motion_covered_pos, ahnorm_motion_covered_neg,
                            ahnorm_range_of_motion)
        (
            ahnorm_motion_covered_abs,
            ahnorm_motion_covered_pos,
            ahnorm_motion_covered_neg,
            ahnorm_range_of_motion
        ) = _driftless_cmes(adduction_h, hip_right_range, ms_elapsed,
                            ahnorm_motion_covered_abs, ahnorm_motion_covered_pos, ahnorm_motion_covered_neg,
                            ahnorm_range_of_motion)

        (
            fhnorm_motion_covered_abs,
            fhnorm_motion_covered_pos,
            fhnorm_motion_covered_neg,
            fhnorm_range_of_motion
        ) = _driftless_cmes(flexion_h, hip_left_range, ms_elapsed,
                            fhnorm_motion_covered_abs, fhnorm_motion_covered_pos, fhnorm_motion_covered_neg,
                            fhnorm_range_of_motion)
        (
            fhnorm_motion_covered_abs,
            fhnorm_motion_covered_pos,
            fhnorm_motion_covered_neg,
            fhnorm_range_of_motion
        ) = _driftless_cmes(flexion_h, hip_right_range, ms_elapsed,
                            fhnorm_motion_covered_abs, fhnorm_motion_covered_pos, fhnorm_motion_covered_neg,
                            fhnorm_range_of_motion)

    data['adduc_motion_covered_abs_lf'] = alnorm_motion_covered_abs
    data['adduc_motion_covered_pos_lf'] = alnorm_motion_covered_pos
    data['adduc_motion_covered_neg_lf'] = alnorm_motion_covered_neg
    data['adduc_range_of_motion_lf'] = alnorm_range_of_motion

    data['flex_motion_covered_abs_lf'] = flnorm_motion_covered_abs
    data['flex_motion_covered_pos_lf'] = flnorm_motion_covered_pos
    data['flex_motion_covered_neg_lf'] = flnorm_motion_covered_neg
    data['flex_range_of_motion_lf'] = flnorm_range_of_motion
    data['contact_duration_lf'] = flcontact_duration

    data['adduc_motion_covered_abs_h'] = ahnorm_motion_covered_abs
    data['adduc_motion_covered_pos_h'] = ahnorm_motion_covered_pos
    data['adduc_motion_covered_neg_h'] = ahnorm_motion_covered_neg
    data['adduc_range_of_motion_h'] = ahnorm_range_of_motion

    data['flex_motion_covered_abs_h'] = fhnorm_motion_covered_abs
    data['flex_motion_covered_pos_h'] = fhnorm_motion_covered_pos
    data['flex_motion_covered_neg_h'] = fhnorm_motion_covered_neg
    data['flex_range_of_motion_h'] = fhnorm_range_of_motion
    data['contact_duration_h'] = fhcontact_duration

    data['adduc_motion_covered_abs_rf'] = arnorm_motion_covered_abs
    data['adduc_motion_covered_pos_rf'] = arnorm_motion_covered_pos
    data['adduc_motion_covered_neg_rf'] = arnorm_motion_covered_neg
    data['adduc_range_of_motion_rf'] = arnorm_range_of_motion

    data['flex_motion_covered_abs_rf'] = frnorm_motion_covered_abs
    data['flex_motion_covered_pos_rf'] = frnorm_motion_covered_pos
    data['flex_motion_covered_neg_rf'] = frnorm_motion_covered_neg
    data['flex_range_of_motion_rf'] = frnorm_range_of_motion
    data['contact_duration_rf'] = frcontact_duration

    return data


@xray_recorder.capture('app.jobs.sessionprocess.run_relative_cmes._drift_agnostic_cmes')
def _drift_agnostic_cmes(cme, data_range, stance):
    """
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
    """

    for i in range(len(data_range)):

        cme_win = stance[data_range[i][0]:data_range[i][1]]
        cme[data_range[i][0]:data_range[i][1]] = _rough_contact_duration(cme_win)

    return cme


@xray_recorder.capture('app.jobs.sessionprocess.run_relative_cmes._driftless_cmes')
def _driftless_cmes(data, ranges, ms_elapsed, mot_cov_abs, mot_cov_pos, mot_cov_neg, range_mot):
    """
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
    """

    for i in range(len(ranges)):

        window = data[ranges[i][0]:ranges[i][1]]
        win_time = ms_elapsed[ranges[i][0]:ranges[i][1]]
        mot_cov_abs[ranges[i][0]:ranges[i][1]] = _norm_motion_covered(window, win_time, cme='abs')
        mot_cov_pos[ranges[i][0]:ranges[i][1]] = _norm_motion_covered(window, win_time, cme='pos')
        mot_cov_neg[ranges[i][0]:ranges[i][1]] = _norm_motion_covered(window, win_time, cme='neg')
        range_mot[ranges[i][0]:ranges[i][1]] = _norm_range_of_motion(window, win_time)

    return mot_cov_abs, mot_cov_pos, mot_cov_neg, range_mot


# @xray_recorder.capture('app.jobs.sessionprocess.run_relative_cmes._norm_range_of_motion')
def _norm_range_of_motion(data, time):
    """
    Function that returns the range of euler angles moved through in the
    provided data window, normalized by the time it took to do so.

    Args --
        data: orientation array stretching across window of interest (phase)
        time: ms_elapsed corresponding to data

    Return --
        mot_range: range of Euler angles moved through per second during the
        window of interest
    """

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

        return mot_range * 1000  # 1000 multiplier puts in units of seconds


# @xray_recorder.capture('app.jobs.sessionprocess.run_relative_cmes._norm_motion_covered')
def _norm_motion_covered(data, time, cme):
    """
    Function that returns the total euler angles moved through in the
    provided data window, normalized by the time it took to do so.

    Args --
        data: orientation array stretching across window of interest (phase)
        time: ms_elapsed corresponding to data

    Return --
        mot_range: sum of motion in Euler angles moved through per second
    """

    # create a copy of the data so as not to rewrite it
    datac = copy.deepcopy(data)

    # find the difference in position between subsequent  points
    inc = np.ediff1d(datac)

    # account for corner cases where data = NaN
    where_are_nans = np.isnan(inc)
    inc[where_are_nans] = 0

    if cme == 'abs':
        inc = np.abs(inc)
    elif cme == 'pos':
        inc = inc[inc > 0]
    elif cme == 'neg':
        inc = inc[inc < 0]

    if np.sum(inc) == 0:
        return np.zeros((len(datac), 1))
    else:
        # fill the returned value and normalize by time
        datac.fill(np.sum(inc))
        mot = datac.reshape(-1, 1)
        time_elapsed = np.sum(time)
        mot = mot/time_elapsed

        return mot * 1000  # 1000 multiplier puts in units of seconds


# @xray_recorder.capture('app.jobs.sessionprocess.run_relative_cmes._rough_contact_duration')
def _rough_contact_duration(stance):
    """
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
    """

    # initialize the variable space
    contact = np.zeros((len(stance), 1)) * np.nan

    # create a mask for non-contact stances
    inv_mask = (stance == 0) | (stance == 1)

    # use the mask to define contact phases, then find contact boundary indices
    contact[inv_mask == False] = 1
    cont_ind = get_ranges(contact, 1)

    # where there is contact, report the duration of the contact
    for i in range(int(cont_ind.shape[0])):
        if cont_ind[i, 1] + 1 == len(stance):
            dur = cont_ind[i, 1] - cont_ind[i, 0] + 1
            contact[cont_ind[i, 0]:cont_ind[i, 1] + 1] = dur
        else:
            dur = cont_ind[i, 1] - cont_ind[i, 0]
            contact[cont_ind[i, 0]:cont_ind[i, 1]] = dur
    return contact / 1000.  # 1000 divisor puts in units of seconds


# @xray_recorder.capture('app.jobs.sessionprocess.run_relative_cmes._detect_long_dynamic')
# def _detect_long_dynamic(dyn_vs_static):
#     """
#     Determine if the data is corrupt because of drift or short switch from dynamic to static algorithm
#     Data is said to be corrupt if
#     1) There are frequent short switches from dynamic to static algorithm within
#        short period of time, currently defined as 5 switches with 4 or fewer points within 5 s
#     2) Too much drift has accumulated if the algorithm does not switch to static from dynamic for
#        extended period of time, currently defined as no static algorithm of 30 points or more for
#        more than 10 mins

#     """
#     min_length = 10 * 100
#     bad_switch_len = 30
#     range_static, length_static = get_ranges(dyn_vs_static, 0, True)
#     short_static = np.where(length_static <= bad_switch_len)[0]
#     short_static_range = range_static[short_static, :]
#     if len(short_static_range) > 0:
#         for i, j in zip(short_static_range[:, 0], short_static_range[:, 1]):
#             dyn_vs_static[i:j] = 8
#     range_dyn, length_dyn = get_ranges(dyn_vs_static, 8, True)
#     long_dynamic = np.where(length_dyn >= min_length)[0]
#     long_dyn_range = range_dyn[long_dynamic, :]
#     return long_dyn_range


# @xray_recorder.capture('app.jobs.sessionprocess.run_relative_cmes._remove_filtered_ends')
# def _remove_filtered_ends(data_range, dyn_range):
#     """
#     Function that takes in arrays containing ranges of data corresponding
#     with a specific filtering, which is to be processed in CMEs, and ranges of
#     data for which dynamic motion has been true for a long time, which is
#     filtered against drift. Trims data around the end of filters. If the end of
#     the filter is near to the end of the data, the range is trimmed. If not, it
#     the range is split around the point, with a pad = 1 pt also removed.

#     Args:
#         data_range - nx2 array, where each row contains the start and end
#             indices of a data window that has met previous criteria for CME calculations
#         dyn_range - mx2 array, where each row contains the start and end
#             indices of dynamic data filtered for drift, according to the
#             function _detect_long_dynamic()

#     Returns:
#         data_range - (n-p)x2 array, containing rows of the arg data_range which
#             do not represent ranges of data overlapping with p ends of
#             dyn_range rows
#     """

#     # set, intialize  vars
#     split_rows = np.array([])
#     del_rows = np.array([])
#     pad = 1  # pad to be removed around filter ends

#     for j in dyn_range[:, 1]:
#         for k in range(len(data_range)):

#             # find intersections of filter ends and data ranges
#             if j in np.arange(data_range[k, 0], data_range[k, 1]):

#                 # if range very short, mark for deletion
#                 if (data_range[k, 1] - data_range[k, 0]) < (2 * pad + 2):
#                     data_range[k, 0] = 0
#                     data_range[k, 1] = 0

#                 # if intersection at very beginning, trim the range
#                 elif (j - data_range[k, 0]) < (pad + 1):
#                     data_range[k, 0] = data_range[k, 0] + 2 * pad + 1

#                 # if intersection at very ending, trim the range
#                 elif (data_range[k, 1] - j) < (pad + 1):
#                     data_range[k, 1] = data_range[k, 1] - (2 * pad) - 1

#                 # if intersection in middle of range, mark for range splitting
#                 else:
#                     split_rows = np.hstack((split_rows, np.array([j])))

#     # where intersection of filter end and data range, split range around it
#     for j in split_rows:
#         index = 0
#         while data_range[index, 1] < j:
#             index = index + 1
#         beg = data_range[index, 0]
#         data_range[index, 0] = j + pad + 1
#         data_range = np.insert(data_range, index, [beg, j - pad - 1], axis=0)

#     # delete rows where an intersection occurred but range too short to trim
#     for k in range(len(data_range)):
#         if (data_range[k, 0] == 0) & (data_range[k, 1] == 0):
#             del_rows = np.hstack((del_rows, np.array([k])))
#     if len(del_rows) != 0:
#         data_range = np.delete(data_range, (list(map(int, del_rows))), axis=0)
#     else:
#         pass

#     return data_range
