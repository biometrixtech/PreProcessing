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
from __future__ import print_function
import gc
import logging
import pandas as pd
import psycopg2
import psycopg2.extras
import boto3

from controlScore import control_score
from scoring import score
import scoringProcessQueries as queries
import columnNames as cols

logger = logging.getLogger()
psycopg2.extras.register_uuid()


def run_scoring(sensor_data, file_name, config):
    """Creates object attributes according to block analysis process.

    Args:
        sensor_data: File handle / StringIO
        file_name
        config: Config object

    Returns:
        result: string signifying success or failure.
        Note: In case of completion for local run, returns movement table.
    """

    data = pd.read_csv(sensor_data, usecols=cols.vars_for_scoring)
    _logger('Data Read')
    del sensor_data

    session_event_id = data.session_event_id[0]
    user_id = data.user_id[0]
    # CONTROL SCORE
    (
        data['control'],
        data['hip_control'],
        data['ankle_control'],
        data['control_lf'],
        data['control_rf']
    ) = control_score(data.LeX, data.ReX, data.HeX, data.ms_elapsed, data.phase_lf, data.phase_rf)

    _logger('DONE WITH CONTROL SCORES!')
    # SCORING
    # Symmetry, Consistency, Destructive/Constructive Multiplier and
    # Duration
    # At this point we need to load the historical data for the subject

    # read historical data
    try:
        path = "{}/{}".format(config.ENVIRONMENT, user_id)
        s3 = boto3.resource('s3')
        objs = list(s3.Bucket(config.S3_BUCKET_HISTORY).objects.filter(Prefix=path))
        if len(objs) == 1:
            obj = s3.Bucket(config.S3_BUCKET_HISTORY).Object(path)
            fileobj = obj.get()
            body = fileobj["Body"]
            user_hist = pd.read_csv(body)
            del body
            user_hist.columns = cols.columns_hist
        elif len(data.LeX) > 50000:
            user_hist = data
        else:
            _logger("There's no historical data and current data isn't long enough!")
            # Can't complete scoring, delete data from movement table and exit
            return "Fail!"

    except Exception:
        _logger("Cannot read historical user data from s3!")
        raise
        if config.AWS:
            raise
        else:
            try:
                user_hist = pd.read_csv(config.FP_SCORINGHIST + '/' + user_id)
            except:
                raise IOError("User history not found in s3/local directory")

    _logger("user history captured")
    gc.collect()

    mech_stress_scale = 1000000
    (
        data['consistency'],
        data['hip_consistency'],
        data['ankle_consistency'],
        data['consistency_lf'],
        data['consistency_rf'],
        data['symmetry'],
        data['hip_symmetry'],
        data['ankle_symmetry'],
        data['destr_multiplier'],
        data['dest_mech_stress'],
        data['const_mech_stress'],
        data['block_duration'],
        data['session_duration'],
        data['block_mech_stress_elapsed'],
        data['session_mech_stress_elapsed']
    ) = score(data, user_hist, mech_stress_scale)
    del user_hist
    _logger("DONE WITH SCORING!")
    gc.collect()

    data.mech_stress = data.mech_stress/mech_stress_scale
    # Round the data to 6th decimal point
    data = data.round(6)

    # Output data
    fileobj = open(config.FP_OUTPUT + '/' + file_name, 'wb')
    data.to_csv(fileobj, index=False, na_rep='', columns=cols.column_scoring_out)
    del data
    _logger("DONE WRITING OUTPUT FILE")

    # conn, cur = _connect_db(config)
    # cur.execute(queries.quer_update_session_events, (session_event_id,))
    # conn.commit()
    # conn.close()

    _logger("DONE UPDATING DATABASE")

    return "Success!"


def _connect_db(config):
    """
    Start a connection to the database
    """
    try:
        conn = psycopg2.connect(
            dbname=config.DB_NAME,
            user=config.DB_USERNAME,
            host=config.DB_HOST,
            password=config.DB_PASSWORD)
        cur = conn.cursor()

    except psycopg2.Error as error:
        logger.warning("Cannot connect to DB")
        raise error
    else:
        return conn, cur


def _logger(message):
    print(message)


