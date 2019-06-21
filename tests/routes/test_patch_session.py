from tests.routes.core import execute_api, jwt_token


def test_session_patch_no_auth(set_up):
    endpoint = 'session'
    method = 'PATCH'
    expected_status = 401
    execute_api(endpoint, method, None, expected_status, None, 'CREATE_COMPLETE')


def test_session_patch_invalid_uuid(set_up):
    endpoint = 'session/foobar'
    method = 'PATCH'
    authorization = jwt_token
    expected_status = 400
    execute_api(endpoint, method, None, expected_status, authorization, 'CREATE_COMPLETE')


def test_session_patch_non_existent(set_up):
    endpoint = 'session/00000000-0000-4000-8000-000000000000'
    method = 'PATCH'
    authorization = jwt_token
    expected_status = 404
    execute_api(endpoint, method, None, expected_status, authorization, 'CREATE_COMPLETE')


def test_session_patch_uip_to_uc(set_up):
    endpoint = 'session'
    method = 'PATCH'
    authorization = jwt_token
    body = {'session_status': 'UPLOAD_COMPLETE'}
    expected_status = 400
    execute_api(endpoint, method, body, expected_status, authorization, 'CREATE_COMPLETE')

