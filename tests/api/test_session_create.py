from base_test import BaseTest, get_api_service_token

# This has username = '00:00:00:00:00'
jwt_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6IjAwOjAwOjAwOjAwOjAwIn0._EtGIW4hbbJAbAywUrtonMwZgQuuU8dSyOrPZEF6TJE'


class TestSessionCreateNoAuth(BaseTest):
    endpoint = 'session'
    method = 'POST'
    expected_status = 401


class TestSessionCreateWrongMethod(BaseTest):
    endpoint = 'session'
    method = 'GET'
    authorization = get_api_service_token()
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


# class TestFirmwareGetInvalidVersion(BaseTest):
#     endpoint = 'firmware/accessory/fourtytwo'
#     method = 'GET'
#     expected_status = 404
#
#
# class TestFirmwareGet10(BaseTest):
#     endpoint = 'firmware/accessory/1.0'
#     method = 'GET'
#     expected_status = 200
#
#     def validate_response(self, body, headers, status):
#         self.assertIn('firmware', body)
#         self.assertIn('device_type', body['firmware'])
#         self.assertEqual('accessory', body['firmware']['device_type'])
#         self.assertIn('version', body['firmware'])
#         self.assertEqual('1.0', body['firmware']['version'])
#
#
# class TestFirmwareGetLatest(BaseTest):
#     endpoint = 'firmware/accessory/latest'
#     method = 'GET'
#     expected_status = 200
#
#     def validate_response(self, body, headers, status):
#         self.assertIn('firmware', body)
#         self.assertIn('device_type', body['firmware'])
#         self.assertEqual('accessory', body['firmware']['device_type'])
#         self.assertIn('version', body['firmware'])
#         self.assertNotEqual('latest', body['firmware']['version'])
#         self.assertNotEqual('1.0', body['firmware']['version'])

