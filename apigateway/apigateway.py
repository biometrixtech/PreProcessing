from aws_xray_sdk.core import xray_recorder, patch_all
from flask import request, Response, jsonify
from flask_lambda import FlaskLambda
import json
import sys
import traceback

from auth import get_authorisation_from_auth
from exceptions import ApplicationException
from datastore import SessionDatastore
from serialisable import json_serialise

patch_all()


class ApiResponse(Response):
    @classmethod
    def force_type(cls, rv, environ=None):
        if isinstance(rv, dict):
            # Round-trip through our JSON serialiser to make it parseable by AWS's
            rv = json.loads(json.dumps(rv, sort_keys=True, default=json_serialise))
            rv = jsonify(rv)
        return super().force_type(rv, environ)


app = FlaskLambda(__name__)
app.response_class = ApiResponse
app.url_map.strict_slashes = False

from routes.session import app as session_routes
app.register_blueprint(session_routes, url_prefix='/v1/session')
app.register_blueprint(session_routes, url_prefix='/preprocessing/session')


@app.route('/v1/status', methods=['POST'])
@app.route('/preprocessing/status', methods=['POST'])
def handle_status():
    access = get_authorisation_from_auth(request.headers['Authorization'])
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

    return ret


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


@app.errorhandler(500)
def handle_server_error(e):
    tb = sys.exc_info()[2]
    return {'message': str(e.with_traceback(tb))}, 500, {'Status': type(e).__name__}


@app.errorhandler(404)
def handle_unrecognised_endpoint(_):
    return {"message": "You must specify an endpoint"}, 404, {'Status': 'UnrecognisedEndpoint'}


@app.errorhandler(405)
def handle_unrecognised_method(_):
    return {"message": "The given method is not supported for this endpoint"}, 405, {'Status': 'UnsupportedMethod'}


@app.errorhandler(ApplicationException)
def handle_application_exception(e):
    traceback.print_exception(*sys.exc_info())
    return {'message': e.message}, e.status_code, {'Status': e.status_code_text}


def handler(event, context):
    print(json.dumps(event))

    # Trim trailing slashes from urls
    event['path'] = event['path'].rstrip('/')

    ret = app(event, context)
    ret['headers'].update({
        'Content-Type': 'application/json',
        'Access-Control-Allow-Methods': 'DELETE,GET,HEAD,OPTIONS,PATCH,POST,PUT',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Origin': '*',
    })

    # Unserialise JSON output so AWS can immediately serialise it again...
    ret['body'] = ret['body'].decode('utf-8')

    if ret['headers']['Content-Type'] == 'application/octet-stream':
        ret['isBase64Encoded'] = True

    print(json.dumps(ret))
    return ret


if __name__ == '__main__':
    app.run(debug=True)
