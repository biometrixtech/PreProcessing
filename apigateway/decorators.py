from flask import request
from functools import wraps
from uuid import UUID
import jwt
import os
import re
from exceptions import UnauthorizedException


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
            authenticate_user_jwt(token)
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
    print({'jwt': token})
    if 'sub' in token:
        raw_user_id = token['sub']
    elif 'user_id' in token:
        raw_user_id = token['user_id']
    else:
        raise UnauthorizedException('No user id in token')

    if ':' in raw_user_id:
        region, principal = raw_user_id.split(':', 1)
    else:
        region, principal = os.environ['AWS_REGION'], raw_user_id

    if region != os.environ['AWS_REGION']:
        raise UnauthorizedException('Mismatching region in token')
    if not validate_uuid4(principal):
        raise UnauthorizedException('Principal is not a valid uuid')

    return principal


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
