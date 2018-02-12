from serialisable import json_serialise
from collections import OrderedDict
import boto3
import json
import logging
import os
import sys

from aws_xray_sdk.core import xray_recorder, patch_all
patch_all()

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ApplicationException(Exception):
    pass


def handler(event, _):
    try:
        logger.info(json.dumps(event))

        endpoint = event['endpoint']
        body = event['body-json']

        if endpoint == 'Status':
            access = get_authorisation_from_auth(event['auth'])
            logger.info(json.dumps(access))
            sessions = get_sessions_for_date_and_access(
                body['startDate'],
                body['endDate'],
                access['user_ids'],
                access['team_ids'],
                access['training_group_ids']
            )
            ret = {'Sessions': {}}
            for status in ['UPLOAD_IN_PROGRESS', 'UPLOAD_COMPLETE', 'PROCESSING_IN_PROGRESS', 'PROCESSING_COMPLETE', 'PROCESSING_FAILED']:
                ret['Sessions'][status] = [s for s in sessions if s.session_status == status]
        else:
            raise ApplicationException("UnrecognisedEndpoint")

        # Round-trip through our JSON serialiser to make it parseable by AWS's
        return json.loads(json.dumps(ret, sort_keys=True, default=json_serialise), object_pairs_hook=OrderedDict)

    except ApplicationException:
        raise
    except BaseException as e:
        tb = sys.exc_info()[2]
        raise ApplicationException("ServerError --> {}: {}".format(type(e).__name__, e)).with_traceback(tb)


@xray_recorder.capture('entrypoints.apigateway.get_notifications_for_date_and_access')
def get_sessions_for_date_and_access(start_date, end_date, allowed_users, allowed_teams, allowed_training_groups):
    from datastore import SessionDatastore
    from operator import attrgetter

    event_date = start_date if start_date == end_date else (start_date, end_date)
    store = SessionDatastore()
    user_sessions = [session for i in allowed_users for session in store.get(event_date, user_id=i)]
    team_sessions = [session for i in allowed_teams for session in store.get(event_date, team_id=i)]
    tg_sessions = [session for i in allowed_training_groups for session in store.get(event_date, training_group_id=i)]

    all_sessions = sorted(user_sessions + team_sessions + tg_sessions, key=attrgetter('event_date'))

    return all_sessions


@xray_recorder.capture('entrypoints.apigateway.get_authorisation_from_auth')
def get_authorisation_from_auth(auth):
    user_id = auth['principal']
    query_results = query_postgres(
        """SELECT
          teams_users.team_id AS team_id,
          training_groups_users.training_group_id AS training_group_id
        FROM users
        LEFT JOIN teams_users ON teams_users.user_id = users.id
        LEFT JOIN training_groups_users ON training_groups_users.user_id=users.id
        WHERE users.id = %s
        AND users.role > 1""",
        [user_id]
    )
    ret = {
        'user_ids': [user_id],
        'team_ids': list(set([row.get('team_id') for row in query_results])),
        'training_group_ids': list(set([row.get('team_id') for row in query_results])),
    }
    return ret


@xray_recorder.capture('entrypoints.apigateway.query_postgres')
def query_postgres(query, parameters):
    lambda_client = boto3.client('lambda', region_name=os.environ['AWS_REGION'])
    res = json.loads(lambda_client.invoke(
        FunctionName='arn:aws:lambda:us-west-2:887689817172:function:infrastructure-dev-querypostgres',
        Payload=json.dumps({
            "Queries": [{"Query": query, "Parameters": parameters}],
            "Config": {"ENVIRONMENT": os.environ['ENVIRONMENT']}
        }),
    )['Payload'].read().decode('utf-8'))
    result, error = res['Results'][0], res['Errors'][0]
    if error is not None:
        raise Exception(error)
    else:
        return result if len(result) else []


def assert_valid_body(body, schema):
    # TODO
    if False:
        raise ApplicationException("InvalidBody")
    pass
