#!/usr/bin/env python
# Entrypoint when called as a batch job
import os
from datetime import datetime
import boto3
import json
import sys


def send_success(meta, output):
    if 'TaskToken' in meta:
        sfn_client = boto3.client('stepfunctions', region_name='us-east-1')
        sfn_client.send_task_success(
            taskToken=meta['TaskToken'],
            output=json.dumps({
                "Meta": {
                    "ExecutionArn": meta.get('ExecutionArn', None),
                    "BatchJob": {
                        "Id": '',
                        "Name": ''
                    },
                    "TaskToken": meta.get('TaskToken')
                },
                "Status": 'SUCCEEDED',
                "Output": output
            })
        )

    
def send_failure(meta, exception):
    if 'TaskToken' in meta:
        sfn_client = boto3.client('stepfunctions', region_name='us-east-1')
        sfn_client.send_task_failure(
            taskToken=meta['TaskToken'],
            error="An exception was thrown",
            cause=json.dumps(exception)
        )


def load_parameters(keys):
    print('Retrieving configuration from SSM')
    ssm_client = boto3.client('ssm', region_name='us-east-1')
    response = ssm_client.get_parameters(
        Names=['preprocessing.{}.{}'.format(os.environ['ENVIRONMENT'], key.lower()) for key in keys],
        WithDecryption=True
    )
    params = {p['Name'].split('.')[-1].upper(): p['Value'] for p in response['Parameters']}
    # Export to environment
    for k, v in params.items():
        os.environ[k] = v
    return params


if __name__ == '__main__':
    input_data = meta_data = None
    print(sys.argv)

    try:
        script = sys.argv[1]
        input_data = json.loads(sys.argv[2])
        meta_data = json.loads(sys.argv[3])

        print([script, input_data, meta_data])

        if script == 'downloadandchunk':
            print('Running downloadAndChunk()')
            from downloadAndChunk import downloadAndChunk
            res = downloadAndChunk.script_handler(input_data.get('S3Bucket', None), input_data.get('S3Path', None))
            send_success(meta_data, res)

        elif script == 'sessionprocess2':
            print('Running downloadAndChunk()')
            load_parameters(['MS_MODEL'])
            from sessionProcess2 import sessionProcess
            sessionProcess.script_handler(
                input_data.get('Filename', None),
                input_data.get('Data', {})
            )
            send_success(meta_data, {})

        elif script == 'noop':
            # A noop job used as a 'gate', using job dependencies to recombine parallel tasks
            send_success(meta_data, {})

        elif script == 'scoring':
            print('Running scoring()')
            from scoring import scoringProcess
            output_file = scoringProcess.script_handler(
                input_data.get('Filenames', None),
                input_data.get('Data', {})
            )
            send_success(meta_data, {"Filename": output_file})

        elif script == 'writemongo':
            print('Uploading to mongodb database')
            from writemongo import writemongo
            writemongo.script_handler(
                input_data.get('Filename', None)
            )

    except Exception:
        send_failure(meta_data)
        raise


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError("Type not serializable")
