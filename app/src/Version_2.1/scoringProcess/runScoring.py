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

from controlScore import control_score
from scoring import score
import createTables as ct
import dataObject as do
import scoringProcessQueries as queries
from columnNames import column_scoring_out

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
    COLUMN_SCORING_OUT = column_scoring_out
    cont_write = 'biometrix-sessionprocessedcontainer'
    cont_read = 'biometrix-scoringcontainer'

    # Connect to the database
    conn, cur, s3 = _connect_db_s3()

    # Create a RawFrame object with initial data
#    sdata = np.genfromtxt(sensor_data, delimiter=',', names=True)
#    columns = sdata.dtype.names
    sdata = pd.read_csv(sensor_data)
    columns = sdata.columns
    data = do.RawFrame(sdata, columns)
    del sdata
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
        obj = s3.Bucket(cont_read).Object('user_hist.csv')
        fileobj = obj.get()
        body = fileobj["Body"].read()
        hist_data = cStringIO.StringIO(body)
        user_hist = pd.read_csv(hist_data)
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
    del user_hist
    _logger("DONE WITH SCORING!")
    # combine into movement data table
    movement_data = ct.create_movement_data(len(data.LaX), data)
    del data
    # write to s3 container
    _write_table_s3(movement_data, file_name, s3, cont_write)
    _logger("DONE WRITING TO S3")
    # write table to DB
    result = _write_table_db(movement_data, cur, conn)
    _logger("DONE WITH SCORING PROCESS")

    return result


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


def _write_table_db(movement_data, cur, conn):
    """Update the movement table with all the scores
    Args:
        movement_data: numpy recarray with complete data
        cur: cursor pointing to the current db connection
        conn: db connection
    Returns:
        result: string signifying success
    """
    movement_data_pd = pd.DataFrame(movement_data)
    movement_data_pd = movement_data_pd.replace('None', 'NaN')
    fileobj_db = cStringIO.StringIO()
    try:
        # create a temporary table with the schema of movement table
        cur.execute(queries.quer_create)
        movement_data_pd.to_csv(fileobj_db, index=False, header=False,
                                na_rep='NaN', columns=COLUMN_SCORING_OUT)
        del movement_data_pd
        # copy data to the empty temp table
        fileobj_db.seek(0)
        cur.copy_from(file=fileobj_db, table='temp_mov', sep=',', null='NaN',
                      columns=COLUMN_SCORING_OUT)
        del fileobj_db
        # copy relevant columns from temp table to movement table
        cur.execute(queries.quer_update)
        conn.commit()
        # drop temp table
        cur.execute(queries.quer_drop)
        conn.commit()
        conn.close()
    except Exception as error:
        if AWS:
            logger.warning("Cannot write movement data to DB!")
            raise error
        else:
            print "Cannot write movement data to DB!"
            return "Success!"
    else:
        return "Success!"


def _write_table_s3(movement_data, file_name, s3, cont):
    """write final table to s3. In case of local run, if it can't be written to
    s3, it'll be written locally
    """
    movement_data_pd = pd.DataFrame(movement_data)
    try:
        fileobj = cStringIO.StringIO()
        movement_data_pd.to_csv(fileobj, index=False)
        del movement_data_pd
        fileobj.seek(0)
        s3.Bucket(cont).put_object(Key="movement_" + file_name, Body=fileobj)
    except:
        if AWS:
            del fileobj
            logger.warning("Cannot write movement table to s3")
        else:
            print "Cannot write file to s3 writing locally!"
            movement_data_pd = pd.DataFrame(movement_data)
            movement_data_pd.to_csv("movement_" + file_name, index=False)
            del movement_data_pd


if __name__ == "__main__":
    file_name = '9f08e748-ceeb-42bf-a00a-29e465358def'
    data = '9f08e748-ceeb-42bf-a00a-29e465358def'
    out_data = run_scoring(data, file_name, aws=False)
#    sdata = pd.read_csv(data)
    pass

