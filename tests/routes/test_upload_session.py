from tests.routes.core import execute_api, jwt_token


def test_session_upload_no_auth():
    endpoint = 'session/911bffe6-2649-5b74-825a-7481bdf5920e/upload'
    method = 'POST'
    expected_status = 401
    execute_api(endpoint, method, None, expected_status, None, 'CREATE_COMPLETE')


def test_session_upload_invalid_uuid():
    endpoint = 'session/foobar/upload'
    method = 'POST'
    authorization = jwt_token
    expected_status = 400
    execute_api(endpoint, method, None, expected_status, authorization, 'CREATE_COMPLETE')


def test_session_upload_non_existent():
    endpoint = 'session/00000000-0000-4000-8000-000000000000/upload'
    method = 'POST'
    authorization = jwt_token
    expected_status = 404
    execute_api(endpoint, method, None, expected_status, authorization, 'CREATE_COMPLETE')