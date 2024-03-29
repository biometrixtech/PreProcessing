from aws_xray_sdk.core import xray_recorder
from collections import OrderedDict
import logging
import pandas as pd
import numpy as np

from ..job import Job
from config import get_mongo_collection
from .aggregate import aggregate
from .define_blocks import define_active_blocks, define_cadence_zone
from utils import format_datetime_from_epoch_time, filter_data


_logger = logging.getLogger()

_input_columns = [
    # 'obs_index',
    'epoch_time',
    'ms_elapsed',
    'active',
    'phase_lf',
    'phase_rf',
    'grf',
    'grf_lf',
    'grf_rf',
    'total_accel',
    'acc_lf_z',
    'acc_hip_z',
    'acc_rf_z',
    'euler_lf_x',
    'euler_lf_y',
    'euler_hip_x',
    'euler_hip_y',
    'euler_hip_z',
    'euler_rf_x',
    'euler_rf_y',
    'stance',
    'remove',
    'change_of_direction'
    # 'adduc_motion_covered_abs_lf', 'adduc_motion_covered_pos_lf', 'adduc_motion_covered_neg_lf',
    # 'adduc_range_of_motion_lf',
    # 'flex_motion_covered_abs_lf', 'flex_motion_covered_pos_lf', 'flex_motion_covered_neg_lf',
    # 'flex_range_of_motion_lf',
    # 'adduc_motion_covered_abs_h', 'adduc_motion_covered_pos_h', 'adduc_motion_covered_neg_h',
    # 'adduc_range_of_motion_h',
    # 'flex_motion_covered_abs_h', 'flex_motion_covered_pos_h', 'flex_motion_covered_neg_h',
    # 'flex_range_of_motion_h',
    # 'adduc_motion_covered_abs_rf', 'adduc_motion_covered_pos_rf', 'adduc_motion_covered_neg_rf',
    # 'adduc_range_of_motion_rf',
    # 'flex_motion_covered_abs_rf', 'flex_motion_covered_pos_rf', 'flex_motion_covered_neg_rf',
    # 'flex_range_of_motion_rf',
    # 'stance',
]


class AggregateblocksJob(Job):

    @xray_recorder.capture('app.jobs.aggregateblocks._run')
    def _run(self):

        data = self.datastore.get_data('scoring', columns=_input_columns)
        mongo_collection = get_mongo_collection('ACTIVEBLOCKS')
        mongo_collection.delete_many({'sessionId': self.datastore.session_id})

        user_mass = float(self.datastore.get_metadatum('user_mass', 60))
        data.grf /= 1000000.
        data['euler_hip_y_diff'] = np.ediff1d(data.euler_hip_y.values, to_begin=0)

        data.loc[data.stance == 0, 'active'] = 0
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
        # accel
        data['total_accel'] = data['total_accel'] * active_ind
        data['change_of_direction'] = data['change_of_direction'] * data['active']
        data['acc_hip_z'] = filter_data(data.acc_hip_z.values, filt='low', highcut=35)

        # get cadence zones
        define_cadence_zone(data)
        # segment data into blocks
        active_blocks = define_active_blocks(data['active'].values)
        _logger.info("Beginning iteration over {} blocks".format(len(active_blocks)))
        last_active_index = 0
        for block in active_blocks:
            if block.end_index >= len(data):
                block.end_index = len(data) - 1
            block.get_unit_blocks(data)

            block_start = str(pd.to_datetime(data['epoch_time'][block.start_index], unit='ms'))
            block_end = str(pd.to_datetime(data['epoch_time'][block.end_index], unit='ms'))
            block_data = data.loc[block.start_index:block.end_index, :]

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
            for ub in block.unit_blocks:
                if ub.end_index >= len(data):
                    ub.end_index = len(data) - 1
                unit_block_data = data.loc[ub.start_index:ub.end_index]
                ub.set_complexity_flags(unit_block_data)
                if ub.cadence_zone != 0:
                    unit_block_record = OrderedDict()
                    unit_block_start = str(pd.to_datetime(data['epoch_time'][ub.start_index], unit='ms'))
                    unit_block_end = str(pd.to_datetime(data['epoch_time'][ub.end_index], unit='ms'))
                    unit_block_record['timeStart'] = unit_block_start
                    unit_block_record['timeEnd'] = unit_block_end
                    unit_block_record['cadence_zone'] = ub.cadence_zone
                    unit_block_record['change_of_direction'] = ub.change_of_direction
                    unit_block_record['accelerating'] = ub.accelerating
                    unit_block_record['decelerating'] = ub.decelerating

                    unit_block_record = aggregate(unit_block_data, unit_block_record, user_mass, agg_level='unit_blocks')

                    unit_blocks.append(unit_block_record)
                if ub.cadence_zone > 10:
                    last_active_index = ub.end_index

            record_out['unitBlocks'] = unit_blocks

            query = {'sessionId': self.datastore.session_id, 'timeStart': block_start}
            mongo_collection.replace_one(query, record_out, upsert=True)

            _logger.info("Wrote a bock record")
        if len(active_blocks) != 0 and last_active_index != 0:
            # get end_date as last index of last non-walking unit block
            end_date = format_datetime_from_epoch_time(data['epoch_time'][last_active_index] / 1000)
            self.datastore.put_metadata({'end_date': end_date})
        else:
            self.datastore.put_metadata({'failure': "NO_ACTIVE_DATA"})
            raise Exception("No active block data")
