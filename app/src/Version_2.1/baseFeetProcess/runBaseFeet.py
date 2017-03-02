# -*- coding: utf-8 -*-
"""
Created on Tue Oct 18 15:18:54 2016

@author: court
"""
import cStringIO
#import sys
import logging
import os

import boto3
import numpy as np
import pandas as pd
import psycopg2
import requests
from base64 import b64decode

import prePreProcessing as ppp
from errors import ErrorMessageBase, RPushDataBase
from placementCheck import placement_check
import checkProcessed as cp
from columnNames import columns_calib

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def record_base_feet(sensor_data, file_name, aws=True):
    """Checks the validity of base calibration step and writes transformed
    base feet calibration data to the database.

    Args:
        sensor_data: sensor data fro base feet calibration in csv format
        file_name: filename for the sensor_data file

    Returns:
        status: Success/Failure
        Pushes notification to user for failure/success of base feet
        calibration step.
        Save transformed data to database with indicator of success/failure
    """
    global AWS
    global KMS
    global SUB_FOLDER
    AWS = aws
    # Read the encrypted environment variables
    db_name = os.environ['db_name']
    db_host = os.environ['db_host']
    db_username = os.environ['db_username']
    db_password = os.environ['db_password']
    sub_folder = os.environ['cont_write']

    #Decrypt the environment variables
    KMS = boto3.client('kms')
    db_name = KMS.decrypt(CiphertextBlob=b64decode(db_name))['Plaintext']
    db_host = KMS.decrypt(CiphertextBlob=b64decode(db_host))['Plaintext']
    db_username = KMS.decrypt(CiphertextBlob=b64decode(db_username))['Plaintext']
    db_password = KMS.decrypt(CiphertextBlob=b64decode(db_password))['Plaintext']
    SUB_FOLDER = KMS.decrypt(CiphertextBlob=b64decode(sub_folder))['Plaintext']+'/'

    cont_write = 'biometrix-baseanatomicalcalibrationprocessedcontainer'
    # Query to read user_id linked to the given data_filename
    quer_read = """select user_id from base_anatomical_calibration_events
                   where feet_sensor_data_filename = (%s);"""

    # Two update queries for when the tests pass/fail
    quer_fail = """update base_anatomical_calibration_events set
                   failure_type = (%s),
                   feet_processed_sensor_data_filename = (%s),
                   user_success = (%s),
                   updated_at = now()
                   where feet_sensor_data_filename=(%s);"""

    quer_success = """update base_anatomical_calibration_events set
                      feet_processed_sensor_data_filename = (%s),
                      user_success = (%s),
                      updated_at = now(),
                      processed_at = now(),
                      failure_type = 0
                      where feet_sensor_data_filename=(%s);"""

#    quer_rpush = "select fn_send_push_notification(%s, %s, %s)"
    quer_check_status = """select * 
                from fn_get_processing_status_from_ba_event_filename((%s))"""
    ###Connect to the database
    try:
        conn = psycopg2.connect(dbname=db_name, user=db_username, host=db_host,
                                password=db_password)
        cur = conn.cursor()

        # connect to S3 bucket for uploading file
        S3 = boto3.resource('s3')

        # Read the user_id to be used for push notification
        cur.execute(quer_read, (file_name,))
        data_read = cur.fetchall()[0]
        user_id = data_read[0]
        if user_id is None:
            user_id = '00000000-0000-0000-0000-000000000000'
            _logger("user_id associated with file not found", False)
#            logger.warning("user_id associated with file not found")

    except psycopg2.Error as error:
        _logger("Cannot connect to DB", False)
        raise error
    except boto3.exceptions as error:
        _logger("Cannot connect to s3", False)
        raise error
    except IndexError as error:
        _logger("feet_sensor_data_filename not found in table", False)
        raise error
    #define container to write processed file to
#    cont_write = 'biometrix-baseanatomicalcalibrationprocessedcontainer'

    #Read data into structured numpy array
    try:
        data = np.genfromtxt(sensor_data, dtype=float, delimiter=',',
                             names=True)
    except IndexError:
        _logger("Sensor data doesn't have column names!", False)
        return "Fail!"
    if len(data) == 0:
        _logger("Sensor data is empty!", False)
        return "Fail!"
    data.dtype.names = columns_calib
    # check if the raw quaternions have been converted already
    data = cp.handle_processed(data)
    # subset for done (done=2)
    subset_data = ppp.subset_data(old_data=data, subset_value=2)

    # Record percentage and ranges of magn_values for diagonostic purposes
    _record_magn(subset_data, file_name, S3)

    if len(subset_data) == 0:
        _logger("No overlapping samples after time sync", info=False)
        return "Fail!"

    # cut out first of recording where quats are settling
    subset_data_temp = _select_recording(subset_data)
    
    # minimum amount of data required for baseFeet calibration
    min_data_thresh = 0.6*len(subset_data_temp)
    
    # subset for corrupt magnetometer (corrupt_magn=1)
    subset_data = ppp.subset_data(old_data=subset_data_temp, subset_value=1,
                                  missing_or_corrupt='corrupt')
    # check if length of subset data is >= required amount (1.5 sec)
    if len(subset_data) < min_data_thresh:
        #update special_anatomical_calibration_events
        try:
            cur.execute(quer_fail, (1, "", False, file_name))
            conn.commit()
        except psycopg2.Error as error:
            _logger("Cannot write to DB after failure!", False)
        finally:
            _logger("Not enough data after subsetting for bad magn!",
                    info=False)
            _logger("User is: "+ user_id)
            return "Fail!"


    out_file = "processed_" + file_name
    index = subset_data['index']
    corrupt_magn = subset_data['corrupt_magn']
    missing_type = subset_data['missing_type']


    identifiers = np.array([index, corrupt_magn, missing_type]).transpose()

    # Create indicator values
    failure_type = np.array([-999]*len(subset_data))
    indicators = np.array([failure_type]).transpose()

    # Check for duplicate epoch time
    duplicate_index = ppp.check_duplicate_index(index)
    if duplicate_index:
        _logger('Duplicate index.'. False)
    
    # PRE-PRE-PROCESSING
    columns = ['LaX', 'LaY', 'LaZ', 'LqX', 'LqY', 'LqZ', 'HaX',
               'HaY', 'HaZ', 'HqX', 'HqY', 'HqZ', 'RaX', 'RaY', 'RaZ',
               'RqX', 'RqY', 'RqZ']

    # check for missing values for each of acceleration and quaternion values
    for var in columns:
        out, ind = ppp.handling_missing_data(index,
                                             subset_data[var].reshape(-1, 1),
                                             corrupt_magn.reshape(-1, 1),
                                             missing_type.reshape(-1, 1))
        subset_data[var] = out.reshape(-1, )
        if ind in [1, 10]:
            break
        
#        # check if nan's exist even after imputing
#        if np.any(np.isnan(out[missing_type != 1])):  # subsetting for when
#        # a missing value is an intentional blank
#            _logger('Bad data! NaNs exist even after imputing. \
#            Column: ' + var, False)
#            return "Fail!"
        
    # subset for missing type = 3
    subset_data = ppp.subset_data(old_data=subset_data, subset_value=3)
    # check if length of subset data is >= required amount (1.5 sec)
    if len(subset_data) < min_data_thresh:
        return "Fail!"

    if ind != 0:
        # rpush
        msg = ErrorMessageBase(ind).error_message
#        r_push_data = RPushDataBase(ind).value
        #update special_anatomical_calibration_events
        try:
            cur.execute(quer_fail, (ind, out_file, False, file_name))
            conn.commit()
            conn.close()
        except psycopg2.Error as error:
            _logger("Cannot write to DB after failure!", False)
            raise error

        ### Write to S3
        data_feet = pd.DataFrame(subset_data)
        data_feet['failure_type'] = ind
        f = cStringIO.StringIO()
        data_feet.to_csv(f, index=False)
        f.seek(0)
        try:
            S3.Bucket(cont_write).put_object(Key=SUB_FOLDER+out_file, Body=f)
#            cur.execute(quer_rpush, (user_id, msg, r_push_data))
#            conn.commit()
#            conn.close()
        except boto3.exceptions as error:
            _logger("Can't write to s3 after failure!", False)
            raise error
#        except psycopg2.Error as error:
#            _logger("Cannot write to rpush after failure!", False)
#            raise error
        else:
            _logger("Failure Message: " + msg, False)
            _logger("User is: "+ user_id)
            return "Fail!"

    else:
        # determine the real quartenion
        # Left foot
        left_q_xyz = np.array([subset_data['LqX'], subset_data['LqY'],
                               subset_data['LqZ']]).transpose()
        left_q_wxyz, conv_error = ppp.calc_quaternions(left_q_xyz,
                                                       missing_type)
        len_nan_real_quat = len(np.where(np.isnan(left_q_wxyz[:, 0]))[0])
        _logger('Bad data! Percentage of NaNs in LqW: ' +
        str(len_nan_real_quat), False)
        
        #check for type conversion error in left foot quaternion data
        if conv_error:
            _logger('Error! Type conversion error: LF quat', False)
            return "Fail!"

        # Hip
        hip_q_xyz = np.array([subset_data['HqX'], subset_data['HqY'],
                              subset_data['HqZ']]).transpose()
        hip_q_wxyz, conv_error = ppp.calc_quaternions(hip_q_xyz,
                                                      missing_type)
        len_nan_real_quat = len(np.where(np.isnan(hip_q_wxyz[:, 0]))[0])
        _logger('Bad data! Percentage of NaNs in HqW: ' +
        str(len_nan_real_quat), False)

        #check for type conversion error in hip quaternion data
        if conv_error:
            _logger('Error! Type conversion error: Hip quat', False)
            return "Fail!"

        # Right foot
        right_q_xyz = np.array([subset_data['RqX'], subset_data['RqY'],
                                subset_data['RqZ']]).transpose()
        right_q_wxyz, conv_error = ppp.calc_quaternions(right_q_xyz,
                                                        missing_type)
        len_nan_real_quat = len(np.where(np.isnan(right_q_wxyz[:, 0]))[0])
        _logger('Bad data! Percentage of NaNs in RqW: ' +
        str(len_nan_real_quat), False)
        
        #check for type conversion error in right foot quaternion data
        if conv_error:
            _logger('Error! Type conversion error: RF quat', False)
            return "Fail!"
            
        #Acceleration
        left_acc = np.array([subset_data['LaX'], subset_data['LaY'],
                             subset_data['LaZ']]).transpose()
        hip_acc = np.array([subset_data['HaX'], subset_data['HaY'],
                            subset_data['HaZ']]).transpose()
        right_acc = np.array([subset_data['RaX'], subset_data['RaY'],
                              subset_data['RaZ']]).transpose()
                              
        #create output table as a structured numpy array
        data_o = np.hstack((identifiers, indicators))
        data_o = np.hstack([data_o, subset_data['epoch_time_lf'].reshape(-1, 1)])
        data_o = np.hstack([data_o, subset_data['corrupt_magn_lf'].reshape(-1, 1)])
        data_o = np.hstack((data_o, left_acc))
        data_o = np.hstack((data_o, left_q_wxyz))
        data_o = np.hstack([data_o, subset_data['epoch_time_h'].reshape(-1, 1)])
        data_o = np.hstack([data_o, subset_data['corrupt_magn_h'].reshape(-1, 1)])
        data_o = np.hstack((data_o, hip_acc))
        data_o = np.hstack((data_o, hip_q_wxyz))
        data_o = np.hstack([data_o, subset_data['epoch_time_rf'].reshape(-1, 1)])
        data_o = np.hstack([data_o, subset_data['corrupt_magn_rf'].reshape(-1, 1)])
        data_o = np.hstack((data_o, right_acc))
        data_o = np.hstack((data_o, right_q_wxyz))

        #Columns of the output table
        columns = ['index', 'corrupt_magn', 'missing_type', 'failure_type',
                   'epoch_time_lf', 'corrupt_magn_lf', 'LaX', 'LaY', 'LaZ',
                   'LqW', 'LqX', 'LqY', 'LqZ', 'epoch_time_h', 'corrupt_magn_h',
                   'HaX', 'HaY', 'HaZ', 'HqW', 'HqX', 'HqY', 'HqZ',
                   'epoch_time_rf', 'corrupt_magn_rf', 'RaX', 'RaY',
                   'RaZ', 'RqW', 'RqX', 'RqY', 'RqZ']

        data_o_pd = pd.DataFrame(data_o)
        data_o_pd.columns = columns

        types = [(columns[i].encode(), data_o_pd[k].dtype.type) for\
                    (i, k) in enumerate(columns)]
        dtype = np.dtype(types)
        data_feet = np.zeros(data_o.shape[0], dtype)
        for (i, k) in enumerate(data_feet.dtype.names):
            data_feet[k] = data_o[:, i]
        #Check if the sensors are placed correctly and if the subject is moving
        #around and push respective success/failure message to the user
        ind = placement_check(left_acc, hip_acc, right_acc)
#        ind = 0
#        left_ind = hip_ind = right_ind = mov_ind =False
        if ind != 0:
            # rpush
            msg = ErrorMessageBase(ind).error_message
#            r_push_data = RPushDataBase(ind).value
            #update special_anatomical_calibration_events
            try:
                cur.execute(quer_fail, (ind, out_file, False, file_name))
                conn.commit()
                conn.close()
            except psycopg2.Error as error:
                _logger("Cannot write to DB after failure!", False)
                raise error

            data_feet['failure_type'] = ind
            ### Write to S3
            data_pd = pd.DataFrame(data_feet)
            f = cStringIO.StringIO()
            data_pd.to_csv(f, index=False)
            f.seek(0)
            try:
                S3.Bucket(cont_write).put_object(Key=SUB_FOLDER+out_file, Body=f)
#                cur.execute(quer_rpush, (user_id, msg, r_push_data))
#                conn.commit()
#                conn.close()
            except boto3.exceptions as error:
                _logger("Cannot write to s3 container after failure!", AWS,
                        False)
                raise error
#            except psycopg2.Error as error:
#                _logger("Cannot write to rpush after failure!", False)
#                raise error
            else:
                _logger("Failure Message: " + msg, False)
                _logger("User is: "+ user_id)
                return "Fail!"

        else:
            # rpush
            msg = ErrorMessageBase(ind).error_message
#            r_push_data = RPushDataBase(ind).value
            #update special_anatomical_calibration_events
            try:
                cur.execute(quer_success, (out_file, True, file_name))
                conn.commit()
            except psycopg2.Error as error:
                _logger("Cannot write to DB after success!", False)
                raise error

            data_feet['failure_type'] = ind
            ### Write to S3
            data_pd = pd.DataFrame(data_feet)
            f = cStringIO.StringIO()
            data_pd.to_csv(f, index=False)
            f.seek(0)
            try:
                S3.Bucket(cont_write).put_object(Key=SUB_FOLDER+out_file, Body=f)
#                cur.execute(quer_rpush, (user_id, msg, r_push_data))
#                conn.commit()
#                conn.close()
            except boto3.exceptions as error:
                _logger("Cannot write to s3 container after success!", AWS)
                raise error
#            except psycopg2.Error as error:
#                _logger("Cannot write to rpush after success!", AWS)
#                raise error
            else:
                _logger("Finished writing to s3!")
                _process_sac(file_name, cur, conn, quer_check_status)
                return "Success!"

def _select_recording(data):
    freq = 100
    beg = range(int(1.5 * freq))
    subset_data = np.delete(data, beg, 0)
    return subset_data

def _logger(message, info=True):
    if AWS:
        if info:
            logger.info(message)
        else:
            logger.warning(message)
    else:
        print message

def _record_magn(data, file_name, S3):
    import csv
    cont_magntest = 'biometrix-magntest'
#    cont_magntest = os.environ['cont_magntest']
    magntest_file = os.environ['magntest_file']
#    cont_magntest = KMS.decrypt(CiphertextBlob=b64decode(cont_magntest))['Plaintext']
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
    print files_magntest
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
            _logger("Cannot updage magn logs!", AWS)

    else:
        path = '..\\test_base_and_session_calibration\\magntest_base.csv'
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


def _process_sac(file_name, cur, conn, quer_check_status):
    """
    Check if API call needs to be made to process session calibration file and
    make the call if required.
    """
    if AWS:
        url_encrypted = os.environ['sa_api_url']
        url = KMS.decrypt(CiphertextBlob=b64decode(url_encrypted))['Plaintext']
    else:
        url = "http://sensorprocessingapi-dev.us-west-2.elasticbeanstalk.com/"+\
                "api/sessionanatomical/processfile"
    try:
        cur.execute(quer_check_status, (file_name,))
        status_data_all = cur.fetchall()
        _logger("status data retrieved")
        status_data = status_data_all[0]
    except IndexError:
        conn.close()
        _logger("Couldn't find associated events")
    else:
        conn.close()
        for i in range(len(status_data_all)):
            status_data = status_data_all[i]
            sa_filename = status_data[18]
            _logger(sa_filename)
            #Check if all session_calib files have been received
            sa_lf_rec = status_data[19] is not None
            sa_rf_rec = status_data[20] is not None
            sa_h_rec = status_data[21] is not None
            received = sa_lf_rec and sa_rf_rec and sa_h_rec
            #Check session_calib file hasn't already been processed
            not_sent = status_data[22] is None
            #Check if upload to db has started for all sensors
            sa_lf_up_start = status_data[23] is not None
            sa_rf_up_start = status_data[24] is not None
            sa_h_up_start = status_data[25] is not None
            up_started = sa_lf_up_start and sa_rf_up_start and sa_h_up_start
            #Check if upload to db has completed for all sensors
            sa_lf_up_comp = status_data[26] is not None
            sa_rf_up_comp = status_data[27] is not None
            sa_h_up_comp = status_data[28] is not None
            up_completed = sa_lf_up_comp and sa_rf_up_comp and sa_h_up_comp

            if received and not_sent and up_started and up_completed:
    #            data = {'fileName':sa_filename}
    #            headers = {'Content-type':"application/json; charset=utf-8"}
                _logger("API call started")
                r = requests.post(url+'?fileName='+sa_filename)
                _logger("API call completed!")
                if r.status_code !=200:
                    _logger("Failed to start session calib processing!")
                else:
                    _logger("Successfully started session calib processing!")
            else:
                _logger("Session calib file doesn't need to start processing!")


if __name__ == '__main__':
    path = 'team1_session1_trainingset_anatomicalCalibration.csv'
    result = record_base_feet(path, path, aws=False)
