from flask import request, Blueprint
import datetime

from fathomapi.comms.service import Service
from fathomapi.utils.decorators import require
from fathomapi.utils.xray import xray_recorder
from fathomapi.utils.formatters import format_datetime, parse_datetime

from models.session import Session


app = Blueprint('status', __name__)


@app.route('/sensor', methods=['POST'])
@require.authenticated.any
@xray_recorder.capture('routes.status.get')
def handle_get_upload_status(principal_id=None):
    user_id = principal_id
    accessory_id = request.json.get('accessory_id', None)
    minutes_offset = _get_offset(request.json.get('timezone', '-04:00'))
    accessory = _get_accessory(accessory_id)

    days = request.json.get('days', 14)
    current_time = datetime.datetime.now()
    # temp for testing
    user_id = 'chris'
    sessions = list(Session.get_many(user_id=user_id,
                                     index='user_id-event_date'))
    sessions = [s for s in sessions if s['event_date'] > format_datetime(current_time - datetime.timedelta(days=days))]
    cleaned_sessions_list = []
    for session in sessions:
        cleaned_session = _get_cleaned_session(session, minutes_offset)
        cleaned_sessions_list.append(cleaned_session)
    return {"sessions": cleaned_sessions_list, "accessory": accessory}


def _get_offset(tz):
    offset = tz.split(":")
    hour_offset = int(offset[0])
    minute_offset = int(offset[1])
    if hour_offset < 0:
        minute_offset = hour_offset * 60 - minute_offset
    else:
        minute_offset += hour_offset * 60
    return minute_offset


def _get_accessory(accessory_id):
    if accessory_id is not None:
        # get accessory from hardware api
        HARDWARE_API_VERSION = '2_0'
        accessory_service = Service('hardware', HARDWARE_API_VERSION)
        response = accessory_service.call_apigateway_sync(method='GET',
                                                          endpoint=f'/accessory/{accessory_id}')
        print(response)
        if 'accessory' in response:
            accessory = {}
            accessory['last_sync_date'] = response['accessory'].get('last_sync_date', None)
            accessory['battery_level'] = response['accessory'].get('battery_level', None)
            accessory['firmware_version'] = response['accessory'].get('firmware_version', None)
            if accessory['firmware_version'] == response['latest_firmware'].get('accessory_version', None):
                accessory['firmware_up_to_date'] = True
            else:
                accessory['firmware_up_to_date'] = False
            return accessory
    # if no accessory_id is provided or accessory_id is not found
    # TODO handle this case properly
    accessory = {
        "last_sync_date": None,
        "battery_level": None,
        "firmware_version": None,
        "firmware_up_to_date": False
    }
    return accessory


def _get_cleaned_session(session, minutes_offset):
    item = {}
    event_date = parse_datetime(session['event_date']) - datetime.timedelta(minutes=minutes_offset)
    item['event_date'] = format_datetime(event_date)
    if session.get('end_date', None) is not None:
        end_date = parse_datetime(session['end_date']) - datetime.timedelta(minutes=minutes_offset)
        item['end_date'] = format_datetime(end_date)
    else:
        end_date = None
        item['end_date'] = end_date

    if session.get('upload_end_date', None) is not None:
        upload_end_date = parse_datetime(session['upload_end_date']) - datetime.timedelta(minutes=minutes_offset)
        item['upload_end_date'] = format_datetime(upload_end_date)
    else:
        item['upload_end_date'] = None
    session_status = session.get('session_status', None)
    if session_status in ['CREATE_COMPLETE', 'UPLOAD_IN_PROGRESS', 'UPLOAD_COMPLETE', 'PROCESSING_IN_PROGRESS']:
        item['status'] = 0
    elif session_status in ['PROCESSING_COMPLETE']:
        item['status'] = 1
    else:
        item['status'] = 2
    if end_date is not None:
        item['duration'] = round((end_date - event_date).seconds / 60, 2)
    else:
        item['duration'] = None
    return item
