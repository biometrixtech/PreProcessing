# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 10:41:36 2016

@author: Gautam

Session execution script. Used by athletes during block processes. Takes raw
session data, processes, and returns analyzed data.

Input data called from 'biometrix-blockcontainer'

Output data collected in BlockEvent Table.
"""
from aws_xray_sdk.core import xray_recorder
import logging
import numpy as np

from .extract_geometry import extract_geometry
from .movement_attributes import run_stance_analysis, total_accel
from .phase_detection import combine_phase
from .prep_grf_data import prepare_data
from .run_relative_cme import run_relative_cmes
from .unit_blocks import define_unit_blocks
import utils.quaternion_conversions as qc
from utils import filter_data, get_ranges

logger = logging.getLogger()

_output_columns = [
    'obs_index', 'static_lf', 'static_hip', 'static_rf',
    'time_stamp', 'epoch_time', 'ms_elapsed',
    'active',
    'phase_lf',  'phase_rf',
    'grf', 'grf_lf', 'grf_rf',
    'total_accel',
    'stance',
    'euler_lf_x', 'euler_lf_y', 'euler_lf_z',
    'euler_hip_x', 'euler_hip_y', 'euler_hip_z',
    'euler_rf_x', 'euler_rf_y', 'euler_rf_z',
    'acc_lf_x', 'acc_lf_y', 'acc_lf_z',
    'acc_hip_x', 'acc_hip_y', 'acc_hip_z',
    'acc_rf_x', 'acc_rf_y', 'acc_rf_z',
    'adduc_motion_covered_abs_lf', 'adduc_motion_covered_pos_lf', 'adduc_motion_covered_neg_lf',
    'adduc_range_of_motion_lf',
    'flex_motion_covered_abs_lf', 'flex_motion_covered_pos_lf', 'flex_motion_covered_neg_lf',
    'flex_range_of_motion_lf',
    'contact_duration_lf',
    'adduc_motion_covered_abs_h', 'adduc_motion_covered_pos_h', 'adduc_motion_covered_neg_h',
    'adduc_range_of_motion_h',
    'flex_motion_covered_abs_h', 'flex_motion_covered_pos_h', 'flex_motion_covered_neg_h',
    'flex_range_of_motion_h',
    'contact_duration_h',
    'adduc_motion_covered_abs_rf', 'adduc_motion_covered_pos_rf', 'adduc_motion_covered_neg_rf',
    'adduc_range_of_motion_rf',
    'flex_motion_covered_abs_rf', 'flex_motion_covered_pos_rf', 'flex_motion_covered_neg_rf',
    'flex_range_of_motion_rf',
    'contact_duration_rf'
]


@xray_recorder.capture('app.jobs.sessionprocess.run_session')
def run_session(data, mass, grf_fit, sc):
    """Creates object attributes according to session analysis process.

    Args:
        data: transformed data object with attributes of:
            epoch_time,
            static_lf, acc_lf_x, acc_lf_y, acc_lf_z, quat_lf_x, quat_lf_y, quat_lf_z,
            static_hip, acc_hip_x, acc_hip_y, acc_hip_z, quat_hip_x, quat_hip_y, quat_hip_z,
            static_rf, acc_rf_x, acc_rf_y, acc_rf_z, quat_rf_x, quat_rf_y, quat_rf_z
        mass: user's mass in kg
        grf_fit: keras fitted model for grf prediction
        sc: scaler model to scale data)

    Returns:
        scoring_data: processed data in pandas dataframe with columms defined above in _output_columns
    """
    sampl_freq = 97.5

    # Compute euler angles, geometric interpretation of data as appropriate
    lf_quats = data.loc[:, ['quat_lf_w', 'quat_lf_x', 'quat_lf_y', 'quat_lf_z']].values
    lf_euls = qc.quat_to_euler(
        data.quat_lf_w,
        data.quat_lf_x,
        data.quat_lf_y,
        data.quat_lf_z)
    data['euler_lf_z'] = lf_euls[:, 2].reshape(-1, 1)

    hip_quats = data.loc[:, ['quat_hip_w', 'quat_hip_x', 'quat_hip_y', 'quat_hip_z']].values
    hip_euls = qc.quat_to_euler(
        data.quat_hip_w,
        data.quat_hip_x,
        data.quat_hip_y,
        data.quat_hip_z
    )
    data['euler_hip_z'] = hip_euls[:, 2].reshape(-1, 1)

    rf_quats = data.loc[:, ['quat_rf_w', 'quat_rf_x', 'quat_rf_y', 'quat_rf_z']].values
    rf_euls = qc.quat_to_euler(
        data.quat_rf_w,
        data.quat_rf_x,
        data.quat_rf_y,
        data.quat_rf_z
    )
    data['euler_rf_z'] = rf_euls[:, 2].reshape(-1, 1)

    (
        adduction_lf,
        flexion_lf,
        adduction_h,
        flexion_h,
        adduction_rf,
        flexion_rf
    ) = extract_geometry(lf_quats, hip_quats, rf_quats)

    data['euler_lf_x'] = adduction_lf.reshape(-1, 1)
    data['euler_lf_y'] = flexion_lf.reshape(-1, 1)
    data['euler_hip_x'] = adduction_h.reshape(-1, 1)
    data['euler_hip_y'] = flexion_h.reshape(-1, 1)
    data['euler_rf_x'] = adduction_rf.reshape(-1, 1)
    data['euler_rf_y'] = flexion_rf.reshape(-1, 1)


    # prepare data for grf prediction
    weight = mass * 9.807 / 1000  # convert mass from kg to N
    grf_data, nan_row = prepare_data(data, sc, weight)

    # predict grf
    with xray_recorder.in_subsegment('app.jobs.sessionprocess.run_session.grf_predict'):
        grf_result = grf_fit.predict(grf_data).reshape(-1, 3)
    data['grf'], data['grf_lf'], data['grf_rf'], lf_grf_ind, rf_grf_ind = cleanup_grf(grf_result, weight, len(data), nan_row)

    del grf_data, nan_row, grf_fit
    logger.info('DONE WITH GRF PREDICTION!')

    data['phase_lf'], data['phase_rf'] = combine_phase(data.acc_lf_z, data.acc_rf_z, lf_grf_ind, rf_grf_ind, sampl_freq)
    logger.info('DONE WITH PHASE DETECTION!')

    # MOVEMENT ATTRIBUTES AND PERFORMANCE VARIABLES
    # isolate hip acceleration and euler angle data
    hip_acc = data.loc[:, ['acc_hip_x', 'acc_hip_y', 'acc_hip_z']].values

    # calculate total acceleration
    len_hip_acc = len(hip_acc)
    accel_mag = total_accel(hip_acc).reshape((len_hip_acc, 1))
    data['total_accel'] = accel_mag.reshape(-1, 1)

    # analyze stance
    data['stance'] = run_stance_analysis(data)
    del hip_acc
    logger.info('DONE WITH MOVEMENT ATTRIBUTES AND PERFORMANCE VARIABLES!')

    # new relative CMEs
    data = run_relative_cmes(data)
    logger.info('DONE WITH RELATIVE CME!')


    # DEFINE UNIT ACTIVE BLOCKS
    data.total_accel[data.stance == 0] = 0
    data['active'] = define_unit_blocks(data.total_accel)

    # combine into data table
    scoring_data = data.loc[:, _output_columns]

    logger.info("Table Created")

    # scoring_data = update_stance(scoring_data)
    
    return scoring_data


# @xray_recorder.capture('app.jobs.sessionprocess.update_stance')
# def update_stance(data):
#     length_lf, range_lf = _contact_duration(data.phase_lf.values,
#                                             data.active.values,
#                                             data.epoch_time.values,
#                                             ground_phases=[2, 3])
#     length_rf, range_rf = _contact_duration(data.phase_rf.values,
#                                             data.active.values,
#                                             data.epoch_time.values,
#                                             ground_phases=[2, 3])
#
#     for left_step in range_lf:
#         left_phase = np.unique(data.phase_lf[left_step[0]:left_step[1]].values)
#         if np.all(left_phase == np.array([2., 3.])):
#             left_takeoff = get_ranges(data.phase_lf[left_step[0]:left_step[1]], 3)
#             if len(left_takeoff) > 0:  # has takeoff as part of ground contact
#                 left_takeoff = left_takeoff[0]
#                 if data.phase_lf[left_step[0] + left_takeoff[0] - 1] == 2:  # impact-->takeoff not ground-->takeoff
#                     left_takeoff_start = left_step[0] + left_takeoff[0]
#                     left_end = left_step[1]
#                     right_start = range_rf[:, 0]
#                     right_step = range_rf[(left_takeoff_start <= right_start) & (right_start <= left_end)]
#                     if len(right_step) > 0:  # any right step that starts impact withing left_takeoff
#                         # make sure start of right step is impact
#                         right_step = right_step[0]
#                         if data.phase_rf[right_step[0]] == 2 and 3 in np.unique(data.phase_rf[right_step[0]:right_step[1]].values):
#                             data.loc[left_step[0]:right_step[1], 'stance'] = [6] * (right_step[1] - left_step[0] + 1)
#                     else:
#                         data.loc[left_step[0]:left_step[1], 'stance'] = [2] * (left_step[1] - left_step[0] + 1)
#         step_data = data.loc[left_step[0]:left_step[1]]
#         stance = np.unique(step_data.stance.values)
#         if len(stance) > 1:
#             if np.all(stance == np.array([2., 3.])):
#                 rf_air = np.where(step_data.phase_rf.values == 1)[0]
#                 if len(rf_air) <= 2:
#                     data.loc[left_step[0]:left_step[1], 'stance'] = [3.] * len(step_data)
#                 else:
#                     data.loc[left_step[0]:left_step[1], 'stance'] = [7.] * len(step_data)
#             elif np.all(stance == np.array([2., 6.])):
#                 continue
#             elif np.all(stance == np.array([3., 6.])):
#                 continue
#             elif np.all(stance == np.array([2., 4.])):
#                 data.loc[left_step[0]:left_step[1], 'stance'] = [2.] * len(step_data)
#             elif np.all(stance == np.array([3., 5.])):
#                 data.loc[left_step[0]:left_step[1], 'stance'] = [3.] * len(step_data)
#
#     for right_step in range_rf:
#         right_phase = np.unique(data.phase_rf[right_step[0]:right_step[1]].values)
#         if np.all(right_phase == np.array([2., 3.])):
#             right_takeoff = get_ranges(data.phase_rf[right_step[0]:right_step[1]], 3)
#             if len(right_takeoff) > 0:  # has takeoff as part of ground contact
#                 right_takeoff = right_takeoff[0]
#                 if data.phase_rf[right_step[0] + right_takeoff[0] - 1] == 2:  # impact-->takeoff not ground-->takeoff
#                     right_takeoff_start = right_step[0] + right_takeoff[0]
#                     right_end = right_step[1]
#                     left_start = range_lf[:, 0]
#                     left_step = range_lf[(right_takeoff_start <= left_start) & (left_start <= right_end)]
#                     if len(left_step) > 0:  # any left step that starts impact withing right_takeoff
#                         # make sure start of left step is impact
#                         left_step = left_step[0]
#                         if data.phase_lf[left_step[0]] == 2 and 3 in data.phase_lf[left_step[0]:left_step[1]].values:
#                             data.loc[right_step[0]:left_step[1], 'stance'] = [6] * (left_step[1] - right_step[0] + 1)
#                     else:
#                         data.loc[right_step[0]:right_step[1], 'stance'] = [2] * (right_step[1] - right_step[0] + 1)
#         step_data = data.loc[right_step[0]:right_step[1]]
#         stance = np.unique(step_data.stance.values)
#         if len(stance) > 1:
#             if np.all(stance == np.array([2., 3.])):
#                 lf_air = np.where(step_data.phase_lf.values == 1)[0]
#                 if len(lf_air) <= 2:
#                     data.loc[right_step[0]:right_step[1], 'stance'] = [3.] * len(step_data)
#                 else:
#                     data.loc[right_step[0]:right_step[1], 'stance'] = [7.] * len(step_data)
#             elif np.all(stance == np.array([2., 6.])):
#                 continue
#             elif np.all(stance == np.array([3., 6.])):
#                 continue
#             elif np.all(stance == np.array([2., 4.])):
#                 data.loc[right_step[0]:right_step[1], 'stance'] = [2.] * len(step_data)
#             elif np.all(stance == np.array([3., 5.])):
#                 data.loc[right_step[0]:right_step[1], 'stance'] = [3.] * len(step_data)
#
#     return data


@xray_recorder.capture('app.jobs.sessionprocess.cleanup_grf')
def cleanup_grf(grf_result, weight, length, nan_row):
    left_grf = grf_result[:, 0]
    right_grf = grf_result[:, 1]
    grf = grf_result[:, 2]

    grf = filter_data(grf, filt='low', highcut=18)
    left_grf = filter_data(left_grf, filt='low', highcut=18)
    right_grf = filter_data(right_grf, filt='low', highcut=18)

    # set grf value below certain threshold to 0
    grf[grf <= .1 * weight] = 0
    left_grf[left_grf <= .05 * weight] = 0
    right_grf[right_grf <= .05 * weight] = 0

    # fill in nans for rows with missing predictors
    grf_temp = np.ones(length)
    grf_lf_temp = np.ones(length)
    grf_rf_temp = np.ones(length)
    grf_temp[np.array(list(set(range(length)) - set(nan_row)))] = grf
    grf_lf_temp[np.array(list(set(range(length)) - set(nan_row)))] = left_grf
    grf_rf_temp[np.array(list(set(range(length)) - set(nan_row)))] = right_grf
    # Insert nan for grf where data needed to predict was missing
    if len(nan_row) != 0:
        for i in nan_row:
            grf_temp[i] = grf_temp[i - 1]
            grf_lf_temp[i] = grf_lf_temp[i - 1]
            grf_rf_temp[i] = grf_rf_temp[i - 1]

    lf_ind = np.zeros(len(grf_lf_temp))
    lf_ind[np.where(grf_lf_temp != 0)[0]] = 1
    lf_ranges, lf_ranges_length = get_ranges(lf_ind, 1, True)

    rf_ind = np.zeros(len(grf_rf_temp))
    rf_ind[np.where(grf_rf_temp != 0)[0]] = 1
    rf_ranges, rf_ranges_length = get_ranges(rf_ind, 1, True)

    for r, l in zip(lf_ranges, lf_ranges_length):
        if l < 8:
            lf_ind[r[0]: r[1]] = 0
        elif l < 15 and max(grf_lf_temp[r[0]:r[1]]) < 0.25 * weight:
            lf_ind[r[0]: r[1]] = 0
    for r, l in zip(rf_ranges, rf_ranges_length):
        if l < 8:
            rf_ind[r[0]: r[1]] = 0
        elif l < 15 and max(grf_rf_temp[r[0]:r[1]]) < 0.25 * weight:
            rf_ind[r[0]: r[1]] = 0

    lf_ranges, lf_ranges_length = get_ranges(lf_ind, 0, True)
    rf_ranges, rf_ranges_length = get_ranges(rf_ind, 0, True)

    for r, l in zip(lf_ranges, lf_ranges_length):
        if l < 5:
            lf_ind[r[0]: r[1]] = 1
    for r, l in zip(rf_ranges, rf_ranges_length):
        if l < 5:
            rf_ind[r[0]: r[1]] = 1

    return grf_temp * 1000, grf_lf_temp * 1000, grf_rf_temp * 1000, lf_ind, rf_ind
