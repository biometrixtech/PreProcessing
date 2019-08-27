from .base_test import BaseTest, get_api_service_token
import boto3
import time
from boto3.dynamodb.conditions import Key, Attr

# This has username = '00:00:00:00:00'
jwt_token = get_api_service_token('00:00:00:00:00')

sessions_table = boto3.resource('dynamodb').Table('preprocessing-dev-ingest-sessions')


def _query_dynamodb(resource, key_condition_expression):
    ret = resource.query(
        Select='ALL_ATTRIBUTES',
        Limit=10000,
        KeyConditionExpression=key_condition_expression,
        ConsistentRead=True,
    )
    return ret['Items'][0] if len(ret['Items']) else None


class TestSessionUploadNoAuth(BaseTest):
    endpoint = 'session/ab0bc061-7c79-5e64-a1f6-e6b900257ace/upload'
    method = 'POST'
    expected_status = 401


# class TestSessionUploadInvalidUuid(BaseTest):
#     endpoint = 'session/foobar/upload'
#     method = 'POST'
#     authorization = jwt_token
#     expected_status = 400


# class TestSessionUploadNonExistent(BaseTest):
#   # upload endpoint does not check if the session exists or not
#     endpoint = 'session/00000000-0000-4000-8000-000000000000/upload'
#     method = 'POST'
#     authorization = jwt_token
#     expected_status = 404
#     content_type = 'application/octet-stream'
#     body = "CHTlsVIAAAh/H/w/33v/deEvCH+j9QAwbeUlFGkIf4fyP+pdRpJmVwh05bFcAAAIfwv7v9l6y3PBPgh/o/"


class TestSessionUpload(BaseTest):
    endpoint = 'session/ab0bc061-7c79-5e64-a1f6-e6b900257ace/upload'
    method = 'POST'
    authorization = jwt_token
    expected_status = 202
    content_type = 'application/octet-stream'
    body = "CHTlsVIAAAh/H/w/33v/deEvCH+j9QAwbeUlFGkIf4fyP+pdRpJmVwh05bFcAAAIfwv7v9l6y3PBPgh/o/"
    expected_id = 'ab0bc061-7c79-5e64-a1f6-e6b900257ace'

    def setUp(self):
        sessions_table.put_item(Item={
            'accessory_id': '00:00:00:00:00',
            'created_dateString': '2018-05-14T22:18:22Z',
            'event_date': '2001-01-01T01:23:45Z',
            'id': 'ab0bc061-7c79-5e64-a1f6-e6b900257ace',
            'sensor_ids': ['11:11:11:11:11'],
            'session_status': 'CREATE_COMPLETE',
            'updated_date':	'2018-05-14T22:18:22Z',
            'version': '2.3',
        })
        pass

    def tearDown(self):
        sessions_table.delete_item(Key={'id': self.expected_id})
        pass