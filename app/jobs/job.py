from abc import abstractmethod
from aws_xray_sdk.core import xray_recorder
import boto3
import datetime
import logging
import os
import pandas as pd
import numpy as np


_logger = logging.getLogger(__name__)
_cloudwatch_client = boto3.client('cloudwatch')


class Job:
    def __init__(self, datastore):
        self._datastore = datastore
        self.data = None
        self._underlying_ndarray = None

    @property
    def datastore(self):
        return self._datastore

    @property
    def name(self):
        return self.__class__.__name__.lower().replace('job', '')

    @property
    def event_date(self):
        return self.datastore.get_metadatum('event_date')

    @property
    def user_id(self):
        return self.datastore.get_metadatum('user_id')

    @xray_recorder.capture('app.job.run')
    def run(self):
        _logger.info('Running job {} on session {}'.format(self.name, self.datastore.session_id))
        try:
            xray_recorder.current_segment().put_annotation('batchjob', self.name)
            xray_recorder.current_segment().put_annotation('session_id', self.datastore.session_id)
            self._run()
        except Exception as e:
            _logger.error(e)
            _logger.info('Process did not complete successfully! See error below!')
            raise

    @abstractmethod
    def _run(self):
        raise NotImplementedError

    @xray_recorder.capture('app.job.put_cloudwatch_metric')
    def put_cloudwatch_metric(self, metric_name, value, unit):
        try:
            _cloudwatch_client.put_metric_data(
                Namespace='Preprocessing',
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Dimensions': [
                            {'Name': 'Environment', 'Value': os.environ['ENVIRONMENT']},
                            {'Name': 'Job', 'Value': self.name},
                        ],
                        'Timestamp': datetime.datetime.utcnow(),
                        'Value': value,
                        'Unit': unit,
                    },
                    {
                        'MetricName': metric_name,
                        'Dimensions': [{'Name': 'Environment', 'Value': os.environ['ENVIRONMENT']}],
                        'Timestamp': datetime.datetime.utcnow(),
                        'Value': value,
                        'Unit': unit,
                    },
                ]
            )
        except Exception as e:
            _logger.warning("Could not put cloudwatch metric")
            _logger.warning(repr(e))
            # Continue

    def get_ndarray(self):

        data_values = self.data.values
        data = np.asanyarray(data_values)
        self._underlying_ndarray = data

        return data

    def get_core_data_frame_from_ndarray(self, data):

        self._underlying_ndarray = data

        df = pd.DataFrame({'epoch_time': data[:, 0], 'static_0': data[:, 1], 'acc_0_x': data[:, 2],
                           'acc_0_y': data[:, 3], 'acc_0_z': data[:, 4], 'quat_0_w': data[:, 5],
                           'quat_0_x': data[:, 6], 'quat_0_y': data[:, 7], 'quat_0_z': data[:, 8],
                           'static_1': data[:, 9], 'acc_1_x': data[:, 10], 'acc_1_y': data[:, 11],
                           'acc_1_z': data[:, 12],
                           'quat_1_w': data[:, 13], 'quat_1_x': data[:, 14], 'quat_1_y': data[:, 15],
                           'quat_1_z': data[:, 16],
                           'static_2': data[:, 17], 'acc_2_x': data[:, 18], 'acc_2_y': data[:, 19],
                           'acc_2_z': data[:, 20], 'quat_2_w': data[:, 21], 'quat_2_x': data[:, 22],
                           'quat_2_y': data[:, 23], 'quat_2_z': data[:, 24]})

        return df