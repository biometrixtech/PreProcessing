from builtins import FileNotFoundError
from flask import request, Response
from flask_lambda import FlaskLambda
import json
import os
import sys
import traceback

# Break out of Lambda's X-Ray sandbox so we can define our own segments and attach metadata, annotations, etc, to them
lambda_task_root_key = os.getenv('LAMBDA_TASK_ROOT')
del os.environ['LAMBDA_TASK_ROOT']
from aws_xray_sdk.core import patch_all, xray_recorder
from aws_xray_sdk.core.models.trace_header import TraceHeader
patch_all()
os.environ['LAMBDA_TASK_ROOT'] = lambda_task_root_key

from auth import get_authorisation_from_auth
from exceptions import ApplicationException
from datastore import SessionDatastore
from serialisable import json_serialise


class ApiResponse(Response):
    @classmethod
    def force_type(cls, rv, environ=None):
        if isinstance(rv, (dict, list)):
            # Round-trip through our JSON serialiser to make it parseable by AWS's. Use spaces to facilitate easier
            # parsing on the accessory side.
            rv = Response(
                json.dumps(rv, sort_keys=True, default=json_serialise, separators=(', ', ': ')) + '\n',
                mimetype='application/json'
            )
        return super().force_type(rv, environ)


app = FlaskLambda(__name__)
app.response_class = ApiResponse
app.url_map.strict_slashes = False

from routes.session import app as session_routes
app.register_blueprint(session_routes, url_prefix='/session')


@app.route('/status', methods=['POST'])
def handle_status():
    access = get_authorisation_from_auth()
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


def get_api_version():
    try:
        with open('version', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return '0' * 40
    except:
        return '???'


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

    # Strip mount point and version information from the path
    path_match = re.match(f'^/(?P<mount>({os.environ["SERVICE"]}|v1))(/(?P<version>(\d+(\.\d+)?(\.\d+)?)))?(?P<path>/.+?)/?$', event['path'])
    if path_match is None:
        raise Exception('Invalid path')
    event['path'] = path_match.groupdict()['path']
    api_version = path_match.groupdict()['version']

    # Pass tracing info to X-Ray
    if 'X-Amzn-Trace-Id-Safe' in event['headers']:
        xray_trace = TraceHeader.from_header_str(event['headers']['X-Amzn-Trace-Id-Safe'])
        xray_recorder.begin_segment(
            name='{SERVICE}.{ENVIRONMENT}.fathomai.com'.format(**os.environ),
            traceid=xray_trace.root,
            parent_id=xray_trace.parent
        )
    else:
        xray_recorder.begin_segment(name='{SERVICE}.{ENVIRONMENT}.fathomai.com'.format(**os.environ))

    xray_recorder.current_segment().put_http_meta('url', f"https://{event['headers']['Host']}/{os.environ['SERVICE']}/{api_version}{event['path']}")
    xray_recorder.current_segment().put_http_meta('method', event['httpMethod'])
    xray_recorder.current_segment().put_http_meta('user_agent', event['headers']['User-Agent'])
    xray_recorder.current_segment().put_annotation('environment', os.environ['ENVIRONMENT'])
    xray_recorder.current_segment().put_annotation('version', str(api_version))

    ret = app(event, context)
    ret['headers'].update({
        'Access-Control-Allow-Methods': 'DELETE,GET,HEAD,OPTIONS,PATCH,POST,PUT',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Origin': '*',
        'X-Version': get_api_version(),
    })

    # Unserialise JSON output so AWS can immediately serialise it again...
    ret['body'] = ret['body'].decode('utf-8')

    if ret['headers']['Content-Type'] == 'application/octet-stream':
        ret['isBase64Encoded'] = True

    # xray_recorder.current_segment().http['response'] = {'status': ret['statusCode']}
    xray_recorder.current_segment().put_http_meta('status', ret['statusCode'])
    xray_recorder.current_segment().apply_status_code(ret['statusCode'])
    xray_recorder.end_segment()

    print(json.dumps(ret))
    return ret


if __name__ == '__main__':
    app.run(debug=True)
