from __future__ import print_function

from collections import namedtuple
import boto3
import logging
import os
import subprocess
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

Config = namedtuple('Config', [
    'AWS',
    'ENVIRONMENT',
])


def script_handler(s3_bucket, s3_keys):
    if len(s3_keys) == 0:
        logger.info('downloadAndChunk() called, but with no files')

    base_name = s3_keys[0].rsplit('_', 1)[0]
    logger.info('Running downloadAndChunk on "{}/{}"'.format(s3_bucket, base_name))

    try:
        config = Config(
            AWS=False,
            ENVIRONMENT=os.environ['ENVIRONMENT'],
        )

        filepath = os.path.join(working_directory, 'downloadandchunk', file_name)

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise


if __name__ == '__main__':
    input_file_name = sys.argv[1]
    script_handler('biometrix-sessioncontainer2', input_file_name)
