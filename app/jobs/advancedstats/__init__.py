from pymongo import ASCENDING
import logging

from ..job import Job
from config import get_mongo_collection
import requests
import json
import boto3

_logger = logging.getLogger()


class AdvancedstatsJob(Job):

    def _run(self):
        user_id = self.datastore.get_metadatum('user_id')
        event_date = self.datastore.get_metadatum('event_date')
        unit_blocks = get_unit_blocks(user_id, event_date)
        self._write_session_to_plans(user_id, event_date)

        if len(unit_blocks) > 0:
            # Write out active blocks
            from .summary_analysis_job import SummaryAnalysisJob
            SummaryAnalysisJob(self.datastore, unit_blocks).run()

            from .training_volume_job import TrainingVolumeJob
            TrainingVolumeJob(self.datastore, unit_blocks).run()

            from .complexity_matrix_job import ComplexityMatrixJob
            cmj = ComplexityMatrixJob(self.datastore, unit_blocks)
            cmj.run()

            from .fatigue_processor_job import FatigueProcessorJob
            FatigueProcessorJob(self.datastore, cmj.motion_complexity_single_leg, cmj.motion_complexity_double_leg).run()

            from .asymmetry_processor_job import AsymmetryProcessorJob
            AsymmetryProcessorJob(self.datastore, unit_blocks, cmj.motion_complexity_single_leg, cmj.motion_complexity_double_leg).run()

    def _write_session_to_plans(self, user_id, event_date):
        _service_token = invoke_lambda_sync('users-dev-apigateway-serviceauth', '2_0')
        print(_service_token)
        print(type(_service_token))
        print(_service_token['token'])
        # ['token']
        # # plans_service = Service('plans', '4_0')
        # body = {'user_id': user_id,
        #         'event_date': event_date+'T10:00:00Z',
        #         'sessions': [{'event_date': event_date+'T10:00:00Z'}]}
        # headers = {'Content-Type': 'application/json',
        #            'Authorization': _service_token}
        # requests.post(url='https://apis.dev.fathomai.com/plans/4_0/session/three_sensor_data',
        #               body=body,
        #               headers=headers)


def get_unit_blocks(user, date):
    """
    Load the unit blocks records from MongoDB
    :param user:
    :param date:
    :return:
    """
    collection = get_mongo_collection('ACTIVEBLOCKS')

    # unit_blocks = list(col.find({'userId': {'$eq': user},'eventDate':date},{'unitBlocks':1,'_id':0}))
    unit_blocks = list(collection.find(
        {'userId': {'$eq': user}, 'eventDate': date},
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
