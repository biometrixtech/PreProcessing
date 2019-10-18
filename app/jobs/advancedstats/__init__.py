from pymongo import ASCENDING
import logging

from ..job import Job
from config import get_mongo_collection
import requests
import json
import boto3
import os
from utils import parse_datetime
from .plans_structure import PlansFactory

_logger = logging.getLogger()


class AdvancedstatsJob(Job):

    def _run(self):
        event_date = self.datastore.get_metadatum('event_date')
        active_blocks = get_unit_blocks(self.datastore.session_id, event_date)

        unit_blocks = []
        for a in active_blocks:
            unit_blocks.extend(a["unitBlocks"])

        unit_blocks = [b for b in unit_blocks if b["cadence_zone"] is not None and b["cadence_zone"] != 10 and b["cadence_zone"] != 0]
        unit_blocks = sorted(unit_blocks, key=lambda ub: ub['timeStart'])

        if len(unit_blocks) > 0:

            active_time_start = unit_blocks[0]['timeStart']
            active_time_end = unit_blocks[len(unit_blocks) - 1]['timeEnd']
            # # Write out active blocks
            # from .summary_analysis_job import SummaryAnalysisJob
            # SummaryAnalysisJob(self.datastore, unit_blocks).run()

            # from .training_volume_job import TrainingVolumeJob
            # TrainingVolumeJob(self.datastore, unit_blocks).run()

            from .complexity_matrix_job import ComplexityMatrixJob
            cmj = ComplexityMatrixJob(self.datastore, unit_blocks)
            cmj.run()

            # from .fatigue_processor_job import FatigueProcessorJob
            # FatigueProcessorJob(self.datastore, cmj.motion_complexity_single_leg, cmj.motion_complexity_double_leg).run()

            from .asymmetry_processor_job import AsymmetryProcessorJob, AsymmetryEvents
            asymmetry_events, movement_patterns = AsymmetryProcessorJob(self.datastore, unit_blocks, cmj.motion_complexity_single_leg, active_time_start, active_time_end).run()

            self._write_session_to_plans(asymmetry_events, movement_patterns, active_time_start, active_time_end)

    def _write_session_to_plans(self, asymmetry_events, movement_patterns, active_time_start, active_time_end):
        _service_token = invoke_lambda_sync(f'users-{os.environ["ENVIRONMENT"]}-apigateway-serviceauth', '2_0')['token']
        user_id = self.datastore.get_metadatum('user_id')
        event_date = self.datastore.get_metadatum('event_date')
        end_date = self.datastore.get_metadatum('end_date')

        #seconds_duration = (parse_datetime(end_date) - parse_datetime(event_date)).seconds
        seconds_duration = (parse_datetime(active_time_end) - parse_datetime(active_time_start)).seconds

        headers = {'Content-Type': 'application/json',
                   'Authorization': _service_token}

        plans_api_version = self.datastore.get_metadatum('plans_api_version', '4_4')

        plans_factory = PlansFactory(plans_api_version, os.environ["ENVIRONMENT"], user_id, event_date, self.datastore.session_id,
                                     seconds_duration, end_date)
        plans = plans_factory.get_plans()

        response = requests.post(url=plans.endpoint,
                                 data=json.dumps(plans.get_body(asymmetry_events, movement_patterns)),
                                 headers=headers)

        if plans_api_version != plans_factory.latest_plans_version:
            latest_plans_factory = PlansFactory(plans_factory.latest_plans_version, os.environ["ENVIRONMENT"], user_id, event_date, self.datastore.session_id, seconds_duration)
            latest_plans = latest_plans_factory.get_plans()
            latest_record_out = latest_plans.get_body(asymmetry_events, movement_patterns)
            latest_record_out["plans_version"] = plans_factory.latest_plans_version
            latest_record_out["user_id"] = user_id
            latest_mongo_collection = get_mongo_collection('SESSIONASYMMETRYRESERVE')
            query = {'session_id': self.datastore.session_id, 'user_id': user_id}
            latest_mongo_collection.replace_one(query, latest_record_out, upsert=True)

            _logger.info("Wrote sessionAsymmetryReserve record for " + self.datastore.session_id)

        if response.status_code >= 300:
            _logger.warning(f"API call failed with the following error:\n{response.status_code} {response.text}")
            self.datastore.put_metadata({'failure': 'PLANS_API',
                                         'plans_api_error_code': response.status_code})


def get_unit_blocks(session_id, date):
    """
    Load the unit blocks records from MongoDB
    :param user:
    :param date:
    :return:
    """
    collection = get_mongo_collection('ACTIVEBLOCKS')

    # unit_blocks = list(col.find({'userId': {'$eq': user},'eventDate':date},{'unitBlocks':1,'_id':0}))
    unit_blocks = list(collection.find(
        #{'sessionId': {'$eq': session_id}, 'eventDate': date},
        {'sessionId': {'$eq': session_id}},
        {'unitBlocks': 1, '_id': 1, 'timeStart': 1, 'timeEnd': 1})
    )
    return unit_blocks


def invoke_lambda_sync(function_name, version, payload=None):
    _lambda_client = boto3.client('lambda')
    res = _lambda_client.invoke(
        FunctionName=f'{function_name}:{version}',
        Payload=json.dumps(payload or {}),
    )
    return json.loads(res['Payload'].read())
