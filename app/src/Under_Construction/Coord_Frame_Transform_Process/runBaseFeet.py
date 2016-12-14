# -*- coding: utf-8 -*-
"""
Created on Tue Oct 18 15:18:54 2016

@author: court
"""
#import cStringIO
import sys
#import logging
#
#import boto3
import numpy as np
import pandas as pd
import psycopg2

import basePrePreProcessing as bppp
#import anatomicalCalibration as ac
from errors import ErrorMessageBase, RPushDataBase
from placementCheck import placement_check


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

    #Read data into structured numpy array
    try:
        data = np.genfromtxt(sensor_data, dtype=float, delimiter=',',
                             names=True)
    except IndexError:
        print "Sensor data doesn't have column names!"
#        return "Fail!"
    if len(data) == 0:
        print "Sensor data is empty!"
#        return "Fail!"

    out_file = "base_processed_" + file_name
    epoch_time = data['epoch_time']
    corrupt_magn = data['corrupt_magn']
    missing_type = data['missing_type']

    identifiers = np.array([epoch_time, corrupt_magn,
                            missing_type]).transpose()

    # Create indicator values
    failure_type = np.array([-999]*len(data))
    indicators = np.array([failure_type]).transpose()

    # Check for duplicate epoch time
    duplicate_epoch_time = bppp.check_duplicate_epochtime(epoch_time)
    if duplicate_epoch_time:
        print 'Duplicate epoch time.'
    
    # PRE-PRE-PROCESSING
    columns = ['LaX', 'LaY', 'LaZ', 'LqX', 'LqY', 'LqZ', 'HaX',
               'HaY', 'HaZ', 'HqX', 'HqY', 'HqZ', 'RaX', 'RaY', 'RaZ',
               'RqX', 'RqY', 'RqZ']

    # check for missing values for each of acceleration and quaternion values
    for var in columns:
        out, ind = bppp.handling_missing_data(epoch_time,
                                             data[var].reshape(-1, 1),
                                             corrupt_magn.reshape(-1, 1))
        data[var] = out.reshape(-1, )
        if ind in [1, 10]:
            break
        
        # check if nan's exist even after imputing
        if np.any(np.isnan(out)):
            print 'Bad data! NaNs exist even after imputing. \
            Column: ' , var
#            return "Fail!"

    if ind != 0:

        ### Write to S3
        data_feet = pd.DataFrame(data)
        data_feet['failure_type'] = ind
        data_feet.to_csv(out_file, index=False)


    else:
        # determine the real quartenion
        # Left foot
        left_q_xyz = np.array([data['LqX'], data['LqY'],
                               data['LqZ']]).transpose()
        left_q_wxyz, conv_error = bppp.calc_quaternions(left_q_xyz)
        
        #check for type conversion error in left foot quaternion data
        if conv_error:
            print 'Error! Type conversion error: LF quat'
#            return "Fail!"

        # Hip
        hip_q_xyz = np.array([data['HqX'], data['HqY'],
                              data['HqZ']]).transpose()
        hip_q_wxyz, conv_error = bppp.calc_quaternions(hip_q_xyz)
        
        #check for type conversion error in hip quaternion data
        if conv_error:
            print 'Error! Type conversion error: Hip quat'
#            return "Fail!"

        # Right foot
        right_q_xyz = np.array([data['RqX'], data['RqY'],
                                data['RqZ']]).transpose()
        right_q_wxyz, conv_error = bppp.calc_quaternions(right_q_xyz)
        
        #check for type conversion error in right foot quaternion data
        if conv_error:
            print 'Error! Type conversion error: RF quat'
#            return "Fail!"
            
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

        #Columns of the output table
        columns = ['epoch_time', 'corrupt_magn', 'missing_type', 'failure_type',
                   'LaX', 'LaY', 'LaZ', 'LqW', 'LqX', 'LqY', 'LqZ', 'HaX',
                   'HaY', 'HaZ', 'HqW', 'HqX', 'HqY', 'HqZ', 'RaX', 'RaY',
                   'RaZ', 'RqW', 'RqX', 'RqY', 'RqZ']

        data_o_pd = pd.DataFrame(data_o)
        data_o_pd.columns = columns

        types = [(columns[i].encode(), data_o_pd[k].dtype.type) for \
                    (i, k) in enumerate(columns)]
        dtype = np.dtype(types)
        data_feet = np.zeros(data_o.shape[0], dtype)
        for (i, k) in enumerate(data_feet.dtype.names):
            data_feet[k] = data_o[:, i]
        #Check if the sensors are placed correctly and if the subject is moving
        #around and push respective success/failure message to the user
        ind = 0        
        if ind != 0:


            data_feet['failure_type'] = ind
            ### Write to S3
            data_pd = pd.DataFrame(data_feet)
            data_pd.to_csv(out_file, index=False)

            return data_pd

        else:


            data_feet['failure_type'] = ind
            ### Write to S3
            data_pd = pd.DataFrame(data_feet)
            data_pd.to_csv(out_file, index=False)

            return data_pd


if __name__ == '__main__':
    path = 'Trial_8_Combined_Data.csv'
    result = record_special_feet(path, path)
    