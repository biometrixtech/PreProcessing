from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.models.trace_header import TraceHeader
from flask import request
import json
import jwt
import os
import requests

from exceptions import UnauthorizedException


def get_jwt_from_request():
    if 'Authorization' in request.headers:
        return request.headers['Authorization']
    elif 'jwt' in request.headers:
        # Legacy 10.1 firmware
        return request.headers['jwt']
    else:
        raise UnauthorizedException()


@xray_recorder.capture('entrypoints.apigateway.get_authorisation_from_auth')
def get_authorisation_from_auth():
    jwt_token = jwt.decode(get_jwt_from_request(), verify=False)
    print(json.dumps({'jwt_token': jwt_token}))
    if 'sub' in jwt_token:
        user_id = jwt_token['sub'].split(':')[-1]
    else:
        user_id = jwt_token['user_id']

    user = get_user_from_id(user_id)
    if user is None:
        raise UnauthorizedException()

    return {
        'user_ids': [user['user_id']],
        'team_ids': [user['team_id']] if user['role'] > 1 else [],
        'training_group_ids': user['training_group_ids'] if user['role'] > 1 else [],
    }


def get_accessory_id_from_auth():
    jwt_token = jwt.decode(get_jwt_from_request(), verify=False)
    print(json.dumps({'jwt_token': jwt_token}))
    if 'username' in jwt_token:
        return jwt_token['username'].upper()
    else:
        raise UnauthorizedException('Sessions can only be created by hardware-authenticated clients')


def get_accessory_from_id(accessory_id):
    accessory_res = requests.get(
        'https://hardware.{ENVIRONMENT}.fathomai.com/v1/accessory/{ACCESSORY_ID}'.format(**os.environ, ACCESSORY_ID=accessory_id),
        headers={
            'Authorization': get_api_service_token(),
            'Accept': 'application/json',
            'X-Amzn-Trace-Id-Safe': get_xray_trace_header(),
        }
    )
    if accessory_res.status_code == 200:
        ret = accessory_res.json()['accessory']
        print(json.dumps({'accessory': ret}))
        return ret
    else:
        return None


def get_user_from_id(user_id):
    user_res = requests.get(
        'https://users.{ENVIRONMENT}.fathomai.com/v1/user/{USER_ID}'.format(**os.environ, USER_ID=user_id),
        headers={
            'Authorization': get_api_service_token(),
            'Accept': 'application/json',
            'X-Amzn-Trace-Id-Safe': get_xray_trace_header(),
        }
    )
    if user_res.status_code == 200:
        ret = user_res.json()['user']
        print(json.dumps({'user': ret}))
        return ret
    else:
        return None


def get_api_service_token():
    # TODO
    return jwt.encode({'sub': '00000000-0000-4000-8000-000000000000'}, 'secret', algorithm='HS256')


def get_xray_trace_header():
    xray_segment = xray_recorder.current_subsegment()
    return TraceHeader(
        root=xray_segment.trace_id,
        parent=xray_segment.id,
        sampled=xray_segment.sampled,
    ).to_header_str()
