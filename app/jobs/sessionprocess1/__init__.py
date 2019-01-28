import boto3
import logging

from ..job import Job

_logger = logging.getLogger(__name__)
_s3_client = boto3.client('s3')


class Sessionprocess1Job(Job):

    def _run(self):

        _logger.info("STARTED PROCESSING!")

        _logger.info("LOADING DATA")
        part_number = 0  # TODO chunking
        sdata = self.datastore.get_data(('transformandplacement', part_number))
        _logger.info("DATA LOADED!")

        if len(sdata) == 0:
            raise Exception('Sensor data is empty!')
 
        output_data_batch = run_session(sdata)

        # Output data
        output_data_batch = output_data_batch.replace('None', '')
        output_data_batch = output_data_batch.round(5)
        self.datastore.put_data(('sessionprocess1', part_number), output_data_batch)

        _logger.info('Outcome: Success!')
