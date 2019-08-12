import os
import time
import json
import requests

from aws_xray_sdk.core import xray_recorder
os.environ['ENVIRONMENT'] = 'test'
xray_recorder.configure(sampling=False)
xray_recorder.begin_segment(name="test")

from utils import format_datetime, parse_datetime
from datetime import datetime, timedelta
import tests.mock_users.test_users as test_users
import tests.mock_users.reset_users as reset_users
from tests.app.writemongo.datastore import MockDatastore
from app.jobs.advancedstats import get_unit_blocks, AdvancedstatsJob
from app.jobs.advancedstats.asymmetry_processor_job import AsymmetryProcessorJob
from app.jobs.advancedstats.complexity_matrix_job import ComplexityMatrixJob


if __name__ == '__main__':
    start = time.time()
    history_length = 35

    users = test_users.get_test_users()

    sessions = []
    user_id = ""
    suffix = ""
    make_symmetrical = False

    for u in users:
        if u == "tread_a@200.com":
            sessions = ["38c8215f-c60e-56e4-9c6e-58413f961360",
                        "0f465cc7-1489-5f32-a5a2-3e6a6cf91d8b",
                        "d8d0198c-b186-5158-86d6-e3b623af0ef1"]
            user_id = "6fc48b46-23c8-4490-9885-e109ff63c20e"
            make_symmetrical = False
        elif u == "tread_b@200.com":
            sessions = [
                "a7083021-86e7-5dd1-8245-683bcdf6f6fe",
                "2d8dd78d-2e1e-5e91-83b3-a19181b88eab",
                "b9485ddd-4bf7-559f-9bfc-700bfaffbc86",
                "be2e9653-e0e0-5ae0-a700-56b6bfe0d595"
            ]
            user_id = "4673998d-5206-4275-a048-da5dda6a7342"
            make_symmetrical = False
        elif u == "tread_run@200.com":
            sessions = [
                "f78a9e26-6003-5ac7-8590-3ae4a421dac7",
                "f93e004d-7dd0-56b3-bb22-353750586f5e",
                "7b6c7bba-3250-5d45-949f-1998ff88800d",
                "8331f565-08af-564b-8ae9-f847b17fa851",
                "c7bcaf5e-f4a0-525d-aca9-c9c449f2a39e",
                "2f26eee8-455a-5678-a384-ed5a14c6e54a",
                "398ad5bf-3792-5b63-b07f-60a1e6bda875",
                "07b9b744-3e85-563d-b69a-822148673f58"
            ]
            user_id = "bdb8b194-e748-4197-819b-b356f1fb0629"
            make_symmetrical = False
        elif u == "run_a@200.com":
            sessions = [
                "7bbff8e0-189a-5643-93bc-9730e0fdcd20",
                "39f243c2-6baf-5558-a2df-4f051f88c06f"
            ]
            user_id = "2b4a1792-42c7-460e-9e4c-98627e72cc6f"
            make_symmetrical = False

        elif u == "sym@200.com":
            sessions = [
                "7bbff8e0-189a-5643-93bc-9730e0fdcd20",
                "39f243c2-6baf-5558-a2df-4f051f88c06f"
            ]
            user_id = "7fd0c1d4-61ac-4ce5-9621-16d69501b211"
            make_symmetrical = True

        if len(user_id) > 0:

            reset_users.clear_user(user_id, suffix)

            for s in sessions:
                date = format_datetime(datetime.now())
                active_blocks = get_unit_blocks(s, date)
                unit_blocks = []
                for a in active_blocks:
                    unit_blocks.extend(a["unitBlocks"])

                seconds_duraton = 60 * 91

                # session_time_start = parse_datetime(active_blocks[0]["timeStart"])
                session_time_start = parse_datetime(date)
                session_time_end = format_datetime(session_time_start + timedelta(seconds=seconds_duraton))

                ds = MockDatastore(s, date, user_id, session_time_end)

                cmj = ComplexityMatrixJob(ds, unit_blocks)
                cmj.run()

                job = AsymmetryProcessorJob(ds, unit_blocks, cmj.motion_complexity_single_leg)
                asymmetry_events = job._get_movement_asymmetries()
                if make_symmetrical:
                    for a in asymmetry_events:
                        a.significant = False
                        
                left_apt, right_apt = job._get_session_asymmetry_apts(asymmetry_events)

                # faking duration
                session_time_end = format_datetime(session_time_start + timedelta(seconds=len(asymmetry_events) * 30))

                ds = MockDatastore(s, date, user_id, session_time_end)
                fake_job = AsymmetryProcessorJob(ds, unit_blocks, cmj.motion_complexity_single_leg)

                fake_job.write_movement_asymmetry(asymmetry_events, left_apt, right_apt)

                advanced_stats_job = AdvancedstatsJob(ds)
                advanced_stats_job._write_session_to_plans(left_apt, right_apt)



