from abc import ABC

from ..job import Job


class UnitBlockJob(Job, ABC):
    def __init__(self, datastore, unit_blocks):
        super().__init__(datastore)
        self._user_id = self.datastore.get_metadatum('user_id')
        self._event_date = self.datastore.get_metadatum('event_date')
        self._unit_blocks = unit_blocks
