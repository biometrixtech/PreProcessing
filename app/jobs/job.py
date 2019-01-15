from abc import abstractmethod
import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)


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
            raise e

    @abstractmethod
    def _run(self):
        raise NotImplementedError
