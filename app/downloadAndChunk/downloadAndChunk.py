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


def script_handler(base_name):

    logger.info('Running downloadAndChunk on "{}"'.format(base_name))

    try:
        dynamodb_resource = boto3.resource('dynamodb').Table('preprocessing-{}-ingest-sessions'.format(os.environ['ENVIRONMENT']))
        records = _query_dynamodb(dynamodb_resource, Key('id').eq(base_name))
        logger.info(records)

        if len(records) == 0 or 's3Files' not in records[0]:
            logger.info('downloadAndChunk() called, but there are no corresponding upload records')
        s3_files = records[0]['s3Files']

        # Download file
        s3_client = boto3.client('s3')
        s3_bucket = 'biometrix-preprocessing-{}-{}'.format(os.environ['ENVIRONMENT'], os.environ['AWS_DEFAULT_REGION'])
        for s3_key in s3_files:
            tmp_filename = '/tmp/' + s3_key
            s3_client.download_file(s3_bucket, s3_key, tmp_filename)
            logger.info('Downloaded "{}/{}" from S3'.format(s3_bucket, s3_key))

        if len(records) == 1:
            return '/tmp/{}'.format(s3_files[0])
        else:
            # Concatenate the files together first
            concat_filename = '/tmp/{}'.format(base_name)
            logger.info('Concatenating {} chunks to {}'.format(len(records), concat_filename))
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


def _query_dynamodb(resource, key_condition_expression, exclusive_start_key=None):
    if exclusive_start_key is not None:
        ret = resource.query(
            Select='ALL_ATTRIBUTES',
            Limit=10000,
            KeyConditionExpression=key_condition_expression,
            ExclusiveStartKey=exclusive_start_key,
        )
    else:
        ret = resource.query(
            Select='ALL_ATTRIBUTES',
            Limit=10000,
            KeyConditionExpression=key_condition_expression,
        )
    if 'LastEvaluatedKey' in ret:
        # There are more records to be scanned
        return ret['Items'] + _query_dynamodb(key_condition_expression, ret['LastEvaluatedKey'])
    else:
        # No more items
        return ret['Items']
