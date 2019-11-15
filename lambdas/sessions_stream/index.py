import boto3
from datetime import datetime, timezone
import decimal
import json
import os
import time

from fathomapi.comms.service import Service

logs_client = boto3.client('logs')


USERS_API_VERSION = '2_4'
HARDWARE_API_VERSION = '2_0'
SERVICE_TOKEN = None

def handler(event, _):
    print(json.dumps(event))
    for record in event['Records']:
        if record['eventName'] == 'REMOVE':
            continue

        new_object = load_obj(record['dynamodb'].get('NewImage', {}))
        old_object = load_obj(record['dynamodb'].get('OldImage', {}))

        changes = {k: (old_object.get(k, None), new_object.get(k, None)) for k, _ in
                   set(new_object.items()).symmetric_difference(set(old_object.items()))}

        if 'session_status' in changes and changes['session_status'][1] == 'UPLOAD_IN_PROGRESS':
            print('UPLOAD STARTED')
            if 'user_id' in new_object and new_object['user_id'] != "---":
                _notify_user(new_object['user_id'])

        if 'session_status' in changes and changes['session_status'][1] == 'UPLOAD_COMPLETE':
            print('Beginning SFN execution')
            trigger_sfn(new_object['id'], new_object.get('version', '2.3'))

        if 'user_id' in changes and 'user_id' in new_object and new_object['user_id'] != '---':
            print('Loading data from users service')
            # if SERVICE_TOKEN is None:
            #     SERVICE_TOKEN = invoke_lambda_sync(f'users-{os.environ["ENVIRONMENT"]}-apigateway-serviceauth', '2_0')['token']
            user = Service('users', USERS_API_VERSION).call_apigateway_sync('GET', f"user/{new_object['user_id']}").get('user', None)
            if user is not None:
                try:
                    user_mass = user['biometric_data']['mass']['kg']
                except:
                    user_mass = 70
                data = {'user_mass': decimal.Decimal(str(user_mass)),
                        'plans_api_version': user.get('plans_api_version', None) or '4_4'}
                update_dynamodb(new_object['id'], data)

        if 'accessory_id' in changes:
            print('Loading data from hardware service')
            accessory = Service('hardware', HARDWARE_API_VERSION).call_apigateway_sync('GET', f"accessory/{new_object['accessory_id']}").get('accessory', None)
            if accessory is not None:
                if 'user_id' in new_object and new_object['user_id'] != '---':
                    print("user_id already exists, do not need to update!")
                    update = {}
                else:
                    update = {'user_id': accessory['owner_id'] or '---'}
                if accessory.get('true_time') is not None:
                    update['last_true_time'] = decimal.Decimal(str(accessory['true_time']))
                # if accessory.get('clock_drift_rate') is not None and accessory.get('last_sync_date') is not None:
                #     try:
                #         event_date_epoch_time = _get_epoch_time(new_object['event_date'])
                #         last_sync_epoch_time = _get_epoch_time(accessory['last_sync_date'])
                #         time_since_last_update = event_date_epoch_time - last_sync_epoch_time
                #         if time_since_last_update > 0:
                #             adjustment = time_since_last_update * (accessory['clock_drift_rate'] - 1)  # unit is ms
                #             event_date_epoch_time += adjustment
                #             event_date = _format_datetime_from_epoch_time(event_date_epoch_time)
                #             update['event_date'] = event_date
                #             update['start_time_adjustment'] = str(adjustment)
                #             print(f"event_date: {new_object['event_date']}/ {event_date_epoch_time} \nlast_sync_date:{accessory['last_sync_date']}/ {last_sync_epoch_time} \n clock_drift_rate: {accessory['clock_drift_rate']} \nstart_time_adjustment: {adjustment}")
                #         else:
                #             print("Accessory synced after session started. Do not need to adjust")
                #             print(f"event_date: {new_object['event_date']}/ {event_date_epoch_time} \nlast_sync_date:{accessory['last_sync_date']}/ {last_sync_epoch_time}")
                #     except Exception as e:
                #         print(e)

                if len(update) > 0:
                    update_dynamodb(new_object['id'], update)


def trigger_sfn(session_id, version):
    now = int(datetime.utcnow().timestamp())
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
            "SourceEvent": {"SessionId": session_id, "SensorDataFileVersion": version, "EventType": "Session"}
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


def _get_epoch_time(time_string):
    if time_string is not None:
        return int(parse_datetime(time_string).replace(tzinfo=timezone.utc).timestamp() * 1000)  # get in ms resolution
    else:
        return None


def _format_datetime_from_epoch_time(epoch_time):
    # epoch time is is ms resolution utcfromtimestamp needs it to be in s resolution
    return datetime.utcfromtimestamp(epoch_time / 1000.).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def parse_datetime(date_input):
    for format_string in ["%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ"]:
        try:
            return datetime.strptime(date_input, format_string)
        except ValueError:
            pass
    raise ValueError('date_time must be in ISO8601 format')


def _notify_user(user_id):
    # if SERVICE_TOKEN is None:
    #     SERVICE_TOKEN = invoke_lambda_sync(f'users-{os.environ["ENVIRONMENT"]}-apigateway-serviceauth', '2_0')['token']
    users_service = Service('users', USERS_API_VERSION)
    body = {"message": "Your FathomPRO run has started uploading!",
            "call_to_action": "VIEW_PLAN",
            "expire_in": 15 * 60}  # expire in 15 mins
    users_service.call_apigateway_async(method='POST',
                                        endpoint=f'/user/{user_id}/notify',
                                        body=body)


def invoke_lambda_sync(function_name, version, payload=None):
    _lambda_client = boto3.client('lambda')
    res = _lambda_client.invoke(
        FunctionName=f'{function_name}:{version}',
        Payload=json.dumps(payload or {}),
    )
    return json.loads(res['Payload'].read())


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
