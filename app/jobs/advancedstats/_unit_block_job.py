from abc import ABC

from ..job import Job


class UnitBlockJob(Job, ABC):
    def __init__(self, datastore, unit_blocks):
        super().__init__(datastore)
        self._unit_blocks = unit_blocks
