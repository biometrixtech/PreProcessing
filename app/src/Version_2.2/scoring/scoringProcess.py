from __future__ import print_function

from collections import namedtuple
import json
import logging
import os
import runScoring as rs
import sys

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
])


def script_handler(filenames):

    logger.info('Received scoring request for {}'.format(", ".join(filenames)))

    try:
        config = Config(
            AWS=False,
            DB_HOST=os.environ['DB_HOST'],
            DB_NAME=os.environ['DB_NAME'],
            DB_PASSWORD=os.environ['DB_PASSWORD'],
            DB_USERNAME=os.environ['DB_USERNAME'],
            ENVIRONMENT=os.environ['ENVIRONMENT'],
            FP_INPUT='/net/efs/scoring/input',
            FP_OUTPUT='/net/efs/scoring/output',
        )
        csv_data = []
        header = []
        # for filename in filenames:
        #     with open(os.path.join(config.FP_INPUT, filename), 'r') as f:
        #         lines = f.readlines()
        #         csv_data.extend(lines[1:])
        #         header.extend(lines[0])

        print(len(csv_data))
        header.extend(csv_data)
        del csv_data

        result = rs.run_scoring("\n".join(header), config=config)
        logger.info('outcome:' + result)
        return 'success'

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise

if __name__ == '__main__':
    file_name = json.loads(sys.argv[1])
    script_handler(file_name)
