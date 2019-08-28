from .base_test import BaseTest, get_api_service_token
import boto3
from boto3.dynamodb.conditions import Key, Attr

# This has username = '00:00:00:00:00'
jwt_token = get_api_service_token('00:00:00:00:00')

sessions_table = boto3.resource('dynamodb').Table('preprocessing-dev-ingest-sessions')


def _query_dynamodb(resource, key_condition_expression):
    ret = resource.query(
        Select='ALL_ATTRIBUTES',
        Limit=10000,
        KeyConditionExpression=key_condition_expression,
    )
    return ret['Items'][0] if len(ret['Items']) else None


class TestSessionGetNoAuth(BaseTest):
    endpoint = 'session/911bffe6-2649-5b74-825a-7481bdf5920e'
    method = 'GET'
    expected_status = 401


class TestSessionGetWrongMethod(BaseTest):
    endpoint = 'session/911bffe6-2649-5b74-825a-7481bdf5920e'
    method = 'POST'
    authorization = jwt_token
    expected_status = 405


# class TestSessionGetInvalidUuid(BaseTest):
#     endpoint = 'session/foobar'
#     method = 'GET'
#     authorization = jwt_token
#     expected_status = 400


class TestSessionGetNonExistent(BaseTest):
    endpoint = 'session/00000000-0000-4000-8000-000000000000'
    method = 'GET'
    authorization = jwt_token
    expected_status = 404


class TestSessionGet(BaseTest):
    endpoint = 'session/ab0bc061-7c79-5e64-a1f6-e6b900257ace'
    method = 'GET'
    authorization = jwt_token
    expected_status = 200
    expected_id = 'ab0bc061-7c79-5e64-a1f6-e6b900257ace'

    def validate_aws_pre(self):
        existing = _query_dynamodb(sessions_table, Key('id').eq(self.expected_id))
        if existing is None:
            self.fail('Session should exist prior to test')

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


class TestSessionGetProcessingInProgress(BaseTest):
    endpoint = 'session/ab0bc061-7c79-5e64-a1f6-e6b900257ace'
    method = 'GET'
    authorization = jwt_token
    expected_status = 200
    expected_id = 'ab0bc061-7c79-5e64-a1f6-e6b900257ace'

    def validate_aws_pre(self):
        existing = _query_dynamodb(sessions_table, Key('id').eq(self.expected_id))
        if existing is None:
            self.fail('Session should exist prior to test')

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
        self.assertEqual('PROCESSING_IN_PROGRESS', session['session_status'])

    def setUp(self):
        sessions_table.put_item(Item={
            'accessory_id': '00:00:00:00:00',
            'created_dateString': '2018-05-14T22:18:22Z',
            'event_date': '2001-01-01T01:23:45Z',
            'id': 'ab0bc061-7c79-5e64-a1f6-e6b900257ace',
            'sensor_ids': ['11:11:11:11:11'],
            'session_status': 'PROCESSING_IN_PROGRESS',
            'updated_date':	'2018-05-14T22:18:22Z',
            'version': '2.3',
        })
        pass

    def tearDown(self):
        sessions_table.delete_item(Key={'id': self.expected_id})
        pass
