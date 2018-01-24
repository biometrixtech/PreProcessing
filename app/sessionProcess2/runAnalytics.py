# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 10:41:36 2016

@author: Gautam

Session execution script. Used by athletes during block processes. Takes raw
session data, processes, and returns analyzed data.

Input data called from 'biometrix-blockcontainer'

Output data collected in BlockEvent Table.
"""

import logging
import numpy as np
import pandas as pd
import copy
import psycopg2
import psycopg2.extras

from scipy.signal import butter, filtfilt

import dataObject as do
from prep_grf_data import prepare_data
import movementAttrib as matrib
import balanceCME as cmed
import impactCME as impact
import rateofForceAbsorption as rofa
import rateofForceProduction as rofp
import balancePhaseForce as bpf
import columnNames as cols
import phaseDetection as phase
from detectImpactPhaseIntervals import detect_start_end_imp_phase
from detectTakeoffPhaseIntervals import detect_start_end_takeoff_phase
import quatConvs as qc
import prePreProcessing as ppp
from extractGeometry import extract_geometry
from runRelativeCME import run_relative_CMEs

logger = logging.getLogger()
psycopg2.extras.register_uuid()


def run_session(data_in, file_version, mass, grf_fit, sc, hip_n_transform):
    """Creates object attributes according to session analysis process.

    Args:
        data_in: raw data object with attributes of:
            epoch_time, corrupt_magn, missing_type, LaX, LaY, LaZ, LqX, LqY,
            LqZ, HaX, HaY, HaZ, HqX, HqY, HqZ, RaX, RaY, RaZ, RqX, RqY, RqZ
        file_version: file format and type version (matching accessory sensor dev)
        mass: user's mass in kg
        grf_fit: keras fitted model for grf prediction
        sc: scaler model to scale data
        hip_n_transform: array of neutral hip transformation (used for cme computation in v1 data)

    Returns:
        result: string signifying success or failure.
        Note: In case of completion for local run, returns movement table.
    """
    columns = data_in.columns
    data = do.RawFrame(data_in, columns)
    sampl_freq = 100

    # Compute euler angles, geometric interpretation of data as appropriate
    lf_quats = np.hstack([data.LqW, data.LqX, data.LqY,
                          data.LqZ]).reshape(-1, 4)
    lf_euls = qc.quat_to_euler(lf_quats)
    data.LeZ = lf_euls[:, 2].reshape(-1, 1)

    hip_quats = np.hstack([data.HqW, data.HqX, data.HqY, data.HqZ]).reshape(-1, 4)
    h_euls = qc.quat_to_euler(hip_quats)
    data.HeZ = h_euls[:, 2].reshape(-1, 1)

    rf_quats = np.hstack([data.RqW, data.RqX, data.RqY, data.RqZ]).reshape(-1, 4)
    rf_euls = qc.quat_to_euler(rf_quats)
    data.ReZ = rf_euls[:, 2].reshape(-1, 1)

    (
        adduction_lf,
        flexion_lf,
        adduction_h,
        flexion_h,
        adduction_rf,
        flexion_rf
    ) = extract_geometry(lf_quats, hip_quats, rf_quats)

    if file_version == '1.0':
        data.LeX = lf_euls[:, 0].reshape(-1,1)
        data.LeY = lf_euls[:, 1].reshape(-1,1)
        data.HeX = h_euls[:, 0].reshape(-1,1)
        data.HeY = h_euls[:, 1].reshape(-1,1)
        data.ReX = rf_euls[:, 0].reshape(-1,1)
        data.ReY = rf_euls[:, 1].reshape(-1,1)
    else:
        data.LeX = adduction_lf.reshape(-1, 1)
        data.LeY = flexion_lf.reshape(-1, 1)
        data.HeX = adduction_h.reshape(-1, 1)
        data.HeY = flexion_h.reshape(-1, 1)
        data.ReX = adduction_rf.reshape(-1, 1)
        data.ReY = flexion_rf.reshape(-1, 1)

    del lf_euls, h_euls, rf_euls

    # PHASE DETECTION
    data.phase_lf, data.phase_rf = phase.combine_phase(data.LaZ,
                                                       data.RaZ,
                                                       data.LaZ,
                                                       data.RaZ,
                                                       data.LeY,
                                                       data.ReY,
                                                       sampl_freq)
    logger.info('DONE WITH PHASE DETECTION!')

    # DETECT IMPACT PHASE INTERVALS
    (
        data.impact_phase_lf,
        data.impact_phase_rf,
        lf_imp_range,
        rf_imp_range
    ) = detect_start_end_imp_phase(lph=data.phase_lf, rph=data.phase_rf)
    logger.info('DONE WITH DETECTING IMPACT PHASE INTERVALS')

    # ADD TAKEOFF PHASE DETECTION TO PHASE
    # TODO: Integrate takeoff detection as well as impact and takeoff phase interval
    # detection to phase detection
    # TAKEOFF DETECTION
    phase_lf = copy.copy(data.phase_lf).reshape(-1,)
    phase_rf = copy.copy(data.phase_rf).reshape(-1,)

    # Add takeoff phase for left foot
    # takeoffs from balance phase
    ground_lf = np.array([i in [0, 1] for i in phase_lf]).astype(int)
    ground_to_air = np.where(np.ediff1d(ground_lf, to_begin=0) == -1)[0]
    takeoff = []
    for i in ground_to_air:
        takeoff.append(np.arange(i - 10, i))

    # takeoffs from impact
    air_lf = np.array([i in [2, 3] for i in phase_lf]).astype(int)
    air_lf[np.where(phase_lf == 4)[0]] = 3
    impact_to_air = np.where(np.ediff1d(air_lf, to_begin=0) == -2)[0]
    for i in impact_to_air:
        # find when this impact started
        try:
            impact_start = lf_imp_range[np.where(lf_imp_range[:, 1] == i)[0], 0]
            takeoff_len = int((i - impact_start[0])/2)
            takeoff.append(np.arange(i - takeoff_len, i))
        except IndexError:
            print(i)
            print(impact_start)
    if len(takeoff) > 0:
        takeoff_lf = np.concatenate(takeoff).ravel()
        data.phase_lf[takeoff_lf] = 6

    # Add takeoff phase fo right foot
    # takeoffs from balance phase
    ground_rf = np.array([i in [0, 2] for i in phase_rf]).astype(int)
    ground_to_air = np.where(np.ediff1d(ground_rf, to_begin=0) == -1)[0]
    takeoff = []
    for i in ground_to_air:
        takeoff.append(np.arange(i - 10, i))

    # takeoffs from impact
    air_rf = np.array([i in [1, 3] for i in phase_rf]).astype(int)
    air_rf[np.where(phase_rf == 5)[0]] = 3
    impact_to_air = np.where(np.ediff1d(air_rf, to_begin=0) == -2)[0]
    for i in impact_to_air:
        # find when this impact started
        try:
            impact_start = rf_imp_range[np.where(rf_imp_range[:, 1] == i)[0], 0]
            takeoff_len = int((i - impact_start[0])/2)
            takeoff.append(np.arange(i - takeoff_len, i))
        except IndexError:
            print(i)
            print(impact_start)
    if len(takeoff) > 0:
        takeoff_rf = np.concatenate(takeoff).ravel()
        data.phase_rf[takeoff_rf] = 7

    # ms_elapsed and datetime
    data.time_stamp, data.ms_elapsed = ppp.convert_epochtime_datetime_mselapsed(data.epoch_time)

#%%
    # MOVEMENT ATTRIBUTES AND PERFORMANCE VARIABLES
    # isolate hip acceleration and euler angle data
    hip_acc = np.hstack([data.HaX, data.HaY, data.HaZ])
    hip_eul = np.hstack([data.HeX, data.HeY, data.HeZ])

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
    ) = matrib.plane_analysis(hip_acc, hip_eul, data.ms_elapsed)

    # analyze stance
    data.stance = matrib.run_stance_analysis(data)
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

#%%
    # MOVEMENT QUALITY FEATURES

    # isolate bf quaternions
    lf_quat = np.hstack([data.LqW, data.LqX, data.LqY, data.LqZ])
    hip_quat = np.hstack([data.HqW, data.HqX, data.HqY, data.HqZ])
    rf_quat = np.hstack([data.RqW, data.RqX, data.RqY, data.RqZ])

    # calculate movement attributes
    if file_version == '1.0':
        # special code to rerun v1 data to gather older cmes
        import balanceCMEV1 as cmedv1
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
        ) = cmedv1.calculate_rot_CMEs(lf_quat, hip_quat, rf_quat,
                                      lf_neutral, hip_neutral, rf_neutral,
                                      data.phase_lf, data.phase_rf)
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
        ) = cmed.calculate_rot_CMEs(lf_quat, hip_quat, rf_quat, data.phase_lf, data.phase_rf)
        del lf_quat, hip_quat, rf_quat

    # new relative CMEs
    data = run_relative_CMEs(data)
    logger.info('DONE WITH BALANCE CME!')

    # IMPACT CME
    # define dictionary for msElapsed

    # landing time attributes
    n_landtime, ltime_index, lf_rf_imp_indicator =\
                            impact.sync_time(rf_imp_range[:, 0],
                                             lf_imp_range[:, 0],
                                             float(sampl_freq))

    # landing pattern attributes
    if len(n_landtime) != 0:
        n_landpattern = impact.landing_pattern(data.ReY, data.LeY,
                                               land_time_index=ltime_index,
                                               l_r_imp_ind=lf_rf_imp_indicator,
                                               sampl_rate=sampl_freq,
                                               land_time=n_landtime)
        land_time, land_pattern =\
            impact.continuous_values(n_landpattern, n_landtime,
                                     len(data.LaX), ltime_index)
        data.land_time = land_time.reshape(-1, 1)
        data.land_pattern_rf = land_pattern[:, 0].reshape(-1, 1)
        data.land_pattern_lf = land_pattern[:, 1].reshape(-1, 1)
        del n_landpattern, land_time, land_pattern
    else:
        data.land_time = np.zeros((len(data.LaX), 1))*np.nan
        data.land_pattern_lf = np.zeros((len(data.LaX), 1))*np.nan
        data.land_pattern_rf = np.zeros((len(data.LaX), 1))*np.nan
    del n_landtime, ltime_index, lf_rf_imp_indicator
    logger.info('DONE WITH IMPACT CME!')

    # prepare data for grf prediction
    data.mass = mass*9.807/1000 # convert mass from kg to kN
    grf_data, nan_row = prepare_data(data, sc)

    # predict grf
    grf = grf_fit.predict(grf_data).reshape(-1,)

    # pass predicted data through low-pass filter
    grf = _filter_data(grf, cutoff=35)

    # set grf value below certain threshold to 0
    grf[grf <= .1] = 0
    # fill in nans for rows with missing predictors
    length = len(data_in)
    grf_temp = np.ones(length)
    grf_temp[np.array(list(set(range(length)) - set(nan_row)))] = grf
    # Insert nan for grf where data needed to predict was missing
    if len(nan_row) != 0:
        for i in nan_row:
            grf_temp[i] = np.nan

    data.grf = grf_temp*1000

    del grf_data, nan_row, grf_fit, grf, grf_temp
    logger.info('DONE WITH MECH STRESS!')

    # RATE OF FORCE ABSORPTION
    ##  DETECT IMPACT PHASE INTERVALS AGAIN AFTER IMPACTS ARE DIVIDED INTO IMPACT AND TAKEOFFS
    (
        data.impact_phase_lf,
        data.impact_phase_rf,
        lf_imp_range,
        rf_imp_range
    ) = detect_start_end_imp_phase(lph=data.phase_lf.reshape(-1, 1),
                                   rph=data.phase_rf.reshape(-1, 1))

    rofa_lf, rofa_rf = rofa.det_rofa(lf_imp=lf_imp_range,
                                     rf_imp=rf_imp_range,
                                     grf=data.grf.reshape(-1, 1),
                                     phase_lf=data.phase_lf,
                                     phase_rf=data.phase_rf,
                                     stance=data.stance,
                                     hz=sampl_freq)
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

    rofp_lf, rofp_rf = rofp.det_rofp(lf_takeoff=lf_takeoff_range,
                                     rf_takeoff=rf_takeoff_range,
                                     grf=data.grf.reshape(-1, 1),
                                     phase_lf=data.phase_lf,
                                     phase_rf=data.phase_rf,
                                     stance=data.stance,
                                     hz=sampl_freq)
    # rofp is normalized for user weight
    data.rate_force_production_lf = rofp_lf / (data.mass * 1000)
    data.rate_force_production_rf = rofp_rf / (data.mass * 1000)
    logger.info('DONE WITH RATE OF FORCE PRODUCTION!')

    # MAGNITUDE OF GRF DURING BALANCE PHASE
    data.grf_bal_phase = bpf.bal_phase_force(data) / (data.mass * 1000)

    # combine into data table
    length = len(data.LaX)
    setattr(data, 'loading_lf', np.array([np.nan]*length).reshape(-1, 1))
    setattr(data, 'loading_rf', np.array([np.nan]*length).reshape(-1, 1))
    setattr(data, 'grf_lf', np.array([np.nan]*length).reshape(-1, 1))
    setattr(data, 'grf_rf', np.array([np.nan]*length).reshape(-1, 1))
    scoring_data = pd.DataFrame(data={'obs_index': data.obs_index.reshape(-1,),
                                      'time_stamp': data.time_stamp.reshape(-1,),
                                      'epoch_time': data.epoch_time.reshape(-1,),
                                      'ms_elapsed': data.ms_elapsed.reshape(-1,)})
    for var in cols.column_session2_out[4:]:
        frame = pd.DataFrame(data={var: data.__dict__[var].reshape(-1, )}, index=scoring_data.index)
        frames = [scoring_data, frame]
        scoring_data = pd.concat(frames, axis=1)
        del frame, frames, data.__dict__[var]
    del data

    logger.info("Table Created")

    
    return scoring_data


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
    #%% Transform Data into Neutral Versions, for balanceCME Calculations

   # define length, reshape transform value
    length = len(hip_bf_quats)
    hip_n_transform = np.array(hip_n_transform).reshape(-1, 4)

   # divide static neutral and instantaneous hip data into axial components
    static_hip_neut = qc.quat_to_euler(hip_n_transform)
    neutral_hip_roll = static_hip_neut[0, 0]
    neutral_hip_pitch = static_hip_neut[0, 1]

    neutral_hip_roll = np.full((length, 1), neutral_hip_roll, float)
    neutral_hip_pitch = np.full((length, 1), neutral_hip_pitch, float)
    inst_hip_yaw = qc.quat_to_euler(hip_bf_quats)[:, 2].reshape(-1, 1)

   # combine select data to define neutral hip data
    hip_neutral_euls = np.hstack((neutral_hip_roll, neutral_hip_pitch,
                                  inst_hip_yaw))

   # define hip adjusted inertial frame using instantaneous hip yaw
    hip_aif_euls = np.hstack((np.zeros((length, 2)), inst_hip_yaw))

   # convert all Euler angles to quaternions and return as relevant output
    hip_aif = qc.euler_to_quat(hip_aif_euls)
    hip_neutral = qc.euler_to_quat(hip_neutral_euls)

    lf_neutral = hip_aif # in perfectly neutral stance, lf bf := hip AIF
    rf_neutral = hip_aif # in perfectly neutral stance, rf bf := hip AIF

    return lf_neutral, hip_neutral, rf_neutral
