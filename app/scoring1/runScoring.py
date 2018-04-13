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
#from exceptions import NoHistoricalDataException
#from define_boundaries import define_bounds

logger = logging.getLogger()


def run_scoring(sensor_data, data, output_filename):
    """Creates object attributes according to block analysis process.

    Args:
        sensor_data: File handle / StringIO
        output_filename: Full filepath

    Returns:
        result: string signifying success or failure.
        Note: In case of completion for local run, returns movement table.
    """

    sdata = pd.read_csv(sensor_data)
    print(sdata.columns)
    _logger('Data Read')
    del sensor_data

    # CONTROL SCORE
    (
        sdata['control']
    ) = control_score(sdata.eX)

    _logger('DONE WITH CONTROL SCORES!')
#     SCORING
#     Destructive/Constructive Multiplier and Duration

    sdata = score(sdata)
    _logger("DONE WITH SCORING!")

    accel_scale = 100000
    sdata.total_accel = sdata.total_accel * sdata.ms_elapsed / accel_scale
    # Round the data to 6th decimal point
    sdata = sdata.round(6)


    # Output data
    fileobj = open(output_filename, 'wb')
    sdata.to_csv(fileobj, index=False, na_rep='', columns=cols.column_scoring_out)
    _logger("DONE WRITING OUTPUT FILE")

    #TODO replace computing boundaries for twoMin by active blocks
    # Calculate 15 minute cutoff points
    sdata.set_index(pd.to_datetime(sdata.epoch_time, unit='ms'), drop=False, inplace=True)
    groups = sdata.resample('16T')
    data_end = groups.time_stamp.max()
    # Off-by-two error occurs (probably one for the column headers, and one for splitting before/after a line?).  We also
    # have to ignore the last split, which will end up out-of-range
    boundaries = [x + 2 for x in np.where(sdata.time_stamp.isin(data_end))[0].tolist()][0:-1]

    # boundaries = define_bounds(sdata.active.values)

    return boundaries


def _logger(message):
    print(message)
