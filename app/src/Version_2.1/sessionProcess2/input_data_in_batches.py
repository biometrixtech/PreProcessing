# -*- coding: utf-8 -*-
"""
Created on Fri Jan 27 07:40:55 2017

@author: ankurmanikandan
"""

import logging
import math
import cStringIO
import pickle

import pandas as pd
import numpy as np
import boto3
import psycopg2
import psycopg2.extras

import columnNames as cols
import sessionProcessQueries as queries
import runAnalytics as ra

logger = logging.getLogger()
psycopg2.extras.register_uuid()


def send_batches_of_data(sensor_data, file_name, aws=True):
    
    global AWS
    global COLUMN_SESSION2_OUT
    global COLUMN_SESSION2_TO_DB
    global COLUMN_SESSION2_TO_S3
    AWS = aws
    COLUMN_SESSION2_OUT = cols.column_session2_out
    COLUMN_SESSION2_TO_DB = cols.column_session2_to_DB
    COLUMN_SESSION2_TO_S3 = cols.column_session2_to_s3
    _logger("STARTED PROCESSING!")
    # Define container to which final output data must be written
    cont_write_final = 'biometrix-scoringcontainer'
    
    # Define container that holds models
    cont_models = 'biometrix-globalmodels'
    
    # connect to DB and s3
    conn, cur, s3 = _connect_db_s3()

    # Mechanical Stress            
    # load model
    try:
        ms_obj = s3.Bucket(cont_models).Object('ms_trainmodel.pkl')
        ms_fileobj = ms_obj.get()
        ms_body = ms_fileobj["Body"].read()

        # we're reading the first model on the list, there are multiple
        mstress_fit = pickle.loads(ms_body)
        del ms_body
        del ms_fileobj
        del ms_obj
    except Exception as error:
        if AWS:
            _logger("Cannot load MS model from s3!", info=False)
            raise error
        else:
            try:
                with open('ms_trainmodel.pkl') as model_file:
                    mstress_fit = pickle.load(model_file)
            except:
                raise IOError("MS model file not found in s3/local directory")

    # read sensor data
    try:
        sdata = pd.read_csv(sensor_data)
        del sensor_data
    except:
        _logger("Sensor data doesn't have column names!", info=False)
        return "Fail!"
    if len(sdata) == 0:
        _logger("Sensor data is empty!", info=False)
        return "Fail!"
    _logger("DATA LOADED!")
    #_logger(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    # read user mass 
    user_id = sdata['user_id'][0]
    try:
        cur.execute(queries.quer_read_mass, (user_id,))
        mass = cur.fetchall()[0][0]
    except psycopg2.Error as error:
        _logger("Cannot read user's mass", info=False)
        raise error
    else:
        if mass is None:
            mass = 60

    # number of rows to pass in each batch & number of parts being passed to
    # runAnalytics
    batch_size = 200000
    size = len(sdata)
    batches = int(math.ceil(size/float(batch_size)))
    _logger('number of batches of input data: '+ str(batches))
    sdata['obs_master_index'] = np.array(range(size)).reshape(-1, 1) + 1
#    return sdata  
    # Initialize counter to the count number of parts uploaded in the loop below
    counter = 0

    # looping through each batch of the data file
    s3 = boto3.client('s3')
    mp = s3.create_multipart_upload(Bucket=cont_write_final, Key=file_name)
    for i in range(batches):
        counter += 1
        subset_size = min([len(sdata), batch_size])
        input_data_batch = sdata.iloc[0:subset_size]
        if counter == batches:
            del sdata
        else:
            sdata = sdata.drop(sdata.index[range(subset_size)])
        input_data_batch = input_data_batch.reset_index(drop=True)
        _logger('passing batch ' + str(counter) + ' to runAnalytics')
        _logger(input_data_batch.shape)
        output_data_batch = ra.run_session(input_data_batch, file_name,
                                           mass, mstress_fit, AWS)
        _logger('batch ' + str(counter) + ' processed')
        del input_data_batch  # not used in further computations
        try:
            output_data_batch = output_data_batch.replace('None', '')
            output_data_batch = output_data_batch.replace(-2147483648, '')
            output_data_batch = output_data_batch.replace(-9223372036854775808, '')
            if counter == 1:
                # Write to DB
                cur.execute(queries.quer_create)
                fileobj = cStringIO.StringIO()
                output_data_batch.to_csv(fileobj, index=False, header=False,
                                   na_rep='', columns=COLUMN_SESSION2_TO_DB)
                # copy data to the empty temp table
                fileobj.seek(0)
                cur.copy_from(file=fileobj, table='temp_mov', sep=',', null='',
                              columns=COLUMN_SESSION2_TO_DB)
                # copy relevant columns from temp table to movement table
                cur.execute(queries.quer_update)
                conn.commit()
                # drop temp table
                cur.execute(queries.quer_drop)
                conn.commit()
                del fileobj
    
                # Write first part to s3
                fileobj = cStringIO.StringIO()
                output_data_batch.to_csv(fileobj, index=False, na_rep='',
                                   columns=COLUMN_SESSION2_TO_S3)
                del output_data_batch
                fileobj.seek(0)
                part = s3.upload_part(Bucket=cont_write_final, Key=file_name,
                                      PartNumber=counter,
                                      UploadId=mp['UploadId'], Body=fileobj)
                Parts = [{'PartNumber':counter, 'ETag': part['ETag']}]
                del fileobj
            else:
                # Write to DB
                cur.execute(queries.quer_create)
                fileobj = cStringIO.StringIO()
                output_data_batch.to_csv(fileobj, index=False, header=False,
                                   na_rep='', columns=COLUMN_SESSION2_TO_DB)
                # copy data to the empty temp table
                fileobj.seek(0)
                cur.copy_from(file=fileobj, table='temp_mov', sep=',', null='',
                              columns=COLUMN_SESSION2_TO_DB)
                # copy relevant columns from temp table to movement table
                cur.execute(queries.quer_update)
                conn.commit()
                # drop temp table
                cur.execute(queries.quer_drop)
                conn.commit()
                del fileobj

                # Write part to s3
                fileobj = cStringIO.StringIO()
                output_data_batch.to_csv(fileobj, index=False, header=False,
                                   na_rep='', columns=COLUMN_SESSION2_TO_S3)
                del output_data_batch
                fileobj.seek(0)
                part = s3.upload_part(Bucket=cont_write_final, Key=file_name,
                                      PartNumber=counter,
                                      UploadId=mp['UploadId'], Body=fileobj)
                Parts.append({'PartNumber':counter, 'ETag': part['ETag']})
                del fileobj
        except Exception as error:
            conn.close()
            raise error
        _logger('Completed uploading part: '+str(counter))

#        output_data = output_data.append(output_data_batch, ignore_index=True)
#        del output_data_batch  # not used in further computations
    conn.close()
    if counter == batches:
        _logger('Processing through runAnalytics was a SUCCESS!')
    else:
        _logger('Processing through runAnalytics FAILED!')        
    # Write to S3 and DB
    part_info = {'Parts': Parts}
    s3.complete_multipart_upload(Bucket=cont_write_final, Key=file_name,
                                 UploadId=mp['UploadId'],
                                 MultipartUpload=part_info)

    _logger("Data in S3 and DB!")
    #_logger(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)

    return "Success!"
    
def _logger(message, info=True):
    if AWS:
        if info:
            logger.info(message)
        else:
            logger.warning(message)
    else:
        print message
        
def _connect_db_s3():
    """Start a connection to the database and to s3 resource.
    """
    try:
        conn = psycopg2.connect("""dbname='biometrix' user='ubuntu'
        host='ec2-35-162-107-177.us-west-2.compute.amazonaws.com'
        password='d8dad414c2bb4afd06f8e8d4ba832c19d58e123f'""")
        cur = conn.cursor()
        # Connect to AWS s3 container
        s3 = boto3.resource('s3')
    except psycopg2.Error as error:
        logger.warning("Cannot connect to DB")
        raise error
    except boto3.exceptions as error:
        logger.warning("Cannot connect to s3!")
        raise error
    else:
        return conn, cur, s3

def _read_ids(cur, file_name):
    '''Read relevant ids from database and assign zeros if not found
    Args:
        cur: connection cursor
        file_name: sensor data filename to lookup ids by
    Returns:
        A single list with the following elements in order
        session_event_id: uuid
        training_session_log_id: uuid
        user_id: uuid
        team_regimen_id: uuid
        team_id: uuid
        session_type: integer, should be 1
    '''
    dummy_uuid = '00000000-0000-0000-0000-000000000000'
    try:
        cur.execute(queries.quer_read_ids, (file_name,))
        ids = cur.fetchall()[0]
    except psycopg2.Error as error:
        if AWS:
            logger.warning("Error reading ids!")
            raise error
        else:
            print "Couldn't read ids, assigning dummy"
            session_event_id = dummy_uuid
            training_session_log_id = dummy_uuid
            user_id = dummy_uuid
            team_regimen_id = dummy_uuid
            team_id = dummy_uuid
            session_type = 1
            
    except IndexError:
        if AWS:
            logger.warning("sensor_data_filename not found in DB!")
            raise IndexError
        else:
            print "sensor_data_filename not found in DB! assigning dummy uuid"
            session_event_id = dummy_uuid
            training_session_log_id = dummy_uuid
            user_id = dummy_uuid
            team_regimen_id = dummy_uuid
            team_id = dummy_uuid
            session_type = 1
    else:
        session_event_id = ids[0]
#        if session_event_id is None:
#            session_event_id = dummy_uuid
        training_session_log_id = ids[1]
#        if training_session_log_id is None:
#            training_session_log_id = dummy_uuid
        user_id = ids[2]
#        if user_id is None:
#            user_id = dummy_uuid
        team_regimen_id = ids[3]
#        if team_regimen_id is None:
#            team_regimen_id = dummy_uuid
        team_id = ids[4]
#        if team_id is None:
#            team_id = dummy_uuid
        session_type = ids[5]
        if session_type == 'practice':
            session_type = 1
        elif session_type == 'strength_training':
            session_type = 2
        elif session_type == 'return_to_play':
            session_type = 3
        elif session_type is None:
            session_type = 1

    return (session_event_id, training_session_log_id, user_id, team_regimen_id,
            team_id, session_type)
            
def _read_offsets(cur, session_event_id):
    '''Read the offsets for coordinateframe transformation.
    
    If it's in aws lambda, try to find offsets in DB and raise
    appropriate error,
    If it's a local run for testing, look for associated offsets in DB
    first, if not found, check local memory to see if the offset values
    are stored. If both these fail, ValueError is raised.
    '''
    try:
        cur.execute(queries.quer_read_offsets, (session_event_id,))
        offsets_read = cur.fetchall()[0]
    except psycopg2.Error as error:
        
        if AWS:
            logger.warning("Cannot read transform offsets!")
            raise error
        else:
            try:
                # these should be the offsets calculated by separate runs of 
                # calibration script. If not found, load some random values
                offsets_read = (hip_n_transform, hip_bf_transform,
                                lf_n_transform, lf_bf_transform,
                                rf_n_transform, rf_bf_transform)
            except NameError:
                raise ValueError("No associated offset values found in "+
                                 "the database or local memory")           
    except IndexError as error:
        if AWS:
            logger.warning("Transform offsets cannot be found!")
            raise error
        else:
            try:
                # these should be the offsets calculated by separate runs of 
                # calibration script. If not found, load some random values
                offsets_read = (hip_n_transform, hip_bf_transform,
                                lf_n_transform, lf_bf_transform,
                                rf_n_transform, rf_bf_transform)
            except NameError:
                raise ValueError("No associated offset values found in "+
                                 "the database or local memory")
#                offsets_read = dummy_offsets   
    return offsets_read
        
#%%
if __name__ == "__main__":
    sensor_data = 'c4ed8189-6e1d-47c3-9cc5-446329b10796'
    file_name = 'c4ed8189-6e1d-47c3-9cc5-446329b10796'
    result = send_batches_of_data(sensor_data, file_name, aws=False)