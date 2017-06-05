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
    'DB_HOST',
    'DB_NAME',
    'DB_PASSWORD',
    'DB_USERNAME',
    'ENVIRONMENT',
    'FP_INPUT',
    'FP_OUTPUT',
    'KMS_REGION',
    'MS_MODEL',
    'MS_MODEL_BUCKET',
    'MS_MODEL_PATH',
])


def script_handler(filepath):

    logger.info('Received sessionProcess request for {}'.format(filepath))

    try:
        config = Config(
            AWS=False,
            DB_HOST=os.environ['DB_HOST'],
            DB_NAME=os.environ['DB_NAME'],
            DB_PASSWORD=os.environ['DB_PASSWORD'],
            DB_USERNAME=os.environ['DB_USERNAME'],
            ENVIRONMENT='dev',
            FP_INPUT='/net/efs/sessionprocess2/input',
            FP_OUTPUT='/net/efs/sessionprocess2/output',
            KMS_REGION='us-west-2',
            MS_MODEL=os.environ['MS_MODEL'],
            MS_MODEL_BUCKET='biometrix-globalmodels',
            MS_MODEL_PATH='/net/efs/globalmodels',
        )
        result = idb.send_batches_of_data(filepath, config=config)
        logger.info('outcome:' + result)
        return 'success'

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise

if __name__ == '__main__':
    file_name = sys.argv[1]
    script_handler(file_name)
