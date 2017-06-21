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
from s3fs.core import S3FileSystem

from controlScore import control_score
from scoring import score
import scoringProcessQueries as queries
import columnNames as cols

logger = logging.getLogger()
psycopg2.extras.register_uuid()


def run_scoring(sensor_data, file_name, data, config):
    """Creates object attributes according to block analysis process.

    Args:
        sensor_data: File handle / StringIO
        file_name
        config: Config object

    Returns:
        result: string signifying success or failure.
        Note: In case of completion for local run, returns movement table.
    """

    sdata = pd.read_csv(sensor_data, usecols=cols.vars_for_scoring)
    _logger('Data Read')
    del sensor_data

    user_id = data.get('UserId', None)
    # CONTROL SCORE
    (
        sdata['control'],
        sdata['hip_control'],
        sdata['ankle_control'],
        sdata['control_lf'],
        sdata['control_rf']
    ) = control_score(sdata.LeX, sdata.ReX, sdata.HeX, sdata.ms_elapsed, sdata.phase_lf, sdata.phase_rf)

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
            s3 = S3FileSystem(anon=False)
            user_hist = pd.read_csv(s3.open('{}/{}'.format(config.S3_BUCKET_HISTORY, path), mode='rb'))
            user_hist.columns = cols.columns_hist
        elif len(sdata.LeX) > 50000:
            user_hist = sdata
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
        sdata['consistency'],
        sdata['hip_consistency'],
        sdata['ankle_consistency'],
        sdata['consistency_lf'],
        sdata['consistency_rf'],
        sdata['symmetry'],
        sdata['hip_symmetry'],
        sdata['ankle_symmetry'],
        sdata['destr_multiplier'],
        sdata['dest_mech_stress'],
        sdata['const_mech_stress'],
        sdata['block_duration'],
        sdata['session_duration'],
        sdata['block_mech_stress_elapsed'],
        sdata['session_mech_stress_elapsed']
    ) = score(sdata, user_hist, mech_stress_scale)
    del user_hist
    _logger("DONE WITH SCORING!")
    gc.collect()

    sdata.mech_stress = sdata.mech_stress / mech_stress_scale
    # Round the data to 6th decimal point
    sdata = sdata.round(6)

    # Output data
    fileobj = open(config.FP_OUTPUT + '/' + file_name, 'wb')
    sdata.to_csv(fileobj, index=False, na_rep='', columns=cols.column_scoring_out)
    del sdata
    _logger("DONE WRITING OUTPUT FILE")

    return "Success!"


def _logger(message):
    print(message)


