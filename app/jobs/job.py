from abc import abstractmethod
from aws_xray_sdk.core import xray_recorder
import boto3
import datetime
import logging
import os


_logger = logging.getLogger(__name__)
_cloudwatch_client = boto3.client('cloudwatch')


class Job:
    def __init__(self, datastore):
        self._datastore = datastore

    @property
    def datastore(self):
        return self._datastore

    @property
    def name(self):
        return self.__class__.__name__.lower().replace('job', '')

    def run(self):
        _logger.info('Running job {} on session {}'.format(self.name, self.datastore.session_id))
        try:
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
