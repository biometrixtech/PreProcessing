from __future__ import print_function

import errno
import logging
import numpy as np
import os
import pickle
import sys
from collections import namedtuple
from keras.models import load_model

import columnNames as cols
import runAnalytics
from decode_data import read_file

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.info('Loading sessionProcess')

Config = namedtuple('Config', [
    'AWS',
    'ENVIRONMENT',
    'MS_MODEL_PATH',
    'MS_MODEL',
    'MS_SCALER_PATH',
    'MS_SCALER',
])


def mkdir(path):
    """
    Create a directory, but don't fail if it already exists
    :param path:
    """
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def load_user_mass(data):
    return float(data.get('UserMass', 160)) * 0.453592


def load_grf_model(config):
    path = os.path.join(config.MS_MODEL_PATH, config.MS_MODEL)
    logger.info("Loading grf model from {}".format(path))
    return load_model(path)


def load_grf_scaler(config):
    path = os.path.join(config.MS_SCALER_PATH, config.MS_SCALER)
    logger.info("Loading grf scaler from {}".format(path))
    with open(path) as model_file:
        return pickle.load(model_file)


def script_handler(working_directory, file_name, data):

    logger.info('Received sessionProcess request for {}'.format(file_name))

    try:
        config = Config(
            AWS=False,
            ENVIRONMENT=os.environ['ENVIRONMENT'],
            MS_MODEL_PATH='/net/efs/globalmodels',
            MS_MODEL=os.environ['MS_MODEL'],
            MS_SCALER_PATH='/net/efs/globalscalers',
            MS_SCALER=os.environ['MS_SCALER'],
        )
        mkdir(os.path.join(working_directory, 'sessionprocess2'))

        logger.info("STARTED PROCESSING!")

        # GRF
        # load model
        grf_fit = load_grf_model(config=config)
        sc = load_grf_scaler(config=config)

        logger.info("LOADING DATA")

        # read sensor data
        sdata = read_file(os.path.join(working_directory, 'downloadandchunk', file_name), data.get('Placement'))
        if len(sdata) == 0:
            logger.warning("Sensor data is empty!", info=False)
            return "Fail!"
        logger.info("DATA LOADED!")

        # read user mass
        mass = load_user_mass(data)

        size = len(sdata)
        sdata['obs_index'] = np.array(range(size)).reshape(-1, 1) + 1

        hip_n_transform = data.get('Normalisation', {}).get('Neutral', None)
        if not isinstance(hip_n_transform, list) or len(hip_n_transform) == 0:
            raise Exception('No neutral normalisation quaternion')
        print('hip_n_transform: {}'.format(hip_n_transform))

        # Process the data
        # and pass it as argument to run_session as
        # run_session(sdata, None, mass, grf_fit, sc, hip_n_transform)
        output_data_batch = runAnalytics.run_session(sdata, None, mass, grf_fit, sc, hip_n_transform)

        # Prepare data for dumping
        output_data_batch = output_data_batch.replace('None', '')
        output_data_batch = output_data_batch.round(5)

        # Output data
        fileobj = open(os.path.join(os.path.join(working_directory, 'sessionprocess2', file_name)), 'wb')
        output_data_batch.to_csv(fileobj, index=False, na_rep='', columns=cols.column_session2_out)
        del output_data_batch

        logger.info('Outcome: Success!')
        return 'Success'

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise
