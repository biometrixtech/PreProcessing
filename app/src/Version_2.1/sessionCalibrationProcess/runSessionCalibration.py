# -*- coding: utf-8 -*-
"""
Created on Tue Oct 18 18:30:17 2016

@author: court
"""


import cStringIO
#import sys
import logging

import boto3
import numpy as np
import pandas as pd
import psycopg2

import anatomicalCalibration as ac
from placementCheck import placement_check
import baseCalibration as bc
import prePreProcessing as ppp
import neutralComponents as nc
from errors import ErrorMessageSession, RPushDataSession
import checkProcessed as cp
from columnNames import columns_calib

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
    # Setup Queries based on different situations

    # Read relevant information from base_anatomical_calibration_events
    # based on provided sensor_data_filename and
    # base_anatomical_calibration_event_id tied to the filename
    quer_read = """select user_id,
                          expired,
                          feet_success,
                          hip_success,
                          feet_processed_sensor_data_filename,
                          hip_pitch_transform,
                          hip_roll_transform,
                          lf_roll_transform,
                          rf_roll_transform
                from base_anatomical_calibration_events where
                id = (select base_anatomical_calibration_event_id from
                        session_anatomical_calibration_events where 
                        sensor_data_filename = (%s));"""

    # Update anatomical_calibration_events in case the tests fail
    quer_fail = """update session_anatomical_calibration_events set
                success = (%s),
                failure_type = (%s),
                base_calibration = (%s),
                updated_at = now()
                where sensor_data_filename=(%s);"""

    # For base calibration, update base_anatomical_calibration_events
    quer_base_succ = """update  base_anatomical_calibration_events set
                hip_success = (%s),
                hip_pitch_transform = (%s),
                hip_roll_transform = (%s),
                lf_roll_transform = (%s),
                rf_roll_transform = (%s),
                updated_at = now()
                where id  = (select base_anatomical_calibration_event_id from
                            session_anatomical_calibration_events where
                            sensor_data_filename = (%s));"""

    # For both base and session calibration, update
    # session_anatomical_calibration_events with relevant info
    # for base calibration, session calibration follows base calibration
    # for session calibration, it's independent and uses values read earlier
    quer_session_succ = """update session_anatomical_calibration_events set
                    success = (%s),
                    base_calibration = (%s),
                    hip_n_transform = (%s),
                    hip_bf_transform = (%s),
                    lf_n_transform = (%s),
                    lf_bf_transform = (%s),
                    rf_n_transform = (%s),
                    rf_bf_transform = (%s),
                    updated_at = now()
                    where sensor_data_filename  = (%s);"""

    quer_rpush = "select fn_send_push_notification(%s, %s, %s)"

    # Define containers to read from and write to
    cont_read = 'biometrix-baseanatomicalcalibrationprocessedcontainer'
    cont_write = 'biometrix-sessionanatomicalcalibrationprocessedcontainer'

    try:
        # Connect to the database
        conn = psycopg2.connect("""dbname='biometrix' user='ubuntu'
        host='ec2-35-162-107-177.us-west-2.compute.amazonaws.com' 
        password='d8dad414c2bb4afd06f8e8d4ba832c19d58e123f'""")
        cur = conn.cursor()

        # Connect to AWS S3
        S3 = boto3.resource('s3')

        # Execute the read query and extract relevant indicator info
        cur.execute(quer_read, (file_name, ))
        data_read = cur.fetchall()[0]
        user_id = data_read[0]
        if user_id is None:
            user_id = '00000000-0000-0000-0000-000000000000'
            _logger("user_id associated with file not found", aws, info=False)
    except psycopg2.Error as error:
        _logger("Cannot connect to DB", aws, info=False)
        raise error
    except boto3.exceptions as error:
        _logger("Cannot connect to s3", aws, info=False)
        raise error
    except IndexError as error:
        _logger("sensor_data_filename not found in table", aws, info=False)
        raise error

    expired = data_read[1]
    feet_success = data_read[2]
    hip_success = data_read[3]

    # Read data into structured numpy array
    try:
        data = np.genfromtxt(sensor_data, dtype=float, delimiter=',',
                             names=True)

    except IndexError:
        _logger("Sensor data doesn't have column names!", aws, info=False)
        return "Fail!"
    if len(data) == 0:
        _logger("Sensor data is empty!", aws, info=False)
        return "Fail!"
    data.dtype.names = columns_calib
    #read from S3
    feet_file = data_read[4]
    try:
        obj = S3.Bucket(cont_read).Object(feet_file)
        fileobj = obj.get()
        body = fileobj["Body"].read()
        feet = cStringIO.StringIO(body)
    except boto3.exceptions as error:
        _logger("Cannot read feet_sensor_data from s3!", aws, info=False)
        raise error

    # Read  base feet calibration data from s3
    try:
        feet_data = np.genfromtxt(feet, dtype=float, delimiter=',', names=True)

    except IndexError:
        _logger("Feet data doesn't have column names!",
                aws, info=False)
        raise error
    if len(feet_data) == 0:
        _logger("Feet sensor data is empty!", aws, info=False)

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
    if is_base:
        feet_file = data_read[4]
    else:
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
    
    out_file = "processed_" + file_name
    index = data['index']
    corrupt_magn = data['corrupt_magn']
    missing_type = data['missing_type']

    identifiers = np.array([index, corrupt_magn,
                            missing_type]).transpose()

    # Create indicator values
    failure_type = np.array([-999]*len(data))
    indicators = np.array([failure_type]).transpose()

    # Check for duplicate epoch time
    duplicate_index = ppp.check_duplicate_index(index)
    if duplicate_index:
        _logger('Duplicate index.'. aws, info=False)

    # PRE-PRE-PROCESSING
    
    # subset for 'done'
    subset_data = ppp.subset_data_done(old_data=data)

    # select part of recording to be used in calculations
    subset_data = _select_recording(subset_data)

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

        # check if nan's exist even after imputing
        if np.any(np.isnan(out[missing_type != 1])):  # subsetting for when
        # a missing value is an intentional blank
            _logger('Bad data! NaNs exist even after imputing. \
            Column: ' + var, aws, info=False)
            return "Fail"

    if ind != 0:
        msg = ErrorMessageSession(ind).error_message
        r_push_data = RPushDataSession(ind).value

        # Update special_anatomical_calibration_events
        try:
            cur.execute(quer_fail, (False, ind, is_base, file_name))
            conn.commit()
        except psycopg2.Error as error:
            _logger("Cannot write to DB after failure!", aws, info=False)
            raise error

        ### Write to S3
        data_calib = pd.DataFrame(subset_data)
        data_calib['failure_type'] = ind
        f = cStringIO.StringIO()
        data_calib.to_csv(f, index=False)
        f.seek(0)
        try:
            S3.Bucket(cont_write).put_object(Key=out_file, Body=f)
            cur.execute(quer_rpush, (user_id, msg, r_push_data))
            conn.commit()
            conn.close()
        except boto3.exceptions as error:
            _logger("Can't write to s3 after failure!", aws, info=False)
            raise error
        except psycopg2.Error as error:
            _logger("Cannot write to rpush after failure!", aws, info=False)
            raise error
        else:
            _logger("Failed due to:" + msg, aws, False)
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
        str(len_nan_real_quat), aws, info=False)

        # Check for type conversion error in left foot quaternion data
        if conv_error:
            _logger('Error! Type conversion error: LF quat', aws, info=False)
            return "Fail!"

        # Hip
        hip_q_xyz = np.array([subset_data['HqX'], subset_data['HqY'],
                              subset_data['HqZ']]).transpose()
        hip_q_wxyz, conv_error = ppp.calc_quaternions(hip_q_xyz,
                                                      missing_type)
        len_nan_real_quat = len(np.where(np.isnan(hip_q_wxyz[:, 0]))[0])                                              
        _logger('Bad data! Percentage of NaNs in HqW: ' +
        str(len_nan_real_quat), aws, info=False)

        # Check for type conversion error in hip quaternion data
        if conv_error:
            _logger('Error! Type conversion error: Hip quat', aws, info=False)
            return "Fail!"

        # Right foot
        right_q_xyz = np.array([subset_data['RqX'], subset_data['RqY'],
                                subset_data['RqZ']]).transpose()
        right_q_wxyz, conv_error = ppp.calc_quaternions(right_q_xyz,
                                                        missing_type)
        len_nan_real_quat = len(np.where(np.isnan(right_q_wxyz[:, 0]))[0])                                              
        _logger('Bad data! Percentage of NaNs in RqW: ' +
        str(len_nan_real_quat), aws, info=False)

        #check for type conversion error in right foot quaternion data
        if conv_error:
            _logger('Error! Type conversion error: RF quat', aws, info=False)
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
            r_push_data = RPushDataSession(ind).value
            # Write to SessionAnatomicalCalibrationEvents
            try:
                cur.execute(quer_fail, (False, ind, is_base, file_name))
                conn.commit()
            except psycopg2.Error as error:
                _logger("Cannot write to DB after failure!", aws, info=False)
                raise error


            #write to S3 and rPush
            data_calib['failure_type'] = ind
            data_pd = pd.DataFrame(data_calib)
            f = cStringIO.StringIO()
            data_pd.to_csv(f, index=False)
            f.seek(0)
            try:
                S3.Bucket(cont_write).put_object(Key=out_file, Body=f)
                cur.execute(quer_rpush, (user_id, msg, r_push_data))
                conn.commit()
                conn.close()
            except boto3.exceptions as error:
                _logger("Cannot write to s3 container after failure!",
                        aws, info=False)
                raise error
            except psycopg2.Error as error:
                _logger("Cannot write to rpush after failure!", aws, info=False)
                raise error
            else:
                _logger("Failed due to:" + msg, aws, False)
                return "Fail!"

        else:
            # rPush
            msg = ErrorMessageSession(ind).error_message
            r_push_data = RPushDataSession(ind).value

            ###Write to S3
            data_calib['failure_type'] = ind
            data_pd = pd.DataFrame(data_calib)
            data_pd['base_calibration'] = int(is_base)
            f = cStringIO.StringIO()
            data_pd.to_csv(f, index=False)
            f.seek(0)
            try:
                S3.Bucket(cont_write).put_object(Key=out_file, Body=f)
            except boto3.exceptions as error:
                _logger("Cannot write to s3!", aws, info=False)
                raise error

            if is_base:

                #Run base calibration
                hip_pitch_transform, hip_roll_transform,\
                lf_roll_transform, rf_roll_transform = \
                bc.run_special_calib(data_calib, feet_data)

                # check if the transform values are nan's
                if np.any(np.isnan(hip_pitch_transform)):
                    _logger('Hip pitch transform has missing values.',
                            aws, info=False)
                    raise ValueError('NaN in hip_pitch_transform')
                elif np.any(np.isnan(hip_roll_transform)):
                    _logger('Hip roll transform has missing values.',
                                 aws, info=False)
                    raise ValueError('NaN in hip_roll_transform')
                elif np.any(np.isnan(lf_roll_transform)):
                    _logger('LF roll transform has missing values.',
                                 aws, info=False)
                    raise ValueError('NaN in lf_roll_transform')
                elif np.any(np.isnan(rf_roll_transform)):
                    _logger('RF roll transform has missing values.',
                                 aws, info=False)
                    raise ValueError('NaN in rf_roll_transform')

                hip_p_transform = hip_pitch_transform.reshape(-1, ).tolist()
                hip_r_transform = hip_roll_transform.reshape(-1, ).tolist()
                lf_r_transform = lf_roll_transform.reshape(-1, ).tolist()
                rf_r_transform = rf_roll_transform.reshape(-1, ).tolist()

                # Save base calibration offsets to
                # BaseAnatomicalCalibrationEvent along with hip_success
                try:
                    cur.execute(quer_base_succ, (True, hip_p_transform,
                                                 hip_r_transform,
                                                 lf_r_transform,
                                                 rf_r_transform,
                                                 file_name))
                    conn.commit()
                except psycopg2.Error as error:
                    _logger("Cannot write base transform values to DB",
                            aws, info=False)
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
                            aws, info=False)
                    raise ValueError('NaN in hip_bf_transform')
                elif np.any(np.isnan(lf_bf_transform)):
                    _logger('LF bodyframe transform has missing values.',
                            aws, info=False)
                    raise ValueError('NaN in lf_bf_transform')
                elif np.any(np.isnan(rf_bf_transform)):
                    _logger('RF bodyframe transform has missing values.',
                            aws, info=False)
                    raise ValueError('NaN in rf_bf_transform')
                elif np.any(np.isnan(lf_n_transform)):
                    _logger('LF neutral transform has missing values.',
                            aws, info=False)
                    raise ValueError('NaN in lf_n_transform')
                elif np.any(np.isnan(rf_n_transform)):
                    _logger('RF neutral transform has missing values.',
                            aws, info=False)
                    raise ValueError('NaN in rf_n_transform')
                elif np.any(np.isnan(hip_n_transform)):
                    _logger('Hip neutral transform has missing values.',
                            aws, info=False)
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
                    cur.execute(quer_session_succ, (True, is_base,
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
                            aws, info=False)
                    raise error
                try:
                    cur.execute(quer_rpush, (user_id, msg, r_push_data))
                    conn.commit()
                    conn.close()

                # rPush
                except:
                    _logger("Cannot write to rpush after succcess!",
                            aws, info=False)
                    raise error
                else:
                    return "Success!"

            else:
                # Run session calibration
                hip_bf_transform, lf_bf_transform, rf_bf_transform,\
                lf_n_transform, rf_n_transform, hip_n_transform = \
                ac.run_calib(data_calib, hip_pitch_transform,
                             hip_roll_transform, lf_roll_transform,
                             rf_roll_transform)
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
                    cur.execute(quer_session_succ, (True, is_base,
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
                            aws, info=False)

                # rPush
                try:
                    cur.execute(quer_rpush, (user_id, msg, r_push_data))
                    conn.commit()
                    conn.close()
                except:
                    _logger("Cannot write to rpush after succcess!",
                            aws, info=False)
                    raise error
                else:
                    return "Success!"

def _select_recording(data):
    freq = 100
    beg = range(int(2 * freq))
    end = range(int(4 * freq), len(data))
    ind = beg + end
    subset_data = np.delete(data, ind, 0)
    return subset_data


def _logger(message, aws, info=True):
    if aws:
        if info:
            logger.info(message)
        else:
            logger.warning(message)
    else:
        print message

if __name__ == '__main__':
    path = 'team1_session1_trainingset_anatomicalCalibration.csv'
    result = run_calibration(path, path)
