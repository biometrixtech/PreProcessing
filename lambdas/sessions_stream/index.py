import boto3
import datetime
import decimal
import json
import os
import time

from fathomapi.comms.service import Service

logs_client = boto3.client('logs')


def handler(event, _):
    print(json.dumps(event))
    for record in event['Records']:
        if record['eventName'] == 'REMOVE':
            continue

        new_object = load_obj(record['dynamodb'].get('NewImage', {}))
        old_object = load_obj(record['dynamodb'].get('OldImage', {}))

        changes = {k: (old_object.get(k, None), new_object.get(k, None)) for k, _ in
                   set(new_object.items()).symmetric_difference(set(old_object.items()))}

        if 'session_status' in changes and changes['session_status'][1] == 'UPLOAD_COMPLETE':
            print('Beginning SFN execution')
            trigger_sfn(new_object['id'], new_object.get('version', '2.3'))

        if 'user_id' in changes and new_object['user_id'] != '---':
            print('Loading data from users service')
            user = Service('users', '2_0').call_apigateway_sync('GET', f"user/{new_object['user_id']}").get('user', None)
            if user is not None:
                data = {'user_mass': decimal.Decimal(str(user['biometric_data']['mass']['kg']))}
                if 'teams' in user and len(user['teams']):
                    data['team_id'] = user['teams'][0]['id']
                if 'training_groups' in user and len(user['training_groups']):
                    data['training_group_ids'] = set([tg['id'] for tg in user['training_groups']])
                update_dynamodb(new_object['id'], data)

        if 'accessory_id' in changes:
            print('Loading data from hardware service')
            accessory = Service('hardware', '2_0').call_apigateway_sync('GET', f"accessory/{new_object['accessory_id']}").get('accessory', None)
            if accessory is not None:
                update_dynamodb(new_object['id'], {'user_id': accessory['owner_id'] or '---'})


def trigger_sfn(session_id, version):
    now = int(datetime.datetime.utcnow().timestamp())
    execution_name = '{}-{}'.format(session_id, int(time.time()))
    logs_client.create_log_stream(
        logGroupName=os.environ['LOG_GROUP_NAME'],
        logStreamName=execution_name
    )
    logs_client.put_log_events(
        logGroupName=os.environ['LOG_GROUP_NAME'],
        logStreamName=execution_name,
        logEvents=[{'timestamp': now * 1000, 'message': 'SFN Execution triggered'}]
    )
    boto3.client('stepfunctions').start_execution(
        stateMachineArn=os.environ['STATE_MACHINE_ARN'],
        name=execution_name,
        input=json.dumps({
            "Meta": {"ExecutionName": execution_name},
            "SourceEvent": {"SessionId": session_id, "SensorDataFileVersion": version}
        })
    )


def load_obj(record):
    def cast(t, v):
        return {
            'S': lambda x: x,
            'N': lambda x: float(x),
            'SS': lambda x: frozenset(x),
            'L': lambda x: tuple(load_obj(x)),
            'NULL': lambda x: None,
        }[t](v)

    if isinstance(record, dict):
        return {attr_name: cast(*list(v.items())[0]) for attr_name, v in record.items()}
    elif isinstance(record, list):
        return [cast(*list(v.items())[0]) for v in record]


def update_dynamodb(session_id, updates):
    updates = {k: v for k, v in updates.items() if v is not None}
    update_expression = 'SET {} '.format(', '.join(["{} = :{}".format(k, k) for k in updates.keys()]))
    values = {':' + k: v for (k, v) in updates.items()}
    print('Updating {} with parameters {}'.format(update_expression, values))
    boto3.resource('dynamodb').Table(os.environ['DYNAMODB_TABLE_NAME']).update_item(
        Key={'id': session_id},
        UpdateExpression=update_expression,
        ExpressionAttributeValues=values,
    )


if __name__ == '__main__':
    print('Running')
    data_in = {
        "Records": [
            {
                "eventID": "a04a08498323203e66237c7d0eee86ec",
                "eventName": "INSERT",
                "eventVersion": "1.1",
                "eventSource": "aws:dynamodb",
                "awsRegion": "us-west-2",
                "dynamodb": {
                    "ApproximateCreationDateTime": 1549646155,
                    "Keys": {
                        "id": {
                            "S": "4a5713d1-61b0-4936-911b-f247496b7f06"
                        }
                    },
                    "NewImage": {
                        "trainingGroupIds": {
                            "L": [
                                {
                                    "S": "073ab1da-0fb3-458b-8479-f046b55b7375"
                                }
                            ]
                        },
                        "teamId": {
                            "S": "ac827039-cecc-4e7c-881b-71de423ffb42"
                        },
                        "sessionStatus": {
                            "S": "PROCESSING_COMPLETE"
                        },
                        "id": {
                            "S": "4a5713d1-61b0-4936-911b-f247496b7f06"
                        },
                        "updatedDate": {
                            "S": "2018-04-16T21:10:45Z"
                        },
                        "updated_date": {
                            "S": "2019-02-08T17:15:53Z"
                        },
                        "session_status": {
                            "S": "UPLOAD_IN_PROGRESS"
                        },
                        "userId": {
                            "S": "cc72e186-16a8-42ca-9151-61f78fbc312d"
                        },
                        "version": {
                            "S": "2.3"
                        },
                        "eventDate": {
                            "S": "2018-03-21T19:07:11z"
                        }
                    },
                    "SequenceNumber": "1747524900000000000580872130",
                    "SizeBytes": 382,
                    "StreamViewType": "NEW_AND_OLD_IMAGES"
                },
                "eventSourceARN": "arn:aws:dynamodb:us-west-2:887689817172:table/preprocessing-dev-ingest-sessions/stream/2018-02-06T16:36:26.162"
            }
        ]
    }

    handler(data_in, None)
