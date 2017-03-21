# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 10:41:36 2016

@author: Gautam

Session execution script. Used by athletes during block processes. Takes raw
session data, processes, and returns analyzed data.

Input data called from 'biometrix-blockcontainer'

Output data collected in BlockEvent Table.
"""

import cStringIO
import logging
import numpy as np
import pandas as pd
import psycopg2
import psycopg2.extras
import boto3

import prePreProcessing as ppp
import dataObject as do
# import phaseDetection as phase
#import IAD
import coordinateFrameTransformation as coord
import checkProcessed as cp
import columnNames as cols


logger = logging.getLogger()
psycopg2.extras.register_uuid()


def run_session(sensor_data, file_name, ids_from_db, offsets_read, 
                start, aws=True):
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
    global COLUMN_SESSION1_OUT
    AWS = aws
    COLUMN_SESSION1_OUT = cols.column_session1_out
    team_id = ids_from_db[4]
    user_id = ids_from_db[2]
    team_regimen_id = ids_from_db[3]
    training_session_log_id = ids_from_db[1]
    session_event_id = ids_from_db[0]
    session_type = ids_from_db[5]
    
    # Record percentage and ranges of magn_values for diagonostic purposes
    try:
        S3 = boto3.resource('s3') 
        _record_magn(sensor_data, file_name, S3)
    except:
        _logger("failed to write magn values to s3!")
        
    columns = sensor_data.columns
    data = do.RawFrame(sensor_data, columns)
    del sensor_data
    data = cp.handle_processed(data)

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
#    sampl_freq = 100
    _logger('DONE WITH PRE-PRE-PROCESSING!')
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
    del _transformed_data

    # add neutral data
    data.LqW_n = neutral_data[:, 0].reshape(-1, 1)
    data.LqX_n = neutral_data[:, 1].reshape(-1, 1)
    data.LqY_n = neutral_data[:, 2].reshape(-1, 1)
    data.LqZ_n = neutral_data[:, 3].reshape(-1, 1)
    # reshape hip body transformed data
    data.HqW_n = neutral_data[:, 4].reshape(-1, 1)
    data.HqX_n = neutral_data[:, 5].reshape(-1, 1)
    data.HqY_n = neutral_data[:, 6].reshape(-1, 1)
    data.HqZ_n = neutral_data[:, 7].reshape(-1, 1)
    # reshape right foot body transformed data
    data.RqW_n = neutral_data[:, 8].reshape(-1, 1)
    data.RqX_n = neutral_data[:, 9].reshape(-1, 1)
    data.RqY_n = neutral_data[:, 10].reshape(-1, 1)
    data.RqZ_n = neutral_data[:, 11].reshape(-1, 1)
    del neutral_data
    _logger('DONE WITH COORDINATE FRAME TRANSFORMATION!')
#%%
    # PHASE DETECTION
#    data.phase_lf, data.phase_rf = phase.combine_phase(data.LaZ, data.RaZ,
#                                                       sampl_freq)
#
#    _logger('DONE WITH PHASE DETECTION!')

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
#%%
#    attrib_del = ['columns', 'corrupt_magn', 'corrupt_magn_h',
#                  'corrupt_magn_lf', 'corrupt_magn_rf', 'epoch_time_h',
#                  'epoch_time_lf', 'epoch_time_rf', 'missing_data_indicator']
##    #_logger(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
#    for attrib in attrib_del:
#        del data.__dict__[attrib]


    # set observation index
    data.obs_index = np.array(range(len(data.LaX))).reshape(-1, 1) + start + 1
    length = len(data.LaX)
#
    setattr(data, 'exercise_weight', np.array(['']*length).reshape(-1, 1))
    # setattr(data, 'activity_id', np.array(['']*length).reshape(-1, 1))
    data.corrupt_type = data.corrupt_type.astype(int)
    data.missing_type_lf = data.missing_type_lf.astype(int)
    data.missing_type_h = data.missing_type_h.astype(int)
    data.missing_type_rf = data.missing_type_rf.astype(int)
    data.epoch_time = data.epoch_time.astype(long)
    data.ms_elapsed = data.ms_elapsed.astype(int)
#    N = len(data.LaX)
    session2_data = pd.DataFrame(data={'team_id': np.array([team_id]*length),
                                      'user_id': np.array([user_id]*length),
                                      'team_regimen_id': np.array([team_regimen_id]*length),
                                      'training_session_log_id': np.array([training_session_log_id]*length),
                                      'session_event_id': np.array([session_event_id]*length),
                                      'session_type': np.array([session_type]*length),
                                      'corrupt_type': data.corrupt_type.reshape(-1,),
                                      'missing_type_lf': data.missing_type_lf.reshape(-1,),
                                      'missing_type_h': data.missing_type_h.reshape(-1,),
                                      'missing_type_rf': data.missing_type_rf.reshape(-1,),
                                      'exercise_weight': data.exercise_weight.reshape(-1,),
                                      'obs_index': data.obs_index.reshape(-1,),
                                      'obs_master_index': data.obs_master_index.reshape(-1,),
                                      'time_stamp': data.time_stamp.reshape(-1,),
                                      'epoch_time': data.epoch_time.reshape(-1,),
                                      'ms_elapsed': data.ms_elapsed.reshape(-1,),
                                      'LaX': data.LaX.reshape(-1,),
                                      'LaY': data.LaY.reshape(-1,),
                                      'LaZ': data.LaZ.reshape(-1,),
                                      'LeX': data.LeX.reshape(-1,),
                                      'LeY': data.LeY.reshape(-1,),
                                      'LeZ': data.LeZ.reshape(-1,),
                                      'LqW': data.LqW.reshape(-1,),
                                      'LqX': data.LqX.reshape(-1,),
                                      'LqY': data.LqY.reshape(-1,),
                                      'LqZ': data.LqZ.reshape(-1,),
                                      'HaX': data.HaX.reshape(-1,),
                                      'HaY': data.HaY.reshape(-1,),
                                      'HaZ': data.HaZ.reshape(-1,),
                                      'HeX': data.HeX.reshape(-1,),
                                      'HeY': data.HeY.reshape(-1,),
                                      'HeZ': data.HeZ.reshape(-1,),
                                      'HqW': data.HqW.reshape(-1,),
                                      'HqX': data.HqX.reshape(-1,),
                                      'HqY': data.HqY.reshape(-1,),
                                      'HqZ': data.HqZ.reshape(-1,),
                                      'RaX': data.RaX.reshape(-1,),
                                      'RaY': data.RaY.reshape(-1,),
                                      'RaZ': data.RaZ.reshape(-1,),
                                      'ReX': data.ReX.reshape(-1,),
                                      'ReY': data.ReY.reshape(-1,),
                                      'ReZ': data.ReZ.reshape(-1,),
                                      'RqW': data.RqW.reshape(-1,),
                                      'RqX': data.RqX.reshape(-1,),
                                      'RqY': data.RqY.reshape(-1,),
                                      'RqZ': data.RqZ.reshape(-1,),
                                      'LqW_n': data.LqW_n.reshape(-1,),
                                      'LqX_n': data.LqX_n.reshape(-1,),
                                      'LqY_n': data.LqY_n.reshape(-1,),
                                      'LqZ_n': data.LqZ_n.reshape(-1,),
                                      'HqW_n': data.HqW_n.reshape(-1,),
                                      'HqX_n': data.HqX_n.reshape(-1,),
                                      'HqY_n': data.HqY_n.reshape(-1,),
                                      'HqZ_n': data.HqZ_n.reshape(-1,),
                                      'RqW_n': data.RqW_n.reshape(-1,),
                                      'RqX_n': data.RqX_n.reshape(-1,),
                                      'RqY_n': data.RqY_n.reshape(-1,),
                                      'RqZ_n': data.RqZ_n.reshape(-1,)})
    del data
    _logger("Table Created")

    return session2_data

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
    del _lq_xyz
    #check for type conversion error in left foot quaternion data
    if 2 in corrupt_type_l:
        _logger('Error! Type conversion error: LF quat', info=False)
    setattr(data, 'LqW', _lq_wxyz[:, 0].reshape(-1, 1))
    data.LqX = _lq_wxyz[:, 1].reshape(-1, 1)
    data.LqY = _lq_wxyz[:, 2].reshape(-1, 1)
    data.LqZ = _lq_wxyz[:, 3].reshape(-1, 1)
    del _lq_wxyz
    # hip
    _hq_xyz = np.hstack([data.HqX, data.HqY, data.HqZ])
    _hq_wxyz, corrupt_type_h =\
                    ppp.calc_quaternions(_hq_xyz, data.missing_data_indicator,
                                         data.corrupt_magn)
    #check for type conversion error in hip quaternion data
    del _hq_xyz
    if 2 in corrupt_type_h:
        _logger('Error! Type conversion error: Hip quat', info=False)
    setattr(data, 'HqW', _hq_wxyz[:, 0].reshape(-1, 1))
    data.HqX = _hq_wxyz[:, 1].reshape(-1, 1)
    data.HqY = _hq_wxyz[:, 2].reshape(-1, 1)
    data.HqZ = _hq_wxyz[:, 3].reshape(-1, 1)
    del _hq_wxyz
    # right
    _rq_xyz = np.hstack([data.RqX, data.RqY, data.RqZ])
    _rq_wxyz, corrupt_type_r =\
                    ppp.calc_quaternions(_rq_xyz,
                                         data.missing_data_indicator,
                                         data.corrupt_magn)
    del _rq_xyz
    #check for type conversion error in right foot quaternion data
    if 2 in corrupt_type_r:
        _logger('Error! Type conversion error: RF quat', info=False)
    setattr(data, 'RqW', _rq_wxyz[:, 0].reshape(-1, 1))
    data.RqX = _rq_wxyz[:, 1].reshape(-1, 1)
    data.RqY = _rq_wxyz[:, 2].reshape(-1, 1)
    data.RqZ = _rq_wxyz[:, 3].reshape(-1, 1)
    del _rq_wxyz
    corrupt_types = np.hstack([corrupt_type_l, corrupt_type_h, corrupt_type_r])
    del corrupt_type_l, corrupt_type_h, corrupt_type_r
    corrupt_type = np.max(corrupt_types, axis=1)
    setattr(data, 'corrupt_type', corrupt_type.reshape(-1, 1))

    return data    

def _record_magn(data, file_name, S3):
    import csv
    import os
    from base64 import b64decode
    KMS = boto3.client('kms')
    cont_magntest = 'biometrix-magntest'
    SUB_FOLDER = os.environ['sub_folder']+'/'
#    cont_magntest = os.environ['cont_magntest']
    magntest_file = os.environ['magntest_file']
#    cont_magntest = KMS.decrypt(CiphertextBlob=b64decode(cont_magntest))['Plaintext']
#    SUB_FOLDER = KMS.decrypt(CiphertextBlob=b64decode(sub_folder))['Plaintext']+'/'
    magntest_file = SUB_FOLDER+KMS.decrypt(CiphertextBlob=b64decode(magntest_file))['Plaintext']

    corrupt_magn = data['corrupt_magn']
    percent_corrupt = np.sum(corrupt_magn)/np.float(len(corrupt_magn))
    minimum_lf = np.min(data['corrupt_magn_lf'])
    maximum_lf = np.max(data['corrupt_magn_lf'])
    minimum_h = np.min(data['corrupt_magn_h'])
    maximum_h = np.max(data['corrupt_magn_h'])
    minimum_rf = np.min(data['corrupt_magn_rf'])
    maximum_rf = np.max(data['corrupt_magn_rf'])
    files_magntest = []
    for obj in S3.Bucket(cont_magntest).objects.filter(Prefix=SUB_FOLDER):
        files_magntest.append(obj.key)
    file_present = magntest_file in  files_magntest
    if AWS:
        try:
            if file_present:
                obj = S3.Bucket(cont_magntest).Object(magntest_file)
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
            S3.Bucket(cont_magntest).put_object(Key=magntest_file, Body=feet)
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




#%%
if __name__ == "__main__":
    sensor_data = 'C:\\Users\\dipesh\\Desktop\\biometrix\\aws\\c4ed8189-6e1d-47c3-9cc5-446329b10796'
    file_name = '7803f828-bd32-4e97-860c-34a995f08a9e'
    result = run_session(sensor_data, file_name, aws=False)
