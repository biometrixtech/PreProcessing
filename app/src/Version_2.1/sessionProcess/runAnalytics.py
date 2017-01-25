# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 10:41:36 2016

@author: Gautam

Session execution script. Used by athletes during block processes. Takes raw
session data, processes, and returns analyzed data.

Input data called from 'biometrix-blockcontainer'

Output data collected in BlockEvent Table.
"""
import sys
import pickle
import cStringIO
import logging
import numpy as np
import pandas as pd
import psycopg2
import psycopg2.extras
import boto3
import gc
#import resource
import math
from itertools import islice, count

import prePreProcessing as ppp
import dataObject as do
import phaseDetection as phase
#import IAD
import coordinateFrameTransformation as coord
from mechStressTraining import prepare_data
import movementAttrib as matrib
import balanceCME as cmed
#import quatConvs as qc
import impactCME as impact
#import createTables as ct
import sessionProcessQueries as queries
import checkProcessed as cp
import rateofForceAbsorption as fa
from columnNames import columns_session, column_session_out


logger = logging.getLogger()
psycopg2.extras.register_uuid()


def run_session(sensor_data, file_name, aws=True):
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
    global COLUMN_SESSION_OUT
    AWS = aws
    COLUMN_SESSION_OUT = column_session_out
    #_logger(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
#    soft, hard = resource.getrlimit(resource.RLIMIT_DATA)
#    resource.setrlimit(resource.RLIMIT_DATA, (28000, 56000))
#    _logger(soft)
#    _logger(hard)
    #resource.setrlimit(resource.RLIMIT_STACK, (5000, 10000))

    # Define containers to read from and write to
    cont_write = 'biometrix-sessionprocessedcontainer'
    cont_write_final = 'biometrix-scoringcontainer'

    # Define container that holds models
    cont_models = 'biometrix-globalmodels'
    
    # establish connection to both database and s3 resource
    conn, cur, s3 = _connect_db_s3()
    
    # read session_event_id and other relevant ids
    try:
        ids_from_db = _read_ids(cur, file_name)
    except IndexError:
        return "Fail!"
    session_event_id = ids_from_db[0]

    # read sensor data as ndarray
    try:
        sdata = np.genfromtxt(sensor_data, dtype=float, delimiter=',',
                              names=True)
    except IndexError as error:
        _logger("Sensor data doesn't have column names!", info=False)
        return "Fail!"
    if len(sdata) == 0:
        _logger("Sensor data is empty!", info=False)
        return "Fail!"
    #_logger(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    sdata.dtype.names = columns_session
    # SUBSET DATA
    subset_data = ppp.subset_data(old_data=sdata)
    del sdata
    if len(subset_data) == 0:
        _logger("No overlapping samples after time sync", info=False)
        return "Fail!"
    # Record percentage and ranges of magn_values for diagonostic purposes
#    _record_magn(subset_data, file_name, s3)

    # read transformation offset values from DB/local Memory
    offsets_read = _read_offsets(cur, session_event_id)
    _logger("OFFSETS READ")
    if len(subset_data) == 0:
        _logger("No samples left after subsetting!", info=False)
        return "Fail!"

    columns = subset_data.dtype.names
    data = do.RawFrame(subset_data, columns)
    setattr(data, 'obs_master_index',
            np.array(range(len(data.LaX))).reshape(-1, 1) + 1)
    del subset_data
#    data = sdata.view(np.recarray)
    data = cp.handle_processed(data)
#    data = _add_rawdata(data)
    user_id = ids_from_db[2]
    try:
        cur.execute(queries.quer_read_mass, (user_id,))
        mass = cur.fetchall()[0][0]
    except psycopg2.Error as error:
        _logger("Cannot read user's mass", info=False)
        raise error
    else:
        if mass is None:
            mass = 60
#            raise ValueError("User's mass does not exist in DB!")

    # PRE-PRE-PROCESSING
    # Check for duplicate epoch time
    duplicate_epoch_time = ppp.check_duplicate_epochtime(data.epoch_time)
    if duplicate_epoch_time:
        _logger('Duplicate epoch time.', info=False)
    # check for missing values
    data = ppp.handling_missing_data(data)
    # determine the real quartenion
    data = _real_quaternions(data)
    # convert epoch time to date time and determine milliseconds elapsed
    data.time_stamp, data.ms_elapsed = \
        ppp.convert_epochtime_datetime_mselapsed(data.epoch_time)
    sampl_freq = 100
    _logger('DONE WITH PRE-PRE-PROCESSING!')
    #_logger(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
#%%
    # COORDINATE FRAME TRANSFORMATION

    # pull relevant transform offset values from SessionCalibrationEvent
    hip_n_transform = np.array(offsets_read[0]).reshape(-1, 1)
    if len(hip_n_transform) == 0:
        _logger("Calibration offset value missing", info=False)
        raise ValueError("Missing Offsets")
    hip_bf_transform = np.array(offsets_read[1]).reshape(-1, 1)
    if len(hip_bf_transform) == 0:
        _logger("Calibration offset value missing", info=False)
        raise ValueError("Missing Offsets")
    lf_n_transform = np.array(offsets_read[2]).reshape(-1, 1)
    if len(lf_n_transform) == 0:
        _logger("Calibration offset value missing", info=False)
        raise ValueError("Missing Offsets")
    lf_bf_transform = np.array(offsets_read[3]).reshape(-1, 1)
    if len(lf_bf_transform) == 0:
        _logger("Calibration offset value missing", info=False)
        raise ValueError("Missing Offsets")
    rf_n_transform = np.array(offsets_read[4]).reshape(-1, 1)
    if len(rf_n_transform) == 0:
        _logger("Calibration offset value missing", info=False)
        raise ValueError("Missing Offsets")
    rf_bf_transform = np.array(offsets_read[5]).reshape(-1, 1)
    if len(rf_bf_transform) == 0:
        _logger("Calibration offset value missing", info=False)
        raise ValueError("Missing Offsets")

    # use transform values to adjust coordinate frame of all block data
    _transformed_data, neutral_data =\
            coord.transform_data(data, hip_bf_transform, lf_bf_transform,
                                 rf_bf_transform, lf_n_transform,
                                 rf_n_transform, hip_n_transform)
    # transform neutral orientations for each point in time to ndarray
    neutral_data = np.array(neutral_data)

    # reshape left foot body transformed data
    data.LaX = _transformed_data[:, 1].reshape(-1, 1)
    data.LaY = _transformed_data[:, 2].reshape(-1, 1)
    data.LaZ = _transformed_data[:, 3].reshape(-1, 1)
    data.LeX = _transformed_data[:, 4].reshape(-1, 1)
    data.LeY = _transformed_data[:, 5].reshape(-1, 1)
    data.LeZ = _transformed_data[:, 6].reshape(-1, 1)
    data.LqW = _transformed_data[:, 7].reshape(-1, 1)
    data.LqX = _transformed_data[:, 8].reshape(-1, 1)
    data.LqY = _transformed_data[:, 9].reshape(-1, 1)
    data.LqZ = _transformed_data[:, 10].reshape(-1, 1)
    # reshape hip body transformed data
    data.HaX = _transformed_data[:, 11].reshape(-1, 1)
    data.HaY = _transformed_data[:, 12].reshape(-1, 1)
    data.HaZ = _transformed_data[:, 13].reshape(-1, 1)
    data.HeX = _transformed_data[:, 14].reshape(-1, 1)
    data.HeY = _transformed_data[:, 15].reshape(-1, 1)
    data.HeZ = _transformed_data[:, 16].reshape(-1, 1)
    data.HqW = _transformed_data[:, 17].reshape(-1, 1)
    data.HqX = _transformed_data[:, 18].reshape(-1, 1)
    data.HqY = _transformed_data[:, 19].reshape(-1, 1)
    data.HqZ = _transformed_data[:, 20].reshape(-1, 1)
    # reshape right foot body transformed data
    data.RaX = _transformed_data[:, 21].reshape(-1, 1)
    data.RaY = _transformed_data[:, 22].reshape(-1, 1)
    data.RaZ = _transformed_data[:, 23].reshape(-1, 1)
    data.ReX = _transformed_data[:, 24].reshape(-1, 1)
    data.ReY = _transformed_data[:, 25].reshape(-1, 1)
    data.ReZ = _transformed_data[:, 26].reshape(-1, 1)
    data.RqW = _transformed_data[:, 27].reshape(-1, 1)
    data.RqX = _transformed_data[:, 28].reshape(-1, 1)
    data.RqY = _transformed_data[:, 29].reshape(-1, 1)
    data.RqZ = _transformed_data[:, 30].reshape(-1, 1)
    #_logger(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    del _transformed_data
    gc.collect()
    #_logger(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    _logger('DONE WITH COORDINATE FRAME TRANSFORMATION!')
#%%
    # PHASE DETECTION
    data.phase_lf, data.phase_rf = phase.combine_phase(data.LaZ, data.RaZ,
                                                       sampl_freq)

    _logger('DONE WITH PHASE DETECTION!')

#%%
    # INTELLIGENT ACTIVITY DETECTION (IAD)
    # load model
#    try:
#        iad_obj = s3.Bucket(cont_models).Object('iad_finalized_model.sav')
#        iad_fileobj = iad_obj.get()
#        iad_body = iad_fileobj["Body"].read()
#
#        # we're reading the first model on the list, there are multiple
#        loaded_iad_model = pickle.loads(iad_body)
#    except Exception as error:
#        if AWS:
#            _logger("Cannot load iad_model from s3", info=False)
#            raise error
#        else:
#            try:
#                with open('iad_finalized_model.sav') as model_file:
#                    loaded_iad_model = pickle.load(model_file)
#            except:
#                raise IOError("Model file not found in S3 or local directory")
#
#    # predict activity state
#    iad_features = IAD.preprocess_iad(data, training=False)
#    iad_labels = loaded_iad_model.predict(iad_features)
#    iad_predicted_labels = IAD.label_aggregation(iad_labels)
#    data.activity_id =\
#            IAD.mapping_labels_on_data(iad_predicted_labels,
#                                       len(data.LaX)).reshape(-1, 1)
#
#    _logger('DONE WITH IAD!')
##%%
#    # save sensor data before subsetting
##    sensor_data = ct.create_sensor_data(len(data.LaX), data)
#    # Define attributes to be stored
#    data_pd = pd.DataFrame(data={'team_id': data.team_id.reshape(-1,),
#                                 'user_id': data.user_id.reshape(-1,),
#                                 'team_regimen_id': data.team_regimen_id.reshape(-1,),
#                                 'block_id': data.block_id.reshape(-1,),
#                                 'block_event_id': data.block_event_id.reshape(-1,),
#                                 'training_session_log_id': data.training_session_log_id.reshape(-1,),
#                                 'session_event_id': data.session_event_id.reshape(-1,),
#                                 'session_type': data.session_type.reshape(-1,),
#                                 'obs_index': data.obs_master_index.reshape(-1,),
#                                 'obs_master_index': data.obs_master_index.reshape(-1,),
#                                 'time_stamp': data.time_stamp.reshape(-1,),
#                                 'epoch_time': data.epoch_time.reshape(-1,),
#                                 'ms_elapsed': data.ms_elapsed.reshape(-1,),
#                                 'phase_lf': data.phase_lf.reshape(-1,),
#                                 'phase_rf': data.phase_rf.reshape(-1,),
#                                 'activity_id': data.activity_id.reshape(-1,),
#                                 'LaX': data.LaX.reshape(-1,),
#                                 'LaY': data.LaY.reshape(-1,),
#                                 'LaZ': data.LaZ.reshape(-1,),
#                                 'LqW': data.LqW.reshape(-1,),
#                                 'LqX': data.LqX.reshape(-1,),
#                                 'LqY': data.LqY.reshape(-1,),
#                                 'LqZ': data.LqZ.reshape(-1,),
#                                 'HaX': data.HaX.reshape(-1,),
#                                 'HaY': data.HaY.reshape(-1,),
#                                 'HaZ': data.HaZ.reshape(-1,),
#                                 'HqW': data.HqW.reshape(-1,),
#                                 'HqX': data.HqX.reshape(-1,),
#                                 'HqY': data.HqY.reshape(-1,),
#                                 'HqZ': data.HqZ.reshape(-1,),
#                                 'RaX': data.RaX.reshape(-1,),
#                                 'RaY': data.RaY.reshape(-1,),
#                                 'RaZ': data.RaZ.reshape(-1,),
#                                 'RqW': data.RqW.reshape(-1,),
#                                 'RqX': data.RqX.reshape(-1,),
#                                 'RqY': data.RqY.reshape(-1,),
#                                 'RqZ': data.RqZ.reshape(-1,),
#                                 'raw_LaX': data.raw_LaX.reshape(-1,),
#                                 'raw_LaY': data.raw_LaY.reshape(-1,),
#                                 'raw_LaZ': data.raw_LaZ.reshape(-1,),
#                                 'raw_LqX': data.raw_LqX.reshape(-1,),
#                                 'raw_LqY': data.raw_LqY.reshape(-1,),
#                                 'raw_LqZ': data.raw_LqZ.reshape(-1,),
#                                 'raw_HaX': data.raw_HaX.reshape(-1,),
#                                 'raw_HaY': data.raw_HaY.reshape(-1,),
#                                 'raw_HaZ': data.raw_HaZ.reshape(-1,),
#                                 'raw_HqX': data.raw_HqX.reshape(-1,),
#                                 'raw_HqY': data.raw_HqY.reshape(-1,),
#                                 'raw_HqZ': data.raw_HqZ.reshape(-1,),
#                                 'raw_RaX': data.raw_RaX.reshape(-1,),
#                                 'raw_RaY': data.raw_RaY.reshape(-1,),
#                                 'raw_RaZ': data.raw_RaZ.reshape(-1,),
#                                 'raw_RqX': data.raw_RqX.reshape(-1,),
#                                 'raw_RqY': data.raw_RqY.reshape(-1,),
#                                 'raw_RqZ': data.raw_RqZ.reshape(-1,)})
#
#    _logger("data table created")
##%%
##    data_pd = pd.DataFrame(sensor_data)
#    _logger("converted to pandas")
##    del sensor_data
#    try:
#        fileobj = cStringIO.StringIO()
#        _logger("fileobj created")
#        data_pd.to_csv(fileobj, index=False, compression='gzip')
#        _logger(sys.getsizeof(fileobj))
#        del data_pd
#        fileobj.seek(0)
#        s3.Bucket(cont_write).put_object(Key='processed_'+file_name, Body=fileobj)
#        del fileobj
#    except boto3.exceptions as error:
#        if AWS:
#            _logger("Cannot write table to s3", info=False)
#            raise error
#        else:
#            _logger("Cannot write file to s3 writing locally!")
##
##    _write_table_s3(sensor_data, 'processed_'+file_name, s3, cont_write)
#    _logger("Raw data written to s3")
#    data = _subset_data(data, neutral_data)
#    _logger('DONE SUBSETTING DATA FOR ACTIVITY ID = 1!')

    # set observation index
    data.obs_index = np.array(range(len(data.LaX))).reshape(-1, 1) + 1
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
    #_logger(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    del hip_acc, hip_eul
    #_logger(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    _logger('DONE WITH MOVEMENT ATTRIBUTES AND PERFORMANCE VARIABLES!')
#%%
    # MOVEMENT QUALITY FEATURES

    # isolate bf quaternions
    lf_quat = np.hstack([data.LqW, data.LqX, data.LqY, data.LqZ])
    hip_quat = np.hstack([data.HqW, data.HqX, data.HqY, data.HqZ])
    rf_quat = np.hstack([data.RqW, data.RqX, data.RqY, data.RqZ])

    # isolate neutral quaternions
    lf_neutral = neutral_data[:, :4]
    hip_neutral = neutral_data[:, 4:8]
    rf_neutral = neutral_data[:, 8:]
    del neutral_data

    # calculate movement attributes
    data.contra_hip_drop_lf, data.contra_hip_drop_rf, data.ankle_rot_lf,\
        data.ankle_rot_rf, data.foot_position_lf, data.foot_position_rf,\
        = cmed.calculate_rot_CMEs(lf_quat, hip_quat, rf_quat, lf_neutral,
                                      hip_neutral, rf_neutral, data.phase_lf,\
                                      data.phase_rf)
    del lf_quat, hip_quat, rf_quat
    #_logger(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    del lf_neutral, hip_neutral, rf_neutral
    gc.collect()
    #_logger(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    _logger('DONE WITH BALANCE CME!')
#%%
    # IMPACT CME
    # define dictionary for msElapsed

    # landing time attributes
    n_landtime, ltime_index, lf_rf_imp_indicator =\
                            impact.sync_time(data.phase_rf, data.phase_lf,
                                             sampl_freq)

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
    #_logger(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    del n_landtime, ltime_index, lf_rf_imp_indicator
    #_logger(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    _logger('DONE WITH IMPACT CME!')


#%%
    # MECHANICAL STRESS
    # load model
    try:
        ms_obj = s3.Bucket(cont_models).Object('ms_trainmodel.pkl')
        ms_fileobj = ms_obj.get()
        ms_body = ms_fileobj["Body"].read()

        # we're reading the first model on the list, there are multiple
        mstress_fit = pickle.loads(ms_body)
        del ms_body
        del ms_fileobj
        del ms_obj
    except Exception as error:
        if AWS:
            _logger("Cannot load MS model from s3!", info=False)
            raise error
        else:
            try:
                with open('ms_trainmodel.pkl') as model_file:
                    mstress_fit = pickle.load(model_file)
            except:
                raise IOError("MS model file not found in s3/local directory")
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
    gc.collect()
    _logger('DONE WITH RATE OF FORCE ABSORPTION!')
#%%
    # combine into movement data table
    data = _add_ids(data, ids_from_db)
    length = len(data.LaX)
    setattr(data, 'exercise_weight', np.array(['']*length).reshape(-1, 1))
    setattr(data, 'activity_id', np.array(['']*length).reshape(-1, 1))
    data.missing_type_lf = data.missing_type_lf.astype(int)
    data.missing_type_h = data.missing_type_h.astype(int)
    data.missing_type_rf = data.missing_type_rf.astype(int)
    data.epoch_time = data.epoch_time.astype(long)
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
#    N = len(data.LaX)
#    #_logger(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    scoring_data = pd.DataFrame(data={'team_id': data.team_id.reshape(-1, ),
                                      'user_id': data.user_id.reshape(-1, ),
                                      'team_regimen_id': data.team_regimen_id.reshape(-1, ),
                                      'training_session_log_id': data.training_session_log_id.reshape(-1, ),
                                      'session_event_id': data.session_event_id.reshape(-1, ),
                                      'session_type': data.session_type.reshape(-1, ),
                                      'corrupt_type': data.corrupt_type.reshape(-1, ).astype(int)})
    attrib_del = ['team_id', 'user_id', 'team_regimen_id', 'block_id', 'block_event_id', 'training_session_log_id',
                  'session_event_id', 'session_type', 'exercise_id', 'corrupt_type', 'columns', 'corrupt_magn',
                  'corrupt_magn_h', 'corrupt_magn_lf', 'corrupt_magn_rf', 'epoch_time_h', 'epoch_time_lf',
                  'epoch_time_rf', 'missing_data_indicator']
#    #_logger(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    for attrib in attrib_del:
        del data.__dict__[attrib]
    _logger("completed first frame")
    gc.collect()
    for var in COLUMN_SESSION_OUT[7:]:
        frame = pd.DataFrame(data={var: data.__dict__[var].reshape(-1, )}, index=scoring_data.index)
        frames = [scoring_data, frame]
        scoring_data = pd.concat(frames, axis=1)
        del frame, frames, data.__dict__[var]
    del data
    _logger("Table Created")


    # write table to DB
    scoring_data = scoring_data.replace('None', '')

    _multipartupload_movement_data(scoring_data, file_name, s3, cont_write_final, cur, conn)
    conn.close()

    _logger("Data in S3")
#    result = _write_table_db(movement_data, cur, conn)

    _logger('Done with everything!')

    return "success!"

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
def _connect_db_s3():
    """Start a connection to the database and to s3 resource.
    """
    try:
        conn = psycopg2.connect("""dbname='biometrix' user='ubuntu'
        host='ec2-35-162-107-177.us-west-2.compute.amazonaws.com'
        password='d8dad414c2bb4afd06f8e8d4ba832c19d58e123f'""")
        cur = conn.cursor()
        # Connect to AWS s3 container
        s3 = boto3.resource('s3')
    except psycopg2.Error as error:
        logger.warning("Cannot connect to DB")
        raise error
    except boto3.exceptions as error:
        logger.warning("Cannot connect to s3!")
        raise error
    else:
        return conn, cur, s3
#%%
def _read_ids(cur, file_name):
    '''Read relevant ids from database and assign zeros if not found
    Args:
        cur: connection cursor
        file_name: sensor data filename to lookup ids by
    Returns:
        A single list with the following elements in order
        session_event_id: uuid
        training_session_log_id: uuid
        user_id: uuid
        team_regimen_id: uuid
        team_id: uuid
        session_type: integer, should be 1
    '''
    dummy_uuid = '00000000-0000-0000-0000-000000000000'
    try:
        cur.execute(queries.quer_read_ids, (file_name,))
        ids = cur.fetchall()[0]
    except psycopg2.Error as error:
        if AWS:
            logger.warning("Error reading ids!")
            raise error
        else:
            print "Couldn't read ids, assigning dummy"
            session_event_id = dummy_uuid
            training_session_log_id = dummy_uuid
            user_id = dummy_uuid
            team_regimen_id = dummy_uuid
            team_id = dummy_uuid
            session_type = 1
            
    except IndexError:
        if AWS:
            logger.warning("sensor_data_filename not found in DB!")
            raise IndexError
        else:
            print "sensor_data_filename not found in DB! assigning dummy uuid"
            session_event_id = dummy_uuid
            training_session_log_id = dummy_uuid
            user_id = dummy_uuid
            team_regimen_id = dummy_uuid
            team_id = dummy_uuid
            session_type = 1
    else:
        session_event_id = ids[0]
#        if session_event_id is None:
#            session_event_id = dummy_uuid
        training_session_log_id = ids[1]
#        if training_session_log_id is None:
#            training_session_log_id = dummy_uuid
        user_id = ids[2]
#        if user_id is None:
#            user_id = dummy_uuid
        team_regimen_id = ids[3]
#        if team_regimen_id is None:
#            team_regimen_id = dummy_uuid
        team_id = ids[4]
#        if team_id is None:
#            team_id = dummy_uuid
        session_type = ids[5]
        if session_type == 'practice':
            session_type = 1
        elif session_type == 'strength_training':
            session_type = 2
        elif session_type == 'return_to_play':
            session_type = 3
        elif session_type is None:
            session_type = 1

    return (session_event_id, training_session_log_id, user_id, team_regimen_id,
            team_id, session_type)

#%%
def _read_offsets(cur, session_event_id):
    '''Read the offsets for coordinateframe transformation.
    
    If it's in aws lambda, try to find offsets in DB and raise
    appropriate error,
    If it's a local run for testing, look for associated offsets in DB
    first, if not found, check local memory to see if the offset values
    are stored. If both these fail, ValueError is raised.
    '''
    try:
        cur.execute(queries.quer_read_offsets, (session_event_id,))
        offsets_read = cur.fetchall()[0]
    except psycopg2.Error as error:
        
        if AWS:
            logger.warning("Cannot read transform offsets!")
            raise error
        else:
            try:
                # these should be the offsets calculated by separate runs of 
                # calibration script. If not found, load some random values
                offsets_read = (hip_n_transform, hip_bf_transform,
                                lf_n_transform, lf_bf_transform,
                                rf_n_transform, rf_bf_transform)
            except NameError:
                raise ValueError("No associated offset values found in "+
                                 "the database or local memory")           
    except IndexError as error:
        if AWS:
            logger.warning("Transform offsets cannot be found!")
            raise error
        else:
            try:
                # these should be the offsets calculated by separate runs of 
                # calibration script. If not found, load some random values
                offsets_read = (hip_n_transform, hip_bf_transform,
                                lf_n_transform, lf_bf_transform,
                                rf_n_transform, rf_bf_transform)
            except NameError:
                raise ValueError("No associated offset values found in "+
                                 "the database or local memory")
#                offsets_read = dummy_offsets   
    return offsets_read

#%%
def _add_ids(data, ids):
    # retrieve ids
    session_event_id = ids[0]
    training_session_log_id = ids[1]
    user_id = ids[2]
    team_regimen_id = ids[3]
    team_id = ids[4]
    session_type = ids[5]
    # set ID information
#    dummy_uuid = '00000000-0000-0000-0000-000000000000'
    length = len(data.LaX)
    setattr(data, 'team_id', np.array([team_id]*length).reshape(-1, 1))
    setattr(data, 'user_id', np.array([user_id]*length).reshape(-1, 1))
    setattr(data, 'team_regimen_id',
            np.array([team_regimen_id]*length).reshape(-1, 1))
    setattr(data, 'block_id', np.array(['None']*length).reshape(-1, 1))
    setattr(data, 'block_event_id',
            np.array(['None']*length).reshape(-1, 1))
    setattr(data, 'training_session_log_id',
            np.array([training_session_log_id]*length).reshape(-1, 1))
    setattr(data, 'session_event_id',
            np.array([session_event_id]*length).reshape(-1, 1))
    setattr(data, 'session_type',
            np.array([session_type]*length).reshape(-1, 1))
    setattr(data, 'exercise_id', np.array(['None']*length).reshape(-1, 1))
    return data

#%% 
def _add_rawdata(data):
    # Save raw values in different attributes to later populate table
    # left
    setattr(data, 'raw_LaX', data.LaX)
    setattr(data, 'raw_LaY', data.LaY)
    setattr(data, 'raw_LaZ', data.LaZ)
    setattr(data, 'raw_LqX', data.LqX)
    setattr(data, 'raw_LqY', data.LqY)
    setattr(data, 'raw_LqZ', data.LqZ)
    # hip
    setattr(data, 'raw_HaX', data.HaX)
    setattr(data, 'raw_HaY', data.HaY)
    setattr(data, 'raw_HaZ', data.HaZ)
    setattr(data, 'raw_HqX', data.HqX)
    setattr(data, 'raw_HqY', data.HqY)
    setattr(data, 'raw_HqZ', data.HqZ)
    # right
    setattr(data, 'raw_RaX', data.RaX)
    setattr(data, 'raw_RaY', data.RaY)
    setattr(data, 'raw_RaZ', data.RaZ)
    setattr(data, 'raw_RqX', data.RqX)
    setattr(data, 'raw_RqY', data.RqY)
    setattr(data, 'raw_RqZ', data.RqZ)

    return data

#%%
def _real_quaternions(data):
    """Calculate real quaternion from the imaginary quaternions
    
    Args:
        data: either rawframe object or pandas df with quaternions
    """
    # left
    _lq_xyz = np.hstack([data.LqX, data.LqY, data.LqZ])
    _lq_wxyz, corrupt_type_l =\
                    ppp.calc_quaternions(_lq_xyz, data.missing_data_indicator,
                                         data.corrupt_magn)
    #check for type conversion error in left foot quaternion data
    if 2 in corrupt_type_l:
        _logger('Error! Type conversion error: LF quat', info=False)
    setattr(data, 'LqW', _lq_wxyz[:, 0].reshape(-1, 1))
    data.LqX = _lq_wxyz[:, 1].reshape(-1, 1)
    data.LqY = _lq_wxyz[:, 2].reshape(-1, 1)
    data.LqZ = _lq_wxyz[:, 3].reshape(-1, 1)
    # hip
    _hq_xyz = np.hstack([data.HqX, data.HqY, data.HqZ])
    _hq_wxyz, corrupt_type_h =\
                    ppp.calc_quaternions(_hq_xyz, data.missing_data_indicator,
                                         data.corrupt_magn)
    #check for type conversion error in hip quaternion data
    if 2 in corrupt_type_h:
        _logger('Error! Type conversion error: Hip quat', info=False)
    setattr(data, 'HqW', _hq_wxyz[:, 0].reshape(-1, 1))
    data.HqX = _hq_wxyz[:, 1].reshape(-1, 1)
    data.HqY = _hq_wxyz[:, 2].reshape(-1, 1)
    data.HqZ = _hq_wxyz[:, 3].reshape(-1, 1)
    # right
    _rq_xyz = np.hstack([data.RqX, data.RqY, data.RqZ])
    _rq_wxyz, corrupt_type_r =\
                    ppp.calc_quaternions(_rq_xyz,
                                         data.missing_data_indicator,
                                         data.corrupt_magn)
    #check for type conversion error in right foot quaternion data
    if 2 in corrupt_type_r:
        _logger('Error! Type conversion error: RF quat', info=False)
    setattr(data, 'RqW', _rq_wxyz[:, 0].reshape(-1, 1))
    data.RqX = _rq_wxyz[:, 1].reshape(-1, 1)
    data.RqY = _rq_wxyz[:, 2].reshape(-1, 1)
    data.RqZ = _rq_wxyz[:, 3].reshape(-1, 1)
    corrupt_types = np.hstack([corrupt_type_l, corrupt_type_h, corrupt_type_r])
    corrupt_type = np.max(corrupt_types, axis=1)
    setattr(data, 'corrupt_type', corrupt_type.reshape(-1, 1))

    return data    

#%%
def _subset_data(data, neutral_data):
    """SUBSETTING FOR ACTIVITY ID = 1
    """
    # left foot body transformed data
    data.LaX = data.LaX[data.activity_id == 1].reshape(-1, 1)
    data.LaY = data.LaY[data.activity_id == 1].reshape(-1, 1)
    data.LaZ = data.LaZ[data.activity_id == 1].reshape(-1, 1)
    data.LeX = data.LeX[data.activity_id == 1].reshape(-1, 1)
    data.LeY = data.LeY[data.activity_id == 1].reshape(-1, 1)
    data.LeZ = data.LeZ[data.activity_id == 1].reshape(-1, 1)
    data.LqW = data.LqW[data.activity_id == 1].reshape(-1, 1)
    data.LqX = data.LqX[data.activity_id == 1].reshape(-1, 1)
    data.LqY = data.LqY[data.activity_id == 1].reshape(-1, 1)
    data.LqZ = data.LqZ[data.activity_id == 1].reshape(-1, 1)
    # hip body transformed data
    data.HaX = data.HaX[data.activity_id == 1].reshape(-1, 1)
    data.HaY = data.HaY[data.activity_id == 1].reshape(-1, 1)
    data.HaZ = data.HaZ[data.activity_id == 1].reshape(-1, 1)
    data.HeX = data.HeX[data.activity_id == 1].reshape(-1, 1)
    data.HeY = data.HeY[data.activity_id == 1].reshape(-1, 1)
    data.HeZ = data.HeZ[data.activity_id == 1].reshape(-1, 1)
    data.HqW = data.HqW[data.activity_id == 1].reshape(-1, 1)
    data.HqX = data.HqX[data.activity_id == 1].reshape(-1, 1)
    data.HqY = data.HqY[data.activity_id == 1].reshape(-1, 1)
    data.HqZ = data.HqZ[data.activity_id == 1].reshape(-1, 1)
    # right foot body transformed data
    data.RaX = data.RaX[data.activity_id == 1].reshape(-1, 1)
    data.RaY = data.RaY[data.activity_id == 1].reshape(-1, 1)
    data.RaZ = data.RaZ[data.activity_id == 1].reshape(-1, 1)
    data.ReX = data.ReX[data.activity_id == 1].reshape(-1, 1)
    data.ReY = data.ReY[data.activity_id == 1].reshape(-1, 1)
    data.ReZ = data.ReZ[data.activity_id == 1].reshape(-1, 1)
    data.RqW = data.RqW[data.activity_id == 1].reshape(-1, 1)
    data.RqX = data.RqX[data.activity_id == 1].reshape(-1, 1)
    data.RqY = data.RqY[data.activity_id == 1].reshape(-1, 1)
    data.RqZ = data.RqZ[data.activity_id == 1].reshape(-1, 1)

    # phase
    data.phase_lf = data.phase_lf[
        data.activity_id == 1].reshape(-1, 1)
    data.phase_rf = data.phase_rf[
        data.activity_id == 1].reshape(-1, 1)
    data.obs_master_index = data.obs_master_index[
        data.activity_id == 1].reshape(-1, 1)
    data.epoch_time = data.epoch_time[
        data.activity_id == 1].reshape(-1, 1)
    data.ms_elapsed = data.ms_elapsed[
        data.activity_id == 1].reshape(-1, 1)
    data.time_stamp = data.time_stamp[
        data.activity_id == 1].reshape(-1, 1)

    # identifiers
    data.team_id = data.team_id[
        data.activity_id == 1].reshape(-1, 1)
    data.user_id = data.user_id[
        data.activity_id == 1].reshape(-1, 1)
    data.team_regimen_id = data.team_regimen_id[
        data.activity_id == 1].reshape(-1, 1)
    data.block_id = data.block_id[
        data.activity_id == 1].reshape(-1, 1)
    data.block_event_id = data.block_event_id[
        data.activity_id == 1].reshape(-1, 1)
    data.training_session_log_id = data.training_session_log_id[
        data.activity_id == 1].reshape(-1, 1)
    data.session_event_id = data.session_event_id[
        data.activity_id == 1].reshape(-1, 1)
    data.exercise_id = data.exercise_id[
        data.activity_id == 1].reshape(-1, 1)
    data.session_type = data.session_type[
        data.activity_id == 1].reshape(-1, 1)

    # neutral orientations
    neutral_data = neutral_data[(data.activity_id == 1).reshape(-1,)]

    data.activity_id = data.activity_id[data.activity_id == 1]
    
    return data
#%%
def _write_table_s3(data_table, file_name, s3, cont):
    """write final table to s3
    """
    data_pd = pd.DataFrame(data_table)
    del data_table
    try:
        fileobj = cStringIO.StringIO()
        data_pd.to_csv(fileobj, index=False, compression='gzip')
        _logger(sys.getsizeof(fileobj))
        del data_pd
        fileobj.seek(0)
        s3.Bucket(cont).put_object(Key=file_name, Body=fileobj)
    except boto3.exceptions as error:
        if AWS:
            _logger("Cannot write table to s3", info=False)
            raise error
        else:
            print "Cannot write file to s3 writing locally!"
            movement_data_pd.to_csv("scoring_" + file_name, index=False)
            del movement_data_pd
    else:
        del fileobj
#%%
def _write_table_db(movement_data, cur, conn):
    """Update the movement table with all the scores
    Args:
        movement_data: numpy recarray with complete data
        cur: cursor pointing to the current db connection
        conn: db connection
    Returns:
        result: string signifying success
    """
    movement_data_pd = pd.DataFrame(movement_data)
    movement_data_pd = movement_data_pd.replace('None', 'NaN')
    fileobj_db = cStringIO.StringIO()
    try:
        movement_data_pd.to_csv(fileobj_db, index=False, header=False,
                                na_rep='NaN', columns=COLUMN_SESSION_OUT)
        fileobj_db.seek(0)
        cur.copy_from(file=fileobj_db, table='movement', sep=',', null='NaN',
                      columns=COLUMN_SESSION_OUT)
        conn.commit()
        conn.close()
    except Exception as error:
        if AWS:
            logger.warning("Cannot write movement data to DB!")
            raise error
        else:
            print "Cannot write movement data to DB!"
#            raise error
            return "Success!"
    else:
        return "Success!"

def _record_magn(data, file_name, S3):
    import csv
    corrupt_magn = data['corrupt_magn']
    percent_corrupt = np.sum(corrupt_magn)/np.float(len(corrupt_magn))
    minimum_lf = np.min(data['corrupt_magn_lf'])
    maximum_lf = np.max(data['corrupt_magn_lf'])
    minimum_h = np.min(data['corrupt_magn_h'])
    maximum_h = np.max(data['corrupt_magn_h'])
    minimum_rf = np.min(data['corrupt_magn_rf'])
    maximum_rf = np.max(data['corrupt_magn_rf'])
    files_magntest = []
    for obj in S3.Bucket('biometrix-magntest').objects.all():
        files_magntest.append(obj.key)
    file_present = 'magntest_session' in  files_magntest
    if AWS:
        try:
            if file_present:
                obj = S3.Bucket('biometrix-magntest').Object('magntest_session')
                fileobj = obj.get()
                body = fileobj["Body"].read()
                feet = cStringIO.StringIO(body)
#                feet.seek(0)
                feet_data = pd.read_csv(feet)
                new_row = pd.Series([file_name, percent_corrupt, minimum_lf,
                                     maximum_lf, minimum_h, maximum_h,
                                     minimum_rf, maximum_rf], feet_data.columns)
                feet_data = feet_data.append(new_row, ignore_index=True)
                feet = cStringIO.StringIO()
                feet_data.to_csv(feet, index=False)
                feet.seek(0)
            else:
                feet = cStringIO.StringIO()
                feet.seek(0)
                w = csv.writer(feet, delimiter=',',
                               quoting=csv.QUOTE_NONNUMERIC)
                w.writerow(('file_name', 'percent_corrupt', 'min_magn_lf',
                            'max_magn_lf', 'min_magn_h', 'max_magn_h',
                            'min_magn_rf', 'max_magn_rf'))
                w.writerow((file_name, percent_corrupt,
                            minimum_lf, maximum_lf,
                            minimum_h, maximum_h,
                            minimum_rf, maximum_rf))
                feet.seek(0)
            S3.Bucket('biometrix-magntest').put_object(Key='magntest_session',
                                                       Body=feet)
        except:
            _logger("Cannot updage magn logs!")
    else:
        path = '..\\test_session_and_scoring\\magntest_session.csv'
        try:
            with open(path, 'r') as f:
                f.close()
            with open(path, 'ab') as f:
                w = csv.writer(f,delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
                w.writerow((file_name, percent_corrupt, minimum_lf,maximum_lf,
                            minimum_h, maximum_h, minimum_rf, maximum_rf))
        except IOError:
            with open(path, 'ab') as f:
                w = csv.writer(f,delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
                w.writerow(('file_name', 'percent_corrupt', 'min_magn_lf',
                            'max_magn_lf', 'min_magn_h', 'max_magn_h',
                            'min_magn_rf', 'max_magn_rf'))
                w.writerow((file_name, percent_corrupt, minimum_lf, maximum_lf,
                            minimum_h, maximum_h, minimum_rf, maximum_rf))


def _multipartupload_movement_data(movement_data, file_name_s3, s3, cont, cur, conn):

    # Create a multipart upload request
    print 
    s3 = boto3.client('s3')
    mp = s3.create_multipart_upload(Bucket=cont, Key=file_name_s3)
    
    # Use only a set of columns each time to write to fileobj
    rows_set_size = 30000  # number of rows durin each batch upload (change if needed)
    number_of_rows = len(movement_data)
    rows_set_count = int(math.ceil(number_of_rows/float(rows_set_size)))
#    _logger('number of parts to be uploaded' + str(rows_set_count))
    _logger(str(rows_set_count)+ 'number of parts to be uploaded')
    
    # Initialize counter to the count number of parts uploaded in the loop below
    counter = 0
    # Send the file parts, using FileChunkIO to create a file-like object
    for i in islice(count(), 0, number_of_rows,  rows_set_size):
        counter = counter + 1
        movement_data_subset = movement_data.iloc[i:i+rows_set_size]
        print len(movement_data_subset), ': length of subset'
        fileobj = cStringIO.StringIO()
        if counter == 1:
            movement_data_subset.to_csv(fileobj, index=False, header=False,
                                        na_rep='', columns=COLUMN_SESSION_OUT)
        else:
            movement_data_subset.to_csv(fileobj, index=False, header=False,
                                        na_rep='', columns=COLUMN_SESSION_OUT)
        del movement_data_subset
        fileobj.seek(0)
        cur.copy_from(file=fileobj, table='movement', sep=',', null='',
                      columns=COLUMN_SESSION_OUT)
        conn.commit()
        fileobj.seek(0)
        part = s3.upload_part(Bucket=cont, Key=file_name_s3, PartNumber=counter,
                              UploadId=mp['UploadId'], Body=fileobj)
        if counter == 1:
            Parts = [{'PartNumber':counter, 'ETag': part['ETag']}]
        else:
            Parts.append({'PartNumber':counter, 'ETag': part['ETag']})
        del fileobj
        _logger(str(counter)+ ': this is the counter')
    part_info = {'Parts': Parts}
    s3.complete_multipart_upload(Bucket=cont, Key=file_name_s3, UploadId=mp['UploadId'],
                                 MultipartUpload=part_info) 

#%%
if __name__ == "__main__":
    sensor_data = 'C:\\Users\\dipesh\\Desktop\\biometrix\\aws\\bdb02f8d-e51a-4ad5-9f04-8f4a60591bcc.csv'
    file_name = '7803f828-bd32-4e97-860c-34a995f08a9e'
    result = run_session(sensor_data, file_name, aws=False)
