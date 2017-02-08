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
#import numpy as np
import pandas as pd
import psycopg2
import psycopg2.extras
import boto3
import math
from itertools import islice, count

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
    AWS = aws
    COLUMN_SCORING_OUT = cols.column_scoring_out
    cont_write = 'biometrix-sessionprocessedcontainer'
    cont_read = 'biometrix-scoringhist'

    # Connect to the database
    conn, cur, s3 = _connect_db_s3()

    # Create a RawFrame object with initial data
#    sdata = np.genfromtxt(sensor_data, delimiter=',', names=True)
#    columns = sdata.dtype.names
    sdata = pd.read_csv(sensor_data)
    columns = sdata.columns
    data = do.RawFrame(sdata, columns)
    del sdata
    session_event_id = data.session_event_id[0]
    user_id = data.user_id[0]
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
        obj = s3.Bucket(cont_read).Object(user_id)
        fileobj = obj.get()
        body = fileobj["Body"]
#        body = fileobj["Body"].read()
#        hist_data = cStringIO.StringIO(body)
        user_hist = pd.read_csv(body)
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

    data.consistency, data.hip_consistency, \
        data.ankle_consistency, data.consistency_lf, \
        data.consistency_rf, data.symmetry, \
        data.hip_symmetry, data.ankle_symmetry, \
        data.destr_multiplier, data.dest_mech_stress, \
        data.const_mech_stress, data.block_duration, \
        data.session_duration, data.block_mech_stress_elapsed, \
        data.session_mech_stress_elapsed = score(data, user_hist)
#    del user_hist
    _logger("DONE WITH SCORING!")
    # combine into movement data table
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


def _logger(message, info=True):
    if AWS:
        if info:
            logger.info(message)
        else:
            logger.warning(message)
    else:
        print message


#def _write_table_db(movement_data, cur, conn):
#    """Update the movement table with all the scores
#    Args:
#        movement_data: numpy recarray with complete data
#        cur: cursor pointing to the current db connection
#        conn: db connection
#    Returns:
#        result: string signifying success
#    """
#    movement_data_pd = pd.DataFrame(movement_data)
#    movement_data_pd = movement_data_pd.replace('None', 'NaN')
#    fileobj_db = cStringIO.StringIO()
#    try:
#        # create a temporary table with the schema of movement table
#        cur.execute(queries.quer_create)
#        movement_data_pd.to_csv(fileobj_db, index=False, header=False,
#                                na_rep='NaN', columns=COLUMN_SCORING_OUT)
#        del movement_data_pd
#        # copy data to the empty temp table
#        fileobj_db.seek(0)
#        cur.copy_from(file=fileobj_db, table='temp_mov', sep=',', null='NaN',
#                      columns=COLUMN_SCORING_OUT)
#        del fileobj_db
#        # copy relevant columns from temp table to movement table
#        cur.execute(queries.quer_update)
#        conn.commit()
#        # drop temp table
#        cur.execute(queries.quer_drop)
#        conn.commit()
#        conn.close()
#    except Exception as error:
#        if AWS:
#            logger.warning("Cannot write movement data to DB!")
#            raise error
#        else:
#            print "Cannot write movement data to DB!"
#            return "Success!"
#    else:
#        return "Success!"
#

#def _write_table_s3(movement_data, file_name, s3, cont):
#    """write final table to s3. In case of local run, if it can't be written to
#    s3, it'll be written locally
#    """
#    movement_data_pd = pd.DataFrame(movement_data)
#    try:
#        fileobj = cStringIO.StringIO()
#        movement_data_pd.to_csv(fileobj, index=False)
#        del movement_data_pd
#        fileobj.seek(0)
#        s3.Bucket(cont).put_object(Key="movement_" + file_name, Body=fileobj)
#    except:
#        if AWS:
#            del fileobj
#            logger.warning("Cannot write movement table to s3")
#        else:
#            print "Cannot write file to s3 writing locally!"
#            movement_data_pd = pd.DataFrame(movement_data)
#            movement_data_pd.to_csv("movement_" + file_name, index=False)
#            del movement_data_pd
#

def _multipartupload_data(movement_data, file_name, cont, cur, conn, DB=True):

    # Create a multipart upload request
    s3 = boto3.client('s3')
    mp = s3.create_multipart_upload(Bucket=cont, Key=file_name)

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
            part = s3.upload_part(Bucket=cont, Key=file_name,
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
            part = s3.upload_part(Bucket=cont, Key=file_name,
                                  PartNumber=counter,
                                  UploadId=mp['UploadId'], Body=fileobj)
            Parts.append({'PartNumber':counter, 'ETag': part['ETag']})

            del fileobj
    part_info = {'Parts': Parts}
    s3.complete_multipart_upload(Bucket=cont, Key=file_name,
                                 UploadId=mp['UploadId'],
                                 MultipartUpload=part_info)


if __name__ == "__main__":
    data = 'C:\\Users\\dipesh\\Desktop\\biometrix\\aws\\7803f828-bd32-4e97-860c-34a995f08a9e_3'
    file_name = '7803f828-bd32-4e97-860c-34a995f08a9e'
    out_data = run_scoring(data, file_name, aws=False)
#    sdata = pd.read_csv(data)
    pass

