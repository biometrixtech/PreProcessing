from aws_xray_sdk.core import xray_recorder
from boto3.s3.transfer import TransferConfig, S3Transfer
from flask import request, Blueprint
import base64
import boto3
import datetime
import json
import os
import uuid

from auth import get_accessory_from_auth, get_user_from_id
from datastore import SessionDatastore
from exceptions import InvalidSchemaException, ApplicationException, NoSuchEntityException, DuplicateEntityException
from models.session import Session

app = Blueprint('session', __name__)


@app.route('/', methods=['POST'])
@xray_recorder.capture('routes.session.create')
def handle_session_create():
    if not isinstance(request.json, dict):
        raise InvalidSchemaException('Request body must be a dictionary')
    if 'event_date' not in request.json:
        raise InvalidSchemaException('Missing required parameter event_date')
    if 'sensors' not in request.json:
        raise InvalidSchemaException('Missing required parameter sensors')

    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    session = Session(
        event_date=request.json['event_date'],
        end_date=request.json.get('end_date', None),
        session_status='CREATE_COMPLETE',
        created_date=now,
        updated_date=now,
    )

    accessory = get_accessory_from_auth()
    session.accessory_id = accessory['mac_address']
    xray_recorder.current_segment().put_annotation('accessory_id', accessory['mac_address'])
    for sensor in request.json['sensors']:
        if isinstance(sensor, dict):
            session.sensor_ids.add(sensor['mac_address'])
        else:
            session.sensor_ids.add(str(sensor))

    if 'owner_id' in accessory:
        print(json.dumps({'session_user_id': accessory['owner_id']}))
        user = get_user_from_id(accessory['owner_id'])
        if user is not None:
            print(json.dumps({'session_user': user}))
            session.user_id = user['user_id']
            session.team_id = user['team_id']
            session.training_group_ids = set(user['training_group_ids'])
            session.user_mass = user['mass']['kg']
            xray_recorder.current_segment().put_annotation('user_id', session.user_id)

    store = SessionDatastore()
    try:
        store.put(session)
        return {'session': session}, 201
    except DuplicateEntityException:
        print(json.dumps({'message': 'Session already created with id {}'.format(session.get_id())}))
        return {'session': get_session_by_id(session.get_id(), store)}, 201


@app.route('/<session_id>', methods=['GET'])
@xray_recorder.capture('routes.session.get')
def handle_session_get(session_id):
    session = get_session_by_id(session_id)
    xray_recorder.current_segment().put_annotation('accessory_id', session.accessory_id)
    xray_recorder.current_segment().put_annotation('user_id', session.user_id)
    return {'session': session}


@app.route('/<session_id>/upload', methods=['POST'])
@xray_recorder.capture('routes.session.upload')
def handle_session_upload(session_id):
    if request.headers['Content-Type'] != 'application/octet-stream':
        raise ApplicationException(415, 'UnsupportedContentType', 'This endpoint requires the Content-Type application/octet-stream')

    session = get_session_by_id(session_id)
    xray_recorder.current_segment().put_annotation('accessory_id', session.accessory_id)
    xray_recorder.current_segment().put_annotation('sensor_id', ','.join(session.sensor_ids))
    xray_recorder.current_segment().put_annotation('user_id', session.user_id)

    part_number = str(int(datetime.datetime.now().timestamp() * 1000))

    with open('/tmp/binary', 'wb') as f:
        f.write(base64.b64decode(request.get_data()))

    # For now, we integrate with the ingest subservice by saving the file to the S3 ingest bucket.
    s3_bucket = os.environ['S3_INGEST_BUCKET_NAME']
    s3_key = '{}_{}'.format(session.session_id, part_number)
    print(json.dumps({'message': 'Uploading to s3://{}/{}'.format(s3_bucket, s3_key)}))
    # Need to use single threading to prevent X Ray tracing errors
    config = TransferConfig(use_threads=False)
    S3Transfer(client=boto3.client('s3'), config=config).upload_file('/tmp/binary', s3_bucket, s3_key)

    return {'session': session}


@app.route('/<session_id>', methods=['PATCH'])
@xray_recorder.capture('routes.session.patch')
def handle_session_patch(session_id):
    store = SessionDatastore()
    session = get_session_by_id(session_id, store)
    xray_recorder.current_segment().put_annotation('accessory_id', session.accessory_id)
    xray_recorder.current_segment().put_annotation('user_id', session.user_id)

    if 'session_status' in request.json and request.json['session_status'] == 'UPLOAD_COMPLETE':
        session.session_status = 'UPLOAD_COMPLETE'

    store.put(session, True)
    return {'session': session}


@xray_recorder.capture('routes.session.get_session_by_id')
def get_session_by_id(session_id, store=None):
    session_id = session_id.lower()

    if not validate_uuid(session_id, 5) and not validate_uuid(session_id, 4):
        raise InvalidSchemaException('session_id must be a uuid, not "{}"'.format(session_id))

    store = store or SessionDatastore()
    session = store.get(session_id=session_id)
    if len(session) == 1:
        return session[0]
    else:
        raise NoSuchEntityException()


def validate_uuid(uuid_string, version):
    try:
        val = uuid.UUID(uuid_string, version=version)
        # If the uuid_string is a valid hex code, but an invalid uuid4, the UUID.__init__
        # will convert it to a valid uuid4. This is bad for validation purposes.
        return val.hex == uuid_string.replace('-', '')
    except ValueError:
        # If it's a value error, then the string is not a valid hex code for a UUID.
        return False
