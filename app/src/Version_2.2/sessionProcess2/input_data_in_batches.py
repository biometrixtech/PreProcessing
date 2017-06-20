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
from keras.models import load_model

import columnNames as cols
import sessionProcessQueries as queries
import runAnalytics

logger = logging.getLogger()
psycopg2.extras.register_uuid()


def send_batches_of_data(file_path, config, aws=True):
    
    global AWS
    AWS = aws

    _logger("STARTED PROCESSING!")

    # Mechanical Stress
    # load model
    grf_fit = load_grf_model(config=config)
    sc = load_grf_scaler(config=config)

    # read sensor data
    try:
        sdata = pd.read_csv(config.FP_INPUT + '/' + file_path, nrows=900000)
    except Exception as error:
        _logger("Cannot load data!", info=False)
        raise error
    if len(sdata) == 0:
        _logger("Sensor data is empty!", info=False)
        return "Fail!"
    _logger("DATA LOADED!")

    #_logger(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    # read user mass
    mass = load_user_mass(sdata, config=config)

    size = len(sdata)
    sdata['obs_master_index'] = np.array(range(size)).reshape(-1, 1) + 1

    # Process the data
    output_data_batch = runAnalytics.run_session(sdata, None, mass, grf_fit, sc, AWS)

    # Prepare data for dumping
    output_data_batch = output_data_batch.replace('None', '')
    output_data_batch = output_data_batch.round(5)

    # Output data
    fileobj = open(config.FP_OUTPUT + '/' + file_path, 'wb')
    output_data_batch.to_csv(fileobj, index=False, na_rep='', columns=cols.column_session2_out)
    del output_data_batch

    return "Success!"


def load_user_mass(sdata, config):
    user_id = sdata['user_id'][0]

    # FIXME
    if config.DB_HOST == 'MOCK' and config.DB_NAME == 'MOCK':
        return 70

    try:
        (conn, cur) = _connect_db(config=config)
        cur.execute(queries.quer_read_mass, (user_id,))
        mass = cur.fetchall()[0][0]
    except psycopg2.Error as error:
        _logger("Cannot read user's mass", info=False)
        raise error
    else:
        if mass is None:
            mass = 70
        else:
            mass = mass*0.453592

    return mass


def load_grf_model(config):
    path = os.path.join(config.MS_MODEL_PATH, config.MS_MODEL)
    _logger("Loading model from {}".format(path))
    return load_model(path)
#    with open(path) as model_file:
#        return pickle.load(model_file)


def load_grf_scaler(config):
    #TODO(Stephen) need to define path for scaler (same location as grf_model)
    path = os.path.join(config.SCALER_PATH, config.SCALER)
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
