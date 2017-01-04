# -*- coding: utf-8 -*-
"""
Created on Tue Oct 18 15:18:54 2016

@author: court
"""
import cStringIO
#import sys
import logging

import boto3
import numpy as np
import pandas as pd
import psycopg2

import prePreProcessing as ppp
#import anatomicalCalibration as ac
from errors import ErrorMessageBase, RPushDataBase
from placementCheck import placement_check
import checkProcessed as cp

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
            _logger("user_id associated with file not found", aws, False)
#            logger.warning("user_id associated with file not found")
        
    except psycopg2.Error as error:
        _logger("Cannot connect to DB", aws, False)
        raise error
    except boto3.exceptions as error:
        _logger("Cannot connect to s3", aws, False)
        raise error
    except IndexError as error:
        _logger("feet_sensor_data_filename not found in table", aws, False)
        raise error
    #define container to write processed file to
    cont_write = 'biometrix-baseanatomicalcalibrationprocessedcontainer'

    #Read data into structured numpy array
    try:
        data = np.genfromtxt(sensor_data, dtype=float, delimiter=',',
                             names=True)
    except IndexError:
        _logger("Sensor data doesn't have column names!", aws, False)
        return "Fail!"
    if len(data) == 0:
        _logger("Sensor data is empty!", aws, False)
        return "Fail!"

    # check if the raw quaternions have been converted already
    data = cp.handle_processed(data)
    
    out_file = "processed_" + file_name
    epoch_time = data['epoch_time']
    corrupt_magn = data['corrupt_magn']
    missing_type = data['missing_type']

    identifiers = np.array([epoch_time, corrupt_magn, missing_type]).transpose()

    # Create indicator values
    failure_type = np.array([-999]*len(data))
    indicators = np.array([failure_type]).transpose()

    # Check for duplicate epoch time
    duplicate_epoch_time = ppp.check_duplicate_epochtime(epoch_time)
    if duplicate_epoch_time:
        _logger('Duplicate epoch time.'. aws, False)
    
    # PRE-PRE-PROCESSING
    
    # subset for done
    subset_data = ppp.subset_data_done(old_data=data)
    
    columns = ['LaX', 'LaY', 'LaZ', 'LqX', 'LqY', 'LqZ', 'HaX',
               'HaY', 'HaZ', 'HqX', 'HqY', 'HqZ', 'RaX', 'RaY', 'RaZ',
               'RqX', 'RqY', 'RqZ']

    # check for missing values for each of acceleration and quaternion values
    for var in columns:
        out, ind = ppp.handling_missing_data(epoch_time,
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
            Column: ' + var, aws, False)
            return "Fail!"

    if ind != 0:
        # rpush
        msg = ErrorMessageBase(ind).error_message
        r_push_data = RPushDataBase(ind).value
        #update special_anatomical_calibration_events
        try:
            cur.execute(quer_fail, (ind, out_file, False, file_name))
            conn.commit()
        except psycopg2.Error as error:
            _logger("Cannot write to DB after failure!", aws, False)
            raise error

        ### Write to S3
        data_feet = pd.DataFrame(subset_data)
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
            _logger("Can't write to s3 after failure!", aws, False)
            raise error
        except psycopg2.Error as error:
            _logger("Cannot write to rpush after failure!", aws, False)
            raise error
        else:
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
        str(len_nan_real_quat), aws, False)
        
        #check for type conversion error in left foot quaternion data
        if conv_error:
            _logger('Error! Type conversion error: LF quat', aws, False)
            return "Fail!"

        # Hip
        hip_q_xyz = np.array([subset_data['HqX'], subset_data['HqY'],
                              subset_data['HqZ']]).transpose()
        hip_q_wxyz, conv_error = ppp.calc_quaternions(hip_q_xyz,
                                                      missing_type)
        len_nan_real_quat = len(np.where(np.isnan(hip_q_wxyz[:, 0]))[0])
        _logger('Bad data! Percentage of NaNs in HqW: ' +
        str(len_nan_real_quat), aws, False)
        
        #check for type conversion error in hip quaternion data
        if conv_error:
            _logger('Error! Type conversion error: Hip quat', aws, False)
            return "Fail!"

        # Right foot
        right_q_xyz = np.array([subset_data['RqX'], subset_data['RqY'],
                                subset_data['RqZ']]).transpose()
        right_q_wxyz, conv_error = ppp.calc_quaternions(right_q_xyz,
                                                        missing_type)
        len_nan_real_quat = len(np.where(np.isnan(right_q_wxyz[:, 0]))[0])
        _logger('Bad data! Percentage of NaNs in RqW: ' +
        str(len_nan_real_quat), aws, False)
        
        #check for type conversion error in right foot quaternion data
        if conv_error:
            _logger('Error! Type conversion error: RF quat', aws, False)
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
        ind = placement_check(left_acc, hip_acc, right_acc)
#        ind = 0
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
                _logger("Cannot write to DB after failure!", aws, False)
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
                _logger("Cannot write to s3 container after failure!", aws,
                        False)
                raise error
            except psycopg2.Error as error:
                _logger("Cannot write to rpush after failure!", aws, False)
                raise error
            else:
                _logger("Failed placement check!", aws, False)
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
                _logger("Cannot write to DB after success!", aws, False)
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
                _logger("Cannot write to s3 container after success!", aws)
                raise error
            except psycopg2.Error as error:
                _logger("Cannot write to rpush after success!", aws)
                raise error
            else:
                return "Success!"

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
    result = record_base_feet(path, path, aws=False)
