# -*- coding: utf-8 -*-
"""
Created on Tue Oct 18 18:30:17 2016

@author: court
"""


import cStringIO
#import sys
import logging
import os

import boto3
import numpy as np
import pandas as pd
import requests
import psycopg2
from base64 import b64decode

import anatomicalCalibration as ac
from placementCheck import placement_check
import baseCalibration as bc
import prePreProcessing as ppp
import neutralComponents as nc
from errors import ErrorMessageSession, RPushDataSession
import checkProcessed as cp
from columnNames import columns_calib
import sessionCalibrationQueries as queries

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def run_calibration(sensor_data, file_name, aws=True):
    """Checks the validity of base calibration step and writes transformed
    base hip calibration data to the database.
    If valid, writes base and/or session bodyframe and neutral offset
    values for hip, lf and rf to database.
    Args:
        path: filepath for the base/session calibration data.
        file_name: filename for the sensor_data file

    Returns:
        status: Success/Failure
        Pushes notification to user for failure/success of base hip
        calibration step.
        Save transformed data to database with indicator of success/failure
        Save offset values to database
    """
    global AWS
    global KMS
    global SUB_FOLDER
    AWS = aws
    KMS = boto3.client('kms')
    # Read encrypted environment variables
    encrypted_name = os.environ['db_name']
    encrypted_host = os.environ['db_host']
    encrypted_username = os.environ['db_username']
    encrypted_password = os.environ['db_password']
#    encrypted_cont_read = os.environ['cont_read']
    encrypted_sub_folder = os.environ['sub_folder']

    # Decrypt environment variables to plaintext
    db_name = KMS.decrypt(CiphertextBlob=b64decode(encrypted_name))['Plaintext']
    db_host = KMS.decrypt(CiphertextBlob=b64decode(encrypted_host))['Plaintext']
    db_username = KMS.decrypt(CiphertextBlob=b64decode(encrypted_username))['Plaintext']
    db_password = KMS.decrypt(CiphertextBlob=b64decode(encrypted_password))['Plaintext']
#    cont_read = KMS.decrypt(CiphertextBlob=b64decode(encrypted_cont_read))['Plaintext']
    SUB_FOLDER = KMS.decrypt(CiphertextBlob=b64decode(encrypted_sub_folder))['Plaintext']+'/'
    # Define containers to read from and write to
    cont_read = 'biometrix-baseanatomicalcalibrationprocessedcontainer'
    cont_write = 'biometrix-sessionanatomicalcalibrationprocessedcontainer'

    try:
        # Connect to the database
        conn = psycopg2.connect(dbname=db_name, user=db_username, host=db_host,
                                password=db_password)
        cur = conn.cursor()

        # Connect to AWS S3
        S3 = boto3.resource('s3')

        # Execute the read query and extract relevant indicator info
        cur.execute(queries.quer_read, (file_name, ))
        data_read = cur.fetchall()[0]
        user_id = data_read[0]
        if user_id is None:
            user_id = '00000000-0000-0000-0000-000000000000'
            _logger("user_id associated with file not found", info=False)
    except psycopg2.Error as error:
        _logger("Cannot connect to DB", info=False)
        raise error
    except boto3.exceptions as error:
        _logger("Cannot connect to s3", info=False)
        raise error
    except IndexError as error:
        _logger("sensor_data_filename not found in table", info=False)
        raise error

    expired = data_read[1]
    feet_success = data_read[2]
    hip_success = data_read[3]

    # Read data into structured numpy array
    try:
        data = np.genfromtxt(sensor_data, dtype=float, delimiter=',',
                             names=True)

    except IndexError:
        _logger("Sensor data doesn't have column names!", info=False)
        return "Fail!"
    if len(data) == 0:
        _logger("Sensor data is empty!", info=False)
        return "Fail!"
    data.dtype.names = columns_calib
    _logger("Data Loaded")
    #read from S3
    feet_file = data_read[4]
    try:
        obj = S3.Bucket(cont_read).Object(SUB_FOLDER+feet_file)
        fileobj = obj.get()
        body = fileobj["Body"].read()
        feet = cStringIO.StringIO(body)
    except boto3.exceptions as error:
        _logger("Cannot read feet_sensor_data from s3!", info=False)
        raise error

    # Read  base feet calibration data from s3
    try:
        feet_data = np.genfromtxt(feet, dtype=float, delimiter=',', names=True)

    except IndexError:
        _logger("Feet data doesn't have column names!",
                info=False)
        raise error
    if len(feet_data) == 0:
        _logger("Feet sensor data is empty!", info=False)

    # if not expired and feet_success is true and hip_success is true, it's
    # treated as session calibration
    # if hip_success is blank, it's treated as base calibration
    # feet_success should always be true
    # expired should be false
    if not expired and feet_success and hip_success:
        is_base = False
    else:
        is_base = True

    #if it's base, we need the processed_sensor_data_filename
    #if session, we need transform values corresponding to the base calibration

    feet_file = data_read[4]
    if not is_base:
        hip_pitch_transform = np.array(data_read[5]).reshape(-1, 1)
        if len(hip_pitch_transform) == 0:
            is_base = True
        hip_roll_transform = np.array(data_read[6]).reshape(-1, 1)
        if len(hip_roll_transform) == 0:
            is_base = True
        lf_roll_transform = np.array(data_read[7]).reshape(-1, 1)
        if len(lf_roll_transform) == 0:
            is_base = True
        rf_roll_transform = np.array(data_read[8]).reshape(-1, 1)
        if len(rf_roll_transform) == 0:
            is_base = True
    
    # check if the raw quaternions have been converted already
    data = cp.handle_processed(data)
    # subset for 'done'
    subset_data = ppp.subset_data(old_data=data, subset_value=2)
    if len(subset_data) == 0:
        _logger("No overlapping samples after time sync", info=False)
        return "Fail!"

    # select part of recording to be used in calculations
    subset_data_temp = _select_recording(subset_data)
    
    # minimum amount of data required for baseFeet calibration
    min_data_thresh = 0.75*len(subset_data_temp)
    
    # subset for corrupt magnetometer (corrupt_magn=1)
    subset_data = ppp.subset_data(old_data=subset_data_temp, subset_value=1,
                                  missing_or_corrupt='corrupt')
    # check if length of subset data is >= required amount (1.5 sec)
    if len(subset_data) < min_data_thresh:
        _logger("Not enough data after subsetting for bad magn!", info=False)
        _logger("User is: "+ user_id)
        return "Fail!"

    # Record percentage and ranges of magn_values for diagonostic purposes
    _record_magn(subset_data, file_name, S3)

    out_file = "processed_" + file_name
    index = subset_data['index']
    corrupt_magn = subset_data['corrupt_magn']
    missing_type = subset_data['missing_type']

    identifiers = np.array([index, corrupt_magn,
                            missing_type]).transpose()

    # Create indicator values
    failure_type = np.array([-999]*len(subset_data))
    indicators = np.array([failure_type]).transpose()

    # Check for duplicate epoch time
    duplicate_index = ppp.check_duplicate_index(index)
    if duplicate_index:
        _logger('Duplicate index.', info=False)

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
#            Column: ' + var, info=False)
#            return "Fail"

    # subset for missing type = 3
    subset_data = ppp.subset_data(old_data=subset_data, subset_value=3)
    # check if length of subset data is >= required amount (1.5 sec)
    if len(subset_data) < min_data_thresh:
        return "Fail!"


    if ind != 0:
        msg = ErrorMessageSession(ind).error_message
#        r_push_data = RPushDataSession(ind).value

        # Update special_anatomical_calibration_events
        try:
            cur.execute(queries.quer_fail, (False, False, ind, is_base, file_name))
            conn.commit()
            conn.close()
        except psycopg2.Error as error:
            _logger("Cannot write to DB after failure!", info=False)
            raise error

        ### Write to S3
        data_calib = pd.DataFrame(subset_data)
        data_calib['failure_type'] = ind
        f = cStringIO.StringIO()
        data_calib.to_csv(f, index=False)
        f.seek(0)
        try:
            S3.Bucket(cont_write).put_object(Key=SUB_FOLDER+out_file, Body=f)
#            cur.execute(quer_rpush, (user_id, msg, r_push_data))
#            conn.commit()
#            conn.close()
        except boto3.exceptions as error:
            _logger("Can't write to s3 after failure!", info=False)
            raise error
#        except psycopg2.Error as error:
#            _logger("Cannot write to rpush after failure!", info=False)
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
        str(len_nan_real_quat), info=False)

        # Check for type conversion error in left foot quaternion data
        if conv_error:
            _logger('Error! Type conversion error: LF quat', info=False)
            return "Fail!"

        # Hip
        hip_q_xyz = np.array([subset_data['HqX'], subset_data['HqY'],
                              subset_data['HqZ']]).transpose()
        hip_q_wxyz, conv_error = ppp.calc_quaternions(hip_q_xyz,
                                                      missing_type)
        len_nan_real_quat = len(np.where(np.isnan(hip_q_wxyz[:, 0]))[0])
        _logger('Bad data! Percentage of NaNs in HqW: ' +
        str(len_nan_real_quat), info=False)

        # Check for type conversion error in hip quaternion data
        if conv_error:
            _logger('Error! Type conversion error: Hip quat', info=False)
            return "Fail!"

        # Right foot
        right_q_xyz = np.array([subset_data['RqX'], subset_data['RqY'],
                                subset_data['RqZ']]).transpose()
        right_q_wxyz, conv_error = ppp.calc_quaternions(right_q_xyz,
                                                        missing_type)
        len_nan_real_quat = len(np.where(np.isnan(right_q_wxyz[:, 0]))[0])
        _logger('Bad data! Percentage of NaNs in RqW: ' +
        str(len_nan_real_quat), info=False)

        #check for type conversion error in right foot quaternion data
        if conv_error:
            _logger('Error! Type conversion error: RF quat', info=False)
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
        data_o = np.hstack((data_o, left_acc))
        data_o = np.hstack((data_o, left_q_wxyz))
        data_o = np.hstack((data_o, hip_acc))
        data_o = np.hstack((data_o, hip_q_wxyz))
        data_o = np.hstack((data_o, right_acc))
        data_o = np.hstack((data_o, right_q_wxyz))

        # Columns of the output table
        columns = ['index', 'corrupt_magn', 'missing_type', 'failure_type',
                   'LaX', 'LaY', 'LaZ', 'LqW', 'LqX', 'LqY', 'LqZ', 'HaX',
                   'HaY', 'HaZ', 'HqW', 'HqX', 'HqY', 'HqZ', 'RaX', 'RaY',
                   'RaZ', 'RqW', 'RqX', 'RqY', 'RqZ']

        data_o_pd = pd.DataFrame(data_o)
        data_o_pd.columns = columns

        types = [(columns[i].encode(), data_o_pd[k].dtype.type) for\
                    (i, k) in enumerate(columns)]
        dtype = np.dtype(types)
        data_calib = np.zeros(data_o.shape[0], dtype)
        for (i, k) in enumerate(data_calib.dtype.names):
            data_calib[k] = data_o[:, i]
        #Check if the sensors are placed correctly and if the subject is moving
        #around and push respective success/failure message to the user
        ind = placement_check(left_acc, hip_acc, right_acc)
#        left_ind = hip_ind = right_ind = mov_ind =False
        if ind != 0:
            # rPush
            msg = ErrorMessageSession(ind).error_message
#            r_push_data = RPushDataSession(ind).value
            # Write to SessionAnatomicalCalibrationEvents
            try:
                cur.execute(queries.quer_fail, (False, False, ind, is_base, file_name))
                conn.commit()
                conn.close()
            except psycopg2.Error as error:
                _logger("Cannot write to DB after failure!", info=False)
                raise error


            #write to S3 and rPush
            data_calib['failure_type'] = ind
            data_pd = pd.DataFrame(data_calib)
            f = cStringIO.StringIO()
            data_pd.to_csv(f, index=False)
            f.seek(0)
            try:
                S3.Bucket(cont_write).put_object(Key=SUB_FOLDER+out_file, Body=f)
#                cur.execute(quer_rpush, (user_id, msg, r_push_data))
#                conn.commit()
#                conn.close()
            except boto3.exceptions as error:
                _logger("Cannot write to s3 container after failure!", False)
                raise error
#            except psycopg2.Error as error:
#                _logger("Cannot write to rpush after failure!", info=False)
#                raise error
            else:
                _logger("Failure Message: " + msg, False)
                _logger("User is: "+ user_id)
                return "Fail!"

        else:
            # rPush
            msg = ErrorMessageSession(ind).error_message
#            r_push_data = RPushDataSession(ind).value

            ###Write to S3
            data_calib['failure_type'] = ind
            data_pd = pd.DataFrame(data_calib)
            data_pd['base_calibration'] = int(is_base)
            f = cStringIO.StringIO()
            data_pd.to_csv(f, index=False)
            f.seek(0)
            try:
                S3.Bucket(cont_write).put_object(Key=SUB_FOLDER+out_file, Body=f)
            except boto3.exceptions as error:
                _logger("Cannot write to s3!", info=False)
                raise error

            if is_base:

                #Run base calibration
                hip_pitch_transform, hip_roll_transform,\
                lf_roll_transform, rf_roll_transform = \
                bc.run_special_calib(data_calib, feet_data)

                # check if the transform values are nan's
                if np.any(np.isnan(hip_pitch_transform)):
                    _logger('Hip pitch transform has missing values', False)
                    raise ValueError('NaN in hip_pitch_transform')
                elif np.any(np.isnan(hip_roll_transform)):
                    _logger('Hip roll transform has missing values', False)
                    raise ValueError('NaN in hip_roll_transform')
                elif np.any(np.isnan(lf_roll_transform)):
                    _logger('LF roll transform has missing values', False)
                    raise ValueError('NaN in lf_roll_transform')
                elif np.any(np.isnan(rf_roll_transform)):
                    _logger('RF roll transform has missing values', False)
                    raise ValueError('NaN in rf_roll_transform')

                hip_p_transform = hip_pitch_transform.reshape(-1, ).tolist()
                hip_r_transform = hip_roll_transform.reshape(-1, ).tolist()
                lf_r_transform = lf_roll_transform.reshape(-1, ).tolist()
                rf_r_transform = rf_roll_transform.reshape(-1, ).tolist()

                # Save base calibration offsets to
                # BaseAnatomicalCalibrationEvent along with hip_success
                try:
                    cur.execute(queries.quer_base_succ, (True, hip_p_transform,
                                                         hip_r_transform,
                                                         lf_r_transform,
                                                         rf_r_transform,
                                                         False,
                                                         file_name))
                    conn.commit()
                except psycopg2.Error as error:
                    _logger("Cannot write base transform values to DB",
                            info=False)
                    raise error

                # Run session calibration
                hip_bf_transform, lf_bf_transform, rf_bf_transform = \
                ac.run_calib(data_calib, hip_pitch_transform,
                             hip_roll_transform, lf_roll_transform,
                             rf_roll_transform)

                # Calculate neutral transforms
                lf_n_transform, hip_n_transform, rf_n_transform =\
                nc.run_neutral_computations(feet_data, data_calib,
                                            lf_bf_transform,
                                            hip_bf_transform,
                                            rf_bf_transform)

                # Check if bodyframe and neutral transform values are nan's
                if np.any(np.isnan(hip_bf_transform)):
                    _logger('Hip bodyframe transform has missing values.',
                            info=False)
                    raise ValueError('NaN in hip_bf_transform')
                elif np.any(np.isnan(lf_bf_transform)):
                    _logger('LF bodyframe transform has missing values.',
                            info=False)
                    raise ValueError('NaN in lf_bf_transform')
                elif np.any(np.isnan(rf_bf_transform)):
                    _logger('RF bodyframe transform has missing values.',
                            info=False)
                    raise ValueError('NaN in rf_bf_transform')
                elif np.any(np.isnan(lf_n_transform)):
                    _logger('LF neutral transform has missing values.',
                            info=False)
                    raise ValueError('NaN in lf_n_transform')
                elif np.any(np.isnan(rf_n_transform)):
                    _logger('RF neutral transform has missing values.',
                            info=False)
                    raise ValueError('NaN in rf_n_transform')
                elif np.any(np.isnan(hip_n_transform)):
                    _logger('Hip neutral transform has missing values.',
                            info=False)
                    raise ValueError('NaN in hip_n_transform')

                # Save session calibration offsets to
                # SessionAnatomicalCalibrationEvent
                # along with base_calibration=True and success=True
                hip_bf_transform = hip_bf_transform.reshape(-1,).tolist()
                lf_bf_transform = lf_bf_transform.reshape(-1,).tolist()
                rf_bf_transform = rf_bf_transform.reshape(-1,).tolist()
                lf_n_transform = lf_n_transform.reshape(-1,).tolist()
                rf_n_transform = rf_n_transform.reshape(-1,).tolist()
                hip_n_transform = hip_n_transform.reshape(-1,).tolist()

                try:
                    cur.execute(queries.quer_session_succ, (True, True, is_base,
                                                            hip_n_transform,
                                                            hip_bf_transform,
                                                            lf_n_transform,
                                                            lf_bf_transform,
                                                            rf_n_transform,
                                                            rf_bf_transform,
                                                            file_name))
                    conn.commit()
                except psycopg2.Error as error:
                    _logger("Cannot write to DB after success!",
                            info=False)
                    raise error
#                try:
#                    cur.execute(quer_rpush, (user_id, msg, r_push_data))
#                    conn.commit()
#                    conn.close()
#
#                # rPush
#                except:
#                    _logger("Cannot write to rpush after succcess!",
#                            info=False)
#                    raise error
                else:
                    _process_se(file_name, cur, conn, queries.quer_check_status)
                    conn.close()
                    return "Success!"

            else:
                # Run session calibration
                hip_bf_transform, lf_bf_transform, rf_bf_transform = \
                ac.run_calib(data_calib, hip_pitch_transform,
                             hip_roll_transform, lf_roll_transform,
                             rf_roll_transform)
                
                # Calculate neutral transforms
                lf_n_transform, hip_n_transform, rf_n_transform =\
                nc.run_neutral_computations(feet_data, data_calib,
                                            lf_bf_transform,
                                            hip_bf_transform,
                                            rf_bf_transform)

                hip_bf_transform = hip_bf_transform.reshape(-1,).tolist()
                lf_bf_transform = lf_bf_transform.reshape(-1,).tolist()
                rf_bf_transform = rf_bf_transform.reshape(-1,).tolist()
                lf_n_transform = lf_n_transform.reshape(-1,).tolist()
                rf_n_transform = rf_n_transform.reshape(-1,).tolist()
                hip_n_transform = hip_n_transform.reshape(-1,).tolist()

                # Save session calibration offsets to
                # SessionAnatomicalCalibrationEvent
                # along with base_calibration=False and success=True
                try:
                    cur.execute(queries.quer_session_succ, (True, True, is_base,
                                                            hip_n_transform,
                                                            hip_bf_transform,
                                                            lf_n_transform,
                                                            lf_bf_transform,
                                                            rf_n_transform,
                                                            rf_bf_transform,
                                                            file_name))
                    conn.commit()
                except psycopg2.Error as error:
                    _logger("Cannot write to DB after success!",
                            info=False)

#                # rPush
#                try:
#                    cur.execute(quer_rpush, (user_id, msg, r_push_data))
#                    conn.commit()
#                    conn.close()
#                except:
#                    _logger("Cannot write to rpush after succcess!", info=False)
#                    raise error
                else:
                    _process_se(file_name, cur, conn, queries.quer_check_status)
                    conn.close()
                    return "Success!"

def _select_recording(data):
    freq = 100
    beg = range(int(2 * freq))
    end = range(int(4 * freq), len(data))
    ind = beg + end
    subset_data = np.delete(data, ind, 0)
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
        path = '..\\test_base_and_session_calibration\\magntest_session_calib.csv'
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

def _process_se(file_name, cur, conn, quer_check_status):
    """
    Check if API call needs to be made to process session calibration file and
    make the call if required.
    """
    if AWS:
        url_encrypted = os.environ['se_api_url']
        url = KMS.decrypt(CiphertextBlob=b64decode(url_encrypted))['Plaintext']
    else:
        url = "http://sensorprocessingapi-dev.us-west-2.elasticbeanstalk.com/"+\
                "api/sessionevent/processfile"
    try:
        cur.execute(quer_check_status, (file_name,))
        status_data_all = cur.fetchall()
        status_data = status_data_all[0]
    except IndexError:
        conn.close()
        _logger("Couldn't find associated events")
    else:
        conn.close()
        for i in range(len(status_data_all)):
            status_data = status_data_all[i]
            se_filename = status_data[32]
            #Check if all session_event files have been received
            se_lf_rec = status_data[33] is not None
            se_rf_rec = status_data[34] is not None
            se_h_rec = status_data[35] is not None
            received = se_lf_rec and se_rf_rec and se_h_rec
            #Check session_event file hasn't already been processed
            not_sent = status_data[36] is None
            #Check if upload to db has started for all sensors
            se_lf_up_start = status_data[37] is not None
            se_rf_up_start = status_data[38] is not None
            se_h_up_start = status_data[39] is not None
            up_started = se_lf_up_start and se_rf_up_start and se_h_up_start
            #Check if upload to db has completed for all sensors
            se_lf_up_comp = status_data[40] is not None
            se_rf_up_comp = status_data[41] is not None
            se_h_up_comp = status_data[42] is not None
            up_completed = se_lf_up_comp and se_rf_up_comp and se_h_up_comp

            if received and not_sent and up_started and up_completed:
                """make api call here to begin session_event_processing"""
    #            data = {'fileName':se_filename}
    #            headers = {'Content-type':"application/json; charset=utf-8"}
                r = requests.post(url+'?fileName='+se_filename)
                if r.status_code !=200:
                    _logger("Failed to start session event processing!")
                else:
                    _logger("Successfully started session event processing!")
            else:
                _logger("Session event file doesn't need to start processing!")



if __name__ == '__main__':
    path = 'team1_session1_trainingset_anatomicalCalibration.csv'
    result = run_calibration(path, path)
