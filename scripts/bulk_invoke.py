#!/usr/bin/env python3
from __future__ import print_function
from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError
from uuid import UUID
import argparse
import boto3
import datetime

from colorama import Fore, Style

try:
    import builtins as __builtin__
except ImportError:
    import __builtin__


def print(*args, **kwargs):
    if 'colour' in kwargs:
        __builtin__.print(kwargs['colour'], end="")
        del kwargs['colour']

        end = kwargs.get('end', '\n')
        kwargs['end'] = ''
        __builtin__.print(*args, **kwargs)

        __builtin__.print(Style.RESET_ALL, end=end)

    else:
        __builtin__.print(*args, **kwargs)


def get_dynamodb(table, session_id):
    ret = table.query(
        Select='ALL_ATTRIBUTES',
        Limit=10000,
        KeyConditionExpression=Key('id').eq(session_id),
    )
    return ret['Items'][0] if len(ret['Items']) else None


def update_session_status(table, session_id, session_status):
    print('    Setting session_status to {}'.format(session_status))
    table.update_item(
        Key={'id': session_id},
        UpdateExpression='SET session_status = :session_status, updated_date = :updated_date',
        ExpressionAttributeValues={
            ':session_status': session_status,
            ':updated_date': datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        },
    )


def process_session(session_id):
    dest_sessions_table = boto3.resource('dynamodb', region_name=args.region).Table('preprocessing-{}-ingest-sessions'.format(args.environment))

    if args.copy_from_environment or args.copy_from_region:
        # Copy the dynamodb record from one arg/region to the other
        source_region = args.copy_from_region or args.region
        source_environment = args.copy_from_environment or args.environment
        source_sessions_table = boto3.resource('dynamodb', region_name=source_region).Table('preprocessing-{}-ingest-sessions'.format(source_environment))

        print('    Copying the session record from {}-{}'.format(source_environment, source_region))

        try:
            existing_record = get_dynamodb(source_sessions_table, session_id)
            existing_record['session_status'] = 'UPLOAD_IN_PROGRESS'
            existing_record['updated_date'] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

            if 's3_files' in existing_record:
                s3_files = existing_record.get('s3_files')
                del existing_record['s3_files']
            elif 's3Files' in existing_record:
                s3_files = existing_record['s3Files']
                del existing_record['s3Files']
            else:
                raise Exception('No s3_files key in DDB record')

            dest_sessions_table.put_item(
                Item=existing_record,
                ConditionExpression=Attr('id').not_exists()
            )
        except ClientError as e:
            if 'ConditionalCheckFailed' in str(e):
                print('    A session with id {} already exists in {}-{}'.format(session_id, args.environment, args.region), colour=Fore.RED)
                exit(1)
            raise

        # Copy the S3 files
        source_bucket = boto3.resource('s3').Bucket('biometrix-preprocessing-{}-{}'.format(source_environment, source_region))
        dest_bucket = boto3.resource('s3').Bucket('biometrix-preprocessing-{}-{}'.format(args.environment, args.region))
        count = 1
        for s3_file in sorted(s3_files):
            print('    Copying {}/{} ({})'.format(count, len(s3_files), s3_file))
            dest_bucket.copy({'Bucket': source_bucket.name, 'Key': s3_file}, s3_file)
            count += 1

    else:
        # Reset the status flag in dynamodb to UPLOAD_IN_PROGRESS
        update_session_status(dest_sessions_table, session_id, 'UPLOAD_IN_PROGRESS')

    # Finally set the status flag to completed again to start processing
    update_session_status(dest_sessions_table, session_id, 'UPLOAD_COMPLETE')


def validate_uuid5(uuid_string):
    try:
        val = UUID(uuid_string, version=5)
        # If the uuid_string is a valid hex code, but an invalid uuid4, the UUID.__init__
        # will convert it to a valid uuid4. This is bad for validation purposes.
        if str(val.hex) == str(uuid_string.replace('-', '')):
            return uuid_string
        print(len(val.hex), len(uuid_string.replace('-', '')))
        for i in range(len(val.hex)): print(val.hex[i], uuid_string.replace('-', '')[i], val.hex[i] == uuid_string.replace('-', '')[i])
    except ValueError:
        # If it's a value error, then the string is not a valid hex code for a UUID.
        pass
    raise argparse.ArgumentTypeError('{} is not a valid uuid'.format(uuid_string))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Invoke a test file')
    parser.add_argument('sessions',
                        nargs='+',
                        # type=validate_uuid5,
                        help='The session(s) to run')
    parser.add_argument('--region', '-r',
                        help='AWS Region',
                        default='us-west-2')
    parser.add_argument('--environment', '-e',
                        help='Environment',
                        default='dev')
    parser.add_argument('--copy-from-environment',
                        dest='copy_from_environment',
                        help='Environment to copy file from')
    parser.add_argument('--copy-from-region',
                        dest='copy_from_region',
                        help='Environment to copy file from')

    args = parser.parse_args()

    if args.copy_from_environment or args.copy_from_region:
        # Need to check that the region-environment pair is different
        if (args.copy_from_region or args.region) == args.region and (args.copy_from_environment or args.environment) == args.environment:
            parser.error('--copy-from-region and --copy-from-environment must point to a different environment')

    count = 1
    for session in args.sessions:
        print('Invoking  {count}/{total} ({session})'.format(count=count, total=len(args.sessions), session=session), colour=Fore.CYAN)
        process_session(session)
        count += 1
