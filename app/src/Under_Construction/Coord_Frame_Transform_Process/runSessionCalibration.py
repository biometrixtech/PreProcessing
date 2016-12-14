# -*- coding: utf-8 -*-
"""
Created on Tue Oct 18 18:30:17 2016

@author: court
"""


#import cStringIO
#import sys
#import logging

#import boto3
import numpy as np
import pandas as pd
#import psycopg2

import anatomicalCalibration as ac
#from placementCheck import placement_check
import baseCalibration as bc
import calibPrePreProcessing as cppp
from errors import ErrorMessageSession, RPushDataSession


def run_calibration(sensor_data, file_name, feet):

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

    # Read relevant information from special_anatomical_calibration_events
    # based on provided sensor_data_filename and
    # special_anatomical_calibration_event_id tied to the filename

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

        ### Write to S3
        data_calib = pd.DataFrame(data)
        data_calib['failure_type'] = ind
#        data_calib.to_csv(out_file, index=False)

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

        ind = 0
        if ind != 0:



            #write to S3 and rPush
            data_calib['failure_type'] = ind
            data_pd = pd.DataFrame(data_calib)
#            data_pd.to_csv(out_file, index=False)

            return data_pd, offsets

        else:


            ###Write to S3
            data_calib['failure_type'] = ind
            data_pd = pd.DataFrame(data_calib)
            data_pd['base_calibration'] = int(is_base)
#            data_pd.to_csv(out_file, index=False)


            if is_base:
                # Read  base feet calibration data from s3
                try:
                    feet_data = np.genfromtxt(feet, dtype=float, delimiter=',',
                                              names=True)
                except IndexError:
                    print "Feet data doesn't have column names!"

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

                offsets = [hip_bf_transform, lf_bf_transform, \
                    rf_bf_transform, hip_n_transform, lf_n_transform, \
                    rf_n_transform, hip_pitch_transform, hip_roll_transform, \
                    lf_roll_transform, rf_roll_transform]

                return data_pd, offsets

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

                offsets = [hip_bf_transform, lf_bf_transform, \
                    rf_bf_transform, hip_n_transform, lf_n_transform, \
                    rf_n_transform, hip_pitch_transform, hip_roll_transform, \
                    lf_roll_transform, rf_roll_transform]

                return data_pd, offsets


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