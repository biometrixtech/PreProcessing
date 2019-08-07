import jwt
from tests.routes.core import execute_api, jwt_token


def get_api_service_token():
    # TODO
    return jwt.encode({'sub': '00000000-0000-4000-8000-000000000000'}, 'secret', algorithm='HS256')


def test_status_no_auth():
    endpoint = 'status'
    method = 'POST'
    expected_status = 401
    execute_api(endpoint, method, None, expected_status, None, 'CREATE_COMPLETE')


def test_status_wrong_method():
    endpoint = 'status'
    method = 'GET'
    authorization = jwt_token
    expected_status = 405
    execute_api(endpoint, method, None, expected_status, authorization, 'CREATE_COMPLETE')


def test_status_no_user_in_jwt():
    endpoint = 'status'
    method = 'POST'
    authorization = get_api_service_token()
    expected_status = 401
    execute_api(endpoint, method, None, expected_status, authorization, 'CREATE_COMPLETE')


def test_status_empty_body():
    endpoint = 'status'
    method = 'POST'
    authorization = jwt_token
    body = None
    expected_status = 500
    execute_api(endpoint, method, body, expected_status, authorization, 'CREATE_COMPLETE')


def test_status():
    endpoint = 'status'
    method = 'POST'
    authorization = jwt_token
    body = {'start_date': '2018-04-20', 'end_date': '2018-04-24'}
    expected_status = 200
    execute_api(endpoint, method, body, expected_status, authorization, 'CREATE_COMPLETE')

    # not sure what statuses should be returned for this method:
    # def validate_response(self, body, headers, status):
    #     self.assertIn('sessions', body)
    #     sessions = body['sessions']
    #     self.assertIn("PROCESSING_COMPLETE", sessions)
    #     self.assertIn("PROCESSING_FAILED", sessions)
    #     self.assertIn("PROCESSING_IN_PROGRESS", sessions)
    #     self.assertIn("UPLOAD_COMPLETE", sessions)
    #     self.assertIn("UPLOAD_IN_PROGRESS", sessions)