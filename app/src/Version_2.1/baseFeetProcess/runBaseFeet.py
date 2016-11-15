# -*- coding: utf-8 -*-
"""
Created on Tue Oct 18 15:18:54 2016

@author: court
"""
import cStringIO
import sys
import logging

import boto3
import numpy as np
import pandas as pd
import psycopg2

import prePreProcessing as ppp
import anatomicalCalibration as ac
from errors import ErrorMessageBase, RPushDataBase

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def record_special_feet(sensor_data, file_name):
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
    
    # Query to read user_id linked to the given data_filename
    quer_read = """select user_id from base_anatomical_calibration_events
                where feet_sensor_data_filename = (%s);"""

    # Two update queries for when the tests pass/fail
    quer_fail = """update base_anatomical_calibration_events set
        failure_type = (%s),
        feet_processed_sensor_data_filename = (%s),
        feet_success = (%s),
        updated_at = now()
        where feet_sensor_data_filename=(%s);"""

    quer_success = """update base_anatomical_calibration_events set
        feet_processed_sensor_data_filename = (%s),
        feet_success = (%s),
        updated_at = now()
        where feet_sensor_data_filename=(%s);"""

    quer_rpush = "select fn_send_push_notification(%s, %s, %s)"
    ###Connect to the database
    try:
        conn = psycopg2.connect("""dbname='biometrix' user='ubuntu'
        host='ec2-35-162-107-177.us-west-2.compute.amazonaws.com' 
        password='d8dad414c2bb4afd06f8e8d4ba832c19d58e123f'""")
        cur = conn.cursor()
        
        # connect to S3 bucket for uploading file
        S3 = boto3.resource('s3')
        
        # Read the user_id to be used for push notification
        cur.execute(quer_read, (file_name,))
        data_read = cur.fetchall()[0]
        user_id = data_read[0]
        if user_id is None:
            user_id = '00000000-0000-0000-0000-000000000000'
            logger.warning("user_id associated with file not found")
        
    except psycopg2.Error as error:
        logger.warning("Cannot connect to DB")
        raise error
    except boto3.exceptions as error:
        logger.warning("Cannot connect to s3")
        raise error
    except IndexError as error:
        logger.warning("feet_sensor_data_filename not found in table")
        raise error
    #define container to write processed file to
    cont_write = 'biometrix-baseanatomicalcalibrationprocessedcontainer'

    #Read data into structured numpy array
    try:
        data = np.genfromtxt(sensor_data, dtype=float, delimiter=',',
                             names=True)
    except IndexError:
        logger.info("Sensor data doesn't have column names!")
        return "Fail!"
    if len(data) == 0:
        logger.info("Sensor data is empty!")
        return "Fail!"

    out_file = "processed_" + file_name
    epoch_time = data['epoch_time']
    corrupt_magn = data['corrupt_magn']
    missing_type = data['missing_type']

    identifiers = np.array([epoch_time, corrupt_magn, missing_type]).transpose()

    # Create indicator values
    failure_type = np.array([-999]*len(data))
    indicators = np.array([failure_type]).transpose()

    # PRE-PRE-PROCESSING
    columns = ['LaX', 'LaY', 'LaZ', 'LqX', 'LqY', 'LqZ', 'HaX',
               'HaY', 'HaZ', 'HqX', 'HqY', 'HqZ', 'RaX', 'RaY', 'RaZ',
               'RqX', 'RqY', 'RqZ']

    # check for missing values for each of acceleration and quaternion values
    for var in columns:
        out, ind = ppp.handling_missing_data(epoch_time,
                                             data[var].reshape(-1, 1),
                                             corrupt_magn.reshape(-1, 1))
        data[var] = out.reshape(-1, )
        if ind in [1, 10]:
            break

    if ind != 0:
        # rpush
        msg = ErrorMessageBase(ind).error_message
        r_push_data = RPushDataBase(ind).value
        #update special_anatomical_calibration_events
        try:
            cur.execute(quer_fail, (ind, out_file, False, file_name))
            conn.commit()
        except psycopg2.Error as error:
            logger.warning("Cannot write to DB after failure!")
            raise error

        ### Write to S3
        data_feet = pd.DataFrame(data)
        data_feet['failure_type'] = ind
        f = cStringIO.StringIO()
        data_feet.to_csv(f, index=False)
        f.seek(0)
        try:
            S3.Bucket(cont_write).put_object(Key=out_file, Body=f)
            cur.execute(quer_rpush, (user_id, msg, r_push_data))
            conn.commit()
            conn.close()
        except boto3.exceptions as error:
            logger.warning("Can't write to s3 after fail!")
            raise error
        except psycopg2.Error as error:
            logger.warning("Cannot write to rpush after fail!")
            raise error
        else:
            return "Fail!"

    else:
        # determine the real quartenion
        # Left foot
        left_q_xyz = np.array([data['LqX'], data['LqY'],
                               data['LqZ']]).transpose()
        left_q_wxyz, conv_error = ppp.calc_quaternions(left_q_xyz)
        
        #check for type conversion error in left foot quaternion data
        if conv_error:
            logger.warning('Error! Type conversion error: LF quat')
            return "Fail!"

        # Hip
        hip_q_xyz = np.array([data['HqX'], data['HqY'],
                              data['HqZ']]).transpose()
        hip_q_wxyz, conv_error = ppp.calc_quaternions(hip_q_xyz)
        
        #check for type conversion error in hip quaternion data
        if conv_error:
            logger.warning('Error! Type conversion error: Hip quat')
            return "Fail!"

        # Right foot
        right_q_xyz = np.array([data['RqX'], data['RqY'],
                                data['RqZ']]).transpose()
        right_q_wxyz, conv_error = ppp.calc_quaternions(right_q_xyz)
        
        #check for type conversion error in right foot quaternion data
        if conv_error:
            logger.warning('Error! Type conversion error: RF quat')
            return "Fail!"

        #create output table as a structured numpy array
        data_o = np.hstack((identifiers, indicators))
        data_o = np.hstack((data_o, left_acc))
        data_o = np.hstack((data_o, left_q_wxyz))
        data_o = np.hstack((data_o, hip_acc))
        data_o = np.hstack((data_o, hip_q_wxyz))
        data_o = np.hstack((data_o, right_acc))
        data_o = np.hstack((data_o, right_q_wxyz))

        #Columns of the output table
        columns = ['epoch_time', 'corrupt_magn', 'missing_type', 'failure_type',
                   'LaX', 'LaY', 'LaZ', 'LqW', 'LqX', 'LqY', 'LqZ', 'HaX',
                   'HaY', 'HaZ', 'HqW', 'HqX', 'HqY', 'HqZ', 'RaX', 'RaY',
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
        ind = ac.placement_check(left_acc, hip_acc, right_acc)
#        left_ind = hip_ind = right_ind = mov_ind =False
        if ind != 0:
            # rpush
            msg = ErrorMessageBase(ind).error_message
            r_push_data = RPushDataBase(ind).value
            #update special_anatomical_calibration_events
            try:
                cur.execute(quer_fail, (ind, out_file, False, file_name))
                conn.commit()
            except psycopg2.Error as error:
                logger.warning("Cannot write to DB after failure!")
                raise error

            data_feet['failure_type'] = ind
            ### Write to S3
            data_pd = pd.DataFrame(data_feet)
            f = cStringIO.StringIO()
            data_pd.to_csv(f, index=False)
            f.seek(0)
            try:
                S3.Bucket(cont_write).put_object(Key=out_file, Body=f)
                cur.execute(quer_rpush, (user_id, msg, r_push_data))
                conn.commit()
                conn.close()
            except boto3.exceptions as error:
                logger.warning("Cannot write to s3 container after failure!")
                raise error
            except psycopg2.Error as error:
                logger.warning("Cannot write to rpush after failure!")
                raise error
            else:
                return "Fail!"

        else:
            # rpush
            msg = ErrorMessageBase(ind).error_message
            r_push_data = RPushDataBase(ind).value
            #update special_anatomical_calibration_events
            try:
                cur.execute(quer_success, (out_file, True, file_name))
                conn.commit()
            except psycopg2.Error as error:
                logger.warning("Cannot write to DB after success!")
                raise error

            data_feet['failure_type'] = ind
            ### Write to S3
            data_pd = pd.DataFrame(data_feet)
            f = cStringIO.StringIO()
            data_pd.to_csv(f, index=False)
            f.seek(0)
            try:
                S3.Bucket(cont_write).put_object(Key=out_file, Body=f)
                cur.execute(quer_rpush, (user_id, msg, r_push_data))
                conn.commit()
                conn.close()
            except boto3.exceptions as error:
                logger.info("Cannot write to s3 container after success!")
                raise error
            except psycopg2.Error as error:
                logger.info("Cannot write to rpush after success!")
                raise error
            else:
                return "Success!"


if __name__ == '__main__':
    path = 'team1_session1_trainingset_anatomicalCalibration.csv'
    result = record_special_feet(path, path)
