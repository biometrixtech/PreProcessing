from base_test import BaseTest, get_api_service_token
import boto3
import time
from boto3.dynamodb.conditions import Key, Attr

# This has username = '00:00:00:00:00'
jwt_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6IjAwOjAwOjAwOjAwOjAwIn0._EtGIW4hbbJAbAywUrtonMwZgQuuU8dSyOrPZEF6TJE'

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
    endpoint = 'session/911bffe6-2649-5b74-825a-7481bdf5920e/upload'
    method = 'POST'
    expected_status = 401


class TestSessionUploadInvalidUuid(BaseTest):
    endpoint = 'session/foobar/upload'
    method = 'POST'
    authorization = get_api_service_token()
    expected_status = 400


class TestSessionUploadNonExistent(BaseTest):
    endpoint = 'session/00000000-0000-4000-8000-000000000000/upload'
    method = 'POST'
    authorization = get_api_service_token()
    expected_status = 404
