import jwt
import os
import requests
import unittest
import pytest
from botocore.exceptions import ClientError
from jose import jwt
import datetime
import json
import os
import uuid
import boto3


_secretsmanager_client = boto3.client('secretsmanager')
_secrets = {}

class BaseTest(object):
    host = 'https://apis.dev.fathomai.com/preprocessing/1_1/'
    endpoint = None
    method = None
    body = None
    authorization = None
    expected_status = None
    headers = {}
    content_type = None

    longMessage = True

    def _get_headers(self):
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'biometrix apitest',
        }
        if self.authorization is not None:
            headers['Authorization'] = self.authorization
        if self.content_type is not None:
            headers['Content-Type'] = self.content_type
        headers.update(self.headers)
        return headers

    def validate_response(self, body, headers, status):
        pass

    def validate_aws_pre(self):
        pass

    def validate_aws_post(self):
        pass

    def fail(self, text):
        print(text)
        pass

    def tearDown(self):
        pass

    def setUp(self):
        pass

    def test(self):

        self.setUp()

        endpoint = os.path.join(self.host, self.endpoint)

        self.validate_aws_pre()

        if self.method == 'GET':
            res = requests.get(endpoint, headers=self._get_headers())
        elif self.method == 'POST':
            res = requests.post(endpoint, json=self.body, headers=self._get_headers())
        elif self.method == 'POST-RAW':
            res = requests.post(endpoint, data=self.body, headers=self._get_headers())
        elif self.method == 'PATCH':
            res = requests.patch(endpoint, json=self.body, headers=self._get_headers())
        else:
            pytest.fail('Unsupported method')

        assert self.expected_status == res.status_code, res.json().get('message', '')

        if 200 <= res.status_code < 300:
            self.validate_response(res.json(), res.headers, res.status_code)

        self.validate_aws_post()
        self.tearDown()

    def assertIn(self, value, res):
        assert value in res

    def assertEqual(self, expected, actual):
        assert expected == actual


def get_api_service_token(sub='00000000-0000-4000-8000-000000000000'):
    delta = datetime.timedelta(days=1)
    rs256_key = get_secret('service_jwt_key')

    token = {
        "auth_time": 1538835893,
        "cognito:username": sub,
        "custom:role": "service",
        "event_id": str(uuid.uuid4()),
        "iss": 'test',
        "token_use": "id",
        'exp': datetime.datetime.utcnow() + delta,
        'iat': datetime.datetime.utcnow(),
        'sub': sub,
    }
    # return jwt.encode({'sub': '00000000-0000-4000-8000-000000000000'}, 'secret', algorithm='RS256')
    jwt_token = jwt.encode(token, rs256_key, headers={'kid': rs256_key['kid']}, algorithm='RS256')
    return jwt_token


def get_secret(secret_name):
    secret_name = secret_name.lower()
    print(f'Getting secret {secret_name}')
    global _secrets
    if secret_name not in _secrets:
        try:
            print(f'Loading from Secrets Manager')
            get_secret_value_response = _secretsmanager_client.get_secret_value(SecretId=f'users/{os.environ["ENVIRONMENT"]}/{secret_name}')
        except ClientError as e:
            raise Exception('SecretsManagerError', json.dumps(e.response), 500)
        else:
            if 'SecretString' in get_secret_value_response:
                _secrets[secret_name] = json.loads(get_secret_value_response['SecretString'])
            else:
                _secrets[secret_name] = get_secret_value_response['SecretBinary']
    print(f'Got secret {secret_name}')
    return _secrets[secret_name]