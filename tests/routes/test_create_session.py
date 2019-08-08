from tests.routes.core import execute_api, jwt_token


def test_session_create_no_auth(set_up):
    endpoint = 'session'
    method = 'POST'
    expected_status = 401
    execute_api(endpoint, method, None, expected_status, None, 'CREATE_COMPLETE')


def test_session_create_wrong_method(set_up):
    endpoint = 'session'
    method = 'GET'
    authorization = jwt_token
    expected_status = 405
    execute_api(endpoint, method, None, expected_status, authorization, 'CREATE_COMPLETE')


def test_session_create_empty_body(set_up):
    endpoint = 'session'
    method = 'POST'
    authorization = jwt_token
    body = None
    expected_status = 400
    execute_api(endpoint, method, body, expected_status, authorization, 'CREATE_COMPLETE')



