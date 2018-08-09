from exceptions import UnauthorizedException
from flask import request
from functools import wraps
from uuid import UUID
import boto3
import json
import jwt
import os
import re


def authentication_required(decorated_function):
    """Decorator to require a JWT token to be passed."""
    @wraps(decorated_function)
    def wrapper(*args, **kwargs):
        if 'Authorization' in request.headers:
            raw_token = request.headers['Authorization']
        elif 'jwt' in request.headers:
            # Legacy 10.1 firmware
            raw_token = request.headers['jwt']
        else:
            raise UnauthorizedException("Must submit a JWT in 'Authorization' header")

        if not raw_token:
            raise UnauthorizedException('No Authorization token provided')
        try:
            token = jwt.decode(raw_token, verify=False)
            validate_token(token)
        except Exception:
            raise UnauthorizedException('Token not a valid JWT')

        try:
            authenticate_user_jwt(raw_token)
            # A dashboard client
            return decorated_function(*args, **kwargs)
        except UnauthorizedException:
            try:
                authenticate_hardware_jwt(token)
                # A hardware client
                return decorated_function(*args, **kwargs)
            except UnauthorizedException:
                raise
    return wrapper


def authenticate_user_jwt(token):
    res = json.loads(boto3.client('lambda').invoke(
        FunctionName='users-{ENVIRONMENT}-apigateway-validateauth'.format(**os.environ),
        Payload=json.dumps({"authorizationToken": token}),
    )['Payload'].read())
    print(res)

    if 'principalId' in res:
        # Success
        return res['principalId']
    elif 'errorMessage' in res:
        # Some failure
        raise UnauthorizedException()


def authenticate_hardware_jwt(token):

    print({'jwt_token': token})
    if 'username' in token:
        principal = token['username']
    else:
        raise UnauthorizedException('No username in token')

    if not validate_mac_address(principal):
        raise UnauthorizedException('Username is not a valid MAC address')

    return principal.upper()


def validate_token(token):
    # TODO
    pass


def validate_mac_address(string):
    return re.match('^[0-9A-Z]{2}:[0-9A-Z]{2}:[0-9A-Z]{2}:[0-9A-Z]{2}:[0-9A-Z]{2}', string.upper())


def validate_uuid4(string):
    try:
        val = UUID(string, version=4)
        # If the uuid_string is a valid hex code, but an invalid uuid4, the UUID.__init__
        # will convert it to a valid uuid4. This is bad for validation purposes.
        return val.hex == string.replace('-', '')
    except ValueError:
        # If it's a value error, then the string is not a valid hex code for a UUID.
        return False
