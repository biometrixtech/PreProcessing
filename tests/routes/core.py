import os
import pytest
import boto3
import requests
import jwt
from boto3.dynamodb.conditions import Key, Attr

# This has username = '00:00:00:00:00'
jwt_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6IjAwOjAwOjAwOjAwOjAwIn0._EtGIW4hbbJAbAywUrtonMwZgQuuU8dSyOrPZEF6TJE'
sessions_table = boto3.resource('dynamodb').Table('preprocessing-dev-ingest-sessions')
expected_id = '911bffe6-2649-5b74-825a-7481bdf5920e'
host = 'https://apis.dev.fathomai.com/preprocessing'


@pytest.fixture(scope="function")
def set_up(request):
    sessions_table.delete_item(Key={'id': expected_id})

    def tear_down():
        sessions_table.delete_item(Key={'id': expected_id})

    request.addfinalizer(tear_down)


def get_api_service_token():
    # TODO
    return jwt.encode({'sub': '00000000-0000-4000-8000-000000000000'}, 'secret', algorithm='HS256')


def _query_dynamodb(resource, key_condition_expression):
    ret = resource.query(
        Select='ALL_ATTRIBUTES',
        Limit=10000,
        KeyConditionExpression=key_condition_expression,
        ConsistentRead=True,  # added this to all tests; was originally just for uploading
    )
    return ret['Items'][0] if len(ret['Items']) else None


def _get_headers(authorization):
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'biometrix apitest',
    }
    if authorization is not None:
        headers['Authorization'] = authorization
    headers.update(headers)
    return headers


def validate_aws_pre():
    existing = _query_dynamodb(sessions_table, Key('id').eq(expected_id))
    assert existing is None, 'Session should not exist prior to test'


def validate_aws_post():
    res = _query_dynamodb(sessions_table, Key('id').eq(expected_id))
    assert res is not None, 'Session should exist after test'
    assert 'id' in res
    assert expected_id == res['id']


def execute_api(endpoint, method, body, expected_status, authorization, response_message):

    endpoint = os.path.join(host, endpoint)

    validate_aws_pre()

    if method == 'GET':
        res = requests.get(endpoint, headers=_get_headers(authorization))
    elif method == 'POST':
        res = requests.post(endpoint, json=body, headers=_get_headers(authorization))
    elif method == 'POST-RAW':
        res = requests.post(endpoint, data=body, headers=_get_headers(authorization))
    elif method == 'PATCH':
        res = requests.patch(endpoint, json=body, headers=_get_headers(authorization))
    else:
        pytest.fail('Unsupported method')

    assert expected_status == res.status_code, res.json().get('message', '')

    if 200 <= res.status_code < 300:
        validate_response(res.json(), res.headers, res.status_code, response_message)

    validate_aws_post()


def validate_response(body, headers, status, message):
    assert 'session' in body
    session = body['session']
    assert 'id' in session
    assert expected_id == session['id']
    assert 'session_status' in session
    assert message == session['session_status']

