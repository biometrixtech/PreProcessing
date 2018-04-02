from aws_xray_sdk.core import xray_recorder
from flask import request, Blueprint
import base64
import boto3
import datetime
import os
import uuid

from auth import get_accessory_from_auth, get_user_from_id
from datastore import SessionDatastore
from exceptions import InvalidSchemaException, ApplicationException, NoSuchEntityException, DuplicateEntityException
from models.session import Session

app = Blueprint('sensor', __name__)


@app.route('/', methods=['POST'])
def handle_session_create():
    if 'event_date' not in request.json:
        raise InvalidSchemaException('Missing required parameter event_date')
    if 'sensors' not in request.json:
        raise InvalidSchemaException('Missing required parameter sensors')

    user_id = team_id = training_group_ids = mass = None
    accessory = get_accessory_from_auth(request.headers['Authorization'])
    if 'owner_id' in accessory:
        print(accessory['owner_id'])
        user = get_user_from_id(accessory['owner_id'])
        if user is not None:
            print(user)
            user_id = user['user_id']
            team_id = user['team_id']
            training_group_ids = set(user['training_group_ids'])
            mass = user['mass']['kg']
        else:
            # TODO
            print('Accessory owner_id does not exist')
    else:
        # TODO
        print('Accessory has no owner_id set')

    store = SessionDatastore()
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    session = Session(
        session_id=None,
        user_id=user_id,
        user_mass=mass,
        team_id=team_id,
        training_group_ids=training_group_ids,
        event_date=request.json['event_date'],
        session_status='CREATE_COMPLETE',
        created_date=now,
        updated_date=now,
        version='2.3',
        s3_files=None
    )


    try:
        store = SessionDatastore()
        store.put(session)
        return {'session': session}, 201
    except DuplicateEntityException:
        print('Session already created with id {}'.format(session.get_id()))
        return {'session': get_session_by_id(session.get_id(), store)}, 200


@app.route('/<session_id>', methods=['GET'])
def handle_session_get(session_id):
    session = get_session_by_id(session_id)
    return {'session': session}


@app.route('/<session_id>/upload', methods=['POST'])
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

    return {'session': session}


@app.route('/<session_id>', methods=['PATCH'])
def handle_session_patch(session_id):
    store = SessionDatastore()
    session = get_session_by_id(session_id, store)

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
