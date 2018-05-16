import jwt
import os
import requests
import unittest


class BaseTest(unittest.TestCase):
    host = 'https://apis.dev.fathomai.com/preprocessing'
    endpoint = None
    method = None
    body = None
    authorization = None
    expected_status = None
    headers = {}

    longMessage = True

    def _get_headers(self):
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'biometrix apitest',
        }
        if self.authorization is not None:
            headers['Authorization'] = self.authorization
        headers.update(self.headers)
        return headers

    def validate_response(self, body, headers, status):
        pass

    def validate_aws_pre(self):
        pass

    def validate_aws_post(self):
        pass

    def test(self):
        if self.endpoint is None:
            # Still in the base class
            self.skipTest('Base class')
            return
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
            self.fail('Unsupported method')

        self.assertEqual(self.expected_status, res.status_code, msg=res.json().get('message', ''))

        if 200 <= res.status_code < 300:
            self.validate_response(res.json(), res.headers, res.status_code)

        self.validate_aws_post()


def get_api_service_token():
    # TODO
    return jwt.encode({'sub': '00000000-0000-4000-8000-000000000000'}, 'secret', algorithm='HS256')
