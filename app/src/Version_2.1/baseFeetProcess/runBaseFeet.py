# -*- coding: utf-8 -*-
"""
Created on Tue Oct 18 15:18:54 2016

@author: court
"""

import numpy as np
import pandas as pd
import psycopg2
import boto3
import cStringIO
import sys

import prePreProcessing as ppp
import anatomicalCalibration as ac
from errors import ErrorMessageBase, RPushDataBase


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
    ###Connect to the database
    try:
        conn = psycopg2.connect("""dbname='biometrix' user='paul' 
        host='ec2-52-36-42-125.us-west-2.compute.amazonaws.com' 
        password='063084cb3b65802dbe01030756e1edf1f2d985ba'""")
    except:
        return 'Fail! Unable to connect to database'
        sys.exit()
    
    cur = conn.cursor()
    
    #Query to read user_id linked to the given data_filename
    quer_read = """select user_id from base_anatomical_calibration_events
                where feet_sensor_data_filename = (%s);"""
                
    ##Two update queries for when the tests pass/fail
    quer_fail = """update base_anatomical_calibration_events set 
        failure_type = (%s),
        feet_processed_sensor_data_filename = (%s),
        feet_success = (%s)
        where feet_sensor_data_filename=(%s);"""

    quer_success = """update base_anatomical_calibration_events set
        feet_processed_sensor_data_filename = (%s),
        feet_success = (%s)
        where feet_sensor_data_filename=(%s);"""
        
    #Read the user_id to be used for push notification
    cur.execute(quer_read, (file_name,))
    data_read = cur.fetchall()[0]
    user_id = data_read[0]
    
    #connect to S3 bucket for uploading file
    S3 = boto3.resource('s3')
    #define container to write processed file to
    cont_write = 'biometrix-specialanatomicalcalibrationprocessedcontainer'    
    
    #Read data into structured numpy array
    data = np.genfromtxt(sensor_data, dtype=float, delimiter=',', names=True)
    
    out_file = "processed_"+ file_name
    epoch_time = data['epoch_time']
    corrupt_magn = data['corrupt_magn']
    missing_type = data['missing_type']
    identifiers = np.array([epoch_time,corrupt_magn,missing_type]).transpose()
    
    # Create indicator values
    failure_type = np.array([-999]*len(data))
    indicators = np.array([failure_type]).transpose()
    
        
    # PRE-PRE-PROCESSING
    columns = ['LaX','LaY','LaZ','LqX','LqY','LqZ','HaX',
           'HaY','HaZ','HqX','HqY','HqZ','RaX','RaY','RaZ',
           'RqX','RqY','RqZ']
           
        # check for missing values for each of acceleration and quaternion values
    for var in columns:
        out, ind = ppp.handling_missing_data(epoch_time,
                                               data[var].reshape(-1,1),
                                                corrupt_magn.reshape(-1,1))      
        data[var] = out.reshape(-1,)        
        if ind in [1,2]:
            break
      
    # determine the real quartenion
    # Left foot
    left_q_xyz = np.array([data['LqX'], data['LqY'], data['LqZ']]).transpose()
    left_q_wxyz = ppp.calc_quaternions(left_q_xyz)
    
    # Hip
    hip_q_xyz = np.array([data['HqX'], data['HqY'], data['HqZ']]).transpose()
    hip_q_wxyz = ppp.calc_quaternions(hip_q_xyz)
    
    # Right foot
    right_q_xyz = np.array([data['RqX'], data['RqY'], data['RqZ']]).transpose()
    right_q_wxyz = ppp.calc_quaternions(right_q_xyz)
    
    #Acceleration
    left_acc = np.array([data['LaX'],data['LaY'],data['LaZ']]).transpose()
    hip_acc = np.array([data['HaX'],data['HaY'],data['HaZ']]).transpose()
    right_acc = np.array([data['RaX'],data['RaY'],data['RaZ']]).transpose()
            
    #create output table as a structured numpy array    
    data_o = np.hstack((identifiers,indicators))
    data_o = np.hstack((data_o, left_acc))
    data_o = np.hstack((data_o,left_q_wxyz))
    data_o = np.hstack((data_o, hip_acc))
    data_o = np.hstack((data_o, hip_q_wxyz))
    data_o = np.hstack((data_o, right_acc))
    data_o = np.hstack((data_o, right_q_wxyz))
    
    #Columns of the output table
    columns = ['epoch_time','corrupt_magn','missing_type','failure_type',
               'LaX','LaY','LaZ','LqW','LqX','LqY','LqZ','HaX',
               'HaY','HaZ','HqW','HqX','HqY','HqZ','RaX','RaY','RaZ','RqW',
               'RqX','RqY','RqZ']
    
    df = pd.DataFrame(data_o)
    df.columns = columns

    types = [(columns[i].encode(), df[k].dtype.type) for\
                (i, k) in enumerate(columns)]
    dtype = np.dtype(types)
    data_feet = np.zeros(data_o.shape[0], dtype)
    for (i, k) in enumerate(data_feet.dtype.names):
        data_feet[k] = data_o[:, i] 

        
    if ind != 0:
        #update special_anatomical_calibration_events
        cur.execute(quer_fail, (1, out_file, False,file_name,))
        conn.commit()
        cur.close()
        conn.close()
        
        data_feet['failure_type']=ind
        ### Write to S3
        data_pd = pd.DataFrame(data_feet)
        f = cStringIO.StringIO()
        data_pd.to_csv(f, index = False)
        f.seek(0)
        S3.Bucket(cont_write).put_object(Key=out_file, Body=f)
        
        #rpush
        msg = ErrorMessageBase(ind).error_message
        r_push_data = RPushDataBase(ind).value
        #####rPUSH INSERT GOES HERE#######
        
        return "Fail!"
        
    else:
        #Check if the sensors are placed correctly and if the subject is moving
        #around and push respective success/failure message to the user
        ind = ac.placement_check(left_acc,hip_acc,right_acc)
#        left_ind = hip_ind = right_ind = mov_ind =False
        if ind!=0:
            #update special_anatomical_calibration_events
            cur.execute(quer_fail, (ind, out_file, False,file_name,))
            conn.commit()
            cur.close()
            conn.close()
            
            data_feet['failure_type']=ind
            ### Write to S3
            data_pd = pd.DataFrame(data_feet)
            f = cStringIO.StringIO()
            data_pd.to_csv(f, index = False)
            f.seek(0)
            S3.Bucket(cont_write).put_object(Key=out_file, Body=f)
            
            ### rPush
            msg = ErrorMessageBase(ind).error_message
            r_push_data = RPushDataBase(ind).value
            #####rPUSH INSERT GOES HERE#######
            
            return "Fail!"
            
        else:
            #update special_anatomical_calibration_events
            cur.execute(quer_success, (out_file, True,file_name,))
            conn.commit()
            cur.close()
            conn.close()
            
            data_feet['failure_type'] = ind
            ### Write to S3
            data_pd = pd.DataFrame(data_feet)
            f = cStringIO.StringIO()
            data_pd.to_csv(f, index = False)
            f.seek(0)
            S3.Bucket(cont_write).put_object(Key=out_file, Body=f)
            
            #rPush            
            msg = ErrorMessageBase(ind).error_message
            r_push_data = RPushDataBase(ind).value
            #####rPUSH INSERT GOES HERE#######
            
            return "Success!"
            
            
if __name__ =='__main__':
    path = 'team1_session1_trainingset_anatomicalCalibration.csv'
    result = record_special_feet(path, path)