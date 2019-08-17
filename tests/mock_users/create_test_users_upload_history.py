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
    symmetrical = []
    dates = []
    for u in users:
        if u == "tread_a@200.com":
            sessions = ["38c8215f-c60e-56e4-9c6e-58413f961360",
                        "0f465cc7-1489-5f32-a5a2-3e6a6cf91d8b",
                        "d8d0198c-b186-5158-86d6-e3b623af0ef1"]
            user_id = "6fc48b46-23c8-4490-9885-e109ff63c20e"

            symmetrical = [False, False, False]
            dates = [format_datetime(datetime.now()),
                     format_datetime(datetime.now() - timedelta(days=2)),
                     format_datetime(datetime.now() - timedelta(days=4))]

        elif u == "tread_a_2@200.com":
            sessions = ["38c8215f-c60e-56e4-9c6e-58413f961360",
                        "0f465cc7-1489-5f32-a5a2-3e6a6cf91d8b",
                        "d8d0198c-b186-5158-86d6-e3b623af0ef1"]
            user_id = "441a296a-6d37-4de3-ba04-bd725da05613"

            symmetrical = [False, False, False]
            dates = [format_datetime(datetime.now()),
                     format_datetime(datetime.now() - timedelta(days=2)),
                     format_datetime(datetime.now() - timedelta(days=4))]
        elif u == "tread_b@200.com":
            sessions = [
                "a7083021-86e7-5dd1-8245-683bcdf6f6fe",
                "2d8dd78d-2e1e-5e91-83b3-a19181b88eab",
                "b9485ddd-4bf7-559f-9bfc-700bfaffbc86",
                "be2e9653-e0e0-5ae0-a700-56b6bfe0d595"
            ]
            user_id = "4673998d-5206-4275-a048-da5dda6a7342"

            symmetrical = [False, False, False, False]
            dates = [format_datetime(datetime.now()),
                     format_datetime(datetime.now() - timedelta(days=2)),
                     format_datetime(datetime.now() - timedelta(days=4)),
                     format_datetime(datetime.now() - timedelta(days=5))]

        elif u == "tread_b_mazen@200.com":
            sessions = [
                "a7083021-86e7-5dd1-8245-683bcdf6f6fe",
                "2d8dd78d-2e1e-5e91-83b3-a19181b88eab",
                "b9485ddd-4bf7-559f-9bfc-700bfaffbc86",
                "be2e9653-e0e0-5ae0-a700-56b6bfe0d595"
            ]
            user_id = "1569f9bb-6de3-49a9-913c-f69d7d763d25"

            symmetrical = [False, False, False, False]
            dates = [format_datetime(datetime.now()),
                     format_datetime(datetime.now() - timedelta(days=2)),
                     format_datetime(datetime.now() - timedelta(days=4)),
                     format_datetime(datetime.now() - timedelta(days=5))]

        elif u == "tread_b_2@200.com":
            sessions = [
                "a7083021-86e7-5dd1-8245-683bcdf6f6fe",
                "2d8dd78d-2e1e-5e91-83b3-a19181b88eab",
                "b9485ddd-4bf7-559f-9bfc-700bfaffbc86",
                "be2e9653-e0e0-5ae0-a700-56b6bfe0d595"
            ]
            user_id = "e72bfb85-9c66-4cbe-8a77-20e5eda0a793"

            symmetrical = [False, False, False, False]
            dates = [format_datetime(datetime.now()),
                     format_datetime(datetime.now() - timedelta(days=2)),
                     format_datetime(datetime.now() - timedelta(days=4)),
                     format_datetime(datetime.now() - timedelta(days=5))]
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
            dates = [format_datetime(datetime.now()),
                     format_datetime(datetime.now() - timedelta(days=2)),
                     format_datetime(datetime.now() - timedelta(days=4)),
                     format_datetime(datetime.now() - timedelta(days=6)),
                     format_datetime(datetime.now() - timedelta(days=8)),
                     format_datetime(datetime.now() - timedelta(days=10)),
                     format_datetime(datetime.now() - timedelta(days=12)),
                     format_datetime(datetime.now() - timedelta(days=14))]

            symmetrical = [False, False, False, False, False, False, False, False]
        elif u == "tread_run_2@200.com":
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
            user_id = "4c8792b2-d5e2-475b-b55d-c16e70dc47aa"
            dates = [format_datetime(datetime.now()),
                     format_datetime(datetime.now() - timedelta(days=2)),
                     format_datetime(datetime.now() - timedelta(days=4)),
                     format_datetime(datetime.now() - timedelta(days=6)),
                     format_datetime(datetime.now() - timedelta(days=8)),
                     format_datetime(datetime.now() - timedelta(days=10)),
                     format_datetime(datetime.now() - timedelta(days=12)),
                     format_datetime(datetime.now() - timedelta(days=14))]

            symmetrical = [False, False, False, False, False, False, False, False]

        elif u == "tread_run_2_mazen@200.com":
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
            user_id = "23e93c04-c7cc-40b3-8e34-e43a9cab286a"
            dates = [format_datetime(datetime.now()),
                     format_datetime(datetime.now() - timedelta(days=2)),
                     format_datetime(datetime.now() - timedelta(days=4)),
                     format_datetime(datetime.now() - timedelta(days=6)),
                     format_datetime(datetime.now() - timedelta(days=8)),
                     format_datetime(datetime.now() - timedelta(days=10)),
                     format_datetime(datetime.now() - timedelta(days=12)),
                     format_datetime(datetime.now() - timedelta(days=14))]

            symmetrical = [False, False, False, False, False, False, False, False]

        elif u == "run_a@200.com":
            sessions = [
                "7bbff8e0-189a-5643-93bc-9730e0fdcd20",
                "39f243c2-6baf-5558-a2df-4f051f88c06f"
            ]
            user_id = "2b4a1792-42c7-460e-9e4c-98627e72cc6f"
            dates = [format_datetime(datetime.now()),
                     format_datetime(datetime.now() - timedelta(days=2))]
            symmetrical = [False, False]

        elif u == "run_a_2@200.com":
            sessions = [
                "7bbff8e0-189a-5643-93bc-9730e0fdcd20",
                "39f243c2-6baf-5558-a2df-4f051f88c06f"
            ]
            user_id = "5c695e58-0aba-4eec-9af1-fa93970d3132"
            dates = [format_datetime(datetime.now()),
                     format_datetime(datetime.now() - timedelta(days=2))]
            symmetrical = [False, False]

        elif u == "run_a_mazen@200.com":
            sessions = [
                "7bbff8e0-189a-5643-93bc-9730e0fdcd20",
                "39f243c2-6baf-5558-a2df-4f051f88c06f"
            ]
            user_id = "110e14e6-8630-48e8-b75d-0caad447d661"
            dates = [format_datetime(datetime.now()),
                     format_datetime(datetime.now() - timedelta(days=2))]
            symmetrical = [False, False]

        elif u == "run_a_3@200.com":
            sessions = [
                "7bbff8e0-189a-5643-93bc-9730e0fdcd20",
                "39f243c2-6baf-5558-a2df-4f051f88c06f"
            ]
            user_id = "9e90e3ef-c6e0-4e2d-a430-a52f1e61a962"
            dates = [format_datetime(datetime.now()),
                     format_datetime(datetime.now() - timedelta(days=2))]
            symmetrical = [False, False]

        elif u == "sym@200.com":
            sessions = [
                "7bbff8e0-189a-5643-93bc-9730e0fdcd20",
                "39f243c2-6baf-5558-a2df-4f051f88c06f"
            ]
            user_id = "7fd0c1d4-61ac-4ce5-9621-16d69501b211"
            dates = [format_datetime(datetime.now()),
                     format_datetime(datetime.now() - timedelta(days=2))]

            symmetrical = [True, True]

        elif u == "sym_2@200.com":
            sessions = [
                "7bbff8e0-189a-5643-93bc-9730e0fdcd20",
                "39f243c2-6baf-5558-a2df-4f051f88c06f"
            ]
            user_id = "aa1534d0-4abd-41c0-9b84-4e414b3d86d4"
            dates = [format_datetime(datetime.now()),
                     format_datetime(datetime.now() - timedelta(days=2))]

            symmetrical = [True, True]

        elif u == "sym_3@200.com":
            sessions = [
                "7bbff8e0-189a-5643-93bc-9730e0fdcd20",
                "39f243c2-6baf-5558-a2df-4f051f88c06f"
            ]
            user_id = "34b47309-7ad5-4222-b865-0f825680541e"
            dates = [format_datetime(datetime.now()),
                     format_datetime(datetime.now() - timedelta(days=2))]

            symmetrical = [True, True]

        elif u == "long_3s@200.com":
            sessions = [
                "958dba09-c338-5118-86a3-d20a559f09c2",
                "c14f1728-b4f5-5fb4-845c-9dc830b3e9bf",
                "b2a95b1b-8d7b-5638-bd69-7299a362c717"
            ]
            user_id = "928f64b5-a761-4278-8724-95a908499fae"
            dates = [format_datetime(datetime.now()),
                     format_datetime(datetime.now() - timedelta(days=2)),
                     format_datetime(datetime.now() - timedelta(days=4))]

            symmetrical = [False, False, False]

        elif u == "long_3s_2@200.com":
            sessions = [
                "958dba09-c338-5118-86a3-d20a559f09c2",
                "c14f1728-b4f5-5fb4-845c-9dc830b3e9bf",
                "b2a95b1b-8d7b-5638-bd69-7299a362c717"
            ]
            user_id = "06a112b3-b07f-4da7-a6bb-16558c5345ea"
            dates = [format_datetime(datetime.now()),
                     format_datetime(datetime.now() - timedelta(days=2)),
                     format_datetime(datetime.now() - timedelta(days=4))]

            symmetrical = [False, False, False]

        elif u == "half_sym@200.com":
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
            user_id = "7cf2f832-a043-468c-8f61-13d07765d2a2"
            dates = [format_datetime(datetime.now()),
                     format_datetime(datetime.now() - timedelta(days=2)),
                     format_datetime(datetime.now() - timedelta(days=4)),
                     format_datetime(datetime.now() - timedelta(days=6)),
                     format_datetime(datetime.now() - timedelta(days=8)),
                     format_datetime(datetime.now() - timedelta(days=10)),
                     format_datetime(datetime.now() - timedelta(days=12)),
                     format_datetime(datetime.now() - timedelta(days=14))]

            symmetrical = [True, False, True, False, True, False, True, False]

        elif u == "half_sym_2@200.com":
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
            user_id = "d81af04a-385e-4a43-ad95-63222549ecc4"
            dates = [format_datetime(datetime.now()),
                     format_datetime(datetime.now() - timedelta(days=2)),
                     format_datetime(datetime.now() - timedelta(days=4)),
                     format_datetime(datetime.now() - timedelta(days=6)),
                     format_datetime(datetime.now() - timedelta(days=8)),
                     format_datetime(datetime.now() - timedelta(days=10)),
                     format_datetime(datetime.now() - timedelta(days=12)),
                     format_datetime(datetime.now() - timedelta(days=14))]

            symmetrical = [True, False, True, False, True, False, True, False]

        if len(user_id) > 0:

            reset_users.clear_user(user_id, suffix)

            for s in range(0, len(sessions)):

                date = dates[s]

                active_blocks = get_unit_blocks(sessions[s], date)
                unit_blocks = []

                active_start = None
                active_end = None

                for a in active_blocks:
                    if active_start is None:
                        active_start = a["timeStart"]
                    if active_end is None:
                        active_end = a["timeEnd"]
                    active_start = min(active_start, a["timeStart"])
                    active_end = max(active_end, a["timeEnd"])
                    unit_blocks.extend(a["unitBlocks"])

                seconds_duration = (parse_datetime(active_end) - parse_datetime(active_start)).seconds

                unit_blocks = sorted(unit_blocks, key=lambda ub: ub['timeStart'])
                unit_blocks = [b for b in unit_blocks if b["cadence_zone"] is not None and b["cadence_zone"] != 10]

                session_time_start = parse_datetime(date)
                session_time_end = format_datetime(session_time_start + timedelta(seconds=seconds_duration))

                ds = MockDatastore(sessions[s], date, user_id, session_time_end)

                cmj = ComplexityMatrixJob(ds, unit_blocks)
                cmj.run()

                job = AsymmetryProcessorJob(ds, unit_blocks, cmj.motion_complexity_single_leg)
                asymmetry_events = job._get_movement_asymmetries()
                make_symmetrical = symmetrical[s]
                if make_symmetrical:
                    for a in asymmetry_events:
                        a.significant = False

                left_apt, right_apt = job._get_session_asymmetry_apts(asymmetry_events)

                job.write_movement_asymmetry(asymmetry_events, left_apt, right_apt)

                advanced_stats_job = AdvancedstatsJob(ds)
                advanced_stats_job._write_session_to_plans(left_apt, right_apt)



