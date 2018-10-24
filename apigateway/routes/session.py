from boto3.s3.transfer import TransferConfig, S3Transfer
from flask import request, Blueprint
import base64
import boto3
import datetime
import json
import os
import re

from fathomapi.api.config import Config
from fathomapi.utils.exceptions import ApplicationException, DuplicateEntityException
from fathomapi.utils.decorators import require
from fathomapi.utils.xray import xray_recorder

from models.session import Session


app = Blueprint('session', __name__)


@app.route('/', methods=['POST'])
@require.authenticated.any
@require.body({'event_date': str, 'sensors': list})
@xray_recorder.capture('routes.session.create')
def handle_session_create(principal_id=None):
    xray_recorder.current_segment().put_annotation('accessory_id', principal_id)

    body = request.json
    body['accessory_id'] = principal_id
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
    xray_recorder.current_segment().put_annotation('accessory_id', session['accessory_id'])
    xray_recorder.current_segment().put_annotation('user_id', session['user_id'])
    return {'session': session}


@app.route('/<uuid:session_id>/upload', methods=['POST'])
@require.authenticated.any
@xray_recorder.capture('routes.session.upload')
def handle_session_upload(session_id):
    session = Session(session_id).get()
    xray_recorder.current_segment().put_annotation('accessory_id', session['accessory_id'])
    xray_recorder.current_segment().put_annotation('sensor_id', ','.join(session['sensor_ids']))
    xray_recorder.current_segment().put_annotation('user_id', session['user_id'])

    # Need to use single threading to prevent X Ray tracing errors
    config = TransferConfig(use_threads=False)
    s3_transfer = S3Transfer(client=boto3.client('s3'), config=config)

    if request.headers['Content-Type'] == 'application/octet-stream':
        with open('/tmp/binary', 'wb') as f:
            f.write(base64.b64decode(request.get_data()))

    elif request.headers['Content-Type'] == 'application/json':
        if isinstance(request.json, dict) and 'src' in request.json:
            match = re.match('^s3://(?P<bucket>biometrix-[a-zA-Z0-9\-]+)/(?P<key>.+)$', request.json['src'])
            if match is not None:
                # Download the file from the foreign S3 bucket
                print(json.dumps({'message': 'Downloading from s3://{}/{}'.format(match.group('bucket'), match.group('key'))}))
                s3_transfer.download_file(match.group('bucket'), match.group('key'), '/tmp/binary')

    if not os.path.isfile('/tmp/binary'):
        raise ApplicationException(
            415,
            'UnsupportedContentType',
            'This endpoint requires the Content-Type application/octet-stream with a binary file content, or application/json with a `src` key referring to an S3 bucket'
        )

    # For now, we integrate with the ingest subservice by saving the file to the S3 ingest bucket.
    s3_bucket = Config.get('S3_INGEST_BUCKET_NAME')
    part_number = str(int(datetime.datetime.now().timestamp() * 1000))
    s3_key = '{}_{}'.format(session_id, part_number)
    print(json.dumps({'message': 'Uploading to s3://{}/{}'.format(s3_bucket, s3_key)}))
    s3_transfer.upload_file('/tmp/binary', s3_bucket, s3_key)

    return {'session': session}


@app.route('/<uuid:session_id>', methods=['PATCH'])
@require.authenticated.any
@xray_recorder.capture('routes.session.patch')
def handle_session_patch(session_id):
    session = Session(session_id).get()
    xray_recorder.current_segment().put_annotation('accessory_id', session['accessory_id'])
    xray_recorder.current_segment().put_annotation('user_id', session['user_id'])

    if 'session_status' in request.json:
        allowed_transitions = [
            ('UPLOAD_IN_PROGRESS', 'UPLOAD_COMPLETE'),
            ('PROCESSING_COMPLETE', 'UPLOAD_IN_PROGRESS'),
            ('PROCESSING_FAILED', 'UPLOAD_IN_PROGRESS'),
        ]
        if (session['session_status'], request.json['session_status']) in allowed_transitions:
            session['session_status'] = request.json['session_status']
        else:
            # https://app.asana.com/0/654140198477919/673983533272813
            return {'message': 'Currently at status {}, cannot change to {}'.format(session['session_status'], request.json['session_status'])}, 200
            # raise InvalidSchemaException('Transition from {} to {} is not allowed'.format(session.session_status, request.json['session_status']))

    session = Session(session_id).patch(request.json)
    return {'session': session}
