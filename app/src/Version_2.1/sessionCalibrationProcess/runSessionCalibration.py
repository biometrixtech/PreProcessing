# -*- coding: utf-8 -*-
"""
Created on Tue Oct 18 18:30:17 2016

@author: court
"""


import numpy as np
import pandas as pd
import psycopg2
import boto3
import cStringIO
import sys

import anatomicalCalibration as ac
import baseCalibration as bc
import prePreProcessing as ppp
from errors import ErrorMessageSession, RPushDataSession


def run_calibration(sensor_data, file_name):
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
    ###Connect to the database
    try:
        conn = psycopg2.connect("""dbname='biometrix' user='ubuntu' 
        host='ec2-35-162-107-177.us-west-2.compute.amazonaws.com' 
        password='d8dad414c2bb4afd06f8e8d4ba832c19d58e123f'""")
    except:
        return 'Fail! Unable to connect to database'
        sys.exit()
    cur = conn.cursor()
    
    ##Setup Queries based on different situations
    
    #Read relevant information from special_anatomical_calibration_events
    #based on provided sensor_data_filename and
    #special_anatomical_calibration_event_id tied to the filename
    quer_read = """select expired, feet_processed_sensor_data_filename,
                feet_success, hip_success, hip_pitch_transform,
                hip_roll_transform, lf_roll_transform, rf_roll_transform,
                user_id
                from base_anatomical_calibration_events where
                id = (select base_anatomical_calibration_event_id from
                        session_anatomical_calibration_events where 
                        sensor_data_filename = (%s));"""
    
    #Update anatomical_calibration_events in case the tests fail
    quer_fail = """update session_anatomical_calibration_events set 
        success = (%s),
        failure_type = (%s),
        base_calibration = (%s),
        updated_at = now()
        where sensor_data_filename=(%s);"""
    
    #For base calibration, update special_anatomical_calibration_events    
    quer_spe_succ = """update  base_anatomical_calibration_events set
                hip_success = (%s),
                hip_pitch_transform = (%s),
                hip_roll_transform = (%s),
                lf_roll_transform = (%s),
                rf_roll_transform = (%s),
                updated_at = now()
                where id  = (select base_anatomical_calibration_event_id from
                            session_anatomical_calibration_events where
                            sensor_data_filename = (%s));"""
    
    #For both base and session calibration, update
    #anatomical_calibration_events with relevant info
    #for base calibration, session calibration follows base calibration
    #for session calibration, it's independent and uses values read earlier
    quer_reg_succ = """update session_anatomical_calibration_events set
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
                        
    #execute the read query and extract relevant indicator info                    
    cur.execute(quer_read, (file_name,))
    data_read = cur.fetchall()[0]
    expired = data_read[0]
    feet_success = data_read[2]
    hip_success = data_read[3]
    user_id = data_read[8]
    
    #if not expired and feet_success is true and hip_success is true, it's
    #treated as session calibration
    #if hip_success is blank, it's treated as base calibration
    #feet_success should always be true
    #expired should be false
    if ~expired and feet_success and hip_success:
        is_base = False
    else:
        is_base = True
        
    #if it's base, we need the processed_sensor_data_filename
    #if session, we need transform values corresponding to the base calibration
    if is_base:
        feet_file = data_read[1]
    else:
        hip_pitch_transform = np.array(data_read[4]).reshape(-1,1)
        hip_roll_transform = np.array(data_read[5]).reshape(-1,1)
        lf_roll_transform = np.array(data_read[6]).reshape(-1,1)
        rf_roll_transform = np.array(data_read[7]).reshape(-1,1)
        
    #Connect to AWS S3 container
    S3 = boto3.resource('s3')
    
    #define containers to read from and write to
    cont_read = 'biometrix-baseanatomicalcalibrationprocessedcontainer'
    cont_write = 'biometrix-sessionanatomicalcalibrationprocessedcontainer' 
        
     
    #read data into numpy array
    data = np.genfromtxt(sensor_data, dtype=float, delimiter=',', names=True)
    out_file = "processed_"+ file_name    
    
    epoch_time = data['epoch_time']
    corrupt_magn = data['corrupt_magn']
    missing_type = data['missing_type']
    identifiers = np.array([epoch_time,corrupt_magn,missing_type]).transpose()
    
    # Create indicator values
    base_calibration = np.array([is_base]*len(data))
    failure_type = np.array([-999]*len(data))
    indicators = np.array([base_calibration, failure_type]).transpose()
    
        
    # PRE-PRE-PROCESSING
    columns = ['epoch_time','corrupt_magn','missing_type','base_calibration',
           'failure_type','LaX','LaY','LaZ','LqX','LqY','LqZ','HaX',
           'HaY','HaZ','HqX','HqY','HqZ','RaX','RaY','RaZ',
           'RqX','RqY','RqZ']
           
    # check for missing values for each of acceleration and quaternion values
    for var in columns[5:]:
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
    columns = ['epoch_time','corrupt_magn','missing_type','base_calibration',
               'failure_type','LaX','LaY','LaZ','LqW','LqX','LqY','LqZ','HaX',
               'HaY','HaZ','HqW','HqX','HqY','HqZ','RaX','RaY','RaZ','RqW',
               'RqX','RqY','RqZ']
    
    
    df = pd.DataFrame(data_o)
    df.columns = columns

    types = [(columns[i].encode(), df[k].dtype.type) for\
                (i, k) in enumerate(columns)]
    dtype = np.dtype(types)
    data_calib = np.zeros(data_o.shape[0], dtype)
    for (i, k) in enumerate(data_calib.dtype.names):
        data_calib[k] = data_o[:, i] 

        
    if ind != 0:
        # In anatomicalcalibrationevent, we need to write 
        # success = False
        #failure_type = 1
        #base = is_base
        #processed_filename = 'some_processed_hip_file.csv
        #where feet_sensor_data_filename=file_name
        cur.execute(quer_fail, (False, ind, is_base, file_name))
        conn.commit()
        cur.close()
        conn.close()
        
        data_calib['failure_type']= ind
            
        #write to S3
        data_pd = pd.DataFrame(data_calib)
        f = cStringIO.StringIO()
        data_pd.to_csv(f, index = False)
        f.seek(0)
        S3.Bucket(cont_write).put_object(Key=out_file, Body=f)
        
        msg = ErrorMessageSession(ind).error_message   
        r_push_data = RPushDataSession(ind).value
        #####rPush INSERT GOES HERE########
        
        return "Fail!"
        
    else:
        #Check if the sensors are placed correctly and if the subject is moving
        #around and push respective success/failure message to the user
        ind = ac.placement_check(left_acc,hip_acc,right_acc)
#        left_ind = hip_ind = right_ind = mov_ind =False
        if ind!=0:
            cur.execute(quer_fail, (False, ind, is_base,file_name))
            conn.commit()
            cur.close()
            conn.close()
            
            data_calib['failure_type']=ind
            
            #write to S3
            data_pd = pd.DataFrame(data_calib)
            f = cStringIO.StringIO()
            data_pd.to_csv(f, index = False)
            f.seek(0)
            S3.Bucket(cont_write).put_object(Key=out_file, Body=f)
            
            ### rPush
            msg = ErrorMessageSession(ind).error_message
            r_push_data = RPushDataSession(ind).value
            #####rPush INSERT GOES HERE########
            
            return "Fail!"

        else:
            data_calib['failure_type']=ind
            
            msg = ErrorMessageSession(ind).error_message
            r_push_data = RPushDataSession(ind).value
            #####rPush INSERT GOES HERE########
            
            ###Write to S3
            data_pd = pd.DataFrame(data_calib)
            data_pd['base_calibration'] = int(is_base)
            f = cStringIO.StringIO()
            data_pd.to_csv(f, index = False)
            f.seek(0)
            S3.Bucket(cont_write).put_object(Key=out_file, Body=f)
            
            ###read from BaseAnatomicalCalibrationEvent table
            ### include all the base calibration offsets if present
            ###Special true if expired = True and feet_success = True
            if is_base:
                #read from S3
                obj = S3.Bucket(cont_read).Object(feet_file)
                fileobj = obj.get()
                body = fileobj["Body"].read()
                feet = cStringIO.StringIO(body)
                
                ### Read from DB, base feet calibration data
                feet_data = np.genfromtxt(feet, dtype=float,
                                          delimiter=',', names=True)
                #Run base calibration
                hip_pitch_transform,hip_roll_transform,\
                lf_roll_transform,rf_roll_transform = \
                bc.run_special_calib(data_calib,feet_data)
                
                hip_pitch_transform = hip_pitch_transform.reshape(-1,).tolist()
                hip_roll_transform = hip_roll_transform.reshape(-1,).tolist()
                lf_roll_transform = lf_roll_transform.reshape(-1,).tolist()
                rf_roll_transform = rf_roll_transform.reshape(-1,).tolist()
                
                ###Save base calibration offsets to 
                ###SpecialAnatomicalCalibrationEvent along with hip_success
                cur.execute(quer_spe_succ, (True,hip_pitch_transform,
                                                   hip_roll_transform,
                                                   lf_roll_transform,
                                                   rf_roll_transform,
                                                   file_name))
                conn.commit()

                #Run session calibration
                hip_bf_transform,lf_bf_transform,rf_bf_transform,\
                lf_n_transform,rf_n_transform,hip_n_transform=\
                ac.run_calib(data_calib, hip_pitch_transform,hip_roll_transform,
                             lf_roll_transform,rf_roll_transform)
                             
                ##Save session calibration offsets to
                #sessionAnatomicalCalibrationEvent
                ##along with base_calibration = True and success = True
                hip_bf_transform = hip_bf_transform.reshape(-1,).tolist()
                lf_bf_transform = lf_bf_transform.reshape(-1,).tolist()
                rf_bf_transform = rf_bf_transform.reshape(-1,).tolist()
                lf_n_transform = lf_n_transform.reshape(-1,).tolist()
                rf_n_transform = rf_n_transform.reshape(-1,).tolist()
                hip_n_transform = hip_n_transform.reshape(-1,).tolist()
                
                ###Save session calibration offsets to 
                #SessionAnatomicalCalibrationEvent
                ###along with base_calibration = False and success = True   
                cur.execute(quer_reg_succ, (True,is_base,
                                                   hip_n_transform,
                                                   hip_bf_transform,
                                                   lf_n_transform,
                                                   lf_bf_transform,
                                                   rf_n_transform,
                                                   rf_bf_transform,
                                                   file_name)) 
                conn.commit()
                cur.close()
                conn.close()
                
                return "Success!"
            
            else:              
                #Run session calibration                
                hip_bf_transform,lf_bf_transform,rf_bf_transform,\
                lf_n_transform,rf_n_transform,hip_n_transform=\
                ac.run_calib(data_calib,hip_pitch_transform,hip_roll_transform,
                             lf_roll_transform,rf_roll_transform)
                hip_bf_transform = hip_bf_transform.reshape(-1,).tolist()
                lf_bf_transform = lf_bf_transform.reshape(-1,).tolist()
                rf_bf_transform = rf_bf_transform.reshape(-1,).tolist()
                lf_n_transform = lf_n_transform.reshape(-1,).tolist()
                rf_n_transform = rf_n_transform.reshape(-1,).tolist()
                hip_n_transform = hip_n_transform.reshape(-1,).tolist()
                ###Save session calibration offsets to 
                #SessionAnatomicalCalibrationEvent
                ###along with base_calibration = False and success = True   
                cur.execute(quer_reg_succ, (True,is_base,
                                                   hip_n_transform,
                                                   hip_bf_transform,
                                                   lf_n_transform,
                                                   lf_bf_transform,
                                                   rf_n_transform,
                                                   rf_bf_transform,
                                                   file_name))
                conn.commit()
                cur.close()
                conn.close() 
                
                return "Success!"

           
if __name__ =='__main__':
    path = 'team1_session1_trainingset_anatomicalCalibration.csv'
    result = run_calibration(path, path)
#    run_calibration(path)