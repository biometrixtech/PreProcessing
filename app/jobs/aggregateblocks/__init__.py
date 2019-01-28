from __future__ import print_function
from collections import OrderedDict
import logging
import pandas as pd
import numpy as np

from ..job import Job
from config import get_mongo_collection
from .aggregate import aggregate
from .define_blocks import define_blocks


_logger = logging.getLogger()

_input_columns = [
    'obs_index',
    'epoch_time',
    'ms_elapsed',
    'active',
    'phase_lf',
    'phase_rf',
    'grf',
    'grf_lf',
    'grf_rf',
    'const_grf',
    'dest_grf',
    'destr_multiplier',
    'symmetry',
    'hip_symmetry',
    'ankle_symmetry',
    'consistency',
    'hip_consistency',
    'ankle_consistency',
    'consistency_lf',
    'consistency_rf',
    'control',
    'hip_control',
    'ankle_control',
    'control_lf',
    'control_rf',
    'total_accel',
    'adduc_motion_covered_abs_lf', 'adduc_motion_covered_pos_lf', 'adduc_motion_covered_neg_lf',
    'adduc_range_of_motion_lf',
    'flex_motion_covered_abs_lf', 'flex_motion_covered_pos_lf', 'flex_motion_covered_neg_lf',
    'flex_range_of_motion_lf',
    'adduc_motion_covered_abs_h', 'adduc_motion_covered_pos_h', 'adduc_motion_covered_neg_h',
    'adduc_range_of_motion_h',
    'flex_motion_covered_abs_h', 'flex_motion_covered_pos_h', 'flex_motion_covered_neg_h',
    'flex_range_of_motion_h',
    'adduc_motion_covered_abs_rf', 'adduc_motion_covered_pos_rf', 'adduc_motion_covered_neg_rf',
    'adduc_range_of_motion_rf',
    'flex_motion_covered_abs_rf', 'flex_motion_covered_pos_rf', 'flex_motion_covered_neg_rf',
    'flex_range_of_motion_rf',
    'stance',
]


class AggregateBlocksJob(Job):

    def _run(self):

        data = self.datastore.get_data(('scoring', '*'))
        mongo_collection = get_mongo_collection('ACTIVEBLOCKS')

        # team_id = input_data.get('TeamId', None)
        # training_group_id = input_data.get('TrainingGroupIds', None)
        # user_id = input_data.get('UserId', None)
        # session_event_id = input_data.get('SessionId', None)
        user_mass = self.datastore.get_metadatum('user_mass', None)
        # event_date = input_data.get('EventDate')

        data.active[data.stance == 0] = 0
        active_ind = np.array([k == 1 for k in data['active']])
        total_ind = np.array([k not in [0, 1] for k in data['stance']]) * active_ind
        data['total_ind'] = total_ind
        lf_ind = np.array([k in [0, 2, 3] for k in data['phase_lf']]) * active_ind
        rf_ind = np.array([k in [0, 2, 3] for k in data['phase_rf']]) * active_ind
        lf_ground = lf_ind * ~rf_ind  # only lf in ground
        rf_ground = ~lf_ind * rf_ind  # only rf in ground

        data['total_grf'] = data['grf'].fillna(value=np.nan) * total_ind
        data['lf_grf'] = data['grf'].fillna(value=np.nan) * lf_ind
        data['rf_grf'] = data['grf'].fillna(value=np.nan) * rf_ind
        data['lf_only_grf'] = data['grf'].fillna(value=np.nan) * lf_ground
        data['rf_only_grf'] = data['grf'].fillna(value=np.nan) * rf_ground

        data['const_grf'] = data['const_grf'].fillna(value=np.nan) * total_ind
        data['dest_grf'] = data['dest_grf'].fillna(value=np.nan) * total_ind
        data['perc_optimal'] = pd.DataFrame(data['const_grf'] / (data['const_grf'] + data['dest_grf']))

        # accel
        data['total_accel'] = data['total_accel'] * active_ind
        data['irregular_accel'] = data['total_accel'] * data['destr_multiplier']

        # scores
        data['symmetry'] = data['symmetry'] * total_ind
        data['hip_symmetry'] = data['hip_symmetry'] * total_ind
        data['ankle_symmetry'] = data['ankle_symmetry'] * total_ind
        data['consistency'] = data['consistency'] * total_ind
        data['hip_consistency'] = data['hip_consistency'] * total_ind
        data['ankle_consistency'] = data['ankle_consistency'] * total_ind
        data['consistency_lf'] = data['consistency_lf'] * lf_ind
        data['consistency_rf'] = data['consistency_rf'] * rf_ind
        data['control'] = data['control'] * total_ind
        data['hip_control'] = data['hip_control'] * total_ind
        data['ankle_control'] = data['ankle_control'] * total_ind
        data['control_lf'] = data['control_lf'] * lf_ind
        data['control_rf'] = data['control_rf'] * rf_ind

        # segment data into blocks
        active_blocks = define_blocks(data['active'].values)
        print("Beginning iteration over {} blocks".format(len(active_blocks)))
        for block in active_blocks:
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

            record_out = aggregate(block_data, record_out, user_mass, agg_level='active_blocks')

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

                unit_block_record = aggregate(unit_block_data, unit_block_record, user_mass, agg_level='unit_blocks')

                unit_blocks.append(unit_block_record)

            record_out['unitBlocks'] = unit_blocks

            query = {'sessionId': self.datastore.session_id, 'timeStart': block_start}
            mongo_collection.replace_one(query, record_out, upsert=True)

            _logger.info("Wrote a bock record")
