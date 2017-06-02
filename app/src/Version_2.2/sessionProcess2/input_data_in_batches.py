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
import boto3
import psycopg2
import psycopg2.extras
from base64 import b64decode

import columnNames as cols
import sessionProcessQueries as queries
import runAnalytics
from botocore.exceptions import ClientError

logger = logging.getLogger()
psycopg2.extras.register_uuid()


def send_batches_of_data(file_path, config, aws=True):
    
    global AWS
    global COLUMN_SESSION2_OUT
    AWS = aws
    COLUMN_SESSION2_OUT = cols.column_session2_out

    _logger("STARTED PROCESSING!")

    # Mechanical Stress            
    # load model
    mstress_fit = load_mechanical_stress_model(config=config)

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
    mass = load_user_mass(sdata)

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


def load_user_mass(sdata):
    user_id = sdata['user_id'][0]

    try:
        _connect_db(config=config)
        cur.execute(queries.quer_read_mass, (user_id,))
        mass = cur.fetchall()[0][0]
    except psycopg2.Error as error:
        _logger("Cannot read user's mass", info=False)
        raise error
    else:
        if mass is None:
            mass = 60

    return mass


def load_mechanical_stress_model(config):
    kms = boto3.client('kms', region_name=config.KMS_REGION)
    ms_model = kms.decrypt(CiphertextBlob=b64decode(config.MS_MODEL))['Plaintext']

    try:
        _logger(config.MS_MODEL_PATH + '/ms_trainmodel.pkl')
        with open(config.MS_MODEL_PATH + '/ms_trainmodel.pkl') as model_file:
            return pickle.load(model_file)
    except:
        raise # IOError("MS model file not found in s3/local directory")

    # try:
    #     s3 = boto3.resource('s3')
    #     ms_obj = s3.Bucket(config.MS_MODEL_BUCKET).Object(config.ENVIRONMENT + '/' + ms_model)
    #     ms_fileobj = ms_obj.get()
    #     ms_body = ms_fileobj["Body"].read()
    #     _logger('Downloaded mechanical stress model')
    #     exit(1)
    #
    #     # we're reading the first model on the list, there are multiple
    #     mstress_fit = pickle.loads(ms_body)
    #     del ms_body
    #     del ms_fileobj
    #     del ms_obj
    # except ClientError:
    #     if config.AWS:
    #         _logger("Cannot load MS model from s3!", info=False)
    #         raise
    #     else:


    # return mstress_fit


def _logger(message, info=True):
    if AWS:
        if info:
            logger.info(message)
        else:
            logger.warning(message)
    else:
        print message
        

def _connect_db(config):
    """Start a connection to the database
    """
    kms = boto3.client('kms', region_name=config.KMS_REGION)

    db_name = config.DB_NAME
    db_host = kms.decrypt(CiphertextBlob=b64decode(config.DB_HOST))['Plaintext']
    db_username = kms.decrypt(CiphertextBlob=b64decode(config.DB_USERNAME))['Plaintext']
    db_password = kms.decrypt(CiphertextBlob=b64decode(config.DB_PASSWORD))['Plaintext']
    _logger('Loaded DB credentials')

    return None, None
    try:
        conn = psycopg2.connect(dbname=db_name, user=db_username, host=db_host, password=db_password)
        cur = conn.cursor()

    except psycopg2.Error as error:
        logger.warning("Cannot connect to DB")
        raise error
    else:
        return conn, cur
