import logging

from ..job import Job

_logger = logging.getLogger()


class CleanupJob(Job):

    def _run(self):
        self.datastore.delete_data()
