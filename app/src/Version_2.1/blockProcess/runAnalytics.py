# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 13:45:56 2016

@author: ankur
"""

import numpy as np
import pandas as pd
import pickle
import sys
import psycopg2
import psycopg2.extras
import boto3
import cStringIO
import logging

import prePreProcessing as ppp
import dataObject as do
import phaseDetection as phase
import IAD
import IED
import coordinateFrameTransformation as coord
from mechStressTraining import prepare_data
import movementAttrib as matrib
import balanceCME as cmed
import quatConvs as qc
import impactCME as impact
from controlScore import control_score
from scoring import score
import createTables as ct


logger = logging.getLogger()
psycopg2.extras.register_uuid()


"""
Block execution script. Used by athletes during block processes. Takes raw
block data, processes, and returns analyzed data.

Input data called from 'biometrix-blockcontainer'

Output data collected in BlockEvent Table.

"""

def _dynamic_name(sdata):
    """ Isolates data from input data object.

    """
    _names = sdata.dtype.names[1:]
    _width = len(_names)+1
    data = sdata.view((float, _width))

    return data


class AnalyticsExecution(object):
    """Creates object attributes according to block analysis process.

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

    def __init__(self, sensor_data, file_name):
        quer_read_block_ids = """select id, block_id from block_events
                                 where sensor_data_filename = (%s)"""

        quer_read_ids = """select * from 
                        fn_get_all_ids_from_block_event_id((%s))"""

        quer_read_offsets = """select hip_n_transform, hip_bf_transform,
            lf_n_transform, lf_bf_transform,
            rf_n_transform, lf_bf_transform from
            session_anatomical_calibration_events where
            id = (select session_anatomical_calibration_event_id 
            from block_events where sensor_data_filename = (%s));"""

        quer_read_exercise_ids = """select exercise_id from blocks_exercises
                                    where block_id = (%s)"""

        quer_read_model = """select exercise_id_combinations, model_file,
                        label_encoding_model_file from exercise_training_models
                        where block_id = (%s)"""

        # Define containers to read from and write to
        ied_read = 'biometrix-trainingprocessedcontainer'
        cont_write = 'biometrix-blockprocessedcontainer'

        # Define container that holds models
        cont_models = 'biometrix-globalmodels'

        # Connect to the database
        try:
            conn = psycopg2.connect("""dbname='biometrix' user='ubuntu' 
            host='ec2-35-162-107-177.us-west-2.compute.amazonaws.com' 
            password='d8dad414c2bb4afd06f8e8d4ba832c19d58e123f'""")
            cur = conn.cursor()
            # Connect to AWS s3 container
            s3 = boto3.resource('s3')

            # Read block_event_id and block_id from block_events table
            cur.execute(quer_read_block_ids, (file_name,))
            block_ids = cur.fetchall()[0]
        except psycopg2.Error as error:
            logger.warning("Cannot connect to DB")
            raise error
        except boto3.exceptions as error:
            logger.warning("Cannot connect to s3!")
            raise error
        except IndexError as error:
            logger.warning("sensor_data_filename not found in DB!")
            raise error
        else:
            block_event_id = block_ids[0]
            block_id = block_ids[1]
            if block_id is None:
                logger.warning("No block_id associated with the block_event!")
                self.result = "Fail!"
                sys.exit()

        #Read the required ids given block_event_id
        try:
            cur.execute(quer_read_ids, (block_event_id,))
            ids = cur.fetchall()[0]
        except psycopg2.Error as error:
            logger.warning("Error reading ids!")
            raise error
        except IndexError:
            logger.warning("Ids returned as blank, assigning 0s!")
            team_id = '00000000-0000-0000-0000-000000000000'
            user_id = '00000000-0000-0000-0000-000000000000'
            team_regimen_id = '00000000-0000-0000-0000-000000000000'
            training_session_log_id = '00000000-0000-0000-0000-000000000000'
            session_event_id = '00000000-0000-0000-0000-000000000000'
            session_type = 2

        team_id = ids[0]
        if team_id is None:
            team_id = '00000000-0000-0000-0000-000000000000'
        user_id = ids[1]
        if user_id is None:
            user_id = '00000000-0000-0000-0000-000000000000'
        team_regimen_id = ids[2]
        if team_regimen_id is None:
            team_regimen_id = '00000000-0000-0000-0000-000000000000'
        training_session_log_id = ids[4]
        if training_session_log_id is None:
            training_session_log_id = '00000000-0000-0000-0000-000000000000'
        session_event_id = ids[5]
        if session_event_id is None:
            session_event_id = '00000000-0000-0000-0000-000000000000'
        session_type = ids[6]
        if session_type is None:
            session_type = 2

        # Read exercise_ids associated with the block
        try:
            cur.execute(quer_read_exercise_ids, (block_id,))
            exercise_ids = np.array(cur.fetchall()).reshape(-1,)
        except psycopg2.Error as error:
            logger.warning("Cannot read exercise_ids for the block!")
            self.result = "Fail!"
            sys.exit()
        #Read transformation offset values
        try:
            cur.execute(quer_read_offsets, (file_name,))
            offsets_read = cur.fetchall()[0]
        except psycopg2.Error as error:
            logger.warning("Cannot read transform offsets!")
            raise error
        except IndexError as error:
            logger.warning("Transform offesets cannot be found!")
            raise error

        # read sensor data as ndarray
        try:
            sdata = np.genfromtxt(sensor_data, dtype=float, delimiter=',',
                                  names=True)
        except IndexError as error:
            logger.warning("Sensor data doesn't have column names!")
            self.result = "Fail!"
            sys.exit()
        if len(sdata) == 0:
            logger.warning("Sensor data is empty!")
            self.result = "Fail!"
            sys.exit()

        columns = sdata.dtype.names
        data = _dynamic_name(sdata)
        self.data = do.RawFrame(data, columns)

        # set ID information (dummy vars for now)
        self.data.team_id = np.array([team_id]*len(sdata)).reshape(-1,1)
        self.data.user_id = np.array([user_id]*len(sdata)).reshape(-1,1)
        self.data.team_regimen_id = np.array([team_regimen_id]*len(sdata))\
                                    .reshape(-1,1)
        self.data.block_id = np.array([block_id]*len(sdata)).reshape(-1,1)
        self.data.block_event_id = np.array([block_event_id]*len(sdata))\
                                    .reshape(-1,1)
        self.data.training_session_log_id = np.array([training_session_log_id]\
                                                    *len(sdata)).reshape(-1,1)
        self.data.session_event_id = np.array([session_event_id]\
                                               *len(sdata)).reshape(-1,1)
        self.data.session_type = np.array([session_type]*len(sdata)).reshape(-1,1)
        self.data.exercise_id = np.array(['']*len(sdata)).reshape(-1,1)

        # Save raw values in different attributes to later populate table
        # left
        self.data.raw_LaX = self.data.LaX
        self.data.raw_LaY = self.data.LaY
        self.data.raw_LaZ = self.data.LaZ
        self.data.raw_LqX = self.data.LqX
        self.data.raw_LqY = self.data.LqY
        self.data.raw_LqZ = self.data.LqZ
        # hip
        self.data.raw_HaX = self.data.HaX
        self.data.raw_HaY = self.data.HaY
        self.data.raw_HaZ = self.data.HaZ
        self.data.raw_HqX = self.data.HqX
        self.data.raw_HqY = self.data.HqY
        self.data.raw_HqZ = self.data.HqZ
        # right
        self.data.raw_RaX = self.data.RaX
        self.data.raw_RaY = self.data.RaY
        self.data.raw_RaZ = self.data.RaZ
        self.data.raw_RqX = self.data.RqX
        self.data.raw_RqY = self.data.RqY
        self.data.raw_RqZ = self.data.RqZ
        self.data.obs_master_index = (np.array(range(len(self.data.raw_LaX)))\
                                        +1).reshape(-1, 1)

        # PRE-PRE-PROCESSING

        # Check for duplicate epoch time
        duplicate_epoch_time = ppp.check_duplicate_epochtime(
        self.data.epoch_time)
        if duplicate_epoch_time:
            logger.warning('Duplicate epoch time.')

        # check for missing values
        self.data = ppp.handling_missing_data(self.data)
        
        # determine the real quartenion
        # left
        _lq_xyz = np.hstack([self.data.LqX, self.data.LqY, self.data.LqZ])
        _lq_wxyz, self.data.corrupt_type = ppp.calc_quaternions(_lq_xyz,
                                        self.data.missing_data_indicator,
                                        self.data.corrupt_magn)
        #check for type conversion error in left foot quaternion data
        if 2 in self.data.corrupt_type:
            logger.warning('Error! Type conversion error: LF quat')
        self.data.LqW = _lq_wxyz[:, 0].reshape(-1, 1)
        self.data.LqX = _lq_wxyz[:, 1].reshape(-1, 1)
        self.data.LqY = _lq_wxyz[:, 2].reshape(-1, 1)
        self.data.LqZ = _lq_wxyz[:, 3].reshape(-1, 1)
        # hip
        _hq_xyz = np.hstack([self.data.HqX, self.data.HqY, self.data.HqZ])
        _hq_wxyz, self.data.corrupt_type = ppp.calc_quaternions(_hq_xyz, 
                                        self.data.missing_data_indicator,
                                        self.data.corrupt_magn)
        #check for type conversion error in hip quaternion data
        if 2 in self.data.corrupt_type:
            logger.warning('Error! Type conversion error: Hip quat')
        self.data.HqW = _hq_wxyz[:, 0].reshape(-1, 1)
        self.data.HqX = _hq_wxyz[:, 1].reshape(-1, 1)
        self.data.HqY = _hq_wxyz[:, 2].reshape(-1, 1)
        self.data.HqZ = _hq_wxyz[:, 3].reshape(-1, 1)
        # right
        _rq_xyz = np.hstack([self.data.RqX, self.data.RqY, self.data.RqZ])
        _rq_wxyz, self.data.corrupt_type = ppp.calc_quaternions(_rq_xyz,
                                        self.data.missing_data_indicator,
                                        self.data.corrupt_magn)
        #check for type conversion error in right foot quaternion data
        if 2 in self.data.corrupt_type:
            logger.warning('Error! Type conversion error: RF quat')
        self.data.RqW = _rq_wxyz[:, 0].reshape(-1, 1)
        self.data.RqX = _rq_wxyz[:, 1].reshape(-1, 1)
        self.data.RqY = _rq_wxyz[:, 2].reshape(-1, 1)
        self.data.RqZ = _rq_wxyz[:, 3].reshape(-1, 1)

        # convert epoch time to date time and determine milliseconds elapsed
        self.data.time_stamp, self.data.ms_elapsed = \
            ppp.convert_epochtime_datetime_mselapsed(self.data.epoch_time)

        logger.info('DONE WITH PRE-PRE-PROCESSING!')  

        # COORDINATE FRAME TRANSFORMATION

        # pull relevant transform offset values from SessionCalibrationEvent
        hip_n_transform = np.array(offsets_read[0]).reshape(-1, 1)
        if len(hip_n_transform) == 0:
            logger.warning("Calibration offset value missing")
            raise ValueError("Missing Offsets")
        hip_bf_transform = np.array(offsets_read[1]).reshape(-1, 1)
        if len(hip_bf_transform) == 0:
            logger.warning("Calibration offset value missing")
            raise ValueError("Missing Offsets")
        lf_n_transform = np.array(offsets_read[2]).reshape(-1, 1)
        if len(lf_n_transform) == 0:
            logger.warning("Calibration offset value missing")
            raise ValueError("Missing Offsets")
        lf_bf_transform = np.array(offsets_read[3]).reshape(-1, 1)
        if len(lf_bf_transform) == 0:
            logger.warning("Calibration offset value missing")
            raise ValueError("Missing Offsets")
        rf_n_transform = np.array(offsets_read[4]).reshape(-1, 1)
        if len(rf_n_transform) == 0:
            logger.warning("Calibration offset value missing")
            raise ValueError("Missing Offsets")
        rf_bf_transform = np.array(offsets_read[5]).reshape(-1, 1)
        if len(rf_bf_transform) == 0:
            logger.warning("Calibration offset value missing")
            raise ValueError("Missing Offsets")

        # use transform values to adjust coordinate frame of all block data
        _transformed_data, neutral_data= coord.transform_data(self.data, 
            hip_bf_transform,lf_bf_transform,rf_bf_transform,lf_n_transform,
            rf_n_transform, hip_n_transform)

        # transform neutral orientations for each point in time to ndarray
        neutral_data = np.array(neutral_data)

        # reshape left foot body transformed data
        self.data.LaX = _transformed_data[:, 1].reshape(-1, 1)
        self.data.LaY = _transformed_data[:, 2].reshape(-1, 1)
        self.data.LaZ = _transformed_data[:, 3].reshape(-1, 1)
        self.data.LeX = _transformed_data[:, 4].reshape(-1, 1)
        self.data.LeY = _transformed_data[:, 5].reshape(-1, 1)
        self.data.LeZ = _transformed_data[:, 6].reshape(-1, 1)
        self.data.LqW = _transformed_data[:, 7].reshape(-1, 1)
        self.data.LqX = _transformed_data[:, 8].reshape(-1, 1)
        self.data.LqY = _transformed_data[:, 9].reshape(-1, 1)
        self.data.LqZ = _transformed_data[:, 10].reshape(-1, 1)
        # reshape hip body transformed data
        self.data.HaX = _transformed_data[:, 11].reshape(-1, 1)
        self.data.HaY = _transformed_data[:, 12].reshape(-1, 1)
        self.data.HaZ = _transformed_data[:, 13].reshape(-1, 1)
        self.data.HeX = _transformed_data[:, 14].reshape(-1, 1)
        self.data.HeY = _transformed_data[:, 15].reshape(-1, 1)
        self.data.HeZ = _transformed_data[:, 16].reshape(-1, 1)
        self.data.HqW = _transformed_data[:, 17].reshape(-1, 1)
        self.data.HqX = _transformed_data[:, 18].reshape(-1, 1)
        self.data.HqY = _transformed_data[:, 19].reshape(-1, 1)
        self.data.HqZ = _transformed_data[:, 20].reshape(-1, 1)
        # reshape right foot body transformed data
        self.data.RaX = _transformed_data[:, 21].reshape(-1, 1)
        self.data.RaY = _transformed_data[:, 22].reshape(-1, 1)
        self.data.RaZ = _transformed_data[:, 23].reshape(-1, 1)
        self.data.ReX = _transformed_data[:, 24].reshape(-1, 1)
        self.data.ReY = _transformed_data[:, 25].reshape(-1, 1)
        self.data.ReZ = _transformed_data[:, 26].reshape(-1, 1)
        self.data.RqW = _transformed_data[:, 27].reshape(-1, 1)
        self.data.RqX = _transformed_data[:, 28].reshape(-1, 1)
        self.data.RqY = _transformed_data[:, 29].reshape(-1, 1)
        self.data.RqZ = _transformed_data[:, 30].reshape(-1, 1)

        logger.info('DONE WITH COORDINATE FRAME TRANSFORMATION!')

        # PHASE DETECTION
        self.data.phase_lf, self.data.phase_rf = phase.combine_phase(
                                            self.data.LaZ, self.data.RaZ, 
                                            self.data.epoch_time)

#        self.data.phase_lf = np.array([0]*len(self.data.LaX))[:,np.newaxis]
#        self.data.phase_rf = np.array([0]*len(self.data.LaX))[:,np.newaxis]
        logger.info('DONE WITH PHASE DETECTION!')

        # CONTROL SCORE
        self.data.control, self.data.hip_control, self.data.ankle_control, \
            self.data.control_lf, self.data.control_rf = control_score(
            self.data.LeX, self.data.ReX, self.data.HeX, self.data.ms_elapsed)

        logger.info('DONE WITH CONTROL SCORES!')  

        # INTELLIGENT ACTIVITY DETECTION (IAD)
        # load model
        try:
            iad_obj = s3.Bucket(cont_models).Object('iad_finalized_model.sav')
            iad_fileobj = iad_obj.get()
            iad_body = iad_fileobj["Body"].read()

            # we're reading the first model on the list, there are multiple
            loaded_iad_model = pickle.loads(iad_body)
        except Exception as error:
            logger.warning("Cannot load iad_model from s3")
            raise error

        # predict activity state
        iad_features = IAD.preprocess_iad(self.data, training = False)
        iad_labels = loaded_iad_model.predict(iad_features)
        iad_predicted_labels = IAD.label_aggregation(iad_labels)
        self.data.activity_id = IAD.mapping_labels_on_data(
                                            iad_predicted_labels, 
                                            len(self.data.LaX)).reshape(-1,1)

        logger.info('DONE WITH IAD!')

        # save sensor data before subsetting
        sensor_data = ct.create_sensor_data(len(self.data.LaX), self.data)
        sensor_data_pd = pd.DataFrame(sensor_data)
        fileobj = cStringIO.StringIO()
        sensor_data_pd.to_csv(fileobj,index = False)
        fileobj.seek(0)
        try:
            s3.Bucket(cont_write).put_object(Key="processed_"
                                            +file_name, Body=fileobj)
        except boto3.exceptions as error:
            logger.warning("Cannot write processed file to s3!")
            raise error


#        # SUBSETTING FOR ACTIVITY ID = 1
#        # left foot body transformed data        
#        self.data.LaX = self.data.LaX[self.data.activity_id == 1].reshape(-1,1)
#        self.data.LaY = self.data.LaY[self.data.activity_id == 1].reshape(-1,1)
#        self.data.LaZ = self.data.LaZ[self.data.activity_id == 1].reshape(-1,1)
#        self.data.LeX = self.data.LeX[self.data.activity_id == 1].reshape(-1,1)
#        self.data.LeY = self.data.LeY[self.data.activity_id == 1].reshape(-1,1)
#        self.data.LeZ = self.data.LeZ[self.data.activity_id == 1].reshape(-1,1)
#        self.data.LqW = self.data.LqW[self.data.activity_id == 1].reshape(-1,1)
#        self.data.LqX = self.data.LqX[self.data.activity_id == 1].reshape(-1,1)
#        self.data.LqY = self.data.LqY[self.data.activity_id == 1].reshape(-1,1)
#        self.data.LqZ = self.data.LqZ[self.data.activity_id == 1].reshape(-1,1)
#        # hip body transformed data
#        self.data.HaX = self.data.HaX[self.data.activity_id == 1].reshape(-1,1)
#        self.data.HaY = self.data.HaY[self.data.activity_id == 1].reshape(-1,1)
#        self.data.HaZ = self.data.HaZ[self.data.activity_id == 1].reshape(-1,1)
#        self.data.HeX = self.data.HeX[self.data.activity_id == 1].reshape(-1,1)
#        self.data.HeY = self.data.HeY[self.data.activity_id == 1].reshape(-1,1)
#        self.data.HeZ = self.data.HeZ[self.data.activity_id == 1].reshape(-1,1)
#        self.data.HqW = self.data.HqW[self.data.activity_id == 1].reshape(-1,1)
#        self.data.HqX = self.data.HqX[self.data.activity_id == 1].reshape(-1,1)
#        self.data.HqY = self.data.HqY[self.data.activity_id == 1].reshape(-1,1)
#        self.data.HqZ = self.data.HqZ[self.data.activity_id == 1].reshape(-1,1)
#        # right foot body transformed data
#        self.data.RaX = self.data.RaX[self.data.activity_id == 1].reshape(-1,1)
#        self.data.RaY = self.data.RaY[self.data.activity_id == 1].reshape(-1,1)
#        self.data.RaZ = self.data.RaZ[self.data.activity_id == 1].reshape(-1,1)
#        self.data.ReX = self.data.ReX[self.data.activity_id == 1].reshape(-1,1)
#        self.data.ReY = self.data.ReY[self.data.activity_id == 1].reshape(-1,1)
#        self.data.ReZ = self.data.ReZ[self.data.activity_id == 1].reshape(-1,1)
#        self.data.RqW = self.data.RqW[self.data.activity_id == 1].reshape(-1,1)
#        self.data.RqX = self.data.RqX[self.data.activity_id == 1].reshape(-1,1)
#        self.data.RqY = self.data.RqY[self.data.activity_id == 1].reshape(-1,1)
#        self.data.RqZ = self.data.RqZ[self.data.activity_id == 1].reshape(-1,1)
# 
#        # phase
#        self.data.phase_lf = self.data.phase_lf[
#            self.data.activity_id == 1].reshape(-1,1)
#        self.data.phase_rf = self.data.phase_rf[
#            self.data.activity_id == 1].reshape(-1,1)
#        self.data.obs_master_index = self.data.obs_master_index[
#            self.data.activity_id == 1].reshape(-1,1)
#        self.data.control = self.data.control[
#            self.data.activity_id==1].reshape(-1,1)
#        self.data.hip_control = self.data.hip_control[
#            self.data.activity_id==1].reshape(-1,1)
#        self.data.ankle_control = self.data.ankle_control[
#            self.data.activity_id==1].reshape(-1,1)
#        self.data.control_lf = self.data.control_lf[
#            self.data.activity_id==1].reshape(-1,1)
#        self.data.control_rf = self.data.control_rf[
#            self.data.activity_id==1].reshape(-1,1)
#        self.data.epoch_time = self.data.epoch_time[
#            self.data.activity_id==1].reshape(-1,1)
#        self.data.ms_elapsed = self.data.ms_elapsed[
#            self.data.activity_id==1].reshape(-1,1)
#        self.data.time_stamp = self.data.time_stamp[
#            self.data.activity_id==1].reshape(-1,1)
#
#        # identifiers
#        self.data.team_id = self.data.team_id[
#            self.data.activity_id==1].reshape(-1,1)
#        self.data.user_id = self.data.user_id[
#            self.data.activity_id==1].reshape(-1,1)
#        self.data.team_regimen_id = self.data.team_regimen_id[
#            self.data.activity_id==1].reshape(-1,1)
#        self.data.block_id = self.data.block_id[
#            self.data.activity_id==1].reshape(-1,1)
#        self.data.block_event_id = self.data.block_event_id[
#            self.data.activity_id==1].reshape(-1,1)
#        self.data.training_session_log_id = self.data.training_session_log_id[
#            self.data.activity_id==1].reshape(-1,1)
#        self.data.session_event_id = self.data.session_event_id[
#            self.data.activity_id==1].reshape(-1,1)
#        self.data.exercise_id = self.data.exercise_id[
#            self.data.activity_id==1].reshape(-1,1)
#        self.data.session_type = self.data.session_type[
#            self.data.activity_id==1].reshape(-1,1)       
#
#        # neutral orientations
#        neutral_data = neutral_data[(self.data.activity_id==1).reshape(-1,)]
#
#        self.data.activity_id = self.data.activity_id[self.data.activity_id==1]

#        logger.info('DONE SUBSETTING DATA FOR ACTIVITY ID = 1!')

        # set observation index
        self.data.obs_index = (np.array(range(len(self.data.LaX)))\
                                +1).reshape(-1,1)

        # MOVEMENT ATTRIBUTES AND PERFORMANCE VARIABLES
        # isolate hip acceleration and euler angle data
        hip_acc = np.hstack([self.data.HaX, self.data.HaY, self.data.HaZ])
        hip_eul = np.hstack([self.data.HeX, self.data.HeY, self.data.HeZ])

        # analyze planes of movement
        self.data.lat,self.data.vert,self.data.horz,self.data.rot,\
            self.data.lat_binary,self.data.vert_binary,self.data.horz_binary,\
            self.data.rot_binary,self.data.stationary_binary,\
            self.data.total_accel = matrib.plane_analysis(hip_acc,hip_eul,
                                                          self.data.ms_elapsed)

        # analyze stance
        self.data.standing,self.data.not_standing \
            = matrib.standing_or_not(hip_eul,self.data.epoch_time)
        self.data.double_leg,self.data.single_leg,self.data.feet_eliminated \
            = matrib.double_or_single_leg(self.data.phase_lf,self.data.phase_rf,
                                          self.data.standing,
                                          self.data.epoch_time)
        self.data.single_leg_stationary,self.data.single_leg_dynamic \
            = matrib.stationary_or_dynamic(self.data.phase_lf,\
                                    self.data.phase_rf,self.data.single_leg,
                                    self.data.epoch_time)

        logger.info('DONE WITH MOVEMENT ATTRIBUTES AND PERFORMANCE VARIABLES!')

        # INTELLIGENT EXERCISE DETECTION (IED)
        #Read IED models from database
        try:
            cur.execute(quer_read_model, (block_id,))
            model_result = cur.fetchall()
        except psycopg2.Error as error:
            logger.warning("cannot read IED model from DB!")
            raise error
        # If it returns blank, the block hasn't been trained, train and add
        if len(model_result) == 0:
            train = True
            insert = True
            exercise_id_combinations = ['a']
        else:
            exercise_id_combinations = np.array(model_result[0][0]).reshape(-1,)
            ied_model = pickle.loads(model_result[0][1][:])
            ied_label_model = pickle.loads(model_result[0][2][:])
            insert = False
            # Check if the block has changed
            if set(exercise_id_combinations) == set(exercise_ids):
               train = False
            else:
               train = True

        if train:
            quer_get_filenames = """select exercise_id, sensor_data_filename 
                                from training_events where exercise_id in %s"""
            exercises = tuple(exercise_ids.reshape(-1,).tolist())
            try:
                cur.execute(quer_get_filenames, (exercises,))
                out = cur.fetchall()
                sensor_files  = np.array(out)[:,1]
                exercises = np.array(out)[:,0]
            except Exception as error:
                logger.warning("Cannot read training file names for exercises!")
                raise error
            #Check if all the exercises in the block have been trained
            if set(exercises) != set(exercise_ids):
                logger.info("coach needs to train system")
                self.result = "Fail!"
                sys.exit()
            else:
                i=0
                for files in sensor_files:
                    try:
                        obj = s3.Bucket(ied_read).Object('processed_'+files)
                        fileobj = obj.get()
                        body = fileobj["Body"].read()
                    except boto3.exceptions as error:
                        logger.info("Cannot read training data for exercise!")
                        raise error
                    else:
                        exercise_data = cStringIO.StringIO(body)
                        if i == 0:
                            block_data = pd.read_csv(exercise_data)
                            block_data.exercise_id = exercises[i]
                            i += 1
                        else:
                            b_data = pd.read_csv(exercise_data)
                            b_data.exercise_id = exercises[i]
                            block_data = block_data.append(b_data)
                            i += 1

                ied_model, ied_label_model = IED.train_ied(block_data)
                ied_features = IED.preprocess_ied(self.data)
                ied_labels = ied_model.predict(ied_features)
                ied_exercise_id = IED.mapping_labels_on_data(ied_labels,
                                                             len(self.data.LaX))\
                                                             .astype(int)
                self.data.exercise_id = ied_label_model.inverse_transform(
                                                         ied_exercise_id)

                quer_update = """update exercise_training_models set 
                            exercise_id_combinations = %s,
                            model_file = (%s),
                            label_encoding_model_file = (%s),
                            updated_at = now()
                            where block_id = (%s)
                        """
                quer_insert = """insert into exercise_training_models
                                (exercise_id_combinations, model_file,
                                label_encoding_model_file, block_id, 
                                created_at, updated_at) values
                                (%s,%s,%s,%s,now(), now())
                                """
                exercise_ids = exercise_ids.reshape(-1,).tolist()
                ser_ied_model = pickle.dumps(ied_model, 2)
                ser_label_model = pickle.dumps(ied_label_model, 2)
                if insert:
                    try:
                        cur.execute(quer_insert, (exercise_ids,
                                        psycopg2.Binary(ser_ied_model),
                                        psycopg2.Binary(ser_label_model),
                                        block_id))
                        conn.commit()
                    except psycopg2.Error as error:
                        logger.info("Cannot write IED model to DB!")
                else:
                    try:
                        cur.execute(quer_update, (exercise_ids,
                                       psycopg2.Binary(ser_ied_model),
                                        psycopg2.Binary(ser_label_model),
                                        block_id))
                        conn.commit()
                    except psycopg2.Error as error:
                        logger.info("Cannot write IED model to DB!")
                logger.info("Trained and predicted IED")

        else:        
            # predict exercise ID
            ied_features = IED.preprocess_ied(self.data, training = False)
            ied_labels = ied_model.predict(ied_features)
            ied_exercise_id = IED.mapping_labels_on_data(ied_labels, 
                                                         len(self.data.LaX
                                                         )).astype(int)
            self.data.exercise_id = ied_label_model.inverse_transform(
                                                     ied_exercise_id)
            logger.info("Predicted IED with stored model")
        logger.info('DONE WITH IED!')

        # MOVEMENT QUALITY FEATURES

        # isolate neutral quaternions
        lf_neutral = neutral_data[:, :4]
        hip_neutral = neutral_data[:, 4:8]
        rf_neutral = neutral_data[:, 8:]

        # isolate actual euler angles                
        hip_euler = np.empty((len(self.data.LaX), 3))
        lf_euler = np.empty((len(self.data.LaX), 3))
        rf_euler = np.empty((len(self.data.LaX), 3))

        for i in range(len(hip_neutral)):
            hip_euler[i] = qc.quat_to_euler(hip_neutral[i])
            lf_euler[i] = qc.quat_to_euler(lf_neutral[i])
            rf_euler[i] = qc.quat_to_euler(rf_neutral[i])

        # define balance CME dictionary
        cme_dict = {'prosupl':[-4, -7, 4, 15], 'hiprotl':[-4, -7, 4, 15],
                    'hipdropl':[-4, -7, 4, 15],'prosupr':[-4, -15, 4, 7],
                    'hiprotr':[-4, -15, 4, 7], 'hipdropr':[-4, -15, 4, 7],
                    'hiprotd':[-4, -7, 4, 7]}  

        # contralateral hip drop attributes
        self.nl_contra = cmed.cont_rot_CME(self.data.HeX, self.data.phase_lf,
                                           [1], hip_euler[:, 0],
                                           cme_dict['hipdropl'])
        self.nr_contra = cmed.cont_rot_CME(self.data.HeX, self.data.phase_rf,
                                           [2], hip_euler[:, 0],
                                           cme_dict['hipdropr'])
        self.data.contra_hip_drop_lf = self.nl_contra[:,1].reshape(-1, 1)
        self.data.contra_hip_drop_lf = self.data.contra_hip_drop_lf*-1 # fix so superior > 0
        self.data.contra_hip_drop_rf = self.nr_contra[:, 1].reshape(-1, 1)

        # pronation/supination attributes
        self.nl_prosup = cmed.cont_rot_CME(self.data.LeX, self.data.phase_lf,
                                           [0,1], lf_euler[:,0],
                                           cme_dict['prosupl'])
        self.nr_prosup = cmed.cont_rot_CME(self.data.ReX, self.data.phase_rf,
                                           [0,2], rf_euler[:,0],
                                           cme_dict['prosupr'])
        self.data.ankle_rot_lf = self.nl_prosup[:,1].reshape(-1,1)
        self.data.ankle_rot_lf = self.data.ankle_rot_lf*-1 # fix so superior > 0
        self.data.ankle_rot_rf = self.nr_prosup[:,1].reshape(-1,1)

        # lateral hip rotation attributes
        self.cont_hiprot = cmed.cont_rot_CME(self.data.HeZ, self.data.phase_lf,
                                             [0,1,2,3,4,5], hip_euler[:,2],
                                             cme_dict['hiprotd'])
        self.data.hip_rot = self.cont_hiprot[:,1].reshape(-1,1)
        self.data.hip_rot = self.data.hip_rot*-1 # fix so clockwise > 0

        logger.info('DONE WITH BALANCE CME!')

        # IMPACT CME
        # define dictionary for msElapsed

        # landing time attributes
        self.n_landtime, self.ltime_index = impact.sync_time(self.data.phase_rf,
                                           self.data.phase_lf, 
                                           self.data.epoch_time,
                                           len(self.data.LaX))
        # landing pattern attributes
        if len(self.n_landtime) != 0:
            self.n_landpattern = impact.landing_pattern(
                                 self.data.ReY,
                                 self.data.LeY, self.n_landtime) 
            self.land_time, self.land_pattern = impact.continuous_values(
                                 self.n_landpattern, self.n_landtime,
                                 len(self.data.LaX), self.ltime_index)
            self.data.land_time = self.land_time[:,0].reshape(-1, 1)
            self.data.land_pattern_rf = self.land_pattern[:, 0].reshape(-1, 1)
            self.data.land_pattern_lf = self.land_pattern[:, 1].reshape(-1, 1)
        else:
            self.data.land_time = np.zeros((len(self.data.LaX),1))*np.nan
            self.data.land_pattern_lf = np.zeros((len(self.data.LaX), 1))*np.nan
            self.data.land_pattern_rf = np.zeros((len(self.data.LaX), 1))*np.nan

        logger.info('DONE WITH IMPACT CME!')

        # MECHANICAL STRESS
        # load model
        try:
            ms_obj = s3.Bucket(cont_models).Object('ms_trainmodel.pkl')
            ms_fileobj = ms_obj.get()
            ms_body = ms_fileobj["Body"].read()

            # we're reading the first model on the list, there are multiple
            mstress_fit = pickle.loads(ms_body)
        except Exception as error:
            logger.info("Cannot load Mechanical stress model from s3!")
            raise error
        ms_data = prepare_data(self.data, False)
        
        # calculate mechanical stress
        self.data.mech_stress = mstress_fit.predict(ms_data).reshape(-1, 1)

        logger.info('DONE WITH MECH STRESS!')

        # SCORING
        # Symmetry, Consistency, Destructive/Constructive Multiplier and
            # Block Duration
            # At this point we need to load the historical data for the subject

        try:
            obj = s3.Bucket(cont_write).Object('subject3_DblSquat_hist.csv')
            fileobj = obj.get()
            body = fileobj["Body"].read()
            hist_data = cStringIO.StringIO(body)
        except Exception as error:
            logger.info("Cannot read historical user data from s3!")
            raise error

        userDB = pd.read_csv(hist_data)
        logger.info("user history captured")
        self.data.consistency, self.data.hip_consistency, \
            self.data.ankle_consistency, self.data.consistency_lf, \
            self.data.consistency_rf, self.data.symmetry, \
            self.data.hip_symmetry, self.data.ankle_symmetry, \
            self.data.destr_multiplier, self.data.dest_mech_stress, \
            self.data.const_mech_stress, self.data.block_duration, \
            self.data.session_duration, self.data.block_mech_stress_elapsed, \
            self.data.session_mech_stress_elapsed = score(self.data,userDB)

        logger.info('DONE WITH EVERYTHING!')

        self.result = "Success!"

        # combine into movement data table
        movement_data = ct.create_movement_data(len(self.data.LaX), self.data)
        movement_data_pd = pd.DataFrame(movement_data)

        fileobj = cStringIO.StringIO()
        movement_data_pd.to_csv(fileobj, index=False)
        fileobj.seek(0)
        try:
            s3.Bucket(cont_write).put_object(Key="movement_"
                                            +file_name, Body=fileobj)
        except:
            logger.warning("Cannot write movement talbe to s3")

        fileobj_db = cStringIO.StringIO()
        try:
            movement_data_pd.to_csv(fileobj_db, index=False, header=False,
                                    na_rep = 'NaN')
            fileobj_db.seek(0)
            cur.copy_from(file=fileobj_db, table='movement',sep=',',
                          columns=movement_data.dtype.names)
            conn.commit()
            conn.close()
        except Exception as error:
            logger.info("Cannot write movement data to DB!")
            raise error
            

if __name__ == "__main__":

    import time
    import pandas as pd
    import os
    mov_data = AnalyticsExecution('team1_session1_Subj1_block2.csv', 
                                  '53a803ac-514d-43c9-950c-a7cacdd1a057')
#    import re
#    import sys
#    f = "data\\team1_Subj3_practice.csv"
#    movement_var = analytics_execution(f)
#    file_paths = os.listdir("data")
##    print file_paths
#    for f in file_paths:
#        start_time = time.time()
#        f = "data\\"+f
##        print f
#        movement_var = analytics_execution(f)
#        print "My program took", time.time() - start_time, "to run"
    
#    print calibration_files
#    sys.path.append('..\\anatomical execution\\lambda1')
#    import runSpecialFeet as rs
    
#    rs.record_spec_feet("..\\data\\strength_training\\calibration\\"+calibration_files[0])
#    data_path = 'team1_Subj1_returnToPlay__block2.csv'
#    data = pd.read_csv(data_path)
#    start_time = time.time()
##    movement_variables = analytics_execution(data_path)
#    print "My program took", time.time() - start_time, "to run" 

    
    