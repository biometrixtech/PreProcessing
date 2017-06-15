#!/usr/bin/env python
# Entrypoint when called as a batch job
import boto3
import json
import sys


def send_success(meta):
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
                "Output": {}
            })
        )

    
def send_failure(meta):
    pass


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

            downloadAndChunk.script_handler(input_data.get('S3Bucket', None), input_data.get('S3Path', None))

            send_success(meta_data)

    except Exception:
        send_failure(meta_data)
        raise
