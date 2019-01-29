from collections import OrderedDict
import logging
import pandas as pd
import numpy as np

from ..job import Job
from .aggregate import aggregate
from .define_blocks import define_blocks
from config import get_mongo_collection


_logger = logging.getLogger()


class Aggregateblocks1Job(Job):

    def _run(self):
        data = self.datastore.get_data('scoring')
        mongo_collection = get_mongo_collection('ACTIVEBLOCKS')

        user_mass = float(self.datastore.get_metadatum('user_mass', None))

        active_ind = np.array([k == 1 for k in data['active']])
        data['total_accel'] = data['total_accel'].fillna(value=np.nan) * active_ind
        data['control'][~active_ind] = np.nan
        data['acc_hip_z'][~active_ind] = np.nan
        data['acc_hip_z'] = np.abs(data['acc_hip_z'])
        # accel
        data['irregular_accel'] = data['total_accel'] * data['destr_multiplier']

        # segment data into blocks
        active_blocks = define_blocks(data['active'].values)
        _logger.info("Beginning iteration over {} blocks".format(len(active_blocks)))
        for block in active_blocks:
            print(block)
            block_start_index = active_blocks[block][0][0]
            block_end_index = active_blocks[block][-1][1]
            if block_end_index >= len(data):
                block_end_index = len(data) - 1
            block_start = str(pd.to_datetime(data['epoch_time'][block_start_index], unit='ms'))
            block_end = str(pd.to_datetime(data['epoch_time'][block_end_index], unit='ms'))
            block_data = data.loc[block_start_index:block_end_index, :]
            record_out = OrderedDict()
            record_out['userId'] = self.datastore.get_metadatum('user_id', None)
            record_out['eventDate'] = self.datastore.get_metadatum('event_date', None)
            record_out['userMass'] = user_mass
            record_out['teamId'] = None
            record_out['trainingGroups'] = None
            record_out['sessionId'] = self.datastore.session_id
            record_out['sessionType'] = '1'

            record_out['timeStart'] = block_start
            record_out['timeEnd'] = block_end

            record_out = aggregate(block_data, record_out)

            unit_blocks = []
            for unit_block in active_blocks[block]:
                unit_block_start_index = unit_block[0]
                unit_block_end_index = unit_block[1]
                if unit_block_end_index >= len(data):
                    unit_block_end_index = len(data) - 1
                unit_block_data = data.loc[unit_block_start_index:unit_block_end_index]
                unit_block_record = OrderedDict()
                unit_block_start = str(pd.to_datetime(data['epoch_time'][unit_block_start_index], unit='ms'))
                unit_block_end = str(pd.to_datetime(data['epoch_time'][unit_block_end_index], unit='ms'))
                unit_block_record['timeStart'] = unit_block_start
                unit_block_record['timeEnd'] = unit_block_end

                unit_block_record = aggregate(unit_block_data, unit_block_record)

                unit_blocks.append(unit_block_record)
            record_out['unitBlocks'] = unit_blocks

            query = {'sessionId': self.datastore.session_id, 'timeStart': block_start}
            mongo_collection.replace_one(query, record_out, upsert=True)

            _logger.info("Wrote a bock record")
        return active_blocks
