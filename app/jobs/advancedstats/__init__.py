from pymongo import ASCENDING
import logging

from ..job import Job
from config import get_mongo_collection
import requests
import json
import boto3
import os
from utils import parse_datetime

_logger = logging.getLogger()


class AdvancedstatsJob(Job):

    def _run(self):
        event_date = self.datastore.get_metadatum('event_date')
        active_blocks = get_unit_blocks(self.datastore.session_id, event_date)

        unit_blocks = []
        for a in active_blocks:
            unit_blocks.extend(a["unitBlocks"])

        if len(unit_blocks) > 0:
            # Write out active blocks
            from .summary_analysis_job import SummaryAnalysisJob
            SummaryAnalysisJob(self.datastore, unit_blocks).run()

            from .training_volume_job import TrainingVolumeJob
            TrainingVolumeJob(self.datastore, unit_blocks).run()

            from .complexity_matrix_job import ComplexityMatrixJob
            cmj = ComplexityMatrixJob(self.datastore, unit_blocks)
            cmj.run()

            # from .fatigue_processor_job import FatigueProcessorJob
            # FatigueProcessorJob(self.datastore, cmj.motion_complexity_single_leg, cmj.motion_complexity_double_leg).run()

            from .asymmetry_processor_job import AsymmetryProcessorJob
            left_apt, right_apt = AsymmetryProcessorJob(self.datastore, unit_blocks, cmj.motion_complexity_single_leg).run()

            self._write_session_to_plans(left_apt, right_apt )

    def _write_session_to_plans(self, left_apt, right_apt):
        _service_token = invoke_lambda_sync(f'users-{os.environ["ENVIRONMENT"]}-apigateway-serviceauth', '2_0')['token']
        user_id = self.datastore.get_metadatum('user_id')
        event_date = self.datastore.get_metadatum('event_date')
        end_date = self.datastore.get_metadatum('end_date')
        seconds_duration = (parse_datetime(end_date) - parse_datetime(event_date)).seconds

        body = {'user_id': user_id,
                'event_date': event_date,
                "session_id": self.datastore.session_id,
                "seconds_duration": seconds_duration,
                "asymmetry": {
                    "left_apt": left_apt,
                    "right_apt": right_apt
                    }
                }  
        headers = {'Content-Type': 'application/json',
                   'Authorization': _service_token}
        requests.post(url=f'https://apis.{os.environ["ENVIRONMENT"]}.fathomai.com/plans/4_3/session/three_sensor_data',
                      data=json.dumps(body),
                      headers=headers)


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
        {'unitBlocks': 1, '_id': 1, 'timeStart': 1, 'timeEnd': 1}).sort('unitBlocks.timeStart', direction=ASCENDING)
    )
    return unit_blocks


def invoke_lambda_sync(function_name, version, payload=None):
    _lambda_client = boto3.client('lambda')
    res = _lambda_client.invoke(
        FunctionName=f'{function_name}:{version}',
        Payload=json.dumps(payload or {}),
    )
    return json.loads(res['Payload'].read())
