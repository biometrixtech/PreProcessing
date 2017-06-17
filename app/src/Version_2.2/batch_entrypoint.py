#!/usr/bin/env python
# Entrypoint when called as a batch job
import os

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

    
def send_failure(meta):
    pass


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
            all_output_files = downloadAndChunk.script_handler(input_data.get('S3Bucket', None), input_data.get('S3Path', None))
            send_success(meta_data, {"Filenames": all_output_files})

        elif script == 'sessionprocess2':
            print('Running downloadAndChunk()')
            load_parameters(['DB_HOST', 'DB_USERNAME', 'DB_PASSWORD', 'DB_NAME', 'MS_MODEL'])
            from sessionProcess2 import sessionProcess
            sessionProcess.script_handler(input_data.get('Filename', None))
            send_success(meta_data, {})

        elif script == 'noop':
            # A noop job used as a 'gate', using job dependencies to recombine parallel tasks
            send_success(meta_data, {})

        elif script == 'scoring':
            print('Running scoring()')
            # load_parameters(['DB_HOST', 'DB_USERNAME', 'DB_PASSWORD', 'DB_NAME'])
            from scoring import scoringProcess
            scoringProcess.script_handler(input_data.get('Filenames', None))
            send_success(meta_data, {})

    except Exception:
        send_failure(meta_data)
        raise
