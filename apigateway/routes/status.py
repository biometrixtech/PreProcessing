from flask import request, Blueprint
import datetime

from fathomapi.utils.decorators import require
from fathomapi.utils.xray import xray_recorder
from fathomapi.utils.formatters import format_datetime, parse_datetime

from models.session import Session


app = Blueprint('status', __name__)


@app.route('/athlete', methods=['GET'])
@require.authenticated.any
@xray_recorder.capture('routes.status.get')
def handle_get_upload_status(principal_id=None):
    user_id = principal_id
    days = int(request.args.get('days', 30))
    current_time = datetime.datetime.now()
    sessions = list(Session.get_many(user_id=user_id,
                                     index='user_id-event_date'))
    sessions = [s for s in sessions if s['event_date'] > format_datetime(current_time - datetime.timedelta(days=days))]
    ret = []
    for session in sessions:
        item = {}
        item['event_date'] = session['event_date']
        item['upload_status'] = 'UPLOAD_NOT_COMPLETE' if session['session_status'] in ['CREATE_COMPLETE', 'UPLOAD_IN_PROGRESS'] else 'UPLOAD_COMPLETE'
        try:
            item['duration'] = round((parse_datetime(session['end_date']) - parse_datetime(session['event_date'])).seconds / 60, 2)
        except:
            item['duration'] = None
        ret.append(item)
    return {"sessions": ret}, 200

 