from __future__ import print_function

import logging
import os
from collections import namedtuple

import sys

import input_data_in_batches as idb

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.info('Loading sessionProcess')

Config = namedtuple('Config', [
    'AWS',
    'ENVIRONMENT',
    'FP_INPUT',
    'FP_OUTPUT',
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


def script_handler(sensor_data_filename, filepath, data):

    logger.info('Received sessionProcess request for {}'.format(filepath))

    try:
        config = Config(
            AWS=False,
            ENVIRONMENT=os.environ['ENVIRONMENT'],
            FP_INPUT='/net/efs/preprocessing/{}/downloadandchunk'.format(sensor_data_filename),
            FP_OUTPUT='/net/efs/preprocessing/{}/sessionprocess2'.format(sensor_data_filename),
            MS_MODEL_PATH='/net/efs/globalmodels',
            MS_MODEL=os.environ['MS_MODEL'],
            MS_SCALER_PATH='/net/efs/globalscalers',
            MS_SCALER=os.environ['MS_SCALER'],
        )
        mkdir(config.FP_OUTPUT)
        result = idb.send_batches_of_data(filepath, data, config=config)
        logger.info('outcome:' + result)
        return 'success'

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise

if __name__ == '__main__':
    file_name = sys.argv[1]
    script_handler(file_name, {"UserMass": 65})
