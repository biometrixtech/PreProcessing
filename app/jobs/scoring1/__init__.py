from __future__ import print_function
import logging

from ..job import Job
from .control_score import control_score
from .scoring import score

_logger = logging.getLogger()

_output_columns = [
    'epoch_time',
    'time_stamp',
    'ms_elapsed',
    'session_duration',
    'active',
    'control',
    'total_accel',
    'destr_multiplier',
    'acc_hip_z'
]


class Scoring1Job(Job):

    def _run(self):

        data = self.datastore.get_data(('sessionprocess1', '*'))

        if data.shape[0] < 2000:
            _logger.error("Current data isn't long enough for scoring!")
            raise Exception("Insufficient data, need 30000 rows, only got {}".format(data.shape[0]))

        # CONTROL SCORE
        (
            data['control']
        ) = control_score(data.eul_hip_x)

        _logger.info('DONE WITH CONTROL SCORES!')

        # SCORING, Destructive/Constructive Multiplier and Duration
        data = score(data)
        _logger.info("DONE WITH SCORING!")

        accel_scale = 100000
        data['total_accel'] = data.total_accel * data.ms_elapsed / accel_scale
        # Round the data to 6th decimal point
        data = data.round(6)

        # TODO replace computing boundaries for twoMin by active blocks

        # Output data
        self.datastore.put_data('scoring1', data, columns=_output_columns)
        _logger.info("DONE WRITING OUTPUT FILE")
