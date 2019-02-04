import pandas as pd

from ..job import Job
from models.fatigue_event import FatigueEvent
from models.session_fatigue import SessionFatigue


class FatigueProcessorJob(Job):

    def __init__(self, datastore, complexity_matrix_single_leg, complexity_matrix_double_leg):
        super().__init__(datastore)
        self._complexity_matrix_single_leg = complexity_matrix_single_leg
        self._complexity_matrix_double_leg = complexity_matrix_double_leg

    def _run(self):
        fatigue_events = self._get_fatigue_events()
        self._session_fatigue = SessionFatigue(fatigue_events)
        self._write_fatigue_cross_tab()
        self._write_fatigue_active_block_cross_tab()

    def _get_fatigue_events(self):

        fatigue_events = []

        for stance, complexity_matrix in [('Single Leg', self._complexity_matrix_single_leg), ('Double Leg', self._complexity_matrix_double_leg)]:
            for keys, mcsl in complexity_matrix.items():
                differs = mcsl.get_decay_parameters()
                for difs in differs:
                    ab = FatigueEvent(mcsl.cma_level, mcsl.grf_level)
                    ab.active_block_id = difs.active_block_id
                    ab.complexity_level = difs.complexity_level
                    ab.attribute_name = difs.attribute_name
                    ab.attribute_label = difs.label
                    ab.orientation = difs.orientation
                    ab.cumulative_end_time = difs.end_time
                    ab.z_score = difs.z_score
                    ab.raw_value = difs.raw_value
                    ab.stance = "Single Leg"
                    ab.time_block = str(difs.time_block)

                    fatigue_events.append(ab)

        return fatigue_events

    def _write_fatigue_cross_tab(self):
        fatigue_frame = pd.DataFrame()
        for f in self._session_fatigue.cma_grf_crosstab():
            ab = pd.DataFrame({
                # 'stance': [f.stance],
                'grf_level': [f.grf_level],
                'cma_level': [f.cma_level],
                'adduc_hip_neg_left_dec': [f.adduc_neg_hip_left_dec],
                'adduc_hip_neg_right_dec': [f.adduc_neg_hip_right_dec],
                'adduc_hip_neg_left_inc': [f.adduc_neg_hip_left_inc],
                'adduc_hip_neg_right_inc': [f.adduc_neg_hip_right_inc],
                'adduc_hip_pos_left_dec': [f.adduc_pos_hip_left_dec],
                'adduc_hip_pos_right_dec': [f.adduc_pos_hip_right_dec],
                'adduc_hip_pos_left_inc': [f.adduc_pos_hip_left_inc],
                'adduc_hip_pos_right_inc': [f.adduc_pos_hip_right_inc],

                'flex_hip_neg_left_dec': [f.flex_neg_hip_left_dec],
                'flex_hip_neg_right_dec': [f.flex_neg_hip_right_dec],
                'flex_hip_neg_left_inc': [f.flex_neg_hip_left_inc],
                'flex_hip_neg_right_inc': [f.flex_neg_hip_right_inc],
                'flex_hip_pos_left_dec': [f.flex_pos_hip_left_dec],
                'flex_hip_pos_right_dec': [f.flex_pos_hip_right_dec],
                'flex_hip_pos_left_inc': [f.flex_pos_hip_left_inc],
                'flex_hip_pos_right_inc': [f.flex_pos_hip_right_inc],

                'adduc_rom_hip_left_dec': [f.adduc_rom_hip_left_dec],
                'adduc_rom_hip_right_dec': [f.adduc_rom_hip_right_dec],
                'adduc_rom_hip_left_inc': [f.adduc_rom_hip_left_inc],
                'adduc_rom_hip_right_inc': [f.adduc_rom_hip_right_inc],
                'flex_rom_hip_left_dec': [f.flex_rom_hip_left_dec],
                'flex_rom_hip_right_dec': [f.flex_rom_hip_right_dec],
                'flex_rom_hip_left_inc': [f.flex_rom_hip_left_inc],
                'flex_rom_hip_right_inc': [f.flex_rom_hip_right_inc],

            }, index=[f.stance])
            fatigue_frame = fatigue_frame.append(ab)

        if fatigue_frame.shape[0] > 0:
            self.datastore.put_data('fatiguextab', fatigue_frame)
            self.datastore.copy_to_s3('fatiguextab', 'advanced-stats', '_'.join([self.event_date, self.user_id]) + "/fatigue_xtab.csv")

    def _write_fatigue_active_block_cross_tab(self):
        fatigue_frame = pd.DataFrame()
        for f in self._session_fatigue.active_block_crosstab():
            ab = pd.DataFrame({
                # 'stance': [f.stance],
                'cumulative_end_time': [f.cumulative_end_time],
                'time_block': [f.time_block],
                'adduc_hip_neg_left_dec': [f.adduc_neg_hip_left_dec],
                'adduc_hip_neg_right_dec': [f.adduc_neg_hip_right_dec],
                'adduc_hip_neg_left_inc': [f.adduc_neg_hip_left_inc],
                'adduc_hip_neg_right_inc': [f.adduc_neg_hip_right_inc],
                'adduc_hip_pos_left_dec': [f.adduc_pos_hip_left_dec],
                'adduc_hip_pos_right_dec': [f.adduc_pos_hip_right_dec],
                'adduc_hip_pos_left_inc': [f.adduc_pos_hip_left_inc],
                'adduc_hip_pos_right_inc': [f.adduc_pos_hip_right_inc],

                'flex_hip_neg_left_dec': [f.flex_neg_hip_left_dec],
                'flex_hip_neg_right_dec': [f.flex_neg_hip_right_dec],
                'flex_hip_neg_left_inc': [f.flex_neg_hip_left_inc],
                'flex_hip_neg_right_inc': [f.flex_neg_hip_right_inc],
                'flex_hip_pos_left_dec': [f.flex_pos_hip_left_dec],
                'flex_hip_pos_right_dec': [f.flex_pos_hip_right_dec],
                'flex_hip_pos_left_inc': [f.flex_pos_hip_left_inc],
                'flex_hip_pos_right_inc': [f.flex_pos_hip_right_inc],

                'adduc_rom_hip_left_dec': [f.adduc_rom_hip_left_dec],
                'adduc_rom_hip_right_dec': [f.adduc_rom_hip_right_dec],
                'adduc_rom_hip_left_inc': [f.adduc_rom_hip_left_inc],
                'adduc_rom_hip_right_inc': [f.adduc_rom_hip_right_inc],
                'flex_rom_hip_left_dec': [f.flex_rom_hip_left_dec],
                'flex_rom_hip_right_dec': [f.flex_rom_hip_right_dec],
                'flex_rom_hip_left_inc': [f.flex_rom_hip_left_inc],
                'flex_rom_hip_right_inc': [f.flex_rom_hip_right_inc],

            }, index=[f.active_block])
            fatigue_frame = fatigue_frame.append(ab)

        if fatigue_frame.shape[0] > 0:
            self.datastore.put_data('fatigueabxtab', fatigue_frame)
            self.datastore.copy_to_s3('fatigueabxtab', 'advanced-stats', '_'.join([self.event_date, self.user_id]) + "/fatigue_ab_xtab.csv")

