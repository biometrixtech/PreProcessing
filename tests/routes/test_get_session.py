import pytest
from tests.routes.core import execute_api, jwt_token, sessions_table, expected_id


@pytest.fixture(scope="function")
def session_set_up(request):
    sessions_table.put_item(Item={
        'accessory_id': '00:00:00:00:00',
        'created_dateString': '2018-05-14T22:18:22Z',
        'event_date': '2001-01-01T01:23:45Z',
        'id': '911bffe6-2649-5b74-825a-7481bdf5920e',
        'sensor_ids': ['11:11:11:11:11'],
        'session_status': 'CREATE_COMPLETE',
        'updated_date': '2018-05-14T22:18:22Z',
        'version': '2.3',
    })

    def tear_down():
        sessions_table.delete_item(Key={'id': expected_id})

    request.addfinalizer(tear_down)


@pytest.fixture(scope="function")
def processing_set_up(request):
    sessions_table.put_item(Item={
        'accessory_id': '00:00:00:00:00',
        'created_dateString': '2018-05-14T22:18:22Z',
        'event_date': '2001-01-01T01:23:45Z',
        'id': '911bffe6-2649-5b74-825a-7481bdf5920e',
        'sensor_ids': ['11:11:11:11:11'],
        'session_status': 'PROCESSING_IN_PROGRESS',
        'updated_date': '2018-05-14T22:18:22Z',
        'version': '2.3',
    })

    def tear_down():
        sessions_table.delete_item(Key={'id': expected_id})

    request.addfinalizer(tear_down)


def test_session_get_no_auth(set_up):
    endpoint = 'session/911bffe6-2649-5b74-825a-7481bdf5920e'
    method = 'GET'
    expected_status = 401
    execute_api(endpoint, method, None, expected_status, None, 'PROCESSING_IN_PROGRESS')


def test_session_get_wrong_method(set_up):
    endpoint = 'session/911bffe6-2649-5b74-825a-7481bdf5920e'
    method = 'POST'
    authorization = jwt_token
    expected_status = 405
    execute_api(endpoint, method, None, expected_status, authorization, 'CREATE_COMPLETE')


def test_session_get_invalid_uuid(set_up):
    endpoint = 'session/foobar'
    method = 'GET'
    authorization = jwt_token
    expected_status = 400
    execute_api(endpoint, method, None, expected_status, authorization, 'CREATE_COMPLETE')


def test_session_get_non_existent(set_up):
    endpoint = 'session/00000000-0000-4000-8000-000000000000'
    method = 'GET'
    authorization = jwt_token
    expected_status = 404
    execute_api(endpoint, method, None, expected_status, authorization, 'CREATE_COMPLETE')


def test_session_get(session_set_up):
    endpoint = 'session/911bffe6-2649-5b74-825a-7481bdf5920e'
    method = 'GET'
    authorization = jwt_token
    expected_status = 200
    execute_api(endpoint, method, None, expected_status, authorization, 'CREATE_COMPLETE')


def test_session_get_processing_in_progress(processing_set_up):
    endpoint = 'session/911bffe6-2649-5b74-825a-7481bdf5920e'
    method = 'GET'
    authorization = jwt_token
    expected_status = 200
    execute_api(endpoint, method, None, expected_status, authorization, 'PROCESSING_IN_PROGRESS')


