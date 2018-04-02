#!/usr/bin/python3
import argparse
from uuid import UUID

import boto3
import datetime
import time
from boto3.dynamodb.conditions import Attr


def invoke_lambda(s3_bucket, s3_key, timestamp):
    payload = '{"Records":[{"s3":{"bucket":{"name":"' + s3_bucket + '"},"object":{"key":"' + s3_key + '"}}, "eventTime": "' + timestamp + '"}]}'
    print(" " * 4 + s3_key)
    lambda_client.invoke(
        FunctionName='preprocessing-{}-ingest-trigger'.format(args.environment),
        Payload=payload,
    )


def process_file(s3_bucket, basename):
    # Reset the status flag in dynamodb to UPLOAD_IN_PROGRESS
    ddb_session_events_table = dynamodb_resource.Table('preprocessing-{}-ingest-sessions'.format(args.environment))
    print('    Setting session_status to UPLOAD_IN_PROGRESS')
    ddb_session_events_table.update_item(
        Key={'id': basename},
        UpdateExpression='SET session_status = :session_status, updated_date = :updated_date',
        ExpressionAttributeValues={
            ':session_status': 'UPLOAD_IN_PROGRESS',
            ':updated_date': datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        },
    )

    if args.reimport:
        # Simulate a CloudWatch Event as if the file was newly-uploaded.  But keep the same 'uploaded at'
        # timestamp to avoid duplicate records
        for s3_file, last_modified in list_s3_files(s3_bucket, basename):
            invoke_lambda(s3_bucket, s3_file, last_modified.strftime("%Y-%m-%dT%H:%M:%SZ"))
    else:
        # Just set the status flag to completed again
        print('    Setting session_status to UPLOAD_COMPLETE')
        ddb_session_events_table.update_item(
            Key={'id': basename},
            ConditionExpression=Attr('id').exists(),
            UpdateExpression='SET session_status = :session_status',
            ExpressionAttributeValues={':session_status': 'UPLOAD_COMPLETE'},
        )


def list_s3_files(s3_bucket, prefix, marker=''):
    ret = []
    resp = s3_client.list_objects(Bucket=s3_bucket, Prefix=prefix, Marker=marker)
    if 'Contents' not in resp:
        raise Exception('File {} not present in S3')
    ret.extend([(x['Key'], x['LastModified']) for x in resp['Contents'] if x['Key'][-8:] != 'combined'])
    if resp['IsTruncated']:
        ret.extend(list_s3_files(s3_bucket, prefix, ret[-1]))
    return sorted(ret)


def validate_uuid4(uuid_string):
    try:
        val = UUID(uuid_string, version=4)
        # If the uuid_string is a valid hex code, but an invalid uuid4, the UUID.__init__
        # will convert it to a valid uuid4. This is bad for validation purposes.
        return val.hex == uuid_string.replace('-', '')
    except ValueError:
        # If it's a value error, then the string is not a valid hex code for a UUID.
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Invoke a test file')
    parser.add_argument('files',
                        type=str,
                        nargs='+',
                        help='The file(s) to run')
    parser.add_argument('--region', '-r',
                        type=str,
                        help='AWS Region',
                        default='us-west-2')
    parser.add_argument('--environment', '-e',
                        type=str,
                        help='Environment',
                        default='dev')
    parser.add_argument('--bucket', '-b',
                        type=str,
                        help='S3 bucket',
                        default='biometrix-preprocessing-{environment}-{region}')
    parser.add_argument('--reimport',
                        action='store_true',
                        dest='reimport',
                        help='Import all parts individually')

    args = parser.parse_args()

    dynamodb_resource = boto3.resource('dynamodb', region_name=args.region)
    lambda_client = boto3.client('lambda', region_name=args.region)
    s3_client = boto3.client('s3')

    files = args.files
    bucket = args.bucket.format(environment=args.environment, region=args.region)

    count = 1
    for key in files:
        print('Invoking  {count}/{total} ({key})'.format(count=count, total=len(files), key=key))
        if not validate_uuid4(key):
            print('{} is not a valid uuid'.format(key))
            continue
        process_file(bucket, key)
        count += 1
