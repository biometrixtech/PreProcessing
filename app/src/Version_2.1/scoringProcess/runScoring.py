# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 13:45:56 2016

@author: ankur
"""
#import sys
#import pickle
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


logger = logging.getLogger()
psycopg2.extras.register_uuid()


"""
Execution script to run scoring. Takes movement quality features and performance
variables and returns scores for control, symmetry and consistency of movement.

Input data:
MQF and PV: tbd
historical MQF and PV: from s3 container (to be changed later)

Output data stored in TrainingEvents or BlockEvents table.

"""



def run_scoring(sensor_data, file_name):
    """Creates object attributes according to block analysis process.

    Args:
        raw data object with attributes of:
            epoch_time, corrupt_magn, missing_type, LaX, LaY, LaZ, LqX, LqY,
            LqZ, HaX, HaY, HaZ, HqX, HqY, HqZ, RaX, RaY, RaZ, RqX, RqY, RqZ

    Returns:
        processed data object with attributes of:
            team_id, user_id, team_regimen_id, block_id, block_event_id,
            training_session_log_id, session_event_id, session_type,
            exercise_id, obs_index, obs_master_index, time_stamp, epoch_time,
            ms_elapsed, phase_lf, phase_rf, activity_id, mech_stress,
            const_mech_stress, dest_mech_stress, total_accel, block_duration,
            session_duration, block_mech_stress_elapsed,
            session_mech_stress_elapsed, destr_multiplier, symmetry,
            hip_symmetry, ankle_symmetry, consistency, hip_consistency,
            ankle_consistency, consistency_lf, consistency_rf, control,
            hip_control, ankle_control, control_lf, control_rf
    """
    cont = 'biometrix-blockprocessedcontainer'
    
    # Connect to the database
    conn, cur, s3 = _connect_db_s3()
    queries = _define_sql_queries()

    # Create a RawFrame object with initial data
    columns = sensor_data.dtype.names
#    data = _dynamic_name(sensor_data)
    data = do.RawFrame(sensor_data, columns)


    # CONTROL SCORE
    data.control, data.hip_control, data.ankle_control, data.control_lf,\
                    data.control_rf = control_score(data.LeX, data.ReX,
                                                    data.HeX, data.ms_elapsed)

    logger.info('DONE WITH CONTROL SCORES!')

    # SCORING
    # Symmetry, Consistency, Destructive/Constructive Multiplier and
    # Duration
    # At this point we need to load the historical data for the subject

    # read historical data
    try:
        obj = s3.Bucket(cont).Object('subject3_DblSquat_hist.csv')
        fileobj = obj.get()
        body = fileobj["Body"].read()
        hist_data = cStringIO.StringIO(body)
    except Exception as error:
        logger.info("Cannot read historical user data from s3!")
        raise error

    userDB = pd.read_csv(hist_data)
    logger.info("user history captured")
    data.consistency, data.hip_consistency, \
        data.ankle_consistency, data.consistency_lf, \
        data.consistency_rf, data.symmetry, \
        data.hip_symmetry, data.ankle_symmetry, \
        data.destr_multiplier, data.dest_mech_stress, \
        data.const_mech_stress, data.block_duration, \
        data.session_duration, data.block_mech_stress_elapsed, \
        data.session_mech_stress_elapsed = score(data, userDB)

    logger.info('DONE WITH EVERYTHING!')


    # combine into movement data table
    movement_data = ct.create_movement_data(len(data.LaX), data)
    result = _write_table_db(movement_data, cur, conn, queries)
    print result


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


#def _dynamic_name(sdata):
#    """ Isolates data from input data object.
#    """
#    _names = sdata.dtype.names[1:]
#    _width = len(_names)+1
#    data = sdata.view((float, _width))
#
#    return data


def _define_sql_queries():
    """Define all the sql queries needed
    """
    quer_create = "CREATE TEMP TABLE temp_mov AS SELECT * FROM movement LIMIT 0"

    # Query to copy data over from temp table to movement table
    quer_update = """UPDATE movement
        set control = temp_mov.control,
            hip_control = temp_mov.hip_control,
            ankle_control = temp_mov.ankle_control,
            control_lf = temp_mov.control_lf,
            control_rf = temp_mov.control_rf,
            consistency = temp_mov.consistency,
            hip_consistency = temp_mov.hip_consistency,
            ankle_consistency = temp_mov.ankle_consistency,
            consistency_lf = temp_mov.consistency_lf,
            consistency_rf = temp_mov.consistency_rf,
            symmetry = temp_mov.symmetry,
            hip_symmetry = temp_mov.hip_symmetry,
            ankle_symmetry = temp_mov.ankle_symmetry,
            destr_multiplier = temp_mov.destr_multiplier,
            dest_mech_stress = temp_mov.dest_mech_stress,
            const_mech_stress = temp_mov.const_mech_stress,
            block_duration = temp_mov.block_duration,
            session_duration = temp_mov.session_duration,
            block_mech_stress_elapsed = temp_mov.block_mech_stress_elapsed,
            session_mech_stress_elapsed = temp_mov.session_mech_stress_elapsed
        from temp_mov
        where movement.user_id = temp_mov.user_id and
              movement.session_id = temp_mov.session_id and
              movement.obs_index = temp_mov.obs_index"""

    # finally drop the temp table
    quer_drop = "DROP TABLE temp_mov"

    return {'quer_create': quer_create, 'quer_update': quer_update,
            'quer_drop': quer_drop}


def _write_table_db(movement_data, cur, conn, queries):
    """Update the movement table with all the scores
    Args:
        movement_data: numpy recarray with complete data
        cur: cursor pointing to the current db connection
        conn: db connection
        queries: sql queries needed to write to the table includes
            queries[0]: create temp table
            queries[1]: update movement table
            queries[2]: drop temp table
    Returns:
        result: string signifying success
    """
    movement_data_pd = pd.DataFrame(movement_data)
#    fileobj = cStringIO.StringIO()
#    movement_data_pd.to_csv(fileobj, index=False)
#    fileobj.seek(0)
#    try:
#        s3.Bucket(cont).put_object(Key="movement_"
#                                         +file_name, Body=fileobj)
#    except:
#        logger.warning("Cannot write movement talbe to s3")

    fileobj_db = cStringIO.StringIO()
    try:
        cur.execute(queries['quer_create'])
        movement_data_pd.to_csv(fileobj_db, index=False, header=False,
                                na_rep='NaN')
        fileobj_db.seek(0)
        cur.copy_from(file=fileobj_db, table='temp_mov', sep=',',
                      columns=movement_data.dtype.names)
        cur.execute(queries['quer_update'])
        conn.commit()
        cur.execute(queries['quer_drop'])
        conn.commit()
        conn.close()
    except Exception as error:
        logger.info("Cannot write movement data to DB!")
        raise error
    else:
        return "Success!"



if __name__ == "__main__":
    pass
