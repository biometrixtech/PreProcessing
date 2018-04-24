from base_test import BaseTest, get_api_service_token
import boto3

jwt_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiZTg1MTQ0ODktOGRlOS00N2UwLWIzZDUtYjE1ZGEyNDQ3ODNmIiwiY3JlYXRlZF9hdCI6IjIwMTgtMDMtMDUgMTc6NDc6NTAgKzAwMDAiLCJzaWduX2luX21ldGhvZCI6Impzb24tYWNjZXNzb3J5Iiwicm9sZSI6ImJpb21ldHJpeF9hZG1pbiJ9.3KOTieGlQaxf8SLF-l4gNr4x8v_z08eX68uUoWQRDMk'


class TestStatusNoAuth(BaseTest):
    endpoint = 'status'
    method = 'GET'
    expected_status = 401


class TestStatusWrongMethod(BaseTest):
    endpoint = 'status'
    method = 'GET'
    authorization = get_api_service_token()
    expected_status = 405


class TestStatusNoUserInJwt(BaseTest):
    endpoint = 'status'
    method = 'POST'
    authorization = get_api_service_token()
    expected_status = 401


class TestStatusEmptyBody(BaseTest):
    endpoint = 'status'
    method = 'POST'
    authorization = jwt_token
    body = None
    expected_status = 500


class TestStatus(BaseTest):
    endpoint = 'status'
    method = 'POST'
    authorization = jwt_token
    body = {'start_date': '2018-04-20', 'end_date': '2018-04-24'}
    expected_status = 200

    def validate_response(self, body, headers, status):
        self.assertIn('sessions', body)
        sessions = body['sessions']
        self.assertIn("PROCESSING_COMPLETE", sessions)
        self.assertIn("PROCESSING_FAILED", sessions)
        self.assertIn("PROCESSING_IN_PROGRESS", sessions)
        self.assertIn("UPLOAD_COMPLETE", sessions)
        self.assertIn("UPLOAD_IN_PROGRESS", sessions)
