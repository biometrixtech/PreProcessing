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
import psycopg2
import psycopg2.extras

from scipy.signal import butter, filtfilt

import dataObject as do
from prep_grf_data import prepare_data
import movementAttrib as matrib
import balanceCME as cmed
import impactCME as impact
import rateofForceAbsorption as fa
import columnNames as cols
import phaseDetection as phase
from detectImpactPhaseIntervals import detect_start_end_imp_phase
import quatConvs as qc
import prePreProcessing as ppp
from extractGeometry import extract_geometry

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
        aws: Boolean indicator for whether we're running locally or on amazon
            aws
    
    Returns:
        result: string signifying success or failure.
        Note: In case of completion for local run, returns movement table.
    """
    columns = data_in.columns
    data_in = ppp.subset_data(old_data=data_in)
    data = do.RawFrame(data_in, columns)
    sampl_freq = 100

    # PHASE DETECTION
    data.phase_lf, data.phase_rf = phase.combine_phase(data.LaZ, data.RaZ,
                                                       sampl_freq)

    logger.info('DONE WITH PHASE DETECTION!')

    # DETECT IMPACT PHASE INTERVALS
    data.impact_phase_lf, data.impact_phase_rf, lf_imp_range, rf_imp_range = detect_start_end_imp_phase(lph=data.phase_lf, rph=data.phase_rf)
    logger.info('DONE WITH DETECTING IMPACT PHASE INTERVALS')

    # ms_elapsed and datetime
    data.time_stamp, data.ms_elapsed = ppp.convert_epochtime_datetime_mselapsed(data.epoch_time)

    # Compute euler angles, geometric interpretation of data as appropriate
    lf_quats = np.hstack([data.LqW, data.LqX, data.LqY,
                          data.LqZ]).reshape(-1, 4)
    lf_euls = qc.quat_to_euler(lf_quats)
    data.LeZ = lf_euls[:, 2].reshape(-1, 1)
    del(lf_euls)

    hip_quats = np.hstack([data.HqW, data.HqX, data.HqY, data.HqZ]).reshape(-1, 4)
    h_euls = qc.quat_to_euler(hip_quats)
    data.HeZ = h_euls[:, 2].reshape(-1, 1)
    del(h_euls)

    rf_quats = np.hstack([data.RqW, data.RqX, data.RqY, data.RqZ]).reshape(-1, 4)
    rf_euls = qc.quat_to_euler(rf_quats)
    data.ReZ = rf_euls[:, 2].reshape(-1, 1)
    del(rf_euls)

    adduction_L, flexion_L, adduction_H, flexion_H, adduction_R, flexion_R = extract_geometry(lf_quats, hip_quats, rf_quats)

    data.LeX = adduction_L.reshape(-1, 1)
    data.LeY = flexion_L.reshape(-1, 1)
    data.HeX = adduction_H.reshape(-1, 1)
    data.HeY = flexion_H.reshape(-1, 1)
    data.ReX = adduction_R.reshape(-1, 1)
    data.ReY = flexion_R.reshape(-1, 1)

#%%
    # MOVEMENT ATTRIBUTES AND PERFORMANCE VARIABLES
    # isolate hip acceleration and euler angle data
    hip_acc = np.hstack([data.HaX, data.HaY, data.HaZ])
    hip_eul = np.hstack([data.HeX, data.HeY, data.HeZ])

    # analyze planes of movement
    data.lat, data.vert, data.horz, data.rot,\
        data.lat_binary, data.vert_binary, data.horz_binary,\
        data.rot_binary, data.stationary_binary,\
        data.total_accel = matrib.plane_analysis(hip_acc, hip_eul,
                                                 data.ms_elapsed)

    # analyze stance
    data.standing, data.not_standing \
        = matrib.standing_or_not(hip_eul, sampl_freq)
    data.double_leg, data.single_leg, data.feet_eliminated \
        = matrib.double_or_single_leg(data.phase_lf, data.phase_rf,
                                      data.standing, sampl_freq)
    data.single_leg_stationary, data.single_leg_dynamic \
        = matrib.stationary_or_dynamic(data.phase_lf, data.phase_rf,
                                       data.single_leg, sampl_freq)
    del hip_acc, hip_eul
    logger.info('DONE WITH MOVEMENT ATTRIBUTES AND PERFORMANCE VARIABLES!')

    # Enumerate plane and stance
    data.stance = np.array([1]*len(data.rot)).reshape(-1, 1)
    data.plane = np.array([0]*len(data.rot)).reshape(-1, 1)
    # Enumerate stance
    data.stance[data.feet_eliminated == 1] = 2
    data.stance[data.double_leg == 1] = 3
    data.stance[data.single_leg_stationary == 1] = 4
    data.stance[data.single_leg_dynamic == 1] = 5

    data.not_standing = np.array([0]*len(data.rot)).reshape(-1, 1)
    data.not_standing[data.stance == 1] = 1

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
    data.plane[(data.rot_binary == 1) & (data.lat_binary == 1) & (data.vert_binary == 1)& (data.horz_binary == 1)] = 15


#%%
    # MOVEMENT QUALITY FEATURES

    # isolate bf quaternions
    lf_quat = np.hstack([data.LqW, data.LqX, data.LqY, data.LqZ])
    hip_quat = np.hstack([data.HqW, data.HqX, data.HqY, data.HqZ])
    rf_quat = np.hstack([data.RqW, data.RqX, data.RqY, data.RqZ])

    # calculate movement attributes
    if file_version == '1.0':
        import balanceCMEV1 as cmedv1
        # isolate neutral quaternions
        lf_neutral, hip_neutral, rf_neutral = _calculate_hip_neutral(hip_quat, hip_n_transform)

        # calculate movement attributes
        data.contra_hip_drop_lf, data.contra_hip_drop_rf, data.ankle_rot_lf,\
            data.ankle_rot_rf, data.foot_position_lf, data.foot_position_rf,\
            = cmedv1.calculate_rot_CMEs(lf_quat, hip_quat, rf_quat, lf_neutral,
                                          hip_neutral, rf_neutral, data.phase_lf,\
                                          data.phase_rf)
        del lf_quat, hip_quat, rf_quat
        del lf_neutral, hip_neutral, rf_neutral
    else:
        data.contra_hip_drop_lf, data.contra_hip_drop_rf, data.ankle_rot_lf,\
            data.ankle_rot_rf, data.foot_position_lf, data.foot_position_rf,\
            = cmed.calculate_rot_CMEs(lf_quat, hip_quat, rf_quat, data.phase_lf, data.phase_rf)
        del lf_quat, hip_quat, rf_quat
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
    grf = _filter_data(grf, cutoff=12)

    # set grf value below certain threshold to 0
    grf[grf <= .1] = np.nan
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
    rofa_lf, rofa_rf = fa.det_rofa(lf_imp=lf_imp_range, rf_imp=rf_imp_range,
                                   laccz=data.LaZ, raccz=data.RaZ,
                                   user_mass=mass, hz=sampl_freq) 
    data.rate_force_absorption_lf = rofa_lf
    data.rate_force_absorption_rf = rofa_rf

    del rofa_lf, rofa_rf
    logger.info('DONE WITH RATE OF FORCE ABSORPTION!')

    # combine into data table
    length = len(data.LaX) 
    setattr(data, 'loading_lf', np.array([np.nan]*length).reshape(-1, 1)) 
    setattr(data, 'loading_rf', np.array([np.nan]*length).reshape(-1, 1)) 
    setattr(data, 'grf_lf', np.array([np.nan]*length).reshape(-1, 1)) 
    setattr(data, 'grf_rf', np.array([np.nan]*length).reshape(-1, 1)) 
    setattr(data, 'rate_force_production_lf', np.array([np.nan]*length).reshape(-1, 1)) 
    setattr(data, 'rate_force_production_rf', np.array([np.nan]*length).reshape(-1, 1))
    scoring_data = pd.DataFrame(data={'obs_index': data.obs_index.reshape(-1, ),
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


