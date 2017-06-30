from __future__ import print_function

from collections import namedtuple
import boto3
import glob
import logging
import os
import pandas
import subprocess
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

Config = namedtuple('Config', [
    'AWS',
    'ENVIRONMENT',
    'FP_DOWNLOADANDCHUNK_OUTPUT',
    'FP_SESSIONPROCESS_OUTPUT',
    'FP_SCORING_OUTPUT',
    'FP_WRITEMONGO_OUTPUT',
])


def script_handler(file_name):

    logger.info('Running cleanup for "{}"'.format(file_name))

    try:
        config = Config(
            AWS=False,
            ENVIRONMENT=os.environ['ENVIRONMENT'],
            FP_INPUT=None,
            FP_DOWNLOADANDCHUNK_OUTPUT='/net/efs/downloadandchunk/output',
            FP_SESSIONPROCESS_OUTPUT='/net/efs/sessionprocess2/output',
            FP_SCORING_OUTPUT='/net/efs/scoring/output',
            FP_WRITEMONGO_OUTPUT=None,
        )

        # Clean up downloadandchunk output directory
        for file in glob.glob(os.path.join(config.FP_DOWNLOADANDCHUNK_OUTPUT, file_name + '-[0-9]*')):
            os.remove(os.path.basename(file))

        # Clean up sessionprocess2 output directory
        for file in glob.glob(os.path.join(config.FP_SESSIONPROCESS_OUTPUT, file_name + '-[0-9]*')):
            os.remove(os.path.basename(file))

        logger.info('Finished cleanup for {}'.format(file_name))
        return {}

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise
