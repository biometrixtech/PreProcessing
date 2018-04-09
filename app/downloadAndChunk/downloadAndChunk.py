from __future__ import print_function
from boto3.dynamodb.conditions import Key
import boto3
import logging
import os
import re
import subprocess
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def script_handler(base_name, output_dir):

    logger.info('Running downloadAndChunk on "{}"'.format(base_name))

    try:
        dynamodb_resource = boto3.resource('dynamodb').Table('preprocessing-{}-ingest-sessions'.format(os.environ['ENVIRONMENT']))
        session = _query_dynamodb(dynamodb_resource, Key('id').eq(base_name))

        if session is None or ('s3_files' not in session and 's3Files' not in session):
            logger.info('downloadAndChunk() called, but there are no corresponding upload records')
        s3_files = sorted(list(session.get('s3_files', session.get('s3Files'))))
        logger.info(s3_files)

        # Download file
        s3_client = boto3.client('s3')
        s3_bucket = 'biometrix-preprocessing-{}-{}'.format(os.environ['ENVIRONMENT'], os.environ['AWS_DEFAULT_REGION'])
        for s3_key in s3_files:
            tmp_filename = '/tmp/' + s3_key
            s3_client.download_file(s3_bucket, s3_key, tmp_filename)
            logger.info('Downloaded "{}/{}" from S3'.format(s3_bucket, s3_key))

        if len(s3_files) == 1:
            source_filename = '/tmp/{}'.format(s3_files[0])
            destination_filename = os.path.join(output_dir, base_name)
            subprocess.check_call('cp {source_file} {dest_file}'.format(
                    source_file=source_filename,
                    dest_file=destination_filename), shell=True)
            return destination_filename
        else:
            # Concatenate the files together first
            # concat_filename = '/tmp/{}'.format(base_name)
            concat_filename = os.path.join(output_dir, base_name)
            logger.info('Concatenating {} chunks to {}'.format(len(s3_files), concat_filename))
            for s3_key in s3_files:
                # Paranoia since we're injecting this into a shell
                if not re.match('^[a-z0-9\-_]+$', s3_key):
                    raise Exception('Insecure S3 key: {}'.format(s3_key))
                subprocess.check_call('cat /tmp/{} >> {}'.format(s3_key, concat_filename), shell=True)
            return concat_filename

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise


def _query_dynamodb(resource, key_condition_expression):
    ret = resource.query(
        Select='ALL_ATTRIBUTES',
        Limit=10000,
        KeyConditionExpression=key_condition_expression,
    )
    return ret['Items'][0] if len(ret['Items']) else None
