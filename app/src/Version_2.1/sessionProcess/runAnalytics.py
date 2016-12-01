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


import prePreProcessing as ppp
import dataObject as do
import phaseDetection as phase
import IAD
import coordinateFrameTransformation as coord
from mechStressTraining import prepare_data
import movementAttrib as matrib
import balanceCME as cmed
import quatConvs as qc
import impactCME as impact
import createTables as ct
import sessionProcessQueries as queries


logger = logging.getLogger()
psycopg2.extras.register_uuid()


def run_session(sensor_data, file_name, aws=True):
    """Creates object attributes according to session analysis process.

    Args:
        raw data object with attributes of:
            epoch_time, corrupt_magn, missing_type, LaX, LaY, LaZ, LqX, LqY,
            LqZ, HaX, HaY, HaZ, HqX, HqY, HqZ, RaX, RaY, RaZ, RqX, RqY, RqZ
    
    Returns:
        processed data object with attributes of:
            team_id, user_id, team_regimen_id, block_id, block_event_id,
            training_session_log_id, session_event_id, session_type,
            exercise_id, obs_index, obs_master_index, time_stamp, epoch_time,
            ms_elapsed, phase_lf, phase_rf, activity_id, mech_stress,
            const_mech_stress, dest_mech_stress, total_accel, block_duration,
            session_duration, block_mech_stress_elapsed,
            session_mech_stress_elapsed, destr_multiplier, symmetry,
            hip_symmetry, ankle_symmetry, consistency, hip_consistency,
            ankle_consistency, consistency_lf, consistency_rf, control,
            hip_control, ankle_control, control_lf, control_rf,
            perc_mech_stress_l, contra_hip_drop_lf, contra_hip_drop_rf, hip_rot,
            ankle_rot_lf,ankle_rot_rf, land_pattern_lf, land_pattern_rf,
            land_time, single_leg_stationary, single_leg_dynamic, double_leg,
            feet_eliminated, rot, lat, vert, horz, rot_binary, lat_binary,
            vert_binary, horz_binary, stationary_binary, LaX, LaY, LaZ, LeX,
            LeY, LeZ, LqW, LqX, LqY, LqZ, HaX, HaY, HaZ, HeX, HeY, HeZ, HqW,
            HqX, HqY, HqZ, RaX, RaY, RaZ, ReX, ReY, ReZ, RqW, RqX, RqY, RqZ
    """

    # Define containers to read from and write to
    cont_write = 'biometrix-sessionprocessedcontainer'
    cont_write_final = 'biometrix-scoringcontainer'

    # Define container that holds models
    cont_models = 'biometrix-globalmodels'
    
    # establish connection to both database and s3 resource
    conn, cur, s3 = _connect_db_s3()
    
    # read session_event_id and other relevant ids
    try:
        ids_from_db = _read_ids(cur, aws, file_name)
    except IndexError:
        return "Fail!"
    session_event_id = ids_from_db[0]

    # read transformation offset values from DB/local Memory
    offsets_read = _read_offsets(cur, session_event_id, aws)

    # read sensor data as ndarray
    try:
        sdata = np.genfromtxt(sensor_data, dtype=float, delimiter=',',
                              names=True)
    except IndexError as error:
        _logger("Sensor data doesn't have column names!", aws, info=False)
        return "Fail!"
    if len(sdata) == 0:
        _logger("Sensor data is empty!", aws, info=False)
        return "Fail!"

    columns = sdata.dtype.names
    data = do.RawFrame(sdata, columns)
    data = _add_ids_rawdata(data, ids_from_db)

    # PRE-PRE-PROCESSING
    # Check for duplicate epoch time
    duplicate_epoch_time = ppp.check_duplicate_epochtime(data.epoch_time)
    if duplicate_epoch_time:
        _logger('Duplicate epoch time.', aws, info=False)

    # check for missing values
    data = ppp.handling_missing_data(data)

    # determine the real quartenion
    data = _real_quaternions(data, aws)

    # convert epoch time to date time and determine milliseconds elapsed
    data.time_stamp, data.ms_elapsed = \
        ppp.convert_epochtime_datetime_mselapsed(data.epoch_time)
    sampl_freq = int(1000./data.ms_elapsed[1])
    _logger('DONE WITH PRE-PRE-PROCESSING!', aws)

    # COORDINATE FRAME TRANSFORMATION

    # pull relevant transform offset values from SessionCalibrationEvent
    hip_n_transform = np.array(offsets_read[0]).reshape(-1, 1)
    if len(hip_n_transform) == 0:
        _logger("Calibration offset value missing", aws, info=False)
        raise ValueError("Missing Offsets")
    hip_bf_transform = np.array(offsets_read[1]).reshape(-1, 1)
    if len(hip_bf_transform) == 0:
        _logger("Calibration offset value missing", aws, info=False)
        raise ValueError("Missing Offsets")
    lf_n_transform = np.array(offsets_read[2]).reshape(-1, 1)
    if len(lf_n_transform) == 0:
        _logger("Calibration offset value missing", aws, info=False)
        raise ValueError("Missing Offsets")
    lf_bf_transform = np.array(offsets_read[3]).reshape(-1, 1)
    if len(lf_bf_transform) == 0:
        _logger("Calibration offset value missing", aws, info=False)
        raise ValueError("Missing Offsets")
    rf_n_transform = np.array(offsets_read[4]).reshape(-1, 1)
    if len(rf_n_transform) == 0:
        _logger("Calibration offset value missing", aws, info=False)
        raise ValueError("Missing Offsets")
    rf_bf_transform = np.array(offsets_read[5]).reshape(-1, 1)
    if len(rf_bf_transform) == 0:
        _logger("Calibration offset value missing", aws, info=False)
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

    _logger('DONE WITH COORDINATE FRAME TRANSFORMATION!', aws)

    # PHASE DETECTION
    data.phase_lf, data.phase_rf = phase.combine_phase(data.LaZ, data.RaZ,
                                                       sampl_freq)

    _logger('DONE WITH PHASE DETECTION!', aws)


    # INTELLIGENT ACTIVITY DETECTION (IAD)
    # load model
    try:
        iad_obj = s3.Bucket(cont_models).Object('iad_finalized_model.sav')
        iad_fileobj = iad_obj.get()
        iad_body = iad_fileobj["Body"].read()

        # we're reading the first model on the list, there are multiple
        loaded_iad_model = pickle.loads(iad_body)
    except Exception as error:
        if aws:
            _logger("Cannot load iad_model from s3", aws, info=False)
            raise error
        else:
            try:
                with open('iad_finalized_model.sav') as model_file:
                    loaded_iad_model = pickle.load(model_file)
            except:
                raise IOError("Model file not found in S3 or local directory")

    # predict activity state
    iad_features = IAD.preprocess_iad(data, training=False)
    iad_labels = loaded_iad_model.predict(iad_features)
    iad_predicted_labels = IAD.label_aggregation(iad_labels)
    data.activity_id =\
            IAD.mapping_labels_on_data(iad_predicted_labels,
                                       len(data.LaX)).reshape(-1, 1)

    _logger('DONE WITH IAD!', aws)

    # save sensor data before subsetting
    sensor_data = ct.create_sensor_data(len(data.LaX), data)
    sensor_data_pd = pd.DataFrame(sensor_data)
    if aws:
        fileobj = cStringIO.StringIO()
        sensor_data_pd.to_csv(fileobj, index=False)
        fileobj.seek(0)
        try:
            s3.Bucket(cont_write).put_object(Key="processed_"+file_name,
                                             Body=fileobj)
        except boto3.exceptions as error:
            _logger("Cannot write processed file to s3!", aws, info=False)
            raise error
    else:
        sensor_data_pd.to_csv("processed_"+file_name, index=False)

#    data = _subset_data(data, neutral_data)
#    _logger('DONE SUBSETTING DATA FOR ACTIVITY ID = 1!', aws)

    # set observation index
    data.obs_index = np.array(range(len(data.LaX))).reshape(-1, 1) + 1

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

    _logger('DONE WITH MOVEMENT ATTRIBUTES AND PERFORMANCE VARIABLES!', aws)

    # MOVEMENT QUALITY FEATURES

    # isolate neutral quaternions
    lf_neutral = neutral_data[:, :4]
    hip_neutral = neutral_data[:, 4:8]
    rf_neutral = neutral_data[:, 8:]

    # isolate actual euler angles
    hip_euler = qc.quat_to_euler(hip_neutral)
    lf_euler = qc.quat_to_euler(lf_neutral)
    rf_euler = qc.quat_to_euler(rf_neutral)

    # define balance CME dictionary

    # contralateral hip drop attributes
    nl_contra = cmed.cont_rot_CME(data.HeX, data.phase_lf, [1], hip_euler[:, 0])
    nr_contra = cmed.cont_rot_CME(data.HeX, data.phase_rf, [2], hip_euler[:, 0])
    data.contra_hip_drop_lf = nl_contra[:, 1].reshape(-1, 1)
    # fix so superior > 0
    data.contra_hip_drop_lf = data.contra_hip_drop_lf* - 1
    data.contra_hip_drop_rf = nr_contra[:, 1].reshape(-1, 1)

    # pronation/supination attributes
    nl_prosup = cmed.cont_rot_CME(data.LeX, data.phase_lf, [0, 1],
                                  lf_euler[:, 0])
    nr_prosup = cmed.cont_rot_CME(data.ReX, data.phase_rf, [0, 2],
                                  rf_euler[:, 0])
    data.ankle_rot_lf = nl_prosup[:, 1].reshape(-1, 1)
    data.ankle_rot_lf = data.ankle_rot_lf*-1 # fix so superior > 0
    data.ankle_rot_rf = nr_prosup[:, 1].reshape(-1, 1)

    # lateral hip rotation attributes
    cont_hiprot = cmed.cont_rot_CME(data.HeZ, data.phase_lf, [0, 1, 2, 3, 4, 5],
                                    hip_euler[:, 2])
    data.hip_rot = cont_hiprot[:, 1].reshape(-1, 1)
    data.hip_rot = data.hip_rot*-1 # fix so clockwise > 0

    _logger('DONE WITH BALANCE CME!', aws)

    # IMPACT CME
    # define dictionary for msElapsed

    # landing time attributes
    n_landtime, ltime_index = impact.sync_time(data.phase_rf, data.phase_lf,
                                               data.epoch_time)
    # landing pattern attributes
    if len(n_landtime) != 0:
        n_landpattern = impact.landing_pattern(data.ReY, data.LeY, n_landtime)
        land_time, land_pattern =\
            impact.continuous_values(n_landpattern, n_landtime,
                                     len(data.LaX), ltime_index)
        data.land_time = land_time[:, 0].reshape(-1, 1)
        data.land_pattern_rf = land_pattern[:, 0].reshape(-1, 1)
        data.land_pattern_lf = land_pattern[:, 1].reshape(-1, 1)
    else:
        data.land_time = np.zeros((len(data.LaX), 1))*np.nan
        data.land_pattern_lf = np.zeros((len(data.LaX), 1))*np.nan
        data.land_pattern_rf = np.zeros((len(data.LaX), 1))*np.nan

    _logger('DONE WITH IMPACT CME!', aws)

    # MECHANICAL STRESS
    # load model
    try:
        ms_obj = s3.Bucket(cont_models).Object('ms_trainmodel.pkl')
        ms_fileobj = ms_obj.get()
        ms_body = ms_fileobj["Body"].read()

        # we're reading the first model on the list, there are multiple
        mstress_fit = pickle.loads(ms_body)
    except Exception as error:
        if aws:
            _logger("Cannot load MS model from s3!", aws, info=False)
            raise error
        else:
            try:
                with open('ms_trainmodel.pkl') as model_file:
                    mstress_fit = pickle.load(model_file)
            except:
                raise IOError("MS model file not found in s3/local directory")
    ms_data = prepare_data(data, False)
    
    # calculate mechanical stress
    data.mech_stress = mstress_fit.predict(ms_data).reshape(-1, 1)

    _logger('DONE WITH MECH STRESS!', aws)


    # combine into movement data table
    movement_data = ct.create_movement_data(len(data.LaX), data)
    movement_data_pd = pd.DataFrame(movement_data)
    
    if aws:
        fileobj = cStringIO.StringIO()
        movement_data_pd.to_csv(fileobj, index=False)
        fileobj.seek(0)
        try:
            s3.Bucket(cont_write_final).put_object(Key="movement_"
                                                   +file_name, Body=fileobj)
        except:
            _logger("Cannot write movement talbe to s3", aws)

        fileobj_db = cStringIO.StringIO()
        try:
            movement_data_pd.to_csv(fileobj_db, index=False, header=False,
                                    na_rep='NaN')
            fileobj_db.seek(0)
            cur.copy_from(file=fileobj_db, table='movement', sep=',',
                          columns=movement_data.dtype.names)
            conn.commit()
            conn.close()
        except Exception as error:
            _logger("Cannot write movement data to DB!", aws, info=False)
            raise error
    else:
        movement_data_pd.to_csv("movement_"+file_name, index=False)

    _logger('Done with everything!', aws)

    return "Success!"


def _logger(message, aws, info=True):
    if aws:
        if info:
            logger.info(message)
        else:
            logger.warning(message)
    else:
        print message


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

def _read_ids(cur, aws, file_name):
    '''Read relevant ids from database and assign zeros if not found
    Args:
        cur: connection cursor
        aws: Boolean to identify if we're running on aws
        filen_name: sensor data filename to lookup ids by
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
        if aws:
            logger.warning("Error reading ids!")
            raise error
        else:
            session_event_id = dummy_uuid
            training_session_log_id = dummy_uuid
            user_id = dummy_uuid
            team_regimen_id = dummy_uuid
            team_id = dummy_uuid
            session_type = 1
            
    except IndexError:
        if aws:
            logger.warning("sensor_data_filename not found in DB!")
            raise IndexError
        else:
            session_event_id = dummy_uuid
            training_session_log_id = dummy_uuid
            user_id = dummy_uuid
            team_regimen_id = dummy_uuid
            team_id = dummy_uuid
            session_type = 1
    else:
        session_event_id = ids[0]
        if session_event_id is None:
            session_event_id = dummy_uuid
        training_session_log_id = ids[1]
        if training_session_log_id is None:
            training_session_log_id = dummy_uuid
        user_id = ids[2]
        if user_id is None:
            user_id = dummy_uuid
        team_regimen_id = ids[3]
        if team_regimen_id is None:
            team_regimen_id = dummy_uuid
        team_id = ids[4]
        if team_id is None:
            team_id = dummy_uuid
        session_type = ids[5]
        if session_type is None:
            session_type = 1

    return (session_event_id, training_session_log_id, user_id, team_regimen_id,
            team_id, session_type)


def _read_offsets(cur, session_event_id, aws):
    '''Read the offsets for coordinateframe transformation.
    
    If it's in aws lambda, it'll try to find offsets in DB and raise
    appropriate error,
    If it's a local run for testing, it'll look for associated offsets in DB
    first, if not found, it'll check local memory to see if the offset values
    are stored. If both these fail, ValueError is raised.
    '''
    try:
        cur.execute(queries.quer_read_offsets, (session_event_id,))
        offsets_read = cur.fetchall()[0]
    except psycopg2.Error as error:
        
        if aws:
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
        if aws:
            logger.warning("Transform offesets cannot be found!")
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


def _add_ids_rawdata(data, ids):
    # retrieve ids
    session_event_id = ids[0]
    training_session_log_id = ids[1]
    user_id = ids[2]
    team_regimen_id = ids[3]
    team_id = ids[4]
    session_type = ids[5]
    # set ID information
    length = len(data.LaX)
    setattr(data, 'team_id', np.array([team_id]*length).reshape(-1, 1))
    setattr(data, 'user_id', np.array([user_id]*length).reshape(-1, 1))
    setattr(data, 'team_regimen_id',
            np.array([team_regimen_id]*length).reshape(-1, 1))
    setattr(data, 'block_id', np.array([None]*length).reshape(-1, 1))
    setattr(data, 'block_event_id',
            np.array([None]*length).reshape(-1, 1))
    setattr(data, 'training_session_log_id',
            np.array([training_session_log_id]*length).reshape(-1, 1))
    setattr(data, 'session_event_id',
            np.array([session_event_id]*length).reshape(-1, 1))
    setattr(data, 'session_type',
            np.array([session_type]*length).reshape(-1, 1))
    setattr(data, 'exercise_id', np.array([None]*length).reshape(-1, 1))

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
    setattr(data, 'obs_master_index',
            np.array(range(len(data.raw_LaX))).reshape(-1, 1) + 1)

    return data


def _real_quaternions(data, aws):
    """Calculate real quaternion from the imaginary quaternions
    
    Args:
        data: either rawframe object or pandas df with quaternions
        aws: indicator for running on aws or locally
    """
    # left
    _lq_xyz = np.hstack([data.LqX, data.LqY, data.LqZ])
    _lq_wxyz, corrupt_type =\
                    ppp.calc_quaternions(_lq_xyz, data.missing_data_indicator,
                                         data.corrupt_magn)
    #check for type conversion error in left foot quaternion data
    if 2 in corrupt_type:
        _logger('Error! Type conversion error: LF quat', aws, info=False)
    setattr(data, 'LqW', _lq_wxyz[:, 0].reshape(-1, 1))
    data.LqX = _lq_wxyz[:, 1].reshape(-1, 1)
    data.LqY = _lq_wxyz[:, 2].reshape(-1, 1)
    data.LqZ = _lq_wxyz[:, 3].reshape(-1, 1)
    # hip
    _hq_xyz = np.hstack([data.HqX, data.HqY, data.HqZ])
    _hq_wxyz, corrupt_type =\
                    ppp.calc_quaternions(_hq_xyz, data.missing_data_indicator,
                                         data.corrupt_magn)
    #check for type conversion error in hip quaternion data
    if 2 in corrupt_type:
        _logger('Error! Type conversion error: Hip quat', aws, info=False)
    setattr(data, 'HqW', _hq_wxyz[:, 0].reshape(-1, 1))
    data.HqX = _hq_wxyz[:, 1].reshape(-1, 1)
    data.HqY = _hq_wxyz[:, 2].reshape(-1, 1)
    data.HqZ = _hq_wxyz[:, 3].reshape(-1, 1)
    # right
    _rq_xyz = np.hstack([data.RqX, data.RqY, data.RqZ])
    _rq_wxyz, corrupt_type =\
                    ppp.calc_quaternions(_rq_xyz,
                                         data.missing_data_indicator,
                                         data.corrupt_magn)
    #check for type conversion error in right foot quaternion data
    if 2 in corrupt_type:
        _logger('Error! Type conversion error: RF quat', aws, info=False)
    setattr(data, 'RqW', _rq_wxyz[:, 0].reshape(-1, 1))
    data.RqX = _rq_wxyz[:, 1].reshape(-1, 1)
    data.RqY = _rq_wxyz[:, 2].reshape(-1, 1)
    data.RqZ = _rq_wxyz[:, 3].reshape(-1, 1)

    return data    


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


if __name__ == "__main__":
    sensor_data = 'trainingset_explosiveJump.csv'
    file_name = 'fakefilename'
    result = run_session(sensor_data, file_name, aws=False)
