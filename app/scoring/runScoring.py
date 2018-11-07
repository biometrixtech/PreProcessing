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
import logging
import pandas as pd
import numpy as np

from controlScore import control_score
from scoring import score
import columnNames as cols
from exceptions import NoHistoricalDataException
from define_boundaries import define_bounds

logger = logging.getLogger()


def run_scoring(sensor_data, historical_data, data, output_filename):
    """Creates object attributes according to block analysis process.

    Args:
        sensor_data: File handle / StringIO
        :param historical_data:
        output_filename: Full filepath

    Returns:
        result: string signifying success or failure.
        Note: In case of completion for local run, returns movement table.
    """

    sdata = pd.read_csv(sensor_data)
    _logger('Data Read')
    del sensor_data

    # CONTROL SCORE
    (
        sdata['control'],
        sdata['hip_control'],
        sdata['ankle_control'],
        sdata['control_lf'],
        sdata['control_rf']
    ) = control_score(sdata.LeX, sdata.HeX, sdata.ReX, sdata.phase_lf, sdata.phase_rf)

    _logger('DONE WITH CONTROL SCORES!')
#     SCORING
#     Symmetry, Consistency, Destructive/Constructive Multiplier and
#     Duration

    # Read historical data
    # user_hist = pd.read_csv(historical_data, usecols=cols.column_user_hist)
    if sdata.shape[0] < 2000:
        _logger("Current data isn't long enough for scoring!")
        raise NoHistoricalDataException("Insufficient data, need 30000 rows, only got {}".format(sdata.shape[0]))

    # _logger("user history captured")

    grf_scale = 1000000
    sdata = score(sdata, grf_scale)
    # del user_hist
    _logger("DONE WITH SCORING!")
    accel_scale = 100000
    sdata.grf = sdata.grf / grf_scale
    sdata.total_accel = sdata.total_accel * sdata.ms_elapsed / accel_scale
    # Round the data to 6th decimal point
    sdata = sdata.round(6)

    # Add nans for future variables
    sdata['symmetry_l'] = np.nan
    sdata['symmetry_r'] = np.nan
    sdata['hip_symmetry_l'] = np.nan
    sdata['hip_symmetry_r'] = np.nan
    sdata['ankle_symmetry_l'] = np.nan
    sdata['ankle_symmetry_r'] = np.nan

    ######################
    # Write debug data to s3
#    import cStringIO
#    import boto3
#    columns = ['epoch_time', 'active', 'grf', 'total_accel',
#               'symmetry', 'hip_symmetry', 'ankle_symmetry',
#               'control', 'hip_control', 'ankle_control', 'control_lf', 'control_rf']
#    fileobj = cStringIO.StringIO()
#    sdata.to_csv(fileobj, index=False, na_rep='', columns=columns)
#
#    fileobj.seek(0)
#    s3 = boto3.resource('s3')
#    s3.Bucket('biometrix-decode').put_object(Key=output_filename + '_scores', Body=fileobj)
    #######################

    # Output data
    fileobj = open(output_filename, 'wb')
    sdata.to_csv(fileobj, index=False, na_rep='', columns=cols.column_scoring_out)
    _logger("DONE WRITING OUTPUT FILE")

    #TODO replace computing boundaries for twoMin by active blocks
    # Calculate 15 minute cutoff points
    # sdata.set_index(pd.to_datetime(sdata.epoch_time, unit='ms'), drop=False, inplace=True)
    # groups = sdata.resample('16T')
    # data_end = groups.time_stamp.max()
    # Off-by-two error occurs (probably one for the column headers, and one for splitting before/after a line?).  We also
    # have to ignore the last split, which will end up out-of-range
    # boundaries = [x + 2 for x in np.where(sdata.time_stamp.isin(data_end))[0].tolist()][0:-1]

    boundaries = define_bounds(sdata.active.values)

    return boundaries


def _logger(message):
    print(message)

