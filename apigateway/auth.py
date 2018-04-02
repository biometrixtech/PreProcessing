from aws_xray_sdk.core import xray_recorder
import jwt
import os
import requests

from exceptions import UnauthorizedException


@xray_recorder.capture('entrypoints.apigateway.get_authorisation_from_auth')
def get_authorisation_from_auth(auth):
    jwt_token = jwt.decode(auth, verify=False)
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


def get_accessory_from_auth(auth):
    jwt_token = jwt.decode(auth, verify=False)
    print(jwt_token)
    if 'username' in jwt_token:
        accessory_id = jwt_token['username']
    else:
        raise UnauthorizedException('Sessions can only be created by hardware-authenticated clients')

    accessory_res = requests.get(
        'https://hardware.{ENVIRONMENT}.fathomai.com/v1/accessory/{ACCESSORY_ID}'.format(**os.environ, ACCESSORY_ID=accessory_id),
        headers={
            'Authorization': get_api_service_token(),
            'Accept': 'application/json'
        }
    )
    if accessory_res.status_code == 200:
        return accessory_res.json()['accessory']
    else:
        raise UnauthorizedException()


def get_user_from_id(user_id):
    user_res = requests.get(
        'https://users.{ENVIRONMENT}.fathomai.com/v1/user/{USER_ID}'.format(**os.environ, USER_ID=user_id),
        headers={
            'Authorization': get_api_service_token(),
            'Accept': 'application/json'
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
