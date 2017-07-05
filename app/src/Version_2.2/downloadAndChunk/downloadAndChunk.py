from __future__ import print_function

from collections import namedtuple
import boto3
import logging
import os
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

Config = namedtuple('Config', [
    'AWS',
    'ENVIRONMENT',
])


def script_handler(s3_bucket, s3_key):

    logger.info('Running downloadAndChunk on "{}/{}"'.format(s3_bucket, s3_key))

    try:
        config = Config(
            AWS=False,
            ENVIRONMENT=os.environ['ENVIRONMENT'],
        )

        s3_client = boto3.client('s3')

        # Download file
        tmp_filename = '/tmp/' + s3_key
        s3_client.download_file(
            s3_bucket,
            config.ENVIRONMENT + '/' + s3_key,
            tmp_filename,
        )
        logger.info('Downloaded "{}/{}" from S3'.format(s3_bucket, s3_key))

        return tmp_filename

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise


if __name__ == '__main__':
    input_file_name = sys.argv[1]
    script_handler('biometrix-sessioncontainer2', input_file_name)
