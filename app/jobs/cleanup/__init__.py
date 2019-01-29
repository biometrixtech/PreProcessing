from aws_xray_sdk.core import xray_recorder
import logging

from ..job import Job

_logger = logging.getLogger()


class CleanupJob(Job):

    @xray_recorder.capture('app.jobs.cleanup._run')
    def _run(self):
        self.datastore.delete_data()
