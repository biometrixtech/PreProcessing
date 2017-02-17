# -*- coding: utf-8 -*-
"""
Created on Tue Oct 18 18:30:17 2016

@author: court
"""


import cStringIO
import sys
import logging

import boto3
import numpy as np
import pandas as pd
import psycopg2

import anatomicalCalibration as ac
from placementCheck import placement_check
import baseCalibration as bc
import calibPrePreProcessing as cppp
from errors import ErrorMessageSession, RPushDataSession

from applyOffset import apply_offsets

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def run_calibration(sensor_data, file_name, feet, calib_bool, left_bool,
                    hip_bool, right_bool, offset):

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
    left_offset = np.zeros(())
    hip_offset = np.zeros(())
    right_offset = np.zeros(())
    # Setup Queries based on different situations

    # Read relevant information from special_anatomical_calibration_events
    # based on provided sensor_data_filename and
    # special_anatomical_calibration_event_id tied to the filename
#    quer_read = """select user_id, expired, feet_success, hip_success,
#                feet_processed_sensor_data_filename, hip_pitch_transform,
#                hip_roll_transform, lf_roll_transform, rf_roll_transform
#                from base_anatomical_calibration_events where
#                id = (select base_anatomical_calibration_event_id from
#                        session_anatomical_calibration_events where 
#                        sensor_data_filename = (%s));"""
#
#    # Update anatomical_calibration_events in case the tests fail
#    quer_fail = """update session_anatomical_calibration_events set
#                success = (%s),
#                failure_type = (%s),
#                base_calibration = (%s),
#                updated_at = now()
#                where sensor_data_filename=(%s);"""
#
#    # For base calibration, update special_anatomical_calibration_events
#    quer_spe_succ = """update  base_anatomical_calibration_events set
#                hip_success = (%s),
#                hip_pitch_transform = (%s),
#                hip_roll_transform = (%s),
#                lf_roll_transform = (%s),
#                rf_roll_transform = (%s),
#                updated_at = now()
#                where id  = (select base_anatomical_calibration_event_id from
#                            session_anatomical_calibration_events where
#                            sensor_data_filename = (%s));"""
#
#    # For both base and session calibration, update
#    # anatomical_calibration_events with relevant info
#    # for base calibration, session calibration follows base calibration
#    # for session calibration, it's independent and uses values read earlier
#    quer_reg_succ = """update session_anatomical_calibration_events set
#                    success = (%s),
#                    base_calibration = (%s),
#                    hip_n_transform = (%s),
#                    hip_bf_transform = (%s),
#                    lf_n_transform = (%s),
#                    lf_bf_transform = (%s),
#                    rf_n_transform = (%s),
#                    rf_bf_transform = (%s),
#                    updated_at = now()
#                    where sensor_data_filename  = (%s);"""
#
#    quer_rpush = "select fn_send_push_notification(%s, %s, %s)"
#
#    # Define containers to read from and write to
#    cont_read = 'biometrix-baseanatomicalcalibrationprocessedcontainer'
#    cont_write = 'biometrix-sessionanatomicalcalibrationprocessedcontainer'
#
#    try:
#        # Connect to the database
#        conn = psycopg2.connect("""dbname='biometrix' user='ubuntu'
#        host='ec2-35-162-107-177.us-west-2.compute.amazonaws.com' 
#        password='d8dad414c2bb4afd06f8e8d4ba832c19d58e123f'""")
#        cur = conn.cursor()
#
#        # Connect to AWS S3
#        S3 = boto3.resource('s3')
#
#        # Execute the read query and extract relevant indicator info
#        cur.execute(quer_read, (file_name, ))
#        data_read = cur.fetchall()[0]
#        user_id = data_read[0]
#        if user_id is None:
#            user_id = '00000000-0000-0000-0000-000000000000'
#            logger.warning("user_id associated with file not found")
#    except psycopg2.Error as error:
#        logger.warning("Cannot connect to DB")
#        raise error
#    except boto3.exceptions as error:
#        logger.warning("Cannot connect to s3")
#        raise error
#    except IndexError as error:
#        logger.warning("sensor_data_filename not found in table")
#        raise error

    expired = False
    feet_success = True
    hip_success = False

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
        feet_file = feet
#    else:
#        hip_pitch_transform = np.array(data_read[5]).reshape(-1, 1)
#        if len(hip_pitch_transform) == 0:
#            is_base = True
#        hip_roll_transform = np.array(data_read[6]).reshape(-1, 1)
#        if len(hip_roll_transform) == 0:
#            is_base = True
#        lf_roll_transform = np.array(data_read[7]).reshape(-1, 1)
#        if len(lf_roll_transform) == 0:
#            is_base = True
#        rf_roll_transform = np.array(data_read[8]).reshape(-1, 1)
#        if len(rf_roll_transform) == 0:
#            is_base = True

    # Read data into structured numpy array
    try:
        data = np.genfromtxt(sensor_data, dtype=float, delimiter=',',
                             names=True)
    except IndexError:
        print "Sensor data doesn't have column names!"
        return "Fail!"
    if len(data) == 0:
        print "Sensor data is empty!"
#        return "Fail!"

    out_file = "session_" + file_name
    epoch_time = data['epoch_time']
    corrupt_magn = data['corrupt_magn']
    missing_type = data['missing_type']

    identifiers = np.array([epoch_time, corrupt_magn,
                            missing_type]).transpose()

    # Create indicator values
    failure_type = np.array([-999]*len(data))
    indicators = np.array([failure_type]).transpose()

    # Check for duplicate epoch time
    duplicate_epoch_time = cppp.check_duplicate_epochtime(epoch_time)
    if duplicate_epoch_time:
        print 'Duplicate epoch time.'

    # PRE-PRE-PROCESSING
    columns = ['LaX', 'LaY', 'LaZ', 'LqX', 'LqY', 'LqZ', 'HaX',
               'HaY', 'HaZ', 'HqX', 'HqY', 'HqZ', 'RaX', 'RaY', 'RaZ',
               'RqX', 'RqY', 'RqZ']

    # check for missing values for each of acceleration and quaternion values
    for var in columns:
        out, ind = cppp.handling_missing_data(epoch_time,
                                             data[var].reshape(-1, 1),
                                             corrupt_magn.reshape(-1, 1))
        data[var] = out.reshape(-1, )
        if ind in [1, 10]:
            break

        # check if nan's exist even after imputing
        if np.any(np.isnan(out)):
            print 'Bad data! NaNs exist even after imputing. \
            Column: ' + var
            return "Fail"

    if ind != 0:
        msg = ErrorMessageSession(ind).error_message
        r_push_data = RPushDataSession(ind).value

        # Update special_anatomical_calibration_events
#        try:
#            cur.execute(quer_fail, (ind, out_file, False, file_name))
#            conn.commit()
#        except psycopg2.Error as error:
#            logger.warning("Cannot write to DB after failure!")
#            raise error

        ### Write to S3
        data_calib = pd.DataFrame(data)
        data_calib['failure_type'] = ind
#        f = cStringIO.StringIO()
#        data_calib.to_csv(out_file, index=False)
#        f.seek(0)
#        try:
#            S3.Bucket(cont_write).put_object(Key=out_file, Body=f)
#            cur.execute(quer_rpush, (user_id, msg, r_push_data))
#            conn.commit()
#            conn.close()
#        except boto3.exceptions as error:
#            logger.warning("Can't write to s3 after failure!")
#            raise error
#        except psycopg2.Error as error:
#            logger.warning("Cannot write to rpush after failure!")
#            raise error
#        else:
#            return "Fail!"
        offsets = ind
        return data_calib, offsets

    else:
        # determine the real quartenion
        # Left foot
        left_q_xyz = np.array([data['LqX'], data['LqY'],
                               data['LqZ']]).transpose()
        left_q_wxyz, conv_error = cppp.calc_quaternions(left_q_xyz)

        # Check for type conversion error in left foot quaternion data
        if conv_error:
            print 'Error! Type conversion error: LF quat'
            return "Fail!"

        # Hip
        hip_q_xyz = np.array([data['HqX'], data['HqY'],
                              data['HqZ']]).transpose()
        hip_q_wxyz, conv_error = cppp.calc_quaternions(hip_q_xyz)

        # Check for type conversion error in hip quaternion data
        if conv_error:
            print 'Error! Type conversion error: Hip quat'
            return "Fail!"

        # Right foot
        right_q_xyz = np.array([data['RqX'], data['RqY'],
                                data['RqZ']]).transpose()
        right_q_wxyz, conv_error = cppp.calc_quaternions(right_q_xyz)

        #check for type conversion error in right foot quaternion data
        if conv_error:
            print 'Error! Type conversion error: RF quat'
            return "Fail!"

        #Acceleration
        left_acc = np.array([data['LaX'], data['LaY'],
                             data['LaZ']]).transpose()
        hip_acc = np.array([data['HaX'], data['HaY'],
                            data['HaZ']]).transpose()
        right_acc = np.array([data['RaX'], data['RaY'],
                              data['RaZ']]).transpose()
        
        # apply offset where appropriate
        if calib_bool:
            if left_bool:
                left_offset = offset
                LqW, LqX, LqY, LqZ, LaX, LaY, LaZ = apply_offsets(
                                    left_q_wxyz[:,0].reshape(-1,1), left_q_wxyz[:,1].reshape(-1,1),
                                    left_q_wxyz[:,2].reshape(-1,1), left_q_wxyz[:,3].reshape(-1,1),
                                    left_acc[:,0].reshape(-1,1), left_acc[:,1].reshape(-1,1),
                                    left_acc[:,2].reshape(-1,1), left_offset)

                left_q_wxyz = np.hstack((LqW, LqX))
                left_q_wxyz = np.hstack((left_q_wxyz, LqY))
                left_q_wxyz = np.hstack((left_q_wxyz, LqZ))
                left_acc = np.hstack((LaX, LaY))
                left_acc = np.hstack((left_acc, LaZ))

            if hip_bool:
                hip_offset = offset
                HqW, HqX, HqY, HqZ, HaX, HaY, HaZ = apply_offsets(
                                    hip_q_wxyz[:,0].reshape(-1,1), hip_q_wxyz[:,1].reshape(-1,1),
                                    hip_q_wxyz[:,2].reshape(-1,1), hip_q_wxyz[:,3].reshape(-1,1),
                                    hip_acc[:,0].reshape(-1,1), hip_acc[:,1].reshape(-1,1),
                                    hip_acc[:,2].reshape(-1,1), hip_offset)

                hip_q_wxyz = np.hstack((HqW, HqX))
                hip_q_wxyz = np.hstack((hip_q_wxyz, HqY))
                hip_q_wxyz = np.hstack((hip_q_wxyz, HqZ))
                hip_acc = np.hstack((HaX, HaY))
                hip_acc = np.hstack((hip_acc, HaZ))

            if right_bool:
                right_offset = offset
                RqW, RqX, RqY, RqZ, RaX, RaY, RaZ = apply_offsets(
                                    right_q_wxyz[:,0].reshape(-1,1), right_q_wxyz[:,1].reshape(-1,1),
                                    right_q_wxyz[:,2].reshape(-1,1), right_q_wxyz[:,3].reshape(-1,1),
                                    right_acc[:,0].reshape(-1,1), right_acc[:,1].reshape(-1,1),
                                    right_acc[:,2].reshape(-1,1), right_offset)

                right_q_wxyz = np.hstack((RqW, RqX))
                right_q_wxyz = np.hstack((right_q_wxyz, RqY))
                right_q_wxyz = np.hstack((right_q_wxyz, RqZ))
                right_acc = np.hstack((RaX, RaY))
                right_acc = np.hstack((right_acc, RaZ))

        #create output table as a structured numpy array
        data_o = np.hstack((identifiers, indicators))
        data_o = np.hstack((data_o, left_acc))
        data_o = np.hstack((data_o, left_q_wxyz))
        data_o = np.hstack((data_o, hip_acc))
        data_o = np.hstack((data_o, hip_q_wxyz))
        data_o = np.hstack((data_o, right_acc))
        data_o = np.hstack((data_o, right_q_wxyz))

        # Columns of the output table
        columns = ['epoch_time', 'corrupt_magn', 'missing_type', 'failure_type',
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
#        ind = placement_check(left_acc, hip_acc, right_acc)
        ind = 0
#        left_ind = hip_ind = right_ind = mov_ind =False
        if ind != 0:
            # rPush
#            msg = ErrorMessageSession(ind).error_message
#            r_push_data = RPushDataSession(ind).value
#            # Write to SessionAnatomicalCalibrationEvents
#            try:
#                cur.execute(quer_fail, (False, ind, is_base, file_name))
#                conn.commit()
#            except psycopg2.Error as error:
#                logger.warning("Cannot write to DB after failure!")
#                raise error


            #write to S3 and rPush
            data_calib['failure_type'] = ind
            data_pd = pd.DataFrame(data_calib)
#            f = cStringIO.StringIO()
#            data_pd.to_csv(out_file, index=False)
#            f.seek(0)
#            try:
#                S3.Bucket(cont_write).put_object(Key=out_file, Body=f)
#                cur.execute(quer_rpush, (user_id, msg, r_push_data))
#                conn.commit()
#                conn.close()
#            except boto3.exceptions as error:
#                logger.warning("Cannot write to s3 container after failure!")
#                raise error
#            except psycopg2.Error as error:
#                logger.warning("Cannot write to rpush after failure!")
#                raise error
#            else:
#                return "Fail!"
            return data_calib, offsets

        else:
            # rPush
            msg = ErrorMessageSession(ind).error_message
            r_push_data = RPushDataSession(ind).value

            ###Write to S3
            data_calib['failure_type'] = ind
            data_pd = pd.DataFrame(data_calib)
            data_pd['base_calibration'] = int(is_base)
#            f = cStringIO.StringIO()
#            data_pd.to_csv(out_file, index=False)
#            f.seek(0)
#            try:
#                S3.Bucket(cont_write).put_object(Key=out_file, Body=f)
#            except boto3.exceptions as error:
#                logger.warning("Cannot write to s3!")
#                raise error

            if is_base:
                #read from S3
#                try:
#                    obj = S3.Bucket(cont_read).Object(feet_file)
#                    fileobj = obj.get()
#                    body = fileobj["Body"].read()
#                    feet = cStringIO.StringIO(body)
#                except boto3.exceptions as error:
#                    logger.warning("Cannot read feet_sensor_data from s3!")
#                    raise error
#
#                # Read  base feet calibration data from s3
                try:
                    feet_data = np.genfromtxt(feet, dtype=float, delimiter=',',
                                              names=True)
                except IndexError:
                    print "Feet data doesn't have column names!"
#                    raise error
#                if len(feet_data) == 0:
#                    logger.warning("Feet sensor data is empty!")
                #Run base calibration
                hip_pitch_transform, hip_roll_transform,\
                lf_roll_transform, rf_roll_transform = \
                bc.run_special_calib(data_calib, feet_data)

                # check if the transform values are nan's
                if np.any(np.isnan(hip_pitch_transform)):
                    print 'Hip pitch transform has missing values.'
                elif np.any(np.isnan(hip_roll_transform)):
                    print 'Hip roll transform has missing values.'
                elif np.any(np.isnan(lf_roll_transform)):
                    print 'LF roll transform has missing values.'
                elif np.any(np.isnan(rf_roll_transform)):
                    print 'RF roll transform has missing values.'

                hip_pitch_transform = hip_pitch_transform.reshape(-1, 1)
                hip_roll_transform = hip_roll_transform.reshape(-1, 1)
                lf_roll_transform = lf_roll_transform.reshape(-1, 1)
                rf_roll_transform = rf_roll_transform.reshape(-1, 1)

                # Save base calibration offsets to
                # BaseAnatomicalCalibrationEvent along with hip_success
#                try:
#                    cur.execute(quer_spe_succ, (True, hip_pitch_transform,
#                                                hip_roll_transform,
#                                                lf_roll_transform,
#                                                rf_roll_transform,
#                                                file_name))
#                    conn.commit()
#                except psycopg2.Error as error:
#                    logger.warning("Cannot write base transform values to DB")
#                    raise error

                # Run session calibration
                hip_bf_transform, lf_bf_transform, rf_bf_transform,\
                lf_n_transform, rf_n_transform, hip_n_transform = \
                ac.run_calib(data_calib, hip_pitch_transform,
                             hip_roll_transform, lf_roll_transform,
                             rf_roll_transform)

                # Check if bodyframe and neutral transform values are nan's
                if np.any(np.isnan(hip_bf_transform)):
                    print 'Hip bodyframe transform has missing values.'
                elif np.any(np.isnan(lf_bf_transform)):
                    print 'LF bodyframe transform has missing values.'
                elif np.any(np.isnan(rf_bf_transform)):
                    print 'RF bodyframe transform has missing values.'
                elif np.any(np.isnan(lf_n_transform)):
                    print 'LF neutral transform has missing values.'
                elif np.any(np.isnan(rf_n_transform)):
                    print 'RF neutral transform has missing values.'
                elif np.any(np.isnan(hip_n_transform)):
                    print 'Hip neutral transform has missing values.'

                # Save session calibration offsets to
                # SessionAnatomicalCalibrationEvent
                # along with base_calibration=True and success=True
                hip_bf_transform = hip_bf_transform.reshape(-1, 1)
                lf_bf_transform = lf_bf_transform.reshape(-1, 1)
                rf_bf_transform = rf_bf_transform.reshape(-1, 1)
                lf_n_transform = lf_n_transform.reshape(-1, 1)
                rf_n_transform = rf_n_transform.reshape(-1, 1)
                hip_n_transform = hip_n_transform.reshape(-1, 1)

#                try:
#                    cur.execute(quer_reg_succ, (True, is_base,
#                                                hip_n_transform,
#                                                hip_bf_transform,
#                                                lf_n_transform,
#                                                lf_bf_transform,
#                                                rf_n_transform,
#                                                rf_bf_transform,
#                                                file_name))
#                    conn.commit()
#                except boto3.exceptions as error:
#                    logger.warning("Cannot write to DB after success!")
#                    raise error
#                try:
#                    cur.execute(quer_rpush, (user_id, msg, r_push_data))
#                    conn.commit()
#                    conn.close()
#
#                # rPush
#                except:
#                    logger.warning("Cannot write to rpush after succcess!")
#                    raise error
#                else:
#                    return "Success!"
                offsets = [hip_bf_transform, lf_bf_transform, \
                    rf_bf_transform, hip_n_transform, lf_n_transform, \
                    rf_n_transform, hip_pitch_transform, hip_roll_transform, \
                    lf_roll_transform, rf_roll_transform]

                return data_calib, offsets

            else:
                # Run session calibration
                hip_bf_transform, lf_bf_transform, rf_bf_transform,\
                lf_n_transform, rf_n_transform, hip_n_transform = \
                ac.run_calib(data_calib, hip_pitch_transform,
                             hip_roll_transform, lf_roll_transform,
                             rf_roll_transform)
                hip_bf_transform = hip_bf_transform.reshape(-1, 1)
                lf_bf_transform = lf_bf_transform.reshape(-1, 1)
                rf_bf_transform = rf_bf_transform.reshape(-1, 1)
                lf_n_transform = lf_n_transform.reshape(-1, 1)
                rf_n_transform = rf_n_transform.reshape(-1, 1)
                hip_n_transform = hip_n_transform.reshape(-1, 1)

                # Save session calibration offsets to
                # SessionAnatomicalCalibrationEvent
                # along with base_calibration=False and success=True
#                try:
#                    cur.execute(quer_reg_succ, (True, is_base,
#                                                hip_n_transform,
#                                                hip_bf_transform,
#                                                lf_n_transform,
#                                                lf_bf_transform,
#                                                rf_n_transform,
#                                                rf_bf_transform,
#                                                file_name))
#                    conn.commit()
#                except psycopg2.Error as error:
#                    logger.warning("Cannot write to DB after success!")
#
#                # rPush
#                try:
#                    cur.execute(quer_rpush, (user_id, msg, r_push_data))
#                    conn.commit()
#                    conn.close()
#                except:
#                    logger.warning("Cannot write to rpush after succcess!")
#                    raise error
#                else:
#                    return "Success!"

                offsets = [hip_bf_transform, lf_bf_transform, \
                    rf_bf_transform, hip_n_transform, lf_n_transform, \
                    rf_n_transform, hip_pitch_transform, hip_roll_transform, \
                    lf_roll_transform, rf_roll_transform]

                return data_calib, offsets


if __name__ == '__main__':
    path = 'Trial_8_Combined_Data.csv'
    feet_path = 'base_processed_Trial_8_Combined_Data.csv'
    result, offsets = run_calibration(path, path, feet_path)
    hip_bf_transform = offsets[0]
    lf_bf_transform = offsets[1]
    rf_bf_transform = offsets[2]
    hip_n_transform = offsets[3]
    lf_n_transform = offsets[4]
    rf_n_transform = offsets[5]
    hip_pitch_transform = offsets[6]
    hip_roll_transform = offsets[7]
    lf_roll_transform = offsets[8]
    rf_roll_transform = offsets[9]