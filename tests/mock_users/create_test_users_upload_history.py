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
        print(u[0])
        if u[0] in ["tread_a@200.com","tread_a_2@200.com"]:
            sessions = ["38c8215f-c60e-56e4-9c6e-58413f961360",
                        "0f465cc7-1489-5f32-a5a2-3e6a6cf91d8b",
                        "d8d0198c-b186-5158-86d6-e3b623af0ef1"]
            user_id = u[1]

            symmetrical = [False, False, False]
            dates = [format_datetime(datetime.now()),
                     format_datetime(datetime.now() - timedelta(days=2)),
                     format_datetime(datetime.now() - timedelta(days=4))]

        elif u[0] in ["tread_b@200.com", "tread_b_2@200.com", "tread_b_mazen@200.com", "full_fte_tread@200.com",
                      "two_pain_tread@200.com", "two_pain_tread_2@200.com", "full_fte_tread_2@200.com"]:
            sessions = [
                "a7083021-86e7-5dd1-8245-683bcdf6f6fe",
                "2d8dd78d-2e1e-5e91-83b3-a19181b88eab",
                "b9485ddd-4bf7-559f-9bfc-700bfaffbc86",
                "be2e9653-e0e0-5ae0-a700-56b6bfe0d595"
            ]
            user_id = u[1]

            symmetrical = [False, False, False, False]
            dates = [format_datetime(datetime.now()),
                     format_datetime(datetime.now() - timedelta(days=2)),
                     format_datetime(datetime.now() - timedelta(days=4)),
                     format_datetime(datetime.now() - timedelta(days=5))]

        elif u[0] in ["tread_run@200.com","tread_run_2@200.com", "ts_tread@200.com", "nc_sore_tread@200.com",
                      "tread_run_2_mazen@200.com", "nc_sore_tread_2@200.com", "ts_tread_2@200.com", "ivonna+demo1@fathomai.com"]:
            sessions = [
                "f78a9e26-6003-5ac7-8590-3ae4a421dac7",
                "f93e004d-7dd0-56b3-bb22-353750586f5e",
                #"7b6c7bba-3250-5d45-949f-1998ff88800d",
                #"8331f565-08af-564b-8ae9-f847b17fa851",
                #"c7bcaf5e-f4a0-525d-aca9-c9c449f2a39e",
                "2f26eee8-455a-5678-a384-ed5a14c6e54a",
                "398ad5bf-3792-5b63-b07f-60a1e6bda875",
                "07b9b744-3e85-563d-b69a-822148673f58"
            ]
            user_id = u[1]
            dates = [format_datetime(datetime.now()),
                     format_datetime(datetime.now() - timedelta(days=2)),
                     format_datetime(datetime.now() - timedelta(days=4)),
                     format_datetime(datetime.now() - timedelta(days=6)),
                     format_datetime(datetime.now() - timedelta(days=8)),
                     #format_datetime(datetime.now() - timedelta(days=10)),
                     #format_datetime(datetime.now() - timedelta(days=12)),
                     #format_datetime(datetime.now() - timedelta(days=14))
                     ]

            symmetrical = [False, False, False, False, False, False, False, False]

        elif u[0] in ["run_a@200.com","run_a_2@200.com","run_a_mazen@200.com", "run_a_3@200.com"]:
            sessions = [
                "7bbff8e0-189a-5643-93bc-9730e0fdcd20",
                "39f243c2-6baf-5558-a2df-4f051f88c06f"
            ]
            user_id = u[1]
            dates = [format_datetime(datetime.now()),
                     format_datetime(datetime.now() - timedelta(days=2))]
            symmetrical = [False, False]

        elif u[0] in ["sym@200.com", "sym_2@200.com", "sym_3@200.com"]:
            sessions = [
                "7bbff8e0-189a-5643-93bc-9730e0fdcd20",
                "39f243c2-6baf-5558-a2df-4f051f88c06f"
            ]
            user_id = u[1]
            dates = [format_datetime(datetime.now()),
                     format_datetime(datetime.now() - timedelta(days=2))]

            symmetrical = [True, True]

        elif u[0] in ["long_3s@200.com","long_3s_2@200.com","full_fte_long@200.com", "nc_long@200.com",
                      "ts_pain_long@200.com","nc_long_2@200.com", "ts_pain_long_2@200.com",
                      "full_fte_long_2@200.com","ivonna+demo2@fathomai.com"]:
            sessions = [
                "958dba09-c338-5118-86a3-d20a559f09c2",
                #"b6b42d70-b66d-5ff3-a8bc-7047e9f3c993",
                "c14f1728-b4f5-5fb4-845c-9dc830b3e9bf",
                #"b2a95b1b-8d7b-5638-bd69-7299a362c717"
            ]
            user_id = u[1]
            dates = [format_datetime(datetime.now()),
                     format_datetime(datetime.now() - timedelta(days=2)),
                     format_datetime(datetime.now() - timedelta(days=4))]

            symmetrical = [False, False, False]

        elif u[0] in ["half_sym@200.com","half_sym_2@200.com"]:
            sessions = [
                "f78a9e26-6003-5ac7-8590-3ae4a421dac7",
                "f93e004d-7dd0-56b3-bb22-353750586f5e",
                #"7b6c7bba-3250-5d45-949f-1998ff88800d",
                # "8331f565-08af-564b-8ae9-f847b17fa851",
                # "c7bcaf5e-f4a0-525d-aca9-c9c449f2a39e",
                "2f26eee8-455a-5678-a384-ed5a14c6e54a",
                "398ad5bf-3792-5b63-b07f-60a1e6bda875",
                "07b9b744-3e85-563d-b69a-822148673f58"
            ]
            user_id = u[1]
            dates = [format_datetime(datetime.now()),
                     format_datetime(datetime.now() - timedelta(days=2)),
                     format_datetime(datetime.now() - timedelta(days=4)),
                     format_datetime(datetime.now() - timedelta(days=6)),
                     format_datetime(datetime.now() - timedelta(days=8)),
                     format_datetime(datetime.now() - timedelta(days=10)),
                     # format_datetime(datetime.now() - timedelta(days=12)),
                     # format_datetime(datetime.now() - timedelta(days=14))
                     ]

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
                #a = active_blocks[0]
                    if active_start is None:
                        active_start = a["timeStart"]
                    if active_end is None:
                        active_end = a["timeEnd"]
                    active_start = min(active_start, a["timeStart"])
                    active_end = max(active_end, a["timeEnd"])
                    unit_blocks.extend(a["unitBlocks"])

                seconds_duration = (parse_datetime(active_end) - parse_datetime(active_start)).seconds

                unit_blocks = [b for b in unit_blocks if b["cadence_zone"] is not None and b["cadence_zone"] != 10]
                unit_blocks = sorted(unit_blocks, key=lambda ub: ub['timeStart'])

                session_time_start = parse_datetime(date)
                session_time_end = format_datetime(session_time_start + timedelta(seconds=seconds_duration))

                ds = MockDatastore(sessions[s], date, user_id, session_time_end)

                cmj = ComplexityMatrixJob(ds, unit_blocks)
                cmj.run()

                job = AsymmetryProcessorJob(ds, unit_blocks, cmj.motion_complexity_single_leg, active_start, active_end)

                movement_events = job._get_movement_asymmetries()
                make_symmetrical = symmetrical[s]
                if make_symmetrical:
                    for a in movement_events:
                        a.anterior_pelvic_tilt.significant = False
                        a.ankle_pitch.significant = False

                #job._update_leg_extensions()

                asymmetry_events = job._get_session_asymmetry_summary(movement_events)

                job.write_movement_asymmetry(movement_events, asymmetry_events, os.environ["ENVIRONMENT"])

                movement_patterns = job._get_movement_patterns()

                job.write_movement_pattern(movement_patterns, os.environ["ENVIRONMENT"])

                # advanced_stats_job = AdvancedstatsJob(ds)
                # advanced_stats_job._write_session_to_plans(asymmetry_events, movement_patterns, unit_blocks[0]["timeStart"],
                #                                            unit_blocks[len(unit_blocks) - 1]["timeEnd"])




