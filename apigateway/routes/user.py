from flask import request, Blueprint
from datetime import datetime, timedelta, timezone

from fathomapi.comms.service import Service
from fathomapi.utils.decorators import require
from fathomapi.utils.xray import xray_recorder
from fathomapi.utils.formatters import format_datetime, parse_datetime
from fathomapi.utils.exceptions import InvalidSchemaException
from models.session import Session


app = Blueprint('user', __name__)
HARDWARE_API_VERSION = '2_0'


@app.route('/<uuid:user_id>/status', methods=['POST'])
@require.authenticated.any
@xray_recorder.capture('routes.user.get_status')
def handle_get_upload_status(user_id, principal_id=None):
    # user_id = principal_id
    accessory_id = request.json.get('accessory_id', None)
    accessory = _get_accessory(accessory_id)

    days = request.json.get('days', 14)
    current_time = datetime.now()
    # Get all sessions for the user
    sessions = list(Session.get_many(user_id=user_id,
                                     index='user_id-event_date'))
    # subset to get relevant dates
    sessions = [s for s in sessions if s['event_date'] > format_datetime(current_time - timedelta(days=days))]
    cleaned_sessions_list = []
    for session in sessions:
        cleaned_session = _get_cleaned_session(session)
        cleaned_sessions_list.append(cleaned_session)
    cleaned_sessions_list = [session for session in cleaned_sessions_list if session['status'] != "CREATE_ATTEMPT_FAILED"]
    return {"sessions": cleaned_sessions_list, "accessory": accessory}


@app.route('/<uuid:user_id>/sessions_today', methods=['POST'])
@require.authenticated.any
@xray_recorder.capture('routes.user.get_session_today')
def handle_get_session_today(user_id, principal_id=None):
    offset = _get_offset()
    current_time = datetime.now()
    current_local_time = current_time + timedelta(minutes=offset)
    # Get all sessions for the user
    sessions = list(Session.get_many(user_id=user_id,
                                     index='user_id-event_date'))
    # subset to get relevant dates
    sessions = [s for s in sessions if s['event_date'] > format_datetime(current_time - timedelta(days=1))]
    cleaned_sessions_list = []
    for session in sessions:
        cleaned_session = _get_cleaned_session(session)
        cleaned_sessions_list.append(cleaned_session)
    cleaned_sessions_list = [session for session in cleaned_sessions_list if session['status'] != "CREATE_ATTEMPT_FAILED" and
                             session['event_date'].split('T')[0] == format_datetime(current_local_time).split('T')[0] and
                             parse_datetime(session['event_date']).hour >= 3]
    return {"sessions": cleaned_sessions_list}


@app.route('/<uuid:user_id>/last_session', methods=['GET'])
@require.authenticated.any
@xray_recorder.capture('routes.user.get_last_session')
def handle_get_last_created_session(user_id):
    days = 30
    current_time = datetime.now()
    # Get all sessions for the user
    sessions = list(Session.get_many(user_id=user_id,
                                     index='user_id-event_date'))
    # subset to last 30 days
    sessions = [s for s in sessions if s['event_date'] > format_datetime(current_time - timedelta(days=days))]
    sessions = sorted(sessions, key=lambda k: k['event_date'], reverse=True)
    for session in sessions:
        if session['session_status'] in ['CREATE_COMPLETE', 'UPLOAD_IN_PROGRESS']:
            try:
                cleaned_session = {
                    "id": session['id'],
                    "event_date": _get_epoch_time(session['event_date']),
                    "end_date": _get_epoch_time(session.get('end_date', None)),
                    "last_true_time": session.get('last_true_time', None)
                }
                if cleaned_session['end_date'] is None:  # if no end_date add 4 hours to start_date
                    cleaned_session['end_date'] = cleaned_session['event_date'] + 4 * 3600
                return {"last_session": cleaned_session}
            except Exception as e:  # if there's some issue with timestamp
                print(e)
                continue

    return {"last_session": None}


def _get_accessory(accessory_id):
    if accessory_id is not None:
        # get accessory from hardware api
        accessory_service = Service('hardware', HARDWARE_API_VERSION)
        response = accessory_service.call_apigateway_sync(method='GET',
                                                          endpoint=f'/accessory/{accessory_id}')
        if 'accessory' in response:  # if accessory_id was found
            accessory = dict()
            accessory['last_sync_date'] = _get_local_time(response['accessory'].get('last_sync_date', None))
            accessory['battery_level'] = response['accessory'].get('battery_level', None)
            accessory['firmware_version'] = response['accessory'].get('firmware_version', None)
            latest_firmware = response['latest_firmware'].get('accessory_version', None)
            if latest_firmware is not None and accessory['firmware_version'] == latest_firmware.split('-')[0]:
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


def _get_cleaned_session(session):
    item = dict()
    # get different times and convert to local timezone
    item['id'] = session['id']
    item['event_date'] = _get_local_time(session['event_date'])
    item['end_date'] = _get_local_time(session.get('end_date', None))
    item['upload_end_date'] = _get_local_time(session.get('upload_end_date', None))
    # item['updated_date'] = _get_local_time(session.get('updated_date', None))
    item['cause_of_failure'] = None
    
    session_status = session.get('session_status', None)

    # The statuses displayed on mobile are UPLOAD_PAUSED, UPLOAD_IN_PROGRESS, PROCESSING_IN_PROGRESS, PROCESSING_FAILED and PROCESSING_COMPLETE
    if session_status == 'UPLOAD_IN_PROGRESS':
        # If uploading check when the last part came in and if more than 4 mins since last upload, UPLOAD_PAUSED
        if session.get('updated_date') is not None and (datetime.now() - parse_datetime(session['updated_date'])).seconds >= 60 * 1:
            item['status'] = 'UPLOAD_PAUSED'
        else:
            item['status'] = 'UPLOAD_IN_PROGRESS'
    elif session_status in ['UPLOAD_COMPLETE', 'PROCESSING_IN_PROGRESS']:
        item['status'] = 'PROCESSING_IN_PROGRESS'
    elif session_status in ['PROCESSING_FAILED']:
        item['status'] = session_status
        # if failed processing, assign one of CALIBRATION, PLACEMENT, ERROR
        session_failure = session.get('failure')
        if session_failure in ['HEADING_DETECTION', 'STILL_DETECTION', 'MARCH_DETECTION', 'NO_MARCH_DETECTION_DATA']:
            item['cause_of_failure'] = 'CALIBRATION'
        elif session_failure == 'LEFT_RIGHT_DETECTION':
            item['cause_of_failure'] = 'PLACEMENT'
        else:
            item['cause_of_failure'] = 'ERROR'
    else:  # all other statuses (PROCESSING_COMPLETE, TOO_SHORT, NO_DATA) return normally
        item['status'] = session_status

    if item['end_date'] is not None and item['event_date'] is not None:
        item['duration'] = round((parse_datetime(item['end_date']) - parse_datetime(item['event_date'])).seconds / 60, 2)
    else:
        item['duration'] = None
    return item


def _get_local_time(utc_time_string):
    offset = _get_offset()
    if utc_time_string is not None:
        try:
            local_time = parse_datetime(utc_time_string) + timedelta(minutes=offset)
            return format_datetime(local_time).replace('Z', '')
        except InvalidSchemaException:
            return None
    else:
        return utc_time_string


def _get_offset():
    tz = request.json.get('timezone', '-04:00')
    offset = tz.split(":")
    hour_offset = int(offset[0])
    minute_offset = int(offset[1])
    if hour_offset < 0:
        minute_offset = hour_offset * 60 - minute_offset
    else:
        minute_offset += hour_offset * 60
    return minute_offset


def _get_epoch_time(time_string):
    if time_string is not None:
        return int(parse_datetime(time_string).replace(tzinfo=timezone.utc).timestamp())
    else:
        return None
