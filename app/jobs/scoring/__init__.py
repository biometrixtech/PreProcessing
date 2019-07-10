from __future__ import print_function
from aws_xray_sdk.core import xray_recorder
import logging
# import numpy as np

from ..job import Job
# from .control_score import control_score
# from .scoring import score

_logger = logging.getLogger()

_output_columns = [
    'obs_index',
    'time_stamp',
    'epoch_time',
    'ms_elapsed',
    # 'session_duration',
    'active',
    # 'loading_lf',
    # 'loading_rf',
    'phase_lf',
    'phase_rf',
    # 'impact_phase_lf',
    # 'impact_phase_rf',
    'grf',
    'grf_lf',
    'grf_rf',
    # 'const_grf',
    # 'dest_grf',
    # 'destr_multiplier',
    # 'session_grf_elapsed',
    # 'symmetry',
    # 'symmetry_l',
    # 'symmetry_r',
    # 'hip_symmetry',
    # 'hip_symmetry_l',
    # 'hip_symmetry_r',
    # 'ankle_symmetry',
    # 'ankle_symmetry_l',
    # 'ankle_symmetry_r',
    # 'consistency',
    # 'hip_consistency',
    # 'ankle_consistency',
    # 'consistency_lf',
    # 'consistency_rf',
    # 'control',
    # 'hip_control',
    # 'ankle_control',
    # 'control_lf',
    # 'control_rf',
    # 'contra_hip_drop_lf',
    # 'contra_hip_drop_rf',
    # 'ankle_rot_lf',
    # 'ankle_rot_rf',
    # 'foot_position_lf',
    # 'foot_position_rf',
    # 'land_pattern_lf',
    # 'land_pattern_rf',
    # 'land_time',
    # 'rate_force_absorption_lf',
    # 'rate_force_absorption_rf',
    # 'rate_force_production_lf',
    # 'rate_force_production_rf',
    'total_accel',
    'stance',
    # 'plane',
    # 'rot',
    # 'lat',
    # 'vert',
    # 'horz',
    'adduc_motion_covered_abs_lf', 'adduc_motion_covered_pos_lf', 'adduc_motion_covered_neg_lf',
    'adduc_range_of_motion_lf',
    'flex_motion_covered_abs_lf', 'flex_motion_covered_pos_lf', 'flex_motion_covered_neg_lf',
    'flex_range_of_motion_lf',
    'contact_duration_lf',
    'adduc_motion_covered_abs_h', 'adduc_motion_covered_pos_h', 'adduc_motion_covered_neg_h',
    'adduc_range_of_motion_h',
    'flex_motion_covered_abs_h', 'flex_motion_covered_pos_h', 'flex_motion_covered_neg_h',
    'flex_range_of_motion_h',
    'contact_duration_h',
    'adduc_motion_covered_abs_rf', 'adduc_motion_covered_pos_rf', 'adduc_motion_covered_neg_rf',
    'adduc_range_of_motion_rf',
    'flex_motion_covered_abs_rf', 'flex_motion_covered_pos_rf', 'flex_motion_covered_neg_rf',
    'flex_range_of_motion_rf',
    'contact_duration_rf']


class ScoringJob(Job):

    @xray_recorder.capture('app.jobs.scoring._run')
    def _run(self):

        data = self.datastore.get_data(('sessionprocess', '*'))

        if data.shape[0] < 2000:
            _logger.error("Current data isn't long enough for scoring!")
            raise Exception("Insufficient data, need 30000 rows, only got {}".format(data.shape[0]))

        # CONTROL SCORE
        # (
        #     data['control'],
        #     data['hip_control'],
        #     data['ankle_control'],
        #     data['control_lf'],
        #     data['control_rf']
        # ) = control_score(data.euler_lf_x, data.euler_hip_x, data.euler_rf_x, data.phase_lf, data.phase_rf)
        # _logger.info('DONE WITH CONTROL SCORES!')

        grf_scale = 1000000
        # data = score(data, grf_scale)
        # _logger.info("DONE WITH SCORING!")

        accel_scale = 100000
        data['grf'] = data.grf / grf_scale
        data['total_accel'] = data.total_accel * data.ms_elapsed / accel_scale

        # Round the data to 6th decimal point
        data = data.round(6)

        # Add nans for future variables
        # data['symmetry_l'] = np.nan
        # data['symmetry_r'] = np.nan
        # data['hip_symmetry_l'] = np.nan
        # data['hip_symmetry_r'] = np.nan
        # data['ankle_symmetry_l'] = np.nan
        # data['ankle_symmetry_r'] = np.nan

        # TODO replace computing boundaries for twoMin by active blocks

        # Output data
        self.datastore.put_data('scoring', data, columns=_output_columns)
        _logger.info("DONE WRITING OUTPUT FILE")
