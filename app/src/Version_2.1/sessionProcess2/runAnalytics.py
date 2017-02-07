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

import dataObject as do
from mechStressTraining import prepare_data
import movementAttrib as matrib
import balanceCME as cmed
import impactCME as impact
import rateofForceAbsorption as fa
import columnNames as cols
import phaseDetection as phase
from detectImpactPhaseIntervals import detect_start_end_imp_phase

logger = logging.getLogger()
psycopg2.extras.register_uuid()


def run_session(data_in, file_name, mass, mstress_fit, aws=True):
    """Creates object attributes according to session analysis process.

    Args:
        sensor_data: raw data object with attributes of:
            epoch_time, corrupt_magn, missing_type, LaX, LaY, LaZ, LqX, LqY,
            LqZ, HaX, HaY, HaZ, HqX, HqY, HqZ, RaX, RaY, RaZ, RqX, RqY, RqZ
        file_name: sensor_data_filename in DB
        AWS: Boolean indicator for whether we're running locally or on amazon
            aws
    
    Returns:
        result: string signifying success or failure.
        Note: In case of completion for local run, returns movement table.
    """
#%%
    global AWS
    global COLUMN_SESSION2_OUT
    AWS = aws
    COLUMN_SESSION2_OUT = cols.column_session2_out
    columns = data_in.columns
    data = do.RawFrame(data_in, columns)
    sampl_freq = 100

#%%
    # PHASE DETECTION
    data.phase_lf, data.phase_rf = phase.combine_phase(data.LaZ, data.RaZ, sampl_freq)

    _logger('DONE WITH PHASE DETECTION!')
    
#%%
    # DETECT IMPACT PHASE INTERVALS
    data.lf_impact_phase, data.rf_impact_phase,\
    lf_imp_range, rf_imp_range = detect_start_end_imp_phase(lph=data.phase_lf,
                                                            rph=data.phase_rf)
    _logger('DONE WITH DETECTING IMPACT PHASE INTERVALS')

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
    _logger('DONE WITH MOVEMENT ATTRIBUTES AND PERFORMANCE VARIABLES!')
    #_logger(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
#%%
    # MOVEMENT QUALITY FEATURES

    # isolate bf quaternions
    lf_quat = np.hstack([data.LqW, data.LqX, data.LqY, data.LqZ])
    hip_quat = np.hstack([data.HqW, data.HqX, data.HqY, data.HqZ])
    rf_quat = np.hstack([data.RqW, data.RqX, data.RqY, data.RqZ])

    # isolate neutral quaternions
    lf_neutral = np.hstack([data.LqW_n, data.LqX_n, data.LqY_n, data.LqZ_n])
    hip_neutral = np.hstack([data.HqW_n, data.HqX_n, data.HqY_n, data.HqZ_n])
    rf_neutral = np.hstack([data.RqW_n, data.RqX_n, data.RqY_n, data.RqZ_n])

    # calculate movement attributes
    data.contra_hip_drop_lf, data.contra_hip_drop_rf, data.ankle_rot_lf,\
        data.ankle_rot_rf, data.foot_position_lf, data.foot_position_rf,\
        = cmed.calculate_rot_CMEs(lf_quat, hip_quat, rf_quat, lf_neutral,
                                      hip_neutral, rf_neutral, data.phase_lf,\
                                      data.phase_rf)
    del lf_quat, hip_quat, rf_quat
    del lf_neutral, hip_neutral, rf_neutral
    _logger('DONE WITH BALANCE CME!')
    #_logger(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
#%%
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
    _logger('DONE WITH IMPACT CME!')
    #_logger(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)


    ms_data, nan_row = prepare_data(data, False)
   
    # calculate mechanical stress
    data.mech_stress = np.abs(mstress_fit.predict(ms_data).reshape(-1, 1))
    #Insert nan for mech_stress where data needed to predict was missing
    if len(nan_row) != 0:
        for i in nan_row:
            data.mech_stress = np.insert(data.mech_stress, i, np.nan, axis=0)
    del ms_data, nan_row, mstress_fit
    _logger('DONE WITH MECH STRESS!')
#%%
    # RATE OF FORCE ABSORPTION
#    mass = 50
    rofa_lf, rofa_rf = fa.det_rofa(l_ph=data.phase_lf, r_ph=data.phase_rf,
                                   laccz=data.LaZ, raccz=data.RaZ,
                                   user_mass=mass, hz=sampl_freq) 
    data.rate_force_absorption_lf = rofa_lf
    data.rate_force_absorption_rf = rofa_rf

    del rofa_lf, rofa_rf
    _logger('DONE WITH RATE OF FORCE ABSORPTION!')
#%%
    # combine into movement data table
#    length = len(data.user_id)
#
    length = len(data.team_id)
    setattr(data, 'activity_id', np.array(['']*length).reshape(-1, 1))
    data.ms_elapsed = data.ms_elapsed.astype(int)
    data.single_leg_stationary = data.single_leg_stationary.astype(int)
    data.single_leg_dynamic = data.single_leg_dynamic.astype(int)
    data.double_leg = data.double_leg.astype(int)
    data.feet_eliminated = data.feet_eliminated.astype(int)
    data.rot_binary = data.rot_binary.astype(int)
    data.lat_binary = data.lat_binary.astype(int)
    data.vert_binary = data.vert_binary.astype(int)
    data.horz_binary = data.horz_binary.astype(int)
    data.stationary_binary = data.stationary_binary.astype(int)
    data.lf_impact_phase = data.lf_impact_phase.astype(int)
    data.rf_impact_phase = data.rf_impact_phase.astype(int)
    scoring_data = pd.DataFrame(data={'team_id': data.team_id.reshape(-1, ),
                                      'user_id': data.user_id.reshape(-1,),
                                      'session_event_id': data.session_event_id.reshape(-1,),
                                      'session_type': data.session_type.reshape(-1,)})
    for var in COLUMN_SESSION2_OUT[4:]:
       frame = pd.DataFrame(data={var: data.__dict__[var].reshape(-1, )}, index=scoring_data.index)
       frames = [scoring_data, frame]
       scoring_data = pd.concat(frames, axis=1)
       del frame, frames, data.__dict__[var]
    del data

    _logger("Table Created")

    
    return scoring_data

#%%
def _logger(message, info=True):
    if AWS:
        if info:
            logger.info(message)
        else:
            logger.warning(message)
    else:
        print message

#%%
if __name__ == "__main__":
    sensor_data = 'C:\\Users\\dipesh\\Desktop\\biometrix\\aws\\c4ed8189-6e1d-47c3-9cc5-446329b10796'
    file_name = '7803f828-bd32-4e97-860c-34a995f08a9e'
    result = run_session(sensor_data, file_name, aws=False)
