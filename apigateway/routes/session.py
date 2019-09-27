from boto3.s3.transfer import TransferConfig, S3Transfer
from flask import request, Blueprint
import base64
import boto3
import datetime
import io
import json
import re
import time

from fathomapi.api.config import Config
from fathomapi.utils.exceptions import ApplicationException, DuplicateEntityException, InvalidSchemaException
from fathomapi.utils.decorators import require
from fathomapi.utils.xray import xray_recorder
from fathomapi.utils.formatters import parse_datetime

from models.session import Session


app = Blueprint('session', __name__)

_ingest_s3_bucket = boto3.resource('s3').Bucket(Config.get('S3_INGEST_BUCKET_NAME'))
# Need to use single threading to prevent X Ray tracing errors
_s3_config = TransferConfig(use_threads=False)


@app.route('/', methods=['POST'])
@require.authenticated.any
@require.body({'event_date': str})
@xray_recorder.capture('routes.session.create')
def handle_session_create(principal_id=None):
    xray_recorder.current_subsegment().put_annotation('accessory_id', principal_id)

    body = request.json
    if body['event_date'] == 'ERROR':  # problem getting event date, set server time
        body['event_date'] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    if 'accessory_id' not in body:
        body['accessory_id'] = principal_id
    else:  # call came from mobile, adjust event date
        body['event_date'] = (parse_datetime(body['event_date']) + datetime.timedelta(seconds=5)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    body['session_status'] = 'CREATE_COMPLETE'

    body['sensor_ids'] = []
    for sensor in request.json['sensors']:
        if isinstance(sensor, dict):
            body['sensor_ids'].append(sensor['mac_address'])
        else:
            body['sensor_ids'].append(str(sensor))

    session_id = Session.generate_uuid(body)
    try:
        session = Session(session_id).create(body)
        return {'session': session}, 201
    except DuplicateEntityException:
        print(json.dumps({'message': 'Session already created with id {}'.format(session_id)}))
        return {'session': Session(session_id).get()}, 201


@app.route('/<uuid:session_id>', methods=['GET'])
@require.authenticated.any
@xray_recorder.capture('routes.session.get')
def handle_session_get(session_id):
    session = Session(session_id).get()
    xray_recorder.current_subsegment().put_annotation('accessory_id', session['accessory_id'])
    xray_recorder.current_subsegment().put_annotation('user_id', session['user_id'])
    return {'session': session}


@app.route('/<uuid:session_id>/upload', methods=['POST'])
@require.authenticated.any
@xray_recorder.capture('routes.session.upload')
def handle_session_upload(session_id):

    # For now, we integrate with the ingest subservice by saving the file to the S3 ingest bucket.
    s3_key = '{}_{}'.format(session_id, str(int(datetime.datetime.now().timestamp() * 1000)))
    print(json.dumps({'message': 'Uploading to s3://{}/{}'.format(_ingest_s3_bucket.name, s3_key)}))

    if request.headers['Content-Type'] == 'application/octet-stream':
        raw_data = base64.b64decode(request.get_data())
        if raw_data[-5:] == b'!!!!!':
            raise InvalidSchemaException('Void character string found at end of body')
        f = io.BytesIO(raw_data)
        _ingest_s3_bucket.upload_fileobj(f, s3_key, Config=_s3_config)

    elif request.headers['Content-Type'] == 'application/json':
        if not isinstance(request.json, dict) or 'src' not in request.json:
            raise InvalidSchemaException('"src" parameter is required for json upload')
        match = re.match('^s3://(?P<bucket>biometrix-[a-zA-Z0-9\-]+)/(?P<key>.+)$', request.json['src'])
        if match is None:
            raise InvalidSchemaException('"src" parameter must be an s3://bucket/key URL')

        # Copy the file from the foreign S3 bucket
        print(json.dumps({'message': 'Downloading from s3://{}/{}'.format(match.group('bucket'), match.group('key'))}))
        boto3.client('s3').download_file(match.group('bucket'), match.group('key'), '/tmp/binary', Config=_s3_config)
        _ingest_s3_bucket.upload_file('/tmp/binary', s3_key, Config=_s3_config)

    else:
        raise ApplicationException(
            415,
            'UnsupportedContentType',
            'This endpoint requires the Content-Type application/octet-stream with a binary file content, or application/json with a `src` key referring to an S3 bucket'
        )

    return {'message': 'Received'}, 202


@app.route('/<uuid:session_id>', methods=['PATCH'])
@require.authenticated.any
@xray_recorder.capture('routes.session.patch')
def handle_session_patch(session_id):
    session = Session(session_id).get()
    xray_recorder.current_subsegment().put_annotation('accessory_id', session['accessory_id'])
    xray_recorder.current_subsegment().put_annotation('user_id', session['user_id'])

    if 'session_status' in request.json:
        allowed_transitions = [
            ('UPLOAD_IN_PROGRESS', 'UPLOAD_COMPLETE'),
            ('PROCESSING_COMPLETE', 'UPLOAD_IN_PROGRESS'),
            ('PROCESSING_FAILED', 'UPLOAD_IN_PROGRESS'),
            ('CREATE_COMPLETE', 'NO_DATA'),
            ('CREATE_COMPLETE', 'TOO_SHORT'),
            ('CREATE_COMPLETE', 'CREATE_ATTEMPT_FAILED')
        ]
        if session['session_status'] == 'UPLOAD_IN_PROGRESS' and request.json['session_status'] == 'NO_DATA':
            request.json['session_status'] = 'UPLOAD_COMPLETE'
        if (session['session_status'], request.json['session_status']) in allowed_transitions:
            session['session_status'] = request.json['session_status']
            if session['session_status'] == 'UPLOAD_COMPLETE':
                request.json['upload_end_date'] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                # https://app.asana.com/0/410356542105212/1126815467611560
                # Race condition between uploads being noted in DynamoDB (from S3 event watcher) and processing starting; hack around with a sleep
                time.sleep(5)
        else:
            # https://app.asana.com/0/654140198477919/673983533272813
            return {'message': 'Currently at status {}, cannot change to {}'.format(session['session_status'], request.json['session_status'])}, 200
            # raise InvalidSchemaException('Transition from {} to {} is not allowed'.format(session.session_status, request.json['session_status']))
    if 'set_end_date' in request.json:
        request.json['end_date'] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        del request.json['set_end_date']

    session = Session(session_id).patch(request.json)
    return {'session': session}
