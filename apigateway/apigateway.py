from fathomapi.api.handler import handler as fathom_handler
from fathomapi.api.flask_app import app

from routes.session import app as session_routes
app.register_blueprint(session_routes, url_prefix='/session')
from routes.status import app as status_routes
app.register_blueprint(status_routes, url_prefix='/status')


def handler(event, context):
    return fathom_handler(event, context)


if __name__ == '__main__':
    app.run(debug=True)


# from flask import request
#
# from auth import get_authorisation_from_auth
# from datastore import SessionDatastore
#
#
# @app.route('/status', methods=['POST'])
# @require.authenticated.any
# def handle_status(principal_id=None):
#     access = get_authorisation_from_auth()
#     sessions = get_sessions_for_date_and_access(
#         request.json['start_date'],
#         request.json['end_date'],
#         access['user_ids'],
#         access['team_ids'],
#         access['training_group_ids']
#     )
#     ret = {'sessions': {}}
#     for status in ['UPLOAD_IN_PROGRESS', 'UPLOAD_COMPLETE', 'PROCESSING_IN_PROGRESS', 'PROCESSING_COMPLETE', 'PROCESSING_FAILED']:
#         ret['sessions'][status] = [s for s in sessions if s.session_status == status]
#
#     return ret
#
#
# @xray_recorder.capture('entrypoints.apigateway.get_notifications_for_date_and_access')
# def get_sessions_for_date_and_access(start_date, end_date, allowed_users, allowed_teams, allowed_training_groups):
#     from operator import attrgetter
#
#     event_date = start_date if start_date == end_date else (start_date, end_date)
#     store = SessionDatastore()
#     user_sessions = [session for i in allowed_users for session in store.get(event_date=event_date, user_id=i)]
#     team_sessions = [session for i in allowed_teams for session in store.get(event_date=event_date, team_id=i)]
#     tg_sessions = [session for i in allowed_training_groups for session in store.get(event_date=event_date, training_group_id=i)]
#
#     all_sessions = sorted(user_sessions + team_sessions + tg_sessions, key=attrgetter('event_date'))
#
#     return all_sessions
