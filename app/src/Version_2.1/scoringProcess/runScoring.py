# -*- coding: utf-8 -*-
"""
Created on Tues Nov 29 13:45:56 2016

@author: dipesh

Execution script to run scoring. Takes movement quality features and performance
variables and returns scores for control, symmetry and consistency of movement.

Input data:
MQF and PV: tbd
historical MQF and PV: from s3 container (to be changed later)

Output data stored in TrainingEvents or BlockEvents table.

"""
#import sys
import cStringIO
import logging
import os
#import numpy as np
import pandas as pd
import psycopg2
import psycopg2.extras
import boto3
import math
from itertools import islice, count
from base64 import b64decode

from controlScore import control_score
from scoring import score
#import createTables as ct
import dataObject as do
import scoringProcessQueries as queries
import columnNames as cols

logger = logging.getLogger()
psycopg2.extras.register_uuid()


def run_scoring(sensor_data, file_name, aws=True):
    """Creates object attributes according to block analysis process.

    Args:
        sensor_data: Processed data that's output of sessionProcess.
        file_name: sensor_data_filename associated with the data in DB
        aws: Boolean indicator for aws/local run

    Returns:
        result: string signifying success or failure.
        Note: In case of completion for local run, returns movement table.
    """
    global AWS
    global COLUMN_SCORING_OUT
    global KMS
    global SUB_FOLDER
    AWS = aws
    COLUMN_SCORING_OUT = cols.column_scoring_out
    KMS = boto3.client('kms')
    # Read encrypted subfolder name
    sub_folder = os.environ['sub_folder']
#    cont_read = os.environ['cont_read']
#    cont_write = os.environ['cont_write']

    # Decrypt container names
#    cont_read = KMS.decrypt(CiphertextBlob=b64decode(cont_read))['Plaintext']
#    cont_write = KMS.decrypt(CiphertextBlob=b64decode(cont_write))['Plaintext']
    cont_write = 'biometrix-sessionprocessedcontainer'
    cont_read = 'biometrix-scoringhist'
    SUB_FOLDER = KMS.decrypt(CiphertextBlob=b64decode(sub_folder))['Plaintext']+'/'
    _logger(SUB_FOLDER)

    # Connect to the database
    conn, cur, s3 = _connect_db_s3()

    # Create a RawFrame object with initial data
#    sdata = np.genfromtxt(sensor_data, delimiter=',', names=True)
#    columns = sdata.dtype.names
    sdata = pd.read_csv(sensor_data)
    columns = sdata.columns
    data = do.RawFrame(sdata, columns)
    del sdata
    session_event_id = data.session_event_id[0][0]
    user_id = data.user_id[0][0]
    # CONTROL SCORE
    data.control, data.hip_control, data.ankle_control, data.control_lf,\
            data.control_rf = control_score(data.LeX, data.ReX, data.HeX,
                                            data.ms_elapsed, data.phase_lf,
                                            data.phase_rf)

    _logger('DONE WITH CONTROL SCORES!')

    # SCORING
    # Symmetry, Consistency, Destructive/Constructive Multiplier and
    # Duration
    # At this point we need to load the historical data for the subject

    # read historical data
    try:
        objs = list(s3.Bucket(cont_read).objects.filter(Prefix=SUB_FOLDER+user_id))
        if len(objs) == 1:
            obj = s3.Bucket(cont_read).Object(SUB_FOLDER+user_id)
            fileobj = obj.get()
            body = fileobj["Body"]
            user_hist = pd.read_csv(body)
            user_hist.columns = cols.columns_hist
        elif len(data.LeX) > 50000:
            user_hist = data
        else:
            _logger("There's no historical data and current data isn't long enough!")
            # Can't complete scoring, delete data from movement table and exit
            cur.execute(queries.quer_delete, (session_event_id, ))
            conn.commit()
            conn.close()
            return "Fail!"
    except Exception as error:
        if AWS:
            _logger("Cannot read historical user data from s3!", info=False)
            raise error
        else:
            try:
                user_hist = pd.read_csv("user_hist.csv")
            except:
                raise IOError("User history not found in s3/local directory")

    _logger("user history captured")

    mech_stress_scale = 1000000
    data.consistency, data.hip_consistency, \
        data.ankle_consistency, data.consistency_lf, \
        data.consistency_rf, data.symmetry, \
        data.hip_symmetry, data.ankle_symmetry, \
        data.destr_multiplier, data.dest_mech_stress, \
        data.const_mech_stress, data.block_duration, \
        data.session_duration, data.block_mech_stress_elapsed, \
        data.session_mech_stress_elapsed = score(data, user_hist,
                                                 mech_stress_scale)
#    del user_hist
    _logger("DONE WITH SCORING!")
    # combine into movement data table
    data.mech_stress = data.mech_stress/mech_stress_scale
    movement_data = pd.DataFrame(data={'team_id': data.team_id.reshape(-1, ),
                                       'user_id': data.user_id.reshape(-1, ),
                                       'session_event_id': data.session_event_id.reshape(-1, ),
                                       'session_type': data.session_type.reshape(-1, )})

    for var in COLUMN_SCORING_OUT[2:]:
        frame = pd.DataFrame(data={var: data.__dict__[var].reshape(-1, )},
                                   index=movement_data.index)
        frames = [movement_data, frame]
        movement_data = pd.concat(frames, axis=1)
        del frame, frames, data.__dict__[var]

#    movement_data = ct.create_movement_table(len(data.LaX), data)
    _logger("table created")
    del data
    # write to s3 and db in parts
    file_name = "movement_"+file_name
    try:
        _multipartupload_data(movement_data, file_name, cont_write, cur, conn)
    except Exception as error:
        conn.close()
        raise error
    else:
        cur.execute(queries.quer_update_session_events, (session_event_id,))
        conn.commit()
        conn.close()
    # write to s3 container
#    _write_table_s3(movement_data, file_name, s3, cont_write)
    _logger("DONE WRITING TO S3 and DB")
    # write table to DB
#    result = _write_table_db(movement_data, cur, conn)
#    _logger("DONE writing to DB")

#    return result
    return "Success!"


def _connect_db_s3():
    """Start a connection to the database and to s3 resource.
    """
    # Read encrypted environment variables for db connection
    db_name = os.environ['db_name']
    db_host = os.environ['db_host']
    db_username = os.environ['db_username']
    db_password = os.environ['db_password']

    # Decrypt the variables
    db_name = KMS.decrypt(CiphertextBlob=b64decode(db_name))['Plaintext']
    db_host = KMS.decrypt(CiphertextBlob=b64decode(db_host))['Plaintext']
    db_username = KMS.decrypt(CiphertextBlob=b64decode(db_username))['Plaintext']
    db_password = KMS.decrypt(CiphertextBlob=b64decode(db_password))['Plaintext']

    try:
        conn = psycopg2.connect(dbname=db_name, user=db_username, host=db_host,
                                password=db_password)
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


def _logger(message, info=True):
    if AWS:
        if info:
            logger.info(message)
        else:
            logger.warning(message)
    else:
        print message


def _multipartupload_data(movement_data, file_name, cont, cur, conn, DB=True):

    # Create a multipart upload request
    s3 = boto3.client('s3')
    mp = s3.create_multipart_upload(Bucket=cont, Key=SUB_FOLDER+file_name)

    # Use only a set of rows each time to write to fileobj
    rows_set_size = 200000  # number of rows durin each batch upload
    number_of_rows = len(movement_data)
    rows_set_count = int(math.ceil(number_of_rows/float(rows_set_size)))
#    _logger('number of parts to be uploaded' + str(rows_set_count))
    _logger('Number of parts to be uploaded: '+ str(rows_set_count))
    
    # Initialize counter to the count number of parts uploaded in the loop below
    counter = 0
    # Send the file parts, using FileChunkIO to create a file-like object
    for i in islice(count(), 0, number_of_rows,  rows_set_size):
        counter = counter + 1
        movement_data_subset = movement_data.iloc[i:i+rows_set_size]
        _logger('length of subset: '+str(len(movement_data_subset)))
#        print len(movement_data_subset), ': length of subset'
        fileobj = cStringIO.StringIO()
        if counter == 1:
            if DB:
                # Write first part to DB
                fileobj = cStringIO.StringIO()
                movement_data_subset.to_csv(fileobj, index=False, header=False,
                                            na_rep='', columns=COLUMN_SCORING_OUT)
                cur.execute(queries.quer_create)
                # copy data to the empty temp table
                fileobj.seek(0)
                cur.copy_from(file=fileobj, table='temp_mov', sep=',', null='',
                              columns=COLUMN_SCORING_OUT)
                # copy relevant columns from temp table to movement table
                cur.execute(queries.quer_update)
                conn.commit()
                # drop temp table
                cur.execute(queries.quer_drop)
                conn.commit()
                del fileobj

            # Write first part to s3
            fileobj = cStringIO.StringIO()
            movement_data_subset.to_csv(fileobj, index=False, na_rep='',
                                        columns=COLUMN_SCORING_OUT)
            del movement_data_subset
            fileobj.seek(0)
            part = s3.upload_part(Bucket=cont, Key=SUB_FOLDER+file_name,
                                  PartNumber=counter,
                                  UploadId=mp['UploadId'], Body=fileobj)
            Parts = [{'PartNumber':counter, 'ETag': part['ETag']}]
            del fileobj
    
        else:
            fileobj = cStringIO.StringIO()
            movement_data_subset.to_csv(fileobj, index=False, header=False,
                                        na_rep='', columns=COLUMN_SCORING_OUT)
            del movement_data_subset
            if DB:
                # Write to DB
                cur.execute(queries.quer_create)
                # copy data to the empty temp table
                fileobj.seek(0)
                cur.copy_from(file=fileobj, table='temp_mov', sep=',', null='',
                              columns=COLUMN_SCORING_OUT)
                # copy relevant columns from temp table to movement table
                cur.execute(queries.quer_update)
                conn.commit()
                # drop temp table
                cur.execute(queries.quer_drop)
                conn.commit()
            # Write to s3
            fileobj.seek(0)
            part = s3.upload_part(Bucket=cont, Key=SUB_FOLDER+file_name,
                                  PartNumber=counter,
                                  UploadId=mp['UploadId'], Body=fileobj)
            Parts.append({'PartNumber':counter, 'ETag': part['ETag']})

            del fileobj
    part_info = {'Parts': Parts}
    s3.complete_multipart_upload(Bucket=cont, Key=SUB_FOLDER+file_name,
                                 UploadId=mp['UploadId'],
                                 MultipartUpload=part_info)


if __name__ == "__main__":
    data = 'C:\\Users\\dipesh\\Desktop\\biometrix\\aws\\7803f828-bd32-4e97-860c-34a995f08a9e_3'
    file_name = '7803f828-bd32-4e97-860c-34a995f08a9e'
    out_data = run_scoring(data, file_name, aws=False)
#    sdata = pd.read_csv(data)
    pass

