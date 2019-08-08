from scipy import stats
import pandas as pd
import statistics
from math import ceil

from ._unit_block_job import UnitBlockJob
from models.categorization_variable import CategorizationVariable
from models.loading_asymmetry import LoadingAsymmetry
from models.loading_asymmetry_summary import LoadingAsymmetrySummary
from models.movement_asymmetry import MovementAsymmetry
from models.unit_block import UnitBlock
from utils import parse_datetime


class AsymmetryDistribution(object):
    def __init__(self):
        self.attribute_label = ""
        self.r_value = 0.0
        self.left_median = 0.0
        self.right_median =0.0
        self.left_min = 0.0
        self.right_min = 0.0
        self.left_max = 0.0
        self.right_max = 0.0
        self.left_q1_sum = 0.0
        self.left_q2_sum = 0.0
        self.left_q3_sum = 0.0
        self.left_q4_sum = 0.0
        self.right_q1_sum = 0.0
        self.right_q2_sum = 0.0
        self.right_q3_sum = 0.0
        self.right_q4_sum = 0.0
        self.time_block = 0.0
        self.start_time = None
        self.end_time = None


class AsymmetryProcessorJob(UnitBlockJob):

    def __init__(self, datastore, unit_blocks, complexity_matrix_single_leg, complexity_matrix_double_leg):
        super().__init__(datastore, unit_blocks)
        self._complexity_matrix_single_leg = complexity_matrix_single_leg
        self._complexity_matrix_double_leg = complexity_matrix_double_leg

    def _run(self):
        session_asymmetry_summaries = self._get_session_asymmetry_summaries()
        self._write_session_asymmetry_summaries(session_asymmetry_summaries)

        movement_events = self._get_movement_asymmetries()
        loading_events = self._get_loading_asymmetries()
        self._write_loading_movement_asymmetry(loading_events, movement_events)

    def _get_session_asymmetry_summaries(self):
        # relative magnitude
        var_list = [
            CategorizationVariable("peak_grf_perc_diff_lf", 0, 5, 5, 10, 10, 100, False, 1),
            CategorizationVariable("peak_grf_perc_diff_rf", 0, 5, 5, 10, 10, 100, False, 2),
            CategorizationVariable("gct_perc_diff_lf", 0, 5, 5, 10, 10, 100, False, 3),
            CategorizationVariable("gct_perc_diff_rf", 0, 5, 5, 10, 10, 100, False, 4),
            CategorizationVariable("peak_grf_gct_left_over", 0, 2.5, 2.5, 5, 5, 100, False, 5),
            CategorizationVariable("peak_grf_gct_left_under", 0, 2.5, 2.5, 5, 5, 10, False, 6),
            CategorizationVariable("peak_grf_gct_right_over", 0, 2.5, 2.5, 5, 5, 100, False, 7),
            CategorizationVariable("peak_grf_gct_right_under", 0, 2.5, 2.5, 5, 5, 10, False, 8)
        ]

        return self._get_variable_asymmetry_summaries(var_list)

    def _get_loading_asymmetries(self):
        events = []
        for stance, complexity_matrix in [('Single Leg', self._complexity_matrix_single_leg), ('Double Leg', self._complexity_matrix_double_leg)]:
            for keys, mcsl in complexity_matrix.items():
                events.append(self._get_loading_asymmetry(
                    "total_grf",
                    mcsl,
                    mcsl.complexity_level,
                    mcsl.cma_level,
                    mcsl.grf_level,
                    stance))

        return events

    @staticmethod
    def _get_loading_asymmetry(attribute, complexity_matrix_cell, complexity_level, cma_level, grf_level, stance):

        asym = LoadingAsymmetry(complexity_level, cma_level, grf_level, stance)
        asym.variable = attribute
        asym.total_left_sum = complexity_matrix_cell.get_steps_sum(attribute, complexity_matrix_cell.left_steps)
        asym.total_right_sum = complexity_matrix_cell.get_steps_sum(attribute, complexity_matrix_cell.right_steps)
        asym.total_left_right_sum = asym.total_left_sum + asym.total_right_sum

        if len(complexity_matrix_cell.left_steps) == 0 or len(complexity_matrix_cell.right_steps) == 0:
            asym.training_asymmetry = asym.total_left_sum - asym.total_right_sum
        else:
            asym.kinematic_asymmetry = asym.total_left_sum - asym.total_right_sum
        asym.total_asymmetry = asym.training_asymmetry + asym.kinematic_asymmetry
        if asym.total_left_right_sum > 0:
            asym.total_percent_asymmetry = (asym.total_asymmetry / asym.total_left_right_sum) * 100

        asym.left_step_count = complexity_matrix_cell.left_step_count
        asym.right_step_count = complexity_matrix_cell.right_step_count
        asym.total_steps = asym.left_step_count + asym.right_step_count
        asym.step_asymmetry = asym.left_step_count - asym.right_step_count
        if asym.total_steps > 0:
            asym.step_count_percent_asymmetry = (asym.step_asymmetry / float(asym.total_steps)) * 100

        asym.ground_contact_time_left = complexity_matrix_cell.left_duration
        asym.ground_contact_time_right = complexity_matrix_cell.right_duration
        asym.total_ground_contact_time = asym.ground_contact_time_left + asym.ground_contact_time_right
        asym.ground_contact_time_asymmetry = asym.ground_contact_time_left - asym.ground_contact_time_right
        if asym.total_ground_contact_time > 0:
            asym.ground_contact_time_percent_asymmetry = (asym.ground_contact_time_asymmetry / float(
                asym.total_ground_contact_time)) * 100

        asym.left_avg_accumulated_grf_sec = complexity_matrix_cell.left_avg_accumulated_grf_sec
        asym.right_avg_accumulated_grf_sec = complexity_matrix_cell.right_avg_accumulated_grf_sec
        asym.accumulated_grf_sec_asymmetry = asym.left_avg_accumulated_grf_sec - asym.right_avg_accumulated_grf_sec
        if asym.right_avg_accumulated_grf_sec > 0:
            asym.accumulated_grf_sec_percent_asymmetry = (asym.left_avg_accumulated_grf_sec /
                                                          float(asym.right_avg_accumulated_grf_sec)) * 100

        return asym

    def _get_movement_asymmetries(self):

        asymm_events = []

        for stance, complexity_matrix in [('Single', self._complexity_matrix_single_leg), ('Double', self._complexity_matrix_double_leg)]:
            for keys, mcsl in complexity_matrix.items():
                events = self._get_movement_asymmetry(
                    mcsl.complexity_level,
                    mcsl.cma_level,
                    mcsl.grf_level,
                    stance,
                    mcsl.left_steps,
                    mcsl.right_steps)

                asymm_events.extend(events)

        return asymm_events

    def _get_movement_asymmetry(self, complexity_level, cma_level, grf_level, stance, left_steps, right_steps):

        unit_block_list_lf = {x.unit_block_number for x in left_steps}
        unit_block_list_rf = {x.unit_block_number for x in right_steps}
        unit_block_list = list(set(unit_block_list_lf).union(unit_block_list_rf))
        unit_block_list.sort()

        # event.adduc_rom_hip = self._get_steps_f_test("adduc_ROM_hip", left_steps, right_steps)
        # event.adduc_motion_covered_tot_hip = self._get_steps_f_test("adduc_motion_covered_total_hip", left_steps, right_steps)
        # event.adduc_motion_covered_pos_hip = self._get_steps_f_test("adduc_motion_covered_pos_hip", left_steps, right_steps)
        # event.adduc_motion_covered_neg_hip = self._get_steps_f_test("adduc_motion_covered_neg_hip", left_steps, right_steps)
        #
        # event.flex_rom_hip = self._get_steps_f_test("flex_ROM_hip", left_steps, right_steps)
        # event.flex_motion_covered_tot_hip = self._get_steps_f_test("flex_motion_covered_total_hip", left_steps, right_steps)
        # event.flex_motion_covered_pos_hip = self._get_steps_f_test("flex_motion_covered_pos_hip", left_steps, right_steps)
        # event.flex_motion_covered_neg_hip = self._get_steps_f_test("flex_motion_covered_neg_hip", left_steps, right_steps)
        unit_blocks = self._unit_blocks

        events = []

        time_block = 0

        for unit_block_number in unit_block_list:

            l_unit_block_steps = list(x for x in left_steps if x.unit_block_number == unit_block_number)
            r_unit_block_steps = list(x for x in right_steps if x.unit_block_number == unit_block_number)

            all_steps = []
            all_steps.extend(l_unit_block_steps)
            all_steps.extend(r_unit_block_steps)

            start_time = None
            end_time = None
            intervals = 0
            seconds = 30

            cumulative_time = list(x.cumulative_end_time for x in all_steps)

            if len(cumulative_time) > 0:
                start_time = min(cumulative_time)
                end_time = max(cumulative_time)
                seconds_diff = end_time - start_time
                intervals = ceil(seconds_diff / float(seconds))

            for i in range(0, intervals):
                event = MovementAsymmetry(complexity_level, cma_level, grf_level, stance)
                l_step_blocks = list(x for x in l_unit_block_steps if
                                     start_time + (i * seconds) <= x.cumulative_end_time <= start_time + (
                                                 (i + 1) * seconds))
                r_step_blocks = list(x for x in r_unit_block_steps if
                                     start_time + (i * seconds) <= x.cumulative_end_time <= start_time + (
                                                 (i + 1) * seconds))
                time_block += 1
                event.anterior_pelvic_tilt_range = self._get_steps_f_test("anterior_pelvic_tilt_range", l_step_blocks,
                                                                          r_step_blocks, time_block)
                if event.anterior_pelvic_tilt_range is None:
                    event.anterior_pelvic_tilt_range = AsymmetryDistribution()
                    event.anterior_pelvic_tilt_range.start_time = start_time + (i * seconds)
                    event.anterior_pelvic_tilt_range.end_time = start_time + ((i + 1) * seconds)
                    event.anterior_pelvic_tilt_range.attribute_label = "anterior_pelvic_tilt_range"
                    event.anterior_pelvic_tilt_range.time_block = time_block
                event.anterior_pelvic_tilt_rate = self._get_steps_f_test("anterior_pelvic_tilt_rate", l_step_blocks,
                                                                         r_step_blocks, time_block)
                if event.anterior_pelvic_tilt_rate is None:
                    event.anterior_pelvic_tilt_rate = AsymmetryDistribution()
                    event.anterior_pelvic_tilt_rate.start_time = start_time + (i * seconds)
                    event.anterior_pelvic_tilt_rate.end_time = start_time + ((i + 1) * seconds)
                    event.anterior_pelvic_tilt_rate.attribute_label = "anterior_pelvic_tilt_rate"
                    event.anterior_pelvic_tilt_rate.time_block = time_block
                events.append(event)

        # outlier_list.extend(self.get_decay_outliers("anteriorPelvicTiltRangeLF", "anteriorPelvicTiltRangeLF", "Left", active_block_list, self.left_steps))
        # outlier_list.extend(self.get_decay_outliers("anteriorPelvicTiltRateLF", "anteriorPelvicTiltRateLF", "Left", active_block_list, self.left_steps))
        # outlier_list.extend(self.get_decay_outliers("anteriorPelvicTiltRangeRF", "anteriorPelvicTiltRangeRF", "Right", active_block_list, self.right_steps))
        # outlier_list.extend(self.get_decay_outliers("anteriorPelvicTiltRateRF", "anteriorPelvicTiltRateRF", "Right", active_block_list, self.right_steps))

        return events

    @staticmethod
    def _get_steps_f_test(attribute, step_list_x, step_list_y, time_block):
        value_list_x = []
        value_list_y = []
        for item in step_list_x:
            if getattr(item, attribute) is not None:
                value_list_x.append(getattr(item, attribute))
        for item in step_list_y:
            if getattr(item, attribute) is not None:
                value_list_y.append(getattr(item, attribute))
        if len(value_list_x) == 0 or len(value_list_y) == 0:
            return None
        else:
            try:
                value_list_x.sort()
                value_list_y.sort()
                r, p = stats.kruskal(value_list_x, value_list_y)
                if p <= .05:
                    all_values = []
                    all_values.extend(step_list_x)
                    all_values.extend(step_list_y)

                    times = list(x.cumulative_end_time for x in all_values)
                    start_time = min(times)
                    end_time = max(times)

                    dist = AsymmetryDistribution()
                    dist.time_block = time_block
                    dist.start_time = start_time
                    dist.attribute_label = attribute
                    dist.end_time = end_time
                    dist.r_value = r
                    dist.left_median = statistics.median(value_list_x)
                    dist.right_median = statistics.median(value_list_y)

                    dist.left_min = min(value_list_x)
                    dist.left_max = max(value_list_x)
                    dist.right_min = min(value_list_y)
                    dist.right_max = max(value_list_y)

                    left_q = (dist.left_max - dist.left_min) / float(4)
                    right_q = (dist.right_max - dist.right_min) / float(4)

                    for i in range(0, 4):
                        if i == 0:
                            dist.left_q1_sum = sum(x for x in value_list_x if dist.left_min + (i * left_q) <= x <= dist.left_min + ((i + 1) * left_q))
                            dist.right_q1_sum = sum(y for y in value_list_y if
                                                   dist.right_min + (i * right_q) <= y <= dist.right_min + ((i + 1) * right_q))
                        elif i == 1:
                            dist.left_q2_sum = sum(x for x in value_list_x if
                                                   dist.left_min + (i * left_q) <= x <=  dist.left_min + ((i + 1) * left_q))
                            dist.right_q2_sum = sum(y for y in value_list_y if
                                                    dist.right_min + (i * right_q) <= y <= dist.right_min + (
                                                                (i + 1) * right_q))
                        elif i == 2:
                            dist.left_q3_sum = sum(x for x in value_list_x if
                                                   dist.left_min + (i * left_q) <= x <=  dist.left_min + ((i + 1) * left_q))
                            dist.right_q3_sum = sum(y for y in value_list_y if
                                                    dist.right_min + (i * right_q) <= y <= dist.right_min + (
                                                                (i + 1) * right_q))
                        elif i == 3:
                            dist.left_q4_sum = sum(x for x in value_list_x if
                                                   dist.left_min + (i * left_q) <= x <=  dist.left_min + ((i + 1) * left_q))
                            dist.right_q4_sum = sum(y for y in value_list_y if
                                                    dist.right_min + (i * right_q) <= y <= dist.right_min + (
                                                                (i + 1) * right_q))

                    return dist
                else:
                    return None
            except ValueError:
                return None

    def _get_variable_asymmetry_summaries(self, variable_list):

        cumulative_end_time = 0

        variable_matrix = {}

        for cat_variable in variable_list:
            variable_matrix[cat_variable.name] = LoadingAsymmetrySummary()
            variable_matrix[cat_variable.name].sort_order = cat_variable.sort_order

        if len(self._unit_blocks) > 0:

            session_time_start = parse_datetime(self._unit_blocks[0].get('unitBlocks')[0].get('timeStart'))

            for ub in self._unit_blocks:
                if len(ub) > 0:

                    unit_bock_count = len(ub.get('unitBlocks'))

                    for n in range(0, unit_bock_count):
                        ub_data = ub.get('unitBlocks')[n]
                        ub_rec = UnitBlock(ub_data)

                        time_end = parse_datetime(ub.get('unitBlocks')[n].get('timeEnd'))
                        cumulative_end_time = (time_end - session_time_start).seconds

                        for variable_name, summary in variable_matrix.items():
                            variable_matrix[variable_name] = self._calc_loading_asymmetry_summary(summary, variable_name, variable_list, ub_rec)

        # do percentage calcs
        for key, asymmetry_summary in variable_matrix.items():
            asymmetry_summary.total_session_time = cumulative_end_time  # not additive
            asymmetry_summary.red_grf_percent = (asymmetry_summary.red_grf / asymmetry_summary.total_grf) * 100
            asymmetry_summary.red_cma_percent = (asymmetry_summary.red_cma / asymmetry_summary.total_cma) * 100
            asymmetry_summary.red_time_percent = (asymmetry_summary.red_time / asymmetry_summary.total_time) * 100
            asymmetry_summary.yellow_grf_percent = (asymmetry_summary.yellow_grf / asymmetry_summary.total_grf) * 100
            asymmetry_summary.yellow_cma_percent = (asymmetry_summary.yellow_cma / asymmetry_summary.total_cma) * 100
            asymmetry_summary.yellow_time_percent = (asymmetry_summary.yellow_time / asymmetry_summary.total_time) * 100
            asymmetry_summary.green_grf_percent = (asymmetry_summary.green_grf / asymmetry_summary.total_grf) * 100
            asymmetry_summary.green_cma_percent = (asymmetry_summary.green_cma / asymmetry_summary.total_cma) * 100
            asymmetry_summary.green_time_percent = (asymmetry_summary.green_time / asymmetry_summary.total_time) * 100

        return variable_matrix

    @staticmethod
    def _calc_loading_asymmetry_summary(summary, variable, variable_list, unit_block_data):

        cat_variable = None

        for v in range(0, len(variable_list)):
            if variable_list[v].name == variable:
                cat_variable = variable_list[v]

        variable_value = getattr(unit_block_data, cat_variable.name)

        summary.variable_name = cat_variable.name

        if variable_value is not None:
            if not cat_variable.invereted:
                if variable_value > cat_variable.yellow_high:
                    summary.red_time += unit_block_data.duration
                    summary.red_grf += unit_block_data.total_grf
                    summary.red_cma += unit_block_data.total_accel
                if cat_variable.green_high < variable_value <= cat_variable.yellow_high:
                    summary.yellow_time += unit_block_data.duration
                    summary.yellow_grf += unit_block_data.total_grf
                    summary.yellow_cma += unit_block_data.total_accel
                if cat_variable.green_low <= variable_value <= cat_variable.green_high:
                    summary.green_time += unit_block_data.duration
                    summary.green_grf += unit_block_data.total_grf
                    summary.green_cma += unit_block_data.total_accel
            else:
                if variable_value > cat_variable.yellow_high:
                    summary.green_time += unit_block_data.duration
                    summary.green_grf += unit_block_data.total_grf
                    summary.green_cma += unit_block_data.total_accel
                if cat_variable.red_high < variable_value <= cat_variable.yellow_high:
                    summary.yellow_time += unit_block_data.duration
                    summary.yellow_grf += unit_block_data.total_grf
                    summary.yellow_cma += unit_block_data.total_accel
                if cat_variable.red_low <= variable_value <= cat_variable.red_high:
                    summary.red_time += unit_block_data.duration
                    summary.red_grf += unit_block_data.total_grf
                    summary.red_cma += unit_block_data.total_accel

        summary.total_time += unit_block_data.duration
        summary.total_grf += unit_block_data.total_grf
        summary.total_cma += unit_block_data.total_accel

        return summary

    def _write_session_asymmetry_summaries(self, session_asymmetry_summaries):
        df = pd.DataFrame()
        for var, f in session_asymmetry_summaries.items():
            ab = pd.DataFrame({
                'sort_order': [f.sort_order],
                'red:grf': [f.red_grf],
                'red:grf_percent': [f.red_grf_percent],
                'red:cma': [f.red_cma],
                'red:cma_percent': [f.red_cma_percent],
                'red:time': [f.red_time],
                'red:time_percent': [f.red_time_percent],
                'yellow:grf': [f.yellow_grf],
                'yellow:grf_percent': [f.yellow_grf_percent],
                'yellow:cma': [f.yellow_cma],
                'yellow:cma_percent': [f.yellow_cma_percent],
                'yellow:time': [f.yellow_time],
                'yellow:time_percent': [f.yellow_time_percent],
                'green:grf': [f.green_grf],
                'green:grf_percent': [f.green_grf_percent],
                'green:cma': [f.green_cma],
                'green:cma_percent': [f.green_cma_percent],
                'green:time': [f.green_time],
                'green:time_percent': [f.green_time_percent],
                'total_grf': [f.total_grf],
                'total_cma': [f.total_cma],
                'total_time': [f.total_time],
                'total_session_time': [f.total_session_time],
                # lots to add here!!!
            }, index=[f.variable_name])
            df = df.append(ab)
        df = df.sort_values("sort_order")

        if df.shape[0] > 0:
            self.datastore.put_data('relmagnitudeasymmetry', df)
            self.datastore.copy_to_s3('relmagnitudeasymmetry', 'advanced-stats', '_'.join([self.event_date, self.user_id]) + "/rel_magnitude_asymmetry.csv")

    def _write_loading_movement_asymmetry(self, loading_events, movement_events):
        df = pd.DataFrame()
        for d in movement_events:
            for f in loading_events:
                if d.cma_level == f.cma_level and d.grf_level == f.grf_level and d.stance == f.stance:
                    ab = pd.DataFrame({
                        # 'complexity_level': [f.complexity_level],
                        'grf_level': [f.grf_level],
                        'cma_level': [f.cma_level],
                        'acc_grf_left': [f.total_left_sum],
                        'acc_grf_right': [f.total_right_sum],
                        'acc_grf_perc_asymm': [f.total_percent_asymmetry],
                        'gc_event_left': [f.left_step_count],
                        'gc_event_right': [f.right_step_count],
                        'gc_event_perc_asymm': [f.step_count_percent_asymmetry],
                        'gct_left': [f.ground_contact_time_left],
                        'gct_right': [f.ground_contact_time_right],
                        'gct_perc_asymm': [f.ground_contact_time_percent_asymmetry],
                        'rate_of_acc_grf_left': [f.left_avg_accumulated_grf_sec],
                        'rate_of_acc_grf_right': [f.right_avg_accumulated_grf_sec],
                        'rate_of_acc_grf_perc_asymm': [f.accumulated_grf_sec_percent_asymmetry],
                        'adduc_rom_hip': [d.adduc_rom_hip_flag()],
                        'adduc_motion_covered_total_hip': [d.adduc_motion_covered_tot_hip_flag()],
                        'adduc_motion_covered_pos_hip': [d.adduc_motion_covered_pos_hip_flag()],
                        'adduc_motion_covered_neg_hip': [d.adduc_motion_covered_neg_hip_flag()],
                        'flex_rom_hip': [d.flex_rom_hip_flag()],
                        'flex_motion_covered_total_hip': [d.adduc_motion_covered_tot_hip_flag()],
                        'flex_motion_covered_pos_hip': [d.adduc_motion_covered_pos_hip_flag()],
                        'flex_motion_covered_neg_hip': [d.adduc_motion_covered_neg_hip_flag()],
                    }, index=[f.stance])
                    df = df.append(ab)

        self.datastore.put_data('loadingmovementasymm', df)
        self.datastore.copy_to_s3('loadingmovementasymm', 'advanced-stats', '_'.join([self.event_date, self.user_id]) + "/loading_movement_asymm.csv")
