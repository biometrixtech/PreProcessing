from base_test import BaseTest
import boto3
from boto3.dynamodb.conditions import Key, Attr

# This has username = '00:00:00:00:00'
jwt_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6IjAwOjAwOjAwOjAwOjAwIn0._EtGIW4hbbJAbAywUrtonMwZgQuuU8dSyOrPZEF6TJE'

sessions_table = boto3.resource('dynamodb').Table('preprocessing-dev-ingest-sessions')


def _query_dynamodb(resource, key_condition_expression):
    ret = resource.query(
        Select='ALL_ATTRIBUTES',
        Limit=10000,
        KeyConditionExpression=key_condition_expression,
    )
    return ret['Items'][0] if len(ret['Items']) else None


class TestSessionCreateNoAuth(BaseTest):
    endpoint = 'session'
    method = 'POST'
    expected_status = 401


class TestSessionCreateWrongMethod(BaseTest):
    endpoint = 'session'
    method = 'GET'
    authorization = jwt_token
    expected_status = 405


class TestSessionCreateEmptyBody(BaseTest):
    endpoint = 'session'
    method = 'POST'
    authorization = jwt_token
    body = None
    expected_status = 400


class TestSessionCreateOneSensor(BaseTest):
    endpoint = 'session'
    method = 'POST'
    authorization = jwt_token
    body = {'event_date': '2001-01-01T01:23:45Z', 'sensors': ['11:11:11:11:11']}
    expected_status = 201
    expected_id = '911bffe6-2649-5b74-825a-7481bdf5920e'

    def validate_aws_pre(self):
        existing = _query_dynamodb(sessions_table, Key('id').eq(self.expected_id))
        if existing is not None:
            self.fail('Session should not exist prior to test')

    def validate_aws_post(self):
        res = _query_dynamodb(sessions_table, Key('id').eq(self.expected_id))
        if res is None:
            self.fail('Session should exist after test')
        self.assertIn('id', res)
        self.assertEqual(self.expected_id, res['id'])

    def validate_response(self, body, headers, status):
        self.assertIn('session', body)
        session = body['session']
        self.assertIn('id', session)
        self.assertEqual(self.expected_id, session['id'])
        self.assertIn('session_status', session)
        self.assertEqual('CREATE_COMPLETE', session['session_status'])

    def setUp(self):
        sessions_table.delete_item(Key={'id': self.expected_id})

    def tearDown(self):
        sessions_table.delete_item(Key={'id': self.expected_id})
