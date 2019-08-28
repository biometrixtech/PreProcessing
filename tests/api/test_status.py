from .base_test import BaseTest, get_api_service_token
import boto3

# jwt_token_2 = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiZTg1MTQ0ODktOGRlOS00N2UwLWIzZDUtYjE1ZGEyNDQ3ODNmIiwiY3JlYXRlZF9hdCI6IjIwMTgtMDMtMDUgMTc6NDc6NTAgKzAwMDAiLCJzaWduX2luX21ldGhvZCI6Impzb24tYWNjZXNzb3J5Iiwicm9sZSI6ImJpb21ldHJpeF9hZG1pbiJ9.3KOTieGlQaxf8SLF-l4gNr4x8v_z08eX68uUoWQRDMk'
jwt_token = get_api_service_token('e8514489-8de9-47e0-b3d5-b15da244783f')

class TestStatusNoAuth(BaseTest):
    endpoint = 'status/sensor'
    method = 'POST'
    expected_status = 401


class TestStatusWrongMethod(BaseTest):
    endpoint = 'status/sensor'
    method = 'GET'
    authorization = jwt_token
    expected_status = 405


# class TestStatusNoUserInJwt(BaseTest):
#     endpoint = 'status/sensor'
#     method = 'POST'
#     body = {"accessory_id": "05:00:00:00:00:00"}
#     authorization = get_api_service_token("05:00:00:00:00:00")
#     expected_status = 401


class TestStatusEmptyBody(BaseTest):
    endpoint = 'status/sensor'
    method = 'POST'
    authorization = jwt_token
    body = None
    expected_status = 500


class TestStatus(BaseTest):
    endpoint = 'status/sensor'
    method = 'POST'
    authorization = jwt_token
    body = {'start_date': '2018-04-20', 'end_date': '2018-04-24'}
    expected_status = 200

    def validate_response(self, body, headers, status):
        self.assertIn('sessions', body)
        self.assertIn('accessory', body)
