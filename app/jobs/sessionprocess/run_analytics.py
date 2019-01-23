# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 10:41:36 2016

@author: Gautam

Session execution script. Used by athletes during block processes. Takes raw
session data, processes, and returns analyzed data.

Input data called from 'biometrix-blockcontainer'

Output data collected in BlockEvent Table.
"""

from scipy.signal import butter, filtfilt
import copy
import logging
import numpy as np
import pandas as pd

from .balance_cme import calculate_rot_cmes, calculate_rot_cmes_v1
from .balance_phase_force import calculate_balance_phase_force
from .data_object import RawFrame
from .detect_impact_phase_intervals import detect_start_end_impact_phase
from .detect_takeoff_phase_intervals import detect_start_end_takeoff_phase
from .extract_geometry import extract_geometry
from .impact_cme import sync_time, landing_pattern, continuous_values
from .movement_attributes import plane_analysis, run_stance_analysis
from .phase_detection import combine_phase, update_phase_grf
from .prep_grf_data import prepare_data
from .rate_of_force_absorption import detect_rate_of_force_absorption
from .rate_of_force_production import detect_rate_of_force_production
from .run_relative_cme import run_relative_cmes
from .unit_blocks import define_unit_blocks
import utils.quaternion_conversions as qc

logger = logging.getLogger()

_output_columns = [
    'obs_index', 'time_stamp', 'epoch_time', 'ms_elapsed',
    'loading_lf', 'loading_rf',
    'active',
    'phase_lf',  'phase_rf', 'impact_phase_lf', 'impact_phase_rf',
    'grf', 'grf_lf', 'grf_rf', 'grf_bal_phase',
    'contra_hip_drop_lf', 'contra_hip_drop_rf',
    'ankle_rot_lf', 'ankle_rot_rf',
    'foot_position_lf', 'foot_position_rf',
    'land_pattern_lf', 'land_pattern_rf', 'land_time',
    'rate_force_absorption_lf', 'rate_force_absorption_rf',
    'rate_force_production_lf', 'rate_force_production_rf', 'total_accel',
    'stance', 'plane', 'rot', 'lat', 'vert', 'horz',
    'euler_lf_x', 'euler_lf_y', 'euler_hip_x', 'euler_hip_y', 'euler_rf_x', 'euler_rf_y',
    'acc_lf_x', 'acc_lf_y', 'acc_lf_z',
    'acc_hip_x', 'acc_hip_y', 'acc_hip_z',
    'acc_rf_x', 'acc_rf_y', 'acc_rf_z',
    'corrupt_lf', 'corrupt_hip', 'corrupt_rf',
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


def run_session(data_in, file_version, mass, grf_fit, grf_fit_left, grf_fit_right, sc, sc_single_leg, hip_n_transform):
    """Creates object attributes according to session analysis process.

    Args:
        data_in: raw data object with attributes of:
            epoch_time, corrupt_magn, missing_type, acc_lf_x, acc_lf_y, acc_lf_z, quat_lf_x, quat_lf_y,
            quat_lf_z, acc_hip_x, acc_hip_y, acc_hip_z, quat_hip_x, quat_hip_y, quat_hip_z, acc_rf_x, acc_rf_y, acc_rf_z, quat_rf_x, quat_rf_y, quat_rf_z
        file_version: file format and type version (matching accessory sensor dev)
        mass: user's mass in kg
        grf_fit: keras fitted model for grf prediction
        grf_fit_left: keras fitted model for grf prediction
        grf_fit_right: keras fitted model for grf prediction
        sc: scaler model to scale data
        sc_single_leg: scaler model to scale data
        hip_n_transform: array of neutral hip transformation (used for cme computation in v1 data)

    Returns:
        result: string signifying success or failure.
        Note: In case of completion for local run, returns movement table.
    """
    columns = data_in.columns
    data = RawFrame(data_in, columns)
    sampl_freq = 100

    # Compute euler angles, geometric interpretation of data as appropriate
    lf_quats = np.hstack([data.quat_lf_w, data.quat_lf_x, data.quat_lf_y,
                          data.quat_lf_z]).reshape(-1, 4)
    lf_euls = qc.quat_to_euler(lf_quats)
    data.euler_lf_z = lf_euls[:, 2].reshape(-1, 1)

    hip_quats = np.hstack([data.quat_hip_w, data.quat_hip_x, data.quat_hip_y, data.quat_hip_z]).reshape(-1, 4)
    h_euls = qc.quat_to_euler(hip_quats)
    data.euler_hip_z = h_euls[:, 2].reshape(-1, 1)

    rf_quats = np.hstack([data.quat_rf_w, data.quat_rf_x, data.quat_rf_y, data.quat_rf_z]).reshape(-1, 4)
    rf_euls = qc.quat_to_euler(rf_quats)
    data.euler_rf_z = rf_euls[:, 2].reshape(-1, 1)

    (
        adduction_lf,
        flexion_lf,
        adduction_h,
        flexion_h,
        adduction_rf,
        flexion_rf
    ) = extract_geometry(lf_quats, hip_quats, rf_quats)

    if file_version == '1.0':
        data.euler_lf_x = lf_euls[:, 0].reshape(-1, 1)
        data.euler_lf_y = lf_euls[:, 1].reshape(-1, 1)
        data.euler_hip_x = h_euls[:, 0].reshape(-1, 1)
        data.euler_hip_y = h_euls[:, 1].reshape(-1, 1)
        data.euler_rf_x = rf_euls[:, 0].reshape(-1, 1)
        data.euler_rf_y = rf_euls[:, 1].reshape(-1, 1)
    else:
        data.euler_lf_x = adduction_lf.reshape(-1, 1)
        data.euler_lf_y = flexion_lf.reshape(-1, 1)
        data.euler_hip_x = adduction_h.reshape(-1, 1)
        data.euler_hip_y = flexion_h.reshape(-1, 1)
        data.euler_rf_x = adduction_rf.reshape(-1, 1)
        data.euler_rf_y = flexion_rf.reshape(-1, 1)

    del lf_euls, h_euls, rf_euls

    # PHASE DETECTION
    data.phase_lf, data.phase_rf = combine_phase(data.acc_lf_z, data.acc_rf_z, data.acc_lf_z, data.acc_rf_z, data.euler_lf_y, data.euler_rf_y, sampl_freq)
    logger.info('DONE WITH PHASE DETECTION!')

    # prepare data for grf prediction
    data.mass = mass*9.807/1000  # convert mass from kg to kN
    grf_data, nan_row = prepare_data(data, sc)

    grf_data_sl, nan_row_sl = prepare_data(data, sc_single_leg, sl=True)

    # predict grf
    grf = grf_fit.predict(grf_data).reshape(-1,)

    # predict left grf (binary 0(air) or 1(ground))
    grf_lf = grf_fit_left.predict(grf_data_sl).reshape(-1,)
    sl_grf_cutoff = .5
    grf_lf[grf_lf <= sl_grf_cutoff] = 0
    grf_lf[grf_lf > sl_grf_cutoff] = 1

    # predict right grf (binary 0(air) or 1(ground))
    grf_rf = grf_fit_right.predict(grf_data_sl).reshape(-1,)
    grf_rf[grf_rf <= sl_grf_cutoff] = 0
    grf_rf[grf_rf > sl_grf_cutoff] = 1

    # pass predicted data through low-pass filter
    grf = _filter_data(grf, cutoff=18)

    # set grf value below certain threshold to 0
    grf[grf <= .2*data.mass] = 0
    # grf[grf <= .1] = 0
    # fill in nans for rows with missing predictors
    length = len(data_in)
    grf_temp = np.ones(length)
    grf_lf_temp = np.ones(length)
    grf_rf_temp = np.ones(length)
    grf_temp[np.array(list(set(range(length)) - set(nan_row)))] = grf
    grf_lf_temp[np.array(list(set(range(length)) - set(nan_row_sl)))] = grf_lf
    grf_rf_temp[np.array(list(set(range(length)) - set(nan_row_sl)))] = grf_rf
    # Insert nan for grf where data needed to predict was missing
    if len(nan_row) != 0:
        for i in nan_row:
            grf_temp[i] = np.nan

    # for right and left grf indicator, in case of missing predictors, assign previous value
    if len(nan_row_sl) != 0:
        for i in nan_row_sl:
            grf_lf_temp[i] = grf_lf_temp[i - 1]
            grf_rf_temp[i] = grf_rf_temp[i - 1]

    data.grf = grf_temp*1000
    data.grf_lf = grf_lf_temp
    data.grf_rf = grf_rf_temp

    del grf_data, nan_row, grf_fit, grf, grf_temp, grf_lf, grf_rf, grf_lf_temp, grf_rf_temp
    logger.info('DONE WITH GRF PREDICTION!')

    (
        data.grf,
        data.phase_lf,
        data.phase_rf
    ) = update_phase_grf(data.grf, data.grf_lf, data.grf_rf, data.phase_lf, data.phase_rf, mass)

    logger.info('DONE UPDATING PHASE WITH GRF')

    # DETECT IMPACT PHASE INTERVALS
    (
        data.impact_phase_lf,
        data.impact_phase_rf,
        lf_imp_range,
        rf_imp_range
    ) = detect_start_end_impact_phase(lph=data.phase_lf, rph=data.phase_rf)
    logger.info('DONE WITH DETECTING IMPACT PHASE INTERVALS')

    # MOVEMENT ATTRIBUTES AND PERFORMANCE VARIABLES
    # isolate hip acceleration and euler angle data
    hip_acc = np.hstack([data.acc_hip_x, data.acc_hip_y, data.acc_hip_z])
    hip_eul = np.hstack([data.euler_hip_x, data.euler_hip_y, data.euler_hip_z])

    # analyze planes of movement
    (
        data.lat,
        data.vert,
        data.horz,
        data.rot,
        data.lat_binary,
        data.vert_binary,
        data.horz_binary,
        data.rot_binary,
        data.stationary_binary,
        data.total_accel
    ) = plane_analysis(hip_acc, hip_eul, data.ms_elapsed)

    # analyze stance
    data.stance = run_stance_analysis(data)
    del hip_acc, hip_eul
    logger.info('DONE WITH MOVEMENT ATTRIBUTES AND PERFORMANCE VARIABLES!')

    # Enumerate plane and stance
    data.plane = np.array([0]*len(data.rot)).reshape(-1, 1)

    # Enumerate plane
    data.plane[data.rot_binary == 1] = 1
    data.plane[data.lat_binary == 1] = 2
    data.plane[data.vert_binary == 1] = 3
    data.plane[data.horz_binary == 1] = 4
    data.plane[(data.rot_binary == 1) & (data.lat_binary == 1)] = 5
    data.plane[(data.rot_binary == 1) & (data.vert_binary == 1)] = 6
    data.plane[(data.rot_binary == 1) & (data.horz_binary == 1)] = 7
    data.plane[(data.lat_binary == 1) & (data.vert_binary == 1)] = 8
    data.plane[(data.lat_binary == 1) & (data.horz_binary == 1)] = 9
    data.plane[(data.vert_binary == 1) & (data.horz_binary == 1)] = 10
    data.plane[(data.rot_binary == 1) & (data.lat_binary == 1) & (data.vert_binary == 1)] = 11
    data.plane[(data.rot_binary == 1) & (data.lat_binary == 1) & (data.horz_binary == 1)] = 12
    data.plane[(data.rot_binary == 1) & (data.vert_binary == 1) & (data.horz_binary == 1)] = 13
    data.plane[(data.lat_binary == 1) & (data.vert_binary == 1) & (data.horz_binary == 1)] = 14
    data.plane[(data.rot_binary == 1) & (data.lat_binary == 1) & (data.vert_binary == 1) & (data.horz_binary == 1)] = 15

    # MOVEMENT QUALITY FEATURES

    # isolate bf quaternions
    lf_quat = np.hstack([data.quat_lf_w, data.quat_lf_x, data.quat_lf_y, data.quat_lf_z])
    hip_quat = np.hstack([data.quat_hip_w, data.quat_hip_x, data.quat_hip_y, data.quat_hip_z])
    rf_quat = np.hstack([data.quat_rf_w, data.quat_rf_x, data.quat_rf_y, data.quat_rf_z])

    # calculate movement attributes
    if file_version == '1.0':
        # special code to rerun v1 data to gather older cmes
        # isolate neutral quaternions
        lf_neutral, hip_neutral, rf_neutral = _calculate_hip_neutral(hip_quat, hip_n_transform)

        # calculate movement attributes
        (
            data.contra_hip_drop_lf,
            data.contra_hip_drop_rf,
            data.ankle_rot_lf,
            data.ankle_rot_rf,
            data.foot_position_lf,
            data.foot_position_rf
        ) = calculate_rot_cmes_v1(lf_quat, hip_quat, rf_quat, lf_neutral, hip_neutral, rf_neutral, data.phase_lf, data.phase_rf)
        del lf_quat, hip_quat, rf_quat
        del lf_neutral, hip_neutral, rf_neutral
    else:
        (
            data.contra_hip_drop_lf,
            data.contra_hip_drop_rf,
            data.ankle_rot_lf,
            data.ankle_rot_rf,
            data.foot_position_lf,
            data.foot_position_rf
        ) = calculate_rot_cmes(lf_quat, hip_quat, rf_quat, data.phase_lf, data.phase_rf)
        del lf_quat, hip_quat, rf_quat

    # new relative CMEs
    data = run_relative_cmes(data)
    logger.info('DONE WITH BALANCE CME!')

    # IMPACT CME
    # define dictionary for msElapsed

    # landing time attributes
    n_landtime, ltime_index, lf_rf_imp_indicator = sync_time(rf_imp_range[:, 0], lf_imp_range[:, 0], float(sampl_freq))

    # landing pattern attributes
    if len(n_landtime) != 0:
        n_landpattern = landing_pattern(data.euler_rf_y, data.euler_lf_y, ltime_index, lf_rf_imp_indicator, sampl_freq, n_landtime)
        land_time, land_pattern = continuous_values(n_landpattern, n_landtime, len(data.acc_lf_x), ltime_index)
        data.land_time = land_time.reshape(-1, 1)
        data.land_pattern_rf = land_pattern[:, 0].reshape(-1, 1)
        data.land_pattern_lf = land_pattern[:, 1].reshape(-1, 1)
        del n_landpattern, land_time, land_pattern
    else:
        data.land_time = np.zeros((len(data.acc_lf_x), 1))*np.nan
        data.land_pattern_lf = np.zeros((len(data.acc_lf_x), 1))*np.nan
        data.land_pattern_rf = np.zeros((len(data.acc_lf_x), 1))*np.nan
    del n_landtime, ltime_index, lf_rf_imp_indicator
    logger.info('DONE WITH IMPACT CME!')

    # RATE OF FORCE ABSORPTION
    # DETECT IMPACT PHASE INTERVALS AGAIN AFTER IMPACTS ARE DIVIDED INTO IMPACT AND TAKEOFFS
    (
        data.impact_phase_lf,
        data.impact_phase_rf,
        lf_imp_range,
        rf_imp_range
    ) = detect_start_end_impact_phase(lph=data.phase_lf.reshape(-1, 1), rph=data.phase_rf.reshape(-1, 1))

    rofa_lf, rofa_rf = detect_rate_of_force_absorption(
        lf_imp=lf_imp_range,
        rf_imp=rf_imp_range,
        grf=data.grf.reshape(-1, 1),
        phase_lf=data.phase_lf,
        phase_rf=data.phase_rf,
        stance=data.stance,
        hz=sampl_freq
    )
    # rofa is normalized for user weight
    data.rate_force_absorption_lf = rofa_lf / (data.mass * 1000)
    data.rate_force_absorption_rf = rofa_rf / (data.mass * 1000)

    logger.info('DONE WITH RATE OF FORCE ABSORPTION!')

    # RATE OF FORCE PRODUCTION
    # DETECT TAKEOFF PHASE INTERVALS
    (
        data.takeoff_phase_lf,
        data.takeoff_phase_rf,
        lf_takeoff_range,
        rf_takeoff_range
    ) = detect_start_end_takeoff_phase(lph=data.phase_lf.reshape(-1, 1),
                                       rph=data.phase_rf.reshape(-1, 1))

    rofp_lf, rofp_rf = detect_rate_of_force_production(
        lf_takeoff=lf_takeoff_range,
        rf_takeoff=rf_takeoff_range,
        grf=data.grf.reshape(-1, 1),
        phase_lf=data.phase_lf,
        phase_rf=data.phase_rf,
        stance=data.stance,
        hz=sampl_freq
    )
    # rofp is normalized for user weight
    data.rate_force_production_lf = rofp_lf / (data.mass * 1000)
    data.rate_force_production_rf = rofp_rf / (data.mass * 1000)
    logger.info('DONE WITH RATE OF FORCE PRODUCTION!')

    # MAGNITUDE OF GRF DURING BALANCE PHASE
    data.grf_bal_phase = calculate_balance_phase_force(data) / (data.mass * 1000)

    # DEFINE UNIT ACTIVE BLOCKS
    data.total_accel[data.stance == 0] = 0
    data.active = define_unit_blocks(data.total_accel)

    # combine into data table
    length = len(data.acc_lf_x)
    setattr(data, 'loading_lf', np.array([np.nan]*length).reshape(-1, 1))
    setattr(data, 'loading_rf', np.array([np.nan]*length).reshape(-1, 1))
    setattr(data, 'grf_lf', np.array([np.nan]*length).reshape(-1, 1))
    setattr(data, 'grf_rf', np.array([np.nan]*length).reshape(-1, 1))
    scoring_data = pd.DataFrame(data={'obs_index': data.obs_index.reshape(-1,),
                                      'time_stamp': data.time_stamp.reshape(-1,),
                                      'epoch_time': data.epoch_time.reshape(-1,),
                                      'ms_elapsed': data.ms_elapsed.reshape(-1,)})
    for var in _output_columns[4:]:
        frame = pd.DataFrame(data={var: data.__dict__[var].reshape(-1, )}, index=scoring_data.index)
        frames = [scoring_data, frame]
        scoring_data = pd.concat(frames, axis=1)
        del frame, frames, data.__dict__[var]
    del data

    logger.info("Table Created")

    # scoring_data = update_stance(scoring_data)
    
    return scoring_data


def update_stance(data):
    length_lf, range_lf = _contact_duration(data.phase_lf.values,
                                            data.active.values,
                                            data.epoch_time.values,
                                            ground_phases=[2, 3])
    length_rf, range_rf = _contact_duration(data.phase_rf.values,
                                            data.active.values,
                                            data.epoch_time.values,
                                            ground_phases=[2, 3])

    for left_step in range_lf:
        left_phase = np.unique(data.phase_lf[left_step[0]:left_step[1]].values)
        if np.all(left_phase == np.array([2., 3.])):
            left_takeoff = _get_ranges(data.phase_lf[left_step[0]:left_step[1]], 3)
            if len(left_takeoff) > 0:  # has takeoff as part of ground contact
                left_takeoff = left_takeoff[0]
                if data.phase_lf[left_step[0] + left_takeoff[0] - 1] == 2:  # impact-->takeoff not ground-->takeoff
                    left_takeoff_start = left_step[0] + left_takeoff[0]
                    left_end = left_step[1]
                    right_start = range_rf[:, 0]
                    right_step = range_rf[(left_takeoff_start <= right_start) & (right_start <= left_end)]
                    if len(right_step) > 0:  # any right step that starts impact withing left_takeoff
                        # make sure start of right step is impact
                        right_step = right_step[0]
                        if data.phase_rf[right_step[0]] == 2 and 3 in np.unique(data.phase_rf[right_step[0]:right_step[1]].values):
                            data.loc[left_step[0]:right_step[1], 'stance'] = [6] * (right_step[1] - left_step[0] + 1)
                    else:
                        data.loc[left_step[0]:left_step[1], 'stance'] = [2] * (left_step[1] - left_step[0] + 1)
        step_data = data.loc[left_step[0]:left_step[1]]
        stance = np.unique(step_data.stance.values)
        if len(stance) > 1:
            if np.all(stance == np.array([2., 3.])):
                rf_air = np.where(step_data.phase_rf.values == 1)[0]
                if len(rf_air) <= 2:
                    data.loc[left_step[0]:left_step[1], 'stance'] = [3.] * len(step_data)
                else:
                    data.loc[left_step[0]:left_step[1], 'stance'] = [7.] * len(step_data)
            elif np.all(stance == np.array([2., 6.])):
                continue
            elif np.all(stance == np.array([3., 6.])):
                continue
            elif np.all(stance == np.array([2., 4.])):
                data.loc[left_step[0]:left_step[1], 'stance'] = [2.] * len(step_data)
            elif np.all(stance == np.array([3., 5.])):
                data.loc[left_step[0]:left_step[1], 'stance'] = [3.] * len(step_data)

    for right_step in range_rf:
        right_phase = np.unique(data.phase_rf[right_step[0]:right_step[1]].values)
        if np.all(right_phase == np.array([2., 3.])):
            right_takeoff = _get_ranges(data.phase_rf[right_step[0]:right_step[1]], 3)
            if len(right_takeoff) > 0:  # has takeoff as part of ground contact
                right_takeoff = right_takeoff[0]
                if data.phase_rf[right_step[0] + right_takeoff[0] - 1] == 2:  # impact-->takeoff not ground-->takeoff
                    right_takeoff_start = right_step[0] + right_takeoff[0]
                    right_end = right_step[1]
                    left_start = range_lf[:, 0]
                    left_step = range_lf[(right_takeoff_start <= left_start) & (left_start <= right_end)]
                    if len(left_step) > 0:  # any left step that starts impact withing right_takeoff
                        # make sure start of left step is impact
                        left_step = left_step[0]
                        if data.phase_lf[left_step[0]] == 2 and 3 in data.phase_lf[left_step[0]:left_step[1]].values:
                            data.loc[right_step[0]:left_step[1], 'stance'] = [6] * (left_step[1] - right_step[0] + 1)
                    else:
                        data.loc[right_step[0]:right_step[1], 'stance'] = [2] * (right_step[1] - right_step[0] + 1)
        step_data = data.loc[right_step[0]:right_step[1]]
        stance = np.unique(step_data.stance.values)
        if len(stance) > 1:
            if np.all(stance == np.array([2., 3.])):
                lf_air = np.where(step_data.phase_lf.values == 1)[0]
                if len(lf_air) <= 2:
                    data.loc[right_step[0]:right_step[1], 'stance'] = [3.] * len(step_data)
                else:
                    data.loc[right_step[0]:right_step[1], 'stance'] = [7.] * len(step_data)
            elif np.all(stance == np.array([2., 6.])):
                continue
            elif np.all(stance == np.array([3., 6.])):
                continue
            elif np.all(stance == np.array([2., 4.])):
                data.loc[right_step[0]:right_step[1], 'stance'] = [2.] * len(step_data)
            elif np.all(stance == np.array([3., 5.])):
                data.loc[right_step[0]:right_step[1], 'stance'] = [3.] * len(step_data)

    return data


def _contact_duration(phase, active, epoch_time, ground_phases):
    """compute contact duration in ms given phase data
    """
    min_gc = 80.
    max_gc = 1500.

    # enumerate phase such that all ground contacts are 0
    _phase = copy.copy(phase)
    _phase[np.array([i in ground_phases for i in _phase])] = 0
    _phase[np.array([i == 0 for i in active])] = 1

    # get index ranges for ground contacts
    ranges = _get_ranges(_phase, 0)
    length = epoch_time[ranges[:, 1]] - epoch_time[ranges[:, 0]]

    length_index = np.where((length >= min_gc) & (length <= max_gc))
    ranges = ranges[length_index]

    # subset to only get the points where ground contacts are within a reasonable window
    length = length[(length >= min_gc) & (length <= max_gc)]

    return length, ranges


def _get_ranges(col_data, value):
    """
    For a given categorical data, determine start and end index for the given value
    start: index where it first occurs
    end: index after the last occurence

    Args:
        col_data
        value: int, value to get ranges for
    Returns:
        ranges: 2d array, start and end index for each occurance of value
    """

    # determine where column data is the relevant value
    is_value = np.array(np.array(col_data == value).astype(int)).reshape(-1, 1)

    # if data starts with given value, range starts with index 0
    if is_value[0] == 1:
        t_b = 1
    else:
        t_b = 0

    # mark where column data changes to and from the given value
    absdiff = np.abs(np.ediff1d(is_value, to_begin=t_b))

    # handle the closing edge
    # if the data ends with the given value, if it was the only point, ignore the range,
    # else assign the last index as end of range
    if is_value[-1] == 1:
        if absdiff[-1] == 0:
            absdiff[-1] = 1
        else:
            absdiff[-1] = 0
    # determine the number of consecutive NaNs
    ranges = np.where(absdiff == 1)[0].reshape((-1, 2))

    return ranges


def _filter_data(x, cutoff=12, fs=100, order=4):
    """forward-backward lowpass butterworth filter
    defaults:
        cutoff freq: 12hz
        sampling rage: 100hz
        order: 4"""
    nyq = 0.5 * fs
    normal_cutoff = cutoff/nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return filtfilt(b, a, x, axis=0)


def _calculate_hip_neutral(hip_bf_quats, hip_n_transform):
    # Transform Data into Neutral Versions, for balanceCME Calculations

    # Define length, reshape transform value
    length = len(hip_bf_quats)
    hip_n_transform = np.array(hip_n_transform).reshape(-1, 4)

    # Divide static neutral and instantaneous hip data into axial components
    static_hip_neut = qc.quat_to_euler(hip_n_transform)
    neutral_hip_roll = static_hip_neut[0, 0]
    neutral_hip_pitch = static_hip_neut[0, 1]

    neutral_hip_roll = np.full((length, 1), neutral_hip_roll, float)
    neutral_hip_pitch = np.full((length, 1), neutral_hip_pitch, float)
    inst_hip_yaw = qc.quat_to_euler(hip_bf_quats)[:, 2].reshape(-1, 1)

    # Combine select data to define neutral hip data
    hip_neutral_euls = np.hstack((neutral_hip_roll, neutral_hip_pitch,
                                  inst_hip_yaw))

    # Define hip adjusted inertial frame using instantaneous hip yaw
    hip_aif_euls = np.hstack((np.zeros((length, 2)), inst_hip_yaw))

    # Convert all Euler angles to quaternions and return as relevant output
    hip_aif = qc.euler_to_quat(hip_aif_euls)
    hip_neutral = qc.euler_to_quat(hip_neutral_euls)

    lf_neutral = hip_aif  # in perfectly neutral stance, lf bf := hip AIF
    rf_neutral = hip_aif  # in perfectly neutral stance, rf bf := hip AIF

    return lf_neutral, hip_neutral, rf_neutral


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

    # Determine where column data is the relevant impact phase value
    isnan = np.array(np.array(col_dat == static).astype(int)).reshape(-1, 1)

    if isnan[0] == 1:
        t_b = 1
    else:
        t_b = 0

    # Mark where column data changes to and from NaN
    absdiff = np.abs(np.ediff1d(isnan, to_begin=t_b))
    if isnan[-1] == 1:
        absdiff = np.concatenate([absdiff, [1]], 0)
    del isnan  # not used in further computations

    # Determine the number of consecutive NaNs
    ranges = np.where(absdiff == 1)[0].reshape((-1, 2))
    length = ranges[:, 1] - ranges[:, 0]

    return ranges, length
