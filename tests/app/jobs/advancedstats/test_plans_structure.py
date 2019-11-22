from app.jobs.advancedstats.asymmetry_processor_job import AsymmetryEvents, TimeBlock
from app.jobs.advancedstats.plans_structure import PlansFactory
from datetime import datetime, timedelta
import os
os.environ["ENVIRONMENT"] = "dev"


def get_asymmetry_events():

    asymmetry_events = AsymmetryEvents()
    asymmetry_events.ankle_pitch_summary.left = 79
    asymmetry_events.ankle_pitch_summary.right = 82
    asymmetry_events.ankle_pitch_summary.symmetric_events = 50
    asymmetry_events.ankle_pitch_summary.asymmetric_events = 100
    asymmetry_events.ankle_pitch_summary.percent_events_asymmetric = 67
    asymmetry_events.anterior_pelvic_tilt_summary.left = 12
    asymmetry_events.anterior_pelvic_tilt_summary.right = 10
    asymmetry_events.anterior_pelvic_tilt_summary.asymmetric_events = 30
    asymmetry_events.anterior_pelvic_tilt_summary.symmetric_events = 60
    asymmetry_events.anterior_pelvic_tilt_summary.percent_events_asymmetric = 33

    return asymmetry_events


def get_movement_events():

    movement_events = []
    m1 = TimeBlock()
    m1.time_block = 0
    m1.start_time = 10
    m1.end_time = 40
    m1.ankle_pitch.left = 81
    m1.ankle_pitch.right = 90
    m1.ankle_pitch.significant = True
    m1.anterior_pelvic_tilt.left = 12
    m1.anterior_pelvic_tilt.right = 10
    m1.anterior_pelvic_tilt.significant = True
    movement_events.append(m1)

    m2 = TimeBlock()
    m2.time_block = 1
    m2.start_time = 41
    m2.end_time = 71
    m2.ankle_pitch.left = 88
    m2.ankle_pitch.right = 89
    m2.ankle_pitch.significant = False
    m2.anterior_pelvic_tilt.left = 11
    m2.anterior_pelvic_tilt.right = 9
    m2.anterior_pelvic_tilt.significant = True
    movement_events.append(m2)

    return movement_events

def test_get_4_3_endpoint():

    asymmetry_events = get_asymmetry_events()
    plans_factory = PlansFactory("4_3", "dev", "tester", datetime.now(), "test_session_id", 600, asymmetry_events)
    plans = plans_factory.get_plans()
    assert f'https://apis.dev.fathomai.com/plans/4_3/session/three_sensor_data' == plans.endpoint


def test_get_4_4_endpoint():

    asymmetry_events = get_asymmetry_events()
    plans_factory = PlansFactory("4_4", "dev", "tester", datetime.now(), "test_session_id", 600, asymmetry_events)
    plans = plans_factory.get_plans()
    assert f'https://apis.dev.fathomai.com/plans/4_4/session/tester/three_sensor_data' == plans.endpoint


def test_get_4_5_endpoint():

    asymmetry_events = get_asymmetry_events()
    plans_factory = PlansFactory("4_5", "dev", "tester", datetime.now(), "test_session_id", 600, asymmetry_events, datetime.now() + timedelta(minutes=30))
    plans = plans_factory.get_plans()
    assert f'https://apis.dev.fathomai.com/plans/4_5/session/tester/three_sensor_data' == plans.endpoint


def test_get_4_6_endpoint():

    asymmetry_events = get_asymmetry_events()
    plans_factory = PlansFactory("4_6", "dev", "tester", datetime.now(), "test_session_id", 600, asymmetry_events, datetime.now() + timedelta(minutes=30))
    plans = plans_factory.get_plans()
    assert f'https://apis.dev.fathomai.com/plans/4_6/session/tester/three_sensor_data' == plans.endpoint


def test_get_4_3_plans_body():
    asymmetry_events = get_asymmetry_events()
    event_date = datetime.now()
    plans_factory = PlansFactory("4_3", "dev", "tester", event_date, "test_session_id", 600, asymmetry_events)
    plans = plans_factory.get_plans()
    assert "tester" == plans.body["user_id"]
    assert "test_session_id" == plans.body["session_id"]
    assert 600 == plans.body["seconds_duration"]
    assert event_date == plans.body["event_date"]
    assert 12 == plans.body["asymmetry"]["left_apt"]
    assert 10 == plans.body["asymmetry"]["right_apt"]
    assert 30 == plans.body["asymmetry"]["asymmetric_events"]
    assert 60 == plans.body["asymmetry"]["symmetric_events"]
    assert "percent_events_asymmetric" not in plans.body["asymmetry"]


def test_get_4_4_plans_body():
    asymmetry_events = get_asymmetry_events()
    event_date = datetime.now()
    plans_factory = PlansFactory("4_4", "dev", "tester", event_date, "test_session_id", 600, asymmetry_events)
    plans = plans_factory.get_plans()
    assert "user_id" not in plans.body
    assert "test_session_id" == plans.body["session_id"]
    assert 600 == plans.body["seconds_duration"]
    assert event_date == plans.body["event_date"]
    assert 12 == plans.body["asymmetry"]["left_apt"]
    assert 10 == plans.body["asymmetry"]["right_apt"]
    assert 30 == plans.body["asymmetry"]["asymmetric_events"]
    assert 60 == plans.body["asymmetry"]["symmetric_events"]
    assert "percent_events_asymmetric" not in plans.body["asymmetry"]


def test_get_4_5_plans_body():
    asymmetry_events = get_asymmetry_events()
    event_date = datetime.now()
    end_date = event_date + timedelta(minutes=30)
    plans_factory = PlansFactory("4_5", "dev", "tester", event_date, "test_session_id", 600, asymmetry_events, end_date)
    plans = plans_factory.get_plans()
    assert "user_id" not in plans.body
    assert "test_session_id" == plans.body["session_id"]
    assert 600 == plans.body["seconds_duration"]
    assert event_date == plans.body["event_date"]
    assert end_date == plans.body["end_date"]
    assert 12 == plans.body["asymmetry"]["apt"]["left"]
    assert 10 == plans.body["asymmetry"]["apt"]["right"]
    assert 30 == plans.body["asymmetry"]["apt"]["asymmetric_events"]
    assert 60 == plans.body["asymmetry"]["apt"]["symmetric_events"]
    assert 33 == plans.body["asymmetry"]["apt"]["percent_events_asymmetric"]

    assert 79 == plans.body["asymmetry"]["ankle_pitch"]["left"]
    assert 82 == plans.body["asymmetry"]["ankle_pitch"]["right"]
    assert 100 == plans.body["asymmetry"]["ankle_pitch"]["asymmetric_events"]
    assert 50 == plans.body["asymmetry"]["ankle_pitch"]["symmetric_events"]
    assert 67 == plans.body["asymmetry"]["ankle_pitch"]["percent_events_asymmetric"]


def test_get_4_6_plans_body():
    asymmetry_events = get_asymmetry_events()
    event_date = datetime.now()
    end_date = event_date + timedelta(minutes=30)
    plans_factory = PlansFactory("4_6", "dev", "tester", event_date, "test_session_id", 600, asymmetry_events, end_date)
    plans = plans_factory.get_plans()
    assert "user_id" not in plans.body
    assert "test_session_id" == plans.body["session_id"]
    assert 600 == plans.body["seconds_duration"]
    assert event_date == plans.body["event_date"]
    assert end_date == plans.body["end_date"]
    assert 12 == plans.body["asymmetry"]["apt"]["left"]
    assert 10 == plans.body["asymmetry"]["apt"]["right"]
    assert 30 == plans.body["asymmetry"]["apt"]["asymmetric_events"]
    assert 60 == plans.body["asymmetry"]["apt"]["symmetric_events"]
    assert 33 == plans.body["asymmetry"]["apt"]["percent_events_asymmetric"]

    assert 79 == plans.body["asymmetry"]["ankle_pitch"]["left"]
    assert 82 == plans.body["asymmetry"]["ankle_pitch"]["right"]
    assert 100 == plans.body["asymmetry"]["ankle_pitch"]["asymmetric_events"]
    assert 50 == plans.body["asymmetry"]["ankle_pitch"]["symmetric_events"]
    assert 67 == plans.body["asymmetry"]["ankle_pitch"]["percent_events_asymmetric"]


def test_get_4_3_plans_mongo_record():
    asymmetry_events = get_asymmetry_events()
    event_date = datetime.now()
    plans_factory = PlansFactory("4_3", "dev", "tester", event_date, "test_session_id", 600, asymmetry_events)
    plans = plans_factory.get_plans()
    movement_events = get_movement_events()
    mongo_record = plans.get_mongo_asymmetry_record(movement_events)
    assert "tester" == mongo_record["user_id"]
    assert "test_session_id" == mongo_record["session_id"]
    assert 600 == mongo_record["seconds_duration"]
    assert event_date == mongo_record["event_date"]
    assert 12 == mongo_record["left_apt"]
    assert 10 == mongo_record["right_apt"]
    assert 30 == mongo_record["asymmetric_events"]
    assert 60 == mongo_record["symmetric_events"]
    assert 33 == mongo_record["percent_events_asymmetric"]
    time_blocks = mongo_record["time_blocks"]
    assert 0 == time_blocks[0]['time_block']
    assert 10 == time_blocks[0]['start_time']
    assert 40 == time_blocks[0]['end_time']
    assert 12 == time_blocks[0]['left']
    assert 10 == time_blocks[0]['right']
    assert True is time_blocks[0]['significant']
    assert 1 == time_blocks[1]['time_block']
    assert 41 == time_blocks[1]['start_time']
    assert 71 == time_blocks[1]['end_time']
    assert 11 == time_blocks[1]['left']
    assert 9 == time_blocks[1]['right']
    assert True is time_blocks[1]['significant']


def test_get_4_4_plans_mongo_record():
    asymmetry_events = get_asymmetry_events()
    event_date = datetime.now()
    plans_factory = PlansFactory("4_4", "dev", "tester", event_date, "test_session_id", 600, asymmetry_events)
    plans = plans_factory.get_plans()
    movement_events = get_movement_events()
    mongo_record = plans.get_mongo_asymmetry_record(movement_events)
    assert "tester" == mongo_record["user_id"]
    assert "test_session_id" == mongo_record["session_id"]
    assert 600 == mongo_record["seconds_duration"]
    assert event_date == mongo_record["event_date"]
    assert 12 == mongo_record["left_apt"]
    assert 10 == mongo_record["right_apt"]
    assert 30 == mongo_record["asymmetric_events"]
    assert 60 == mongo_record["symmetric_events"]
    assert 33 == mongo_record["percent_events_asymmetric"]
    time_blocks = mongo_record["time_blocks"]
    assert 0 == time_blocks[0]['time_block']
    assert 10 == time_blocks[0]['start_time']
    assert 40 == time_blocks[0]['end_time']
    assert 12 == time_blocks[0]['left']
    assert 10 == time_blocks[0]['right']
    assert True is time_blocks[0]['significant']
    assert 1 == time_blocks[1]['time_block']
    assert 41 == time_blocks[1]['start_time']
    assert 71 == time_blocks[1]['end_time']
    assert 11 == time_blocks[1]['left']
    assert 9 == time_blocks[1]['right']
    assert True is time_blocks[1]['significant']


def test_get_4_5_plans_mongo_record():
    asymmetry_events = get_asymmetry_events()
    event_date = datetime.now()
    plans_factory = PlansFactory("4_5", "dev", "tester", event_date, "test_session_id", 600, asymmetry_events)
    plans = plans_factory.get_plans()
    movement_events = get_movement_events()
    mongo_record = plans.get_mongo_asymmetry_record(movement_events)
    assert "tester" == mongo_record["user_id"]
    assert "test_session_id" == mongo_record["session_id"]
    assert 600 == mongo_record["seconds_duration"]
    assert event_date == mongo_record["event_date"]
    assert "left_apt" not in mongo_record
    assert "right_apt" not in mongo_record
    assert "asymmetric_events" not in mongo_record
    assert "symmetric_events" not in mongo_record
    assert "percent_events_asymmetric" not in mongo_record
    time_blocks = mongo_record["time_blocks"]
    assert 0 == time_blocks[0]['time_block']
    assert 10 == time_blocks[0]['start_time']
    assert 40 == time_blocks[0]['end_time']
    assert 12 == time_blocks[0]['apt']['left']
    assert 10 == time_blocks[0]['apt']['right']
    assert True is time_blocks[0]['apt']['significant']
    assert 81 == time_blocks[0]['ankle_pitch']['left']
    assert 90 == time_blocks[0]['ankle_pitch']['right']
    assert True is time_blocks[0]['ankle_pitch']['significant']
    assert 1 == time_blocks[1]['time_block']
    assert 41 == time_blocks[1]['start_time']
    assert 71 == time_blocks[1]['end_time']
    assert 11 == time_blocks[1]['apt']['left']
    assert 9 == time_blocks[1]['apt']['right']
    assert True is time_blocks[1]['apt']['significant']
    assert 88 == time_blocks[1]['ankle_pitch']['left']
    assert 89 == time_blocks[1]['ankle_pitch']['right']
    assert False is time_blocks[1]['ankle_pitch']['significant']


def test_get_4_6_plans_mongo_record():
    asymmetry_events = get_asymmetry_events()
    event_date = datetime.now()
    plans_factory = PlansFactory("4_6", "dev", "tester", event_date, "test_session_id", 600, asymmetry_events)
    plans = plans_factory.get_plans()
    movement_events = get_movement_events()
    mongo_record = plans.get_mongo_asymmetry_record(movement_events)
    assert "tester" == mongo_record["user_id"]
    assert "test_session_id" == mongo_record["session_id"]
    assert 600 == mongo_record["seconds_duration"]
    assert event_date == mongo_record["event_date"]
    assert "left_apt" not in mongo_record
    assert "right_apt" not in mongo_record
    assert "asymmetric_events" not in mongo_record
    assert "symmetric_events" not in mongo_record
    assert "percent_events_asymmetric" not in mongo_record
    time_blocks = mongo_record["time_blocks"]
    assert 0 == time_blocks[0]['time_block']
    assert 10 == time_blocks[0]['start_time']
    assert 40 == time_blocks[0]['end_time']
    assert 12 == time_blocks[0]['apt']['left']
    assert 10 == time_blocks[0]['apt']['right']
    assert True is time_blocks[0]['apt']['significant']
    assert 81 == time_blocks[0]['ankle_pitch']['left']
    assert 90 == time_blocks[0]['ankle_pitch']['right']
    assert True is time_blocks[0]['ankle_pitch']['significant']
    assert 1 == time_blocks[1]['time_block']
    assert 41 == time_blocks[1]['start_time']
    assert 71 == time_blocks[1]['end_time']
    assert 11 == time_blocks[1]['apt']['left']
    assert 9 == time_blocks[1]['apt']['right']
    assert True is time_blocks[1]['apt']['significant']
    assert 88 == time_blocks[1]['ankle_pitch']['left']
    assert 89 == time_blocks[1]['ankle_pitch']['right']
    assert False is time_blocks[1]['ankle_pitch']['significant']