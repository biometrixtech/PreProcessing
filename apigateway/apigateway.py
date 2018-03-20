from aws_xray_sdk.core import xray_recorder, patch_all
from flask import request
from flask_lambda import FlaskLambda
import base64
import boto3
import datetime
import json
import jwt
import os
import requests
import sys
import time
import uuid

from exceptions import ApplicationException, InvalidSchemaException, NoSuchEntityException, UnauthorizedException
from datastore import SessionDatastore
from serialisable import json_serialise
from session import Session

patch_all()
app = FlaskLambda(__name__)


@app.route('/v1/status', methods=['POST'])
@app.route('/preprocessing/status', methods=['POST'])
def handle_status():
    access = get_authorisation_from_auth(request.headers['Authorization'])
    print(json.dumps(access))
    sessions = get_sessions_for_date_and_access(
        request.json['start_date'],
        request.json['end_date'],
        access['user_ids'],
        access['team_ids'],
        access['training_group_ids']
    )
    ret = {'sessions': {}}
    for status in ['UPLOAD_IN_PROGRESS', 'UPLOAD_COMPLETE', 'PROCESSING_IN_PROGRESS', 'PROCESSING_COMPLETE', 'PROCESSING_FAILED']:
        ret['sessions'][status] = [s for s in sessions if s.session_status == status]
    print(ret)

    return json.dumps(ret, sort_keys=True, default=json_serialise)


@app.route('/v1/session', methods=['POST'])
@app.route('/preprocessing/session', methods=['POST'])
def handle_session_create():
    if 'event_date' not in request.json:
        raise InvalidSchemaException('Missing required parameter event_date')
    if 'sensors' not in request.json:
        raise InvalidSchemaException('Missing required parameter sensors')

    user_id = team_id = training_group_ids = None
    accessory = get_accessory_from_auth(request.headers['Authorization'])
    if 'owner_id' in accessory:
        print(accessory['owner_id'])
        user = get_user_from_id(accessory['owner_id'])
        if user is not None:
            print(user)
            user_id = user['user_id']
            team_id = user['team_id']
            training_group_ids = user['training_group_ids']
        else:
            # TODO
            print('Accessory owner_id does not exist')
    else:
        # TODO
        print('Accessory has no owner_id set')

    store = SessionDatastore()
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    session = Session(
        session_id=str(uuid.uuid4()),
        user_id=user_id,
        team_id=team_id,
        training_group_ids=training_group_ids,
        event_date=request.json['event_date'],
        session_status='CREATE_COMPLETE',
        created_date=now,
        updated_date=now,
        version='2.3',
        s3_files=None
    )
    store.put(session)
    # TODO save sensors
    return json.dumps({'session': session}, default=json_serialise), 201


@app.route('/v1/session/<session_id>', methods=['GET'])
@app.route('/preprocessing/session/<session_id>', methods=['GET'])
def handle_session_get(session_id):
    session = get_session_by_id(session_id)
    return json.dumps({'session': session}, default=json_serialise)


@app.route('/v1/session/<session_id>/upload', methods=['POST'])
@app.route('/preprocessing/session/<session_id>/upload', methods=['POST'])
def handle_session_upload(session_id):
    if request.headers['Content-Type'] != 'application/octet-stream':
        raise ApplicationException(415, 'UnsupportedContentType', 'This endpoint requires the Content-Type application/octet-stream')

    session = get_session_by_id(session_id)

    part_number = str(int(datetime.datetime.now().timestamp() * 1000))

    with open('/tmp/binary', 'wb') as f:
        f.write(base64.b64decode(request.get_data()))

    # For now, we integrate with the ingest subservice by saving the file to the S3 ingest bucket.
    s3_bucket = os.environ['S3_INGEST_BUCKET_NAME']
    s3_key = '{}_{}'.format(session.session_id, part_number)
    print('Uploading to s3://{}/{}'.format(s3_bucket, s3_key))
    boto3.client('s3').upload_file('/tmp/binary', s3_bucket, s3_key)

    return json.dumps({'session': session}, default=json_serialise)


@app.route('/v1/session/<session_id>', methods=['PATCH'])
@app.route('/preprocessing/session/<session_id>', methods=['PATCH'])
def handle_session_patch(session_id):
    store = SessionDatastore()
    session = get_session_by_id(session_id, store)

    if 'session_status' in request.json and request.json['session_status'] == 'UPLOAD_COMPLETE':
        session.session_status = 'UPLOAD_COMPLETE'

    store.put(session, True)
    return json.dumps({'session': session}, default=json_serialise)


@xray_recorder.capture('entrypoints.apigateway.get_session_by_id')
def get_session_by_id(session_id, store=None):
    session_id = session_id.lower()

    if not validate_uuid4(session_id):
        raise InvalidSchemaException('session_id must be a uuid')

    store = store or SessionDatastore()
    session = store.get(session_id=session_id)
    if len(session) == 1:
        return session[0]
    else:
        raise NoSuchEntityException()


def validate_uuid4(uuid_string):
    try:
        val = uuid.UUID(uuid_string, version=4)
        # If the uuid_string is a valid hex code, but an invalid uuid4, the UUID.__init__
        # will convert it to a valid uuid4. This is bad for validation purposes.
        return val.hex == uuid_string.replace('-', '')
    except ValueError:
        # If it's a value error, then the string is not a valid hex code for a UUID.
        return False


@xray_recorder.capture('entrypoints.apigateway.get_notifications_for_date_and_access')
def get_sessions_for_date_and_access(start_date, end_date, allowed_users, allowed_teams, allowed_training_groups):
    from operator import attrgetter

    event_date = start_date if start_date == end_date else (start_date, end_date)
    store = SessionDatastore()
    user_sessions = [session for i in allowed_users for session in store.get(event_date=event_date, user_id=i)]
    team_sessions = [session for i in allowed_teams for session in store.get(event_date=event_date, team_id=i)]
    tg_sessions = [session for i in allowed_training_groups for session in store.get(event_date=event_date, training_group_id=i)]

    all_sessions = sorted(user_sessions + team_sessions + tg_sessions, key=attrgetter('event_date'))

    return all_sessions


@xray_recorder.capture('entrypoints.apigateway.get_authorisation_from_auth')
def get_authorisation_from_auth(auth):
    jwt_token = jwt.decode(auth, verify=False)
    print(jwt_token)
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
        return user_res.json()['user']
    else:
        return None


def get_api_service_token():
    # TODO
    return jwt.encode({'sub': '00000000-0000-4000-8000-000000000000'}, 'secret', algorithm='HS256')


@app.errorhandler(500)
def handle_server_error(e):
    tb = sys.exc_info()[2]
    return json.dumps({'message': str(e.with_traceback(tb))}, default=json_serialise), 500, {'Status': type(e).__name__}


@app.errorhandler(404)
def handle_unrecognised_endpoint(_):
    return '{"message": "You must specify an endpoint"}', 404, {'Status': 'UnrecognisedEndpoint'}


@app.errorhandler(405)
def handle_unrecognised_method(_):
    return '{"message": "The method is not allowed for the requested URL."}', 405, {'Status': 'MethodNotSupported'}


@app.errorhandler(ApplicationException)
def handle_application_exception(e):
    print(e)
    return json.dumps({'message': e.message}, default=json_serialise), e.status_code, {'Status': e.status_code_text}


def handler(event, context):
    print(json.dumps(event))
    ret = app(event, context)
    ret['headers'].update({
        'Content-Type': 'application/json',
        'Access-Control-Allow-Methods': 'DELETE,GET,HEAD,OPTIONS,PATCH,POST,PUT',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Origin': '*',
    })
    # Round-trip through our JSON serialiser to make it parseable by AWS's
    print(ret)
    return json.loads(json.dumps(ret, sort_keys=True, default=json_serialise))


if __name__ == '__main__':
    app.run(debug=True)
