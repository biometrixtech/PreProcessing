from __future__ import print_function

from collections import namedtuple
from pymongo import MongoClient
import logging
import os
import pandas
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

Config = namedtuple('Config', [
    'AWS',
    'ENVIRONMENT',
    'FP_INPUT',
    'MONGO_HOST',
    'MONGO_USER',
    'MONGO_PASSWORD',
    'MONGO_DATABASE',
    'MONGO_COLLECTION',
])


def script_handler(file_name):

    logger.info('Running writemongo on "{}"'.format(file_name))

    try:
        config = Config(
            AWS=False,
            ENVIRONMENT=os.environ['ENVIRONMENT'],
            FP_INPUT='/net/efs/writemongo/input',
            MONGO_HOST=os.environ['MONGO_HOST'],
            MONGO_USER=os.environ['MONGO_USER'],
            MONGO_PASSWORD=os.environ['MONGO_PASSWORD'],
            MONGO_DATABASE=os.environ['MONGO_DATABASE'],
            MONGO_COLLECTION=os.environ['MONGO_COLLECTION'],
        )
        return

        mongo_client = MongoClient(config.MONGO_HOST)
        mongo_database = mongo_client[config.MONGO_DATABASE]

        # Authenticate
        mongo_database.authenticate(config.MONGO_USER, config.MONGO_PASSWORD, mechanism='SCRAM-SHA-1')

        mongo_collection = mongo_database[config.MONGO_COLLECTION]

        sdata = pandas.read_csv(os.path.join(config.FP_INPUT, file_name))

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise


if __name__ == '__main__':
    input_file_name = sys.argv[1]
    script_handler(input_file_name)
