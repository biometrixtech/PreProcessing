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


class TestSessionPatchNoAuth(BaseTest):
    endpoint = 'session/911bffe6-2649-5b74-825a-7481bdf5920e'
    method = 'PATCH'
    expected_status = 401


class TestSessionPatchInvalidUuid(BaseTest):
    endpoint = 'session/foobar'
    method = 'PATCH'
    authorization = jwt_token
    expected_status = 400


class TestSessionPatchNonExistent(BaseTest):
    endpoint = 'session/00000000-0000-4000-8000-000000000000'
    method = 'PATCH'
    authorization = jwt_token
    expected_status = 404


class TestSessionPatchUipToUc(BaseTest):
    endpoint = 'session/911bffe6-2649-5b74-825a-7481bdf5920e'
    method = 'PATCH'
    authorization = jwt_token
    body = {'session_status': 'UPLOAD_COMPLETE'}
    expected_status = 400
    expected_id = '911bffe6-2649-5b74-825a-7481bdf5920e'

    def validate_aws_pre(self):
        existing = _query_dynamodb(sessions_table, Key('id').eq(self.expected_id))
        if existing is None:
            self.fail('Session should exist prior to test')
        self.assertIn('session_status', existing)
        self.assertEqual('CREATE_COMPLETE', existing['session_status'])

    def validate_aws_post(self):
        res = _query_dynamodb(sessions_table, Key('id').eq(self.expected_id))
        if res is None:
            self.fail('Session should exist after test')
        self.assertIn('id', res)
        self.assertEqual(self.expected_id, res['id'])
        self.assertIn('session_status', res)
        self.assertEqual('CREATE_COMPLETE', res['session_status'])

    def validate_response(self, body, headers, status):
        self.assertIn('session', body)
        session = body['session']
        self.assertIn('id', session)
        self.assertEqual(self.expected_id, session['id'])

    def setUp(self):
        sessions_table.put_item(Item={
            'accessory_id': '00:00:00:00:00',
            'created_dateString': '2018-05-14T22:18:22Z',
            'event_date': '2001-01-01T01:23:45Z',
            'id': '911bffe6-2649-5b74-825a-7481bdf5920e',
            'sensor_ids': ['11:11:11:11:11'],
            'session_status': 'CREATE_COMPLETE',
            'updated_date':	'2018-05-14T22:18:22Z',
            'version': '2.3',
        })
        pass

    def tearDown(self):
        sessions_table.delete_item(Key={'id': self.expected_id})
        pass
