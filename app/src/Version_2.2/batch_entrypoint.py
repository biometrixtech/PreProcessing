#!/usr/bin/env python
# Entrypoint when called as a batch job
import os
from datetime import datetime
import boto3
import errno
import json
import sys
import time
import traceback


def send_success(meta, output):
    if 'TaskToken' in meta:
        sfn_client = boto3.client('stepfunctions')
        sfn_client.send_task_success(
            taskToken=meta['TaskToken'],
            output=json.dumps({
                "Meta": meta,
                "Status": 'SUCCEEDED',
                "Output": output
            })
        )
    if 'LinearityGroup' in meta:
        sqs_client = boto3.client('sqs')
        response = sqs_client.delete_message(
            QueueUrl=meta['LinearityGroup']['QueueUrl'],
            ReceiptHandle=meta['LinearityGroup']['ReceiptHandle']
        )
        print(response)

    if 'Profiling' in meta:
        meta['Profiling']['EndTime'] = time.time()
        put_cloudwatch_metric(
            'BatchJobProcessTime',
            float(meta_data['Profiling']['EndTime']) - float(meta_data['Profiling']['StartTime']),
            'Seconds'
        )

    
def send_failure(meta, exception):
    task_token = meta.get('TaskTokenFailure', meta.get('TaskToken', None))
    if task_token is not None:
        sfn_client = boto3.client('stepfunctions')
        sfn_client.send_task_failure(
            taskToken=task_token,
            error=type(exception).__name__,
            cause=traceback.format_exc()
        )


def send_heartbeat(meta):
    task_token = meta.get('TaskTokenFailure', meta.get('TaskToken', None))
    if task_token is not None:
        sfn_client = boto3.client('stepfunctions')
        sfn_client.send_task_heartbeat(
            taskToken=task_token,
        )


def chunk_list(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def load_parameters(keys):
    keys_to_load = [key for key in keys if key.upper() not in os.environ]
    if len(keys_to_load) > 0:
        print('Retrieving configuration for [{}] from SSM'.format(", ".join(keys_to_load)))
        ssm_client = boto3.client('ssm')

        for key_batch in chunk_list(keys_to_load, 10):
            response = ssm_client.get_parameters(
                Names=['preprocessing.{}.{}'.format(os.environ['ENVIRONMENT'], key.lower()) for key in key_batch],
                WithDecryption=True
            )
            params = {p['Name'].split('.')[-1].upper(): p['Value'] for p in response['Parameters']}
            # Export to environment
            for k, v in params.items():
                print("Got value for {} from SSM".format(k))
                os.environ[k] = v


def put_cloudwatch_metric(metric_name, value, unit):
    try:
        cloudwatch_client = boto3.client('cloudwatch')
        cloudwatch_client.put_metric_data(
            Namespace='Preprocessing',
            MetricData=[
                {
                    'MetricName': metric_name,
                    'Dimensions': [
                        {'Name': 'Environment', 'Value': os.environ['ENVIRONMENT']},
                        # {'Name': 'JobQueue', 'Value': os.environ['AWS_BATCH_JQ_NAME']},
                        # {'Name': 'ComputeEnvironment', 'Value': os.environ['AWS_BATCH_CE_NAME']},
                        {'Name': 'Job', 'Value': script},
                    ],
                    'Timestamp': datetime.utcnow(),
                    'Value': value,
                    'Unit': unit,
                },
            ]
        )
    except Exception as exception:
        print("Could not put cloudwatch metric")
        print(repr(exception))
        # Continue


def mkdir(path):
    """
    Create a directory, but don't fail if it already exists
    :param path:
    """
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


if __name__ == '__main__':
    input_data = meta_data = None

    try:
        script = sys.argv[1]
        input_data = json.loads(sys.argv[2])
        meta_data = json.loads(sys.argv[3])

        if 'Profiling' in meta_data:
            meta_data['Profiling']['StartTime'] = time.time()
            put_cloudwatch_metric('BatchJobScheduleLatency', float(meta_data['Profiling']['StartTime']) - float(meta_data['Profiling']['ScheduleTime']), 'Seconds')

        sensor_data_filename = input_data.get('SensorDataFilename')
        working_directory = os.path.join('/net/efs/preprocessing', sensor_data_filename)

        if script == 'downloadandchunk':
            print('Running downloadAndChunk()')

            if not os.path.isdir('/net/efs/preprocessing'):
                raise Exception("/net/efs/preprocessing directory does not exist.  Has the EFS filesystem been initialised?")

            from downloadAndChunk import downloadAndChunk
            s3_bucket = input_data.get('S3Bucket', None)
            s3_basepath = input_data.get('S3BasePath', None)
            s3_paths = ["{}{:04d}".format(s3_basepath, i) for i in range(0, input_data.get('PartCount', []))] + [s3_basepath + "complete"]
            tmp_combined_file = downloadAndChunk.script_handler(s3_bucket, s3_paths)

            # Upload combined file back to s3
            s3_client = boto3.client('s3')
            s3_client.upload_file(tmp_combined_file, s3_bucket, s3_basepath + 'combined')

            # Create the working directory
            mkdir(working_directory)

            from chunk import chunk
            mkdir(os.path.join(working_directory, 'downloadandchunk'))
            file_names = chunk.chunk_by_byte(
                tmp_combined_file,
                os.path.join(working_directory, 'downloadandchunk'),
                100000 * 40  # 100,000 records, 40 bytes per record
            )

            os.remove(tmp_combined_file)

            send_success(meta_data, {"Filenames": file_names})

        elif script == 'sessionprocess2':
            print('Running sessionprocess2()')
            load_parameters(['MS_MODEL', 'MS_SCALER'])
            # Use theano backend for keras
            os.environ['KERAS_BACKEND'] = 'theano'
            from sessionProcess2 import sessionProcess
            sessionProcess.script_handler(
                working_directory,
                input_data.get('Filename', None),
                input_data
            )
            send_success(meta_data, {})

        elif script == 'noop':
            print('Noop job')
            # A noop job used as a 'gate', using job dependencies to recombine parallel tasks
            send_success(meta_data, {})

        elif script == 'scoring':
            print('Running scoring()')
            from scoring import scoringProcess
            boundaries = scoringProcess.script_handler(
                working_directory,
                input_data.get('Filenames', None),
                input_data
            )
            print(boundaries)

            # Chunk files for input to writemongo
            from chunk import chunk
            mkdir(os.path.join(working_directory, 'scoring_chunked'))
            file_names = chunk.chunk_by_line(
                os.path.join(working_directory, 'scoring'),
                os.path.join(working_directory, 'scoring_chunked'),
                boundaries
            )

            send_success(meta_data, {"Filenames": file_names})

        elif script == 'aggregatesession':
            print('Computing session aggregations')
            load_parameters([
                'MONGO_HOST_SESSION',
                'MONGO_USER_SESSION',
                'MONGO_PASSWORD_SESSION',
                'MONGO_DATABASE_SESSION',
                'MONGO_COLLECTION_SESSION',
                'MONGO_REPLICASET_SESSION',
            ])
            from sessionAgg import agg_session
            agg_session.script_handler(
                working_directory,
                input_data
            )
            send_success(meta_data, {})

        elif script == 'aggregatetwomin':
            print('Computing two minute aggregations')
            load_parameters([
                'MONGO_HOST_TWOMIN',
                'MONGO_USER_TWOMIN',
                'MONGO_PASSWORD_TWOMIN',
                'MONGO_DATABASE_TWOMIN',
                'MONGO_COLLECTION_TWOMIN',
                'MONGO_REPLICASET_TWOMIN',
            ])
            from twoMinuteAgg import agg_twomin
            agg_twomin.script_handler(
                working_directory,
                input_data.get('Filename', None),
                input_data
            )
            send_success(meta_data, {})

        elif script == 'aggregatedateuser':
            print('Computing date-user aggregations')
            load_parameters([
                'MONGO_HOST_SESSION',
                'MONGO_USER_SESSION',
                'MONGO_PASSWORD_SESSION',
                'MONGO_DATABASE_SESSION',
                'MONGO_REPLICASET_SESSION',
                'MONGO_COLLECTION_SESSION',
                'MONGO_COLLECTION_DATE',
            ])
            from dateAggUser import agg_date_user

            agg_date_user.script_handler(
                input_data
            )
            send_success(meta_data, {})

        elif script == 'aggregateprogcomp':
            print('Computing program composition aggregations')
            load_parameters([
                'MONGO_HOST_SESSION',
                'MONGO_USER_SESSION',
                'MONGO_PASSWORD_SESSION',
                'MONGO_DATABASE_SESSION',
                'MONGO_REPLICASET_SESSION',
                'MONGO_COLLECTION_PROGCOMP',
            ])
            from progComp import prog_comp

            prog_comp.script_handler(
                working_directory,
                input_data
            )
            send_success(meta_data, {})

        elif script == 'aggregateprogcompdate':
            print('Computing program composition date aggregations')
            load_parameters([
                'MONGO_HOST_SESSION',
                'MONGO_USER_SESSION',
                'MONGO_PASSWORD_SESSION',
                'MONGO_DATABASE_SESSION',
                'MONGO_REPLICASET_SESSION',
                'MONGO_COLLECTION_PROGCOMP',
                'MONGO_COLLECTION_PROGCOMPDATE',
            ])
            from progCompDate import prog_comp_date

            prog_comp_date.script_handler(
                input_data
            )
            send_success(meta_data, {})

        elif script == 'aggregateteam':
            print('Computing team aggregations')
            load_parameters([
                'MONGO_HOST_SESSION',
                'MONGO_USER_SESSION',
                'MONGO_PASSWORD_SESSION',
                'MONGO_DATABASE_SESSION',
                'MONGO_REPLICASET_SESSION',
                'MONGO_COLLECTION_DATE',
                'MONGO_COLLECTION_DATETEAM',
                'MONGO_COLLECTION_PROGCOMPDATE',
                'MONGO_HOST_TWOMIN',
                'MONGO_USER_TWOMIN',
                'MONGO_PASSWORD_TWOMIN',
                'MONGO_DATABASE_TWOMIN',
                'MONGO_REPLICASET_TWOMIN',
                'MONGO_COLLECTION_TWOMIN',
                'MONGO_COLLECTION_TWOMINTEAM',
            ])
            from teamAgg import agg_team

            agg_team.script_handler(
                input_data
            )
            send_success(meta_data, {})

        elif script == 'aggregatetraininggroup':
            print('Computing training group aggregations')
            load_parameters([
                'MONGO_HOST_SESSION',
                'MONGO_USER_SESSION',
                'MONGO_PASSWORD_SESSION',
                'MONGO_DATABASE_SESSION',
                'MONGO_REPLICASET_SESSION',
                'MONGO_COLLECTION_DATE',
                'MONGO_COLLECTION_DATETG',
                'MONGO_COLLECTION_PROGCOMP',
                'MONGO_COLLECTION_PROGCOMPDATE',
                'MONGO_HOST_TWOMIN',
                'MONGO_USER_TWOMIN',
                'MONGO_PASSWORD_TWOMIN',
                'MONGO_DATABASE_TWOMIN',
                'MONGO_REPLICASET_TWOMIN',
                'MONGO_COLLECTION_TWOMIN',
                'MONGO_COLLECTION_TWOMINTG',
            ])
            from TGAgg import agg_tg

            agg_tg.script_handler(
                input_data
            )
            send_success(meta_data, {})

        elif script == 'cleanup':
            print('Cleaning up intermediate files')
            from cleanup import cleanup
            cleanup.script_handler(
                working_directory
            )
            send_success(meta_data, {})

        else:
            raise Exception("Unknown batchjob '{}'".format(script))

    except Exception as e:
        print(e)
        send_failure(meta_data, e)
        raise


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError("Type not serializable")
