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
from decode_data import read_file

logger = logging.getLogger()
psycopg2.extras.register_uuid()


def send_batches_of_data(input_filepath, output_filepath, data, config, aws=True):
    
    global AWS
    AWS = aws

    _logger("STARTED PROCESSING!")

    # GRF
    # load model
    grf_fit = load_grf_model(config=config)
    sc = load_grf_scaler(config=config)

    _logger("LOADING DATA")

    # read sensor data
    try:
        sdata = read_file(input_filepath)
    except:
        _logger("Cannot load data!", info=False)
        raise
    if len(sdata) == 0:
        _logger("Sensor data is empty!", info=False)
        return "Fail!"
    _logger("DATA LOADED!")

    # read user mass
    mass = load_user_mass(data)

    size = len(sdata)
    sdata['obs_index'] = np.array(range(size)).reshape(-1, 1) + 1

    hip_n_transform = data.get('HipNTransform', None)
    if not isinstance(hip_n_transform, list) or len(hip_n_transform) == 0:
        hip_n_transform = [0.987955980423897, 0.129494511785864, 0.0839820262430614, -0.0110077895195965]
    print('hip_n_transform: {}'.format(hip_n_transform))

    # Process the data
    # and pass it as argument to run_session as
    # run_session(sdata, None, mass, grf_fit, sc, hip_n_transform, AWS)
    output_data_batch = runAnalytics.run_session(sdata, None, mass, grf_fit, sc, hip_n_transform, AWS)

    # Prepare data for dumping
    output_data_batch = output_data_batch.replace('None', '')
    output_data_batch = output_data_batch.round(5)

    # Output data
    fileobj = open(os.path.join(output_filepath), 'wb')
    output_data_batch.to_csv(fileobj, index=False, na_rep='', columns=cols.column_session2_out)
    del output_data_batch

    return "Success!"


def load_user_mass(data):
    return float(data.get('UserMass', 160)) * 0.453592


def load_grf_model(config):
    path = os.path.join(config.MS_MODEL_PATH, config.MS_MODEL)
    _logger("Loading grf model from {}".format(path))
    return load_model(path)


def load_grf_scaler(config):
    path = os.path.join(config.MS_SCALER_PATH, config.MS_SCALER)
    _logger("Loading grf scaler from {}".format(path))
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
