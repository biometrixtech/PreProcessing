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


def script_handler(filepath, data):

    logger.info('Received sessionProcess request for {}'.format(filepath))

    try:
        config = Config(
            AWS=False,
            ENVIRONMENT=os.environ['ENVIRONMENT'],
            FP_INPUT='/net/efs/sessionprocess2/input',
            FP_OUTPUT='/net/efs/sessionprocess2/output',
            MS_MODEL_PATH='/net/efs/globalmodels',
            MS_MODEL=os.environ['MS_MODEL'],
            MS_SCALER_PATH='/net/efs/globalscalers',
            MS_SCALER=os.environ['MS_SCALER'],
        )
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
