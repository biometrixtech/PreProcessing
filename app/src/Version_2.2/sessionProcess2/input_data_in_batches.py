# -*- coding: utf-8 -*-
"""
Created on Fri Jan 27 07:40:55 2017

@author: ankurmanikandan
"""

import logging
import pickle
import os

import pandas as pd
import numpy as np
import psycopg2
import psycopg2.extras

import columnNames as cols
import sessionProcessQueries as queries
import runAnalytics

logger = logging.getLogger()
psycopg2.extras.register_uuid()


def send_batches_of_data(file_path, data, config, aws=True):
    
    global AWS
    AWS = aws

    _logger("STARTED PROCESSING!")

    # Mechanical Stress
    # load model
    mstress_fit = load_mechanical_stress_model(config=config)

    # read sensor data
    try:
        sdata = pd.read_csv(config.FP_INPUT + '/' + file_path, nrows=900000)
    except:
        _logger("Cannot load data!", info=False)
        raise
    if len(sdata) == 0:
        _logger("Sensor data is empty!", info=False)
        return "Fail!"
    _logger("DATA LOADED!")

    #_logger(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    # read user mass
    mass = load_user_mass(data)

    size = len(sdata)
    sdata['obs_master_index'] = np.array(range(size)).reshape(-1, 1) + 1

    # Process the data
    output_data_batch = runAnalytics.run_session(sdata, None, mass, mstress_fit, AWS)

    # Prepare data for dumping
    output_data_batch = output_data_batch.replace('None', '')
    output_data_batch = output_data_batch.round(5)

    # Output data
    fileobj = open(config.FP_OUTPUT + '/' + file_path, 'wb')
    output_data_batch.to_csv(fileobj, index=False, na_rep='', columns=cols.column_session2_out)
    del output_data_batch

    return "Success!"


def load_user_mass(data):
    return data.get('UserMass', 60)


def load_mechanical_stress_model(config):
    path = os.path.join(config.MS_MODEL_PATH, config.MS_MODEL)
    _logger("Loading model from {}".format(path))
    with open(path) as model_file:
        return pickle.load(model_file)


def _logger(message, info=True):
    if AWS:
        if info:
            logger.info(message)
        else:
            logger.warning(message)
    else:
        print message
