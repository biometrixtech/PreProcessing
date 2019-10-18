from aws_xray_sdk.core import xray_recorder
from collections import OrderedDict
import os
import logging
from config import get_mongo_collection
from scipy import stats
import pandas as pd
import statistics
from math import ceil


from ._unit_block_job import UnitBlockJob
from .plans_structure import PlansFactory
from models.categorization_variable import CategorizationVariable
from models.loading_asymmetry import LoadingAsymmetry
from models.loading_asymmetry_summary import LoadingAsymmetrySummary
from models.movement_asymmetry import MovementAsymmetry
from models.unit_block import UnitBlock
from utils import parse_datetime
from logic.elasticity_regression import ElasticityRegression
from models.movement_pattern import MovementPatterns, MovementPatternStats

_logger = logging.getLogger()


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
        self.significant = False


class AsymmetrySummary(object):
    def __init__(self):
        self.left = 0
        self.right = 0
        self.symmetric_events = 0
        self.asymmetric_events = 0
        self.percent_events_asymmetric = 0


class AsymmetryEvents(object):
    def __init__(self):
        self.anterior_pelvic_tilt_summary = AsymmetrySummary()
        self.ankle_pitch_summary = AsymmetrySummary()
        self.hip_drop_summary = AsymmetrySummary()


class TimeBlockAsymmetry(object):
    def __init__(self):
        self.left = 0
        self.right = 0
        self.significant = False


class TimeBlock(object):
    def __init__(self):
        self.time_block = 0
        self.start_time = None
        self.end_time = None
        self.anterior_pelvic_tilt = TimeBlockAsymmetry()
        self.ankle_pitch = TimeBlockAsymmetry()
        self.hip_drop = TimeBlockAsymmetry()


class AsymmetryProcessorJob(UnitBlockJob):

    def __init__(self, datastore, unit_blocks, complexity_matrix, active_time_start, active_time_end):
        super().__init__(datastore, unit_blocks)
        self.complexity_matrix = complexity_matrix
        self.active_time_start = active_time_start
        self.active_time_end = active_time_end
        #self._complexity_matrix_single_leg = complexity_matrix_single_leg
        #self._complexity_matrix_double_leg = complexity_matrix_double_leg

    def _run(self):
        #session_asymmetry_summaries = self._get_session_asymmetry_summaries()
        #self._write_session_asymmetry_summaries(session_asymmetry_summaries)

        movement_events = self._get_movement_asymmetries()
        asymmetry_events = self._get_session_asymmetry_summary(movement_events)
        self.write_movement_asymmetry(movement_events, asymmetry_events, os.environ["ENVIRONMENT"])

        movement_patterns = self._get_movement_patterns()

        return asymmetry_events, movement_patterns

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

    # def _get_loading_asymmetries(self):
    #     events = []
    #     for stance, complexity_matrix in [('Single Leg', self._complexity_matrix_single_leg), ('Double Leg', self._complexity_matrix_double_leg)]:
    #         for keys, mcsl in complexity_matrix.items():
    #             events.append(self._get_loading_asymmetry(
    #                 "total_grf",
    #                 mcsl,
    #                 mcsl.complexity_level,
    #                 mcsl.cma_level,
    #                 mcsl.grf_level,
    #                 stance))
    #
    #     return events
    #
    # @staticmethod
    # def _get_loading_asymmetry(attribute, complexity_matrix_cell, complexity_level, cma_level, grf_level, stance):
    #
    #     asym = LoadingAsymmetry(complexity_level, cma_level, grf_level, stance)
    #     asym.variable = attribute
    #     asym.total_left_sum = complexity_matrix_cell.get_steps_sum(attribute, complexity_matrix_cell.left_steps)
    #     asym.total_right_sum = complexity_matrix_cell.get_steps_sum(attribute, complexity_matrix_cell.right_steps)
    #     asym.total_left_right_sum = asym.total_left_sum + asym.total_right_sum
    #
    #     if len(complexity_matrix_cell.left_steps) == 0 or len(complexity_matrix_cell.right_steps) == 0:
    #         asym.training_asymmetry = asym.total_left_sum - asym.total_right_sum
    #     else:
    #         asym.kinematic_asymmetry = asym.total_left_sum - asym.total_right_sum
    #     asym.total_asymmetry = asym.training_asymmetry + asym.kinematic_asymmetry
    #     if asym.total_left_right_sum > 0:
    #         asym.total_percent_asymmetry = (asym.total_asymmetry / asym.total_left_right_sum) * 100
    #
    #     asym.left_step_count = complexity_matrix_cell.left_step_count
    #     asym.right_step_count = complexity_matrix_cell.right_step_count
    #     asym.total_steps = asym.left_step_count + asym.right_step_count
    #     asym.step_asymmetry = asym.left_step_count - asym.right_step_count
    #     if asym.total_steps > 0:
    #         asym.step_count_percent_asymmetry = (asym.step_asymmetry / float(asym.total_steps)) * 100
    #
    #     asym.ground_contact_time_left = complexity_matrix_cell.left_duration
    #     asym.ground_contact_time_right = complexity_matrix_cell.right_duration
    #     asym.total_ground_contact_time = asym.ground_contact_time_left + asym.ground_contact_time_right
    #     asym.ground_contact_time_asymmetry = asym.ground_contact_time_left - asym.ground_contact_time_right
    #     if asym.total_ground_contact_time > 0:
    #         asym.ground_contact_time_percent_asymmetry = (asym.ground_contact_time_asymmetry / float(
    #             asym.total_ground_contact_time)) * 100
    #
    #     asym.left_avg_accumulated_grf_sec = complexity_matrix_cell.left_avg_accumulated_grf_sec
    #     asym.right_avg_accumulated_grf_sec = complexity_matrix_cell.right_avg_accumulated_grf_sec
    #     asym.accumulated_grf_sec_asymmetry = asym.left_avg_accumulated_grf_sec - asym.right_avg_accumulated_grf_sec
    #     if asym.right_avg_accumulated_grf_sec > 0:
    #         asym.accumulated_grf_sec_percent_asymmetry = (asym.left_avg_accumulated_grf_sec /
    #                                                       float(asym.right_avg_accumulated_grf_sec)) * 100
    #
    #     return asym
    def _get_session_asymmetry_summary(self, movement_asymmetries):

        left_apt = 0
        right_apt = 0
        apt_sym_count = 0
        apt_asym_count = 0
        left_ankle_pitch = 0
        right_ankle_pitch = 0
        ankle_pitch_sym_count = 0
        ankle_pitch_asym_count = 0
        left_hip_drop = 0
        right_hip_drop = 0
        hip_drop_sym_count = 0
        hip_drop_asym_count = 0
        left_ankle_pitch_list = []
        right_ankle_pitch_list = []
        left_apt_list = []
        right_apt_list = []
        left_hip_drop_list = []
        right_hip_drop_list = []

        # left_ankle_pitch_not_significant_list = []
        # right_ankle_pitch_not_significant_list = []
        # left_apt_not_significant_list = []
        # right_apt_not_significant_list = []
        # left_hip_drop_not_significant_list = []
        # right_hip_drop_not_significant_list = []

        for m in movement_asymmetries:
            if m.anterior_pelvic_tilt.significant:
                left_apt_list.append(m.anterior_pelvic_tilt.left)
                right_apt_list.append(m.anterior_pelvic_tilt.right)
                if m.anterior_pelvic_tilt.left > 0 or m.anterior_pelvic_tilt.right > 0:
                    apt_asym_count += 1
            else:
                if m.anterior_pelvic_tilt.left > 0 or m.anterior_pelvic_tilt.right > 0:
                    apt_sym_count += 1
                    left_apt_list.append(m.anterior_pelvic_tilt.left)
                    right_apt_list.append(m.anterior_pelvic_tilt.right)
            if m.ankle_pitch.significant:
                left_ankle_pitch_list.append(m.ankle_pitch.left)
                right_ankle_pitch_list.append(m.ankle_pitch.right)
                if m.ankle_pitch.left > 0 or m.ankle_pitch.right > 0:
                    ankle_pitch_asym_count += 1
            else:
                if m.ankle_pitch.left > 0 or m.ankle_pitch.right > 0:
                    ankle_pitch_sym_count += 1
                    left_ankle_pitch_list.append(m.ankle_pitch.left)
                    right_ankle_pitch_list.append(m.ankle_pitch.right)
            if m.hip_drop.significant:
                left_hip_drop_list.append(m.hip_drop.left)
                right_hip_drop_list.append(m.hip_drop.right)
                if m.hip_drop.left > 0 or m.hip_drop.right > 0:
                    hip_drop_asym_count += 1
            else:
                if m.hip_drop.left > 0 or m.hip_drop.right > 0:
                    hip_drop_sym_count += 1
                    left_hip_drop_list.append(m.hip_drop.left)
                    right_hip_drop_list.append(m.hip_drop.right)

        events = AsymmetryEvents()

        if len(left_apt_list) > 0:
            left_apt = statistics.median(left_apt_list)
        # elif len(left_apt_not_significant_list) > 0:
        #     left_apt = statistics.median(left_apt_not_significant_list)

        if len(right_apt_list) > 0:
            right_apt = statistics.median(right_apt_list)
        # elif len(right_apt_not_significant_list) > 0:
        #     right_apt = statistics.median(right_apt_not_significant_list)

        events.anterior_pelvic_tilt_summary.left = left_apt
        events.anterior_pelvic_tilt_summary.right = right_apt
        events.anterior_pelvic_tilt_summary.symmetric_events = apt_sym_count
        events.anterior_pelvic_tilt_summary.asymmetric_events = apt_asym_count

        apt_total_count = apt_sym_count + apt_asym_count

        events.anterior_pelvic_tilt_summary.percent_events_asymmetric = 0

        if apt_total_count > 0:
            events.anterior_pelvic_tilt_summary.percent_events_asymmetric = round((apt_asym_count / float(apt_total_count)) * 100)

        if len(left_ankle_pitch_list) > 0:
            left_ankle_pitch = statistics.median(left_ankle_pitch_list)
        # elif len(left_ankle_pitch_not_significant_list) > 0:
        #     left_ankle_pitch = statistics.median(left_ankle_pitch_not_significant_list)

        if len(right_ankle_pitch_list) > 0:
            right_ankle_pitch = statistics.median(right_ankle_pitch_list)
        # elif len(right_ankle_pitch_not_significant_list) > 0:
        #     right_ankle_pitch = statistics.median(right_ankle_pitch_not_significant_list)

        events.ankle_pitch_summary.left = left_ankle_pitch
        events.ankle_pitch_summary.right = right_ankle_pitch
        events.ankle_pitch_summary.symmetric_events = ankle_pitch_sym_count
        events.ankle_pitch_summary.asymmetric_events = ankle_pitch_asym_count

        ankle_pitch_total_count = ankle_pitch_sym_count + ankle_pitch_asym_count

        events.ankle_pitch_summary.percent_events_asymmetric = 0

        if ankle_pitch_total_count > 0:
            events.ankle_pitch_summary.percent_events_asymmetric = round((ankle_pitch_asym_count / float(ankle_pitch_total_count)) * 100)

        # Hip Drop
        if len(left_hip_drop_list) > 0:
            left_hip_drop = statistics.median(left_hip_drop_list)
        # elif len(left_hip_drop_not_significant_list) > 0:
        #     left_hip_drop = statistics.median(left_hip_drop_not_significant_list)

        if len(right_hip_drop_list) > 0:
            right_hip_drop = statistics.median(right_hip_drop_list)
        # elif len(right_hip_drop_not_significant_list) > 0:
        #     right_hip_drop = statistics.median(right_hip_drop_not_significant_list)

        events.hip_drop_summary.left = left_hip_drop
        events.hip_drop_summary.right = right_hip_drop
        events.hip_drop_summary.symmetric_events = hip_drop_sym_count
        events.hip_drop_summary.asymmetric_events = hip_drop_asym_count

        hip_drop_total_count = hip_drop_asym_count + hip_drop_sym_count

        events.hip_drop_summary.percent_events_asymmetric = 0

        if hip_drop_total_count > 0:
            events.hip_drop_summary.percent_events_asymmetric = round((hip_drop_asym_count / float(hip_drop_total_count)) * 100)

        # left_significant_events = [l.left for l in movement_asymmetries if l.significant]
        # right_significant_events = [r.right for r in movement_asymmetries if r.significant]
        #
        # left_apt = 0
        # right_apt = 0
        #
        # if len(left_significant_events) > 0:
        #     left_apt = sum(left_significant_events)
        #
        # if len(right_significant_events) > 0:
        #     right_apt = sum(right_significant_events)

        #return left_apt, right_apt
        return events

    def _get_movement_patterns(self):

        movement_patterns_list = []

        elasticity_regression = ElasticityRegression()

        user_id = self.datastore.get_metadatum('user_id', None)

        for keys, mcsl in self.complexity_matrix.items():

            movement_patterns = elasticity_regression.run_regressions(mcsl.left_steps, mcsl.right_steps)

            movement_patterns.user_id = user_id
            movement_patterns.session_id = self.datastore.session_id

            movement_patterns_list.append(movement_patterns)

        return movement_patterns_list[0]

    def _get_movement_asymmetries(self):

        asymm_events = []

        for keys, mcsl in self.complexity_matrix.items():
            events = self._get_movement_asymmetry(mcsl.left_steps, mcsl.right_steps)

            asymm_events.extend(events)

        return asymm_events

    def _get_movement_asymmetry(self,  left_steps, right_steps):

        unit_block_list_lf = {x.unit_block_number for x in left_steps}
        unit_block_list_rf = {x.unit_block_number for x in right_steps}
        unit_block_list = list(set(unit_block_list_lf).union(unit_block_list_rf))
        unit_block_list.sort()

        #event_date = self.datastore.get_metadatum('event_date')
        #end_date = self.datastore.get_metadatum('end_date')
        #seconds_duration = (parse_datetime(end_date) - parse_datetime(event_date)).seconds

        events = []

        time_block = 0

        last_unit_block_time = 0
        seconds = 30

        for unit_block_number in unit_block_list:

            l_unit_block_steps = list(x for x in left_steps if x.unit_block_number == unit_block_number)
            r_unit_block_steps = list(x for x in right_steps if x.unit_block_number == unit_block_number)

            all_steps = []
            all_steps.extend(l_unit_block_steps)
            all_steps.extend(r_unit_block_steps)

            start_time = None
            end_time = None
            intervals = 0

            cumulative_time = list(x.cumulative_end_time for x in all_steps)

            if len(cumulative_time) > 0:
                start_time = min(cumulative_time)
                end_time = max(cumulative_time)

                seconds_diff = end_time - start_time
                intervals = ceil(seconds_diff / float(seconds))

            for i in range(0, intervals):

                #apt_event = AsymmetryDistribution()
                block_start_time = start_time + (i * seconds)
                block_end_time = min(start_time + ((i + 1) * seconds), end_time)

                if block_start_time > last_unit_block_time and (block_start_time - last_unit_block_time) > 10:
                    seconds_between_blocks = block_start_time - last_unit_block_time
                    gap_intervals = ceil(seconds_between_blocks / float(seconds))
                    for g in range(0, gap_intervals):
                        #gap_event = AsymmetryDistribution()
                        gap_event = TimeBlock()

                        gap_end_time = min(last_unit_block_time + ((g + 1) * seconds), block_start_time)
                        gap_event.start_time = last_unit_block_time + (g * seconds)

                        if (gap_end_time - gap_event.start_time) > 10:
                            gap_event.end_time = gap_end_time
                            gap_event.time_block = time_block
                            events.append(gap_event)
                            time_block += 1
                            #last_unit_block_time = max(gap_end_time, last_unit_block_time)
                last_unit_block_time = max(block_end_time, last_unit_block_time)

                if block_end_time - block_start_time >= 10:
                    l_step_blocks = list(x for x in l_unit_block_steps if
                                         block_start_time <= x.cumulative_end_time <= block_end_time)
                    r_step_blocks = list(x for x in r_unit_block_steps if
                                         block_start_time <= x.cumulative_end_time <= block_end_time)

                    time_block_obj = TimeBlock()
                    time_block_obj.time_block = time_block
                    time_block_obj.start_time = block_start_time
                    time_block_obj.end_time = block_end_time
                    time_block_obj.anterior_pelvic_tilt = TimeBlockAsymmetry()
                    time_block_obj.ankle_pitch = TimeBlockAsymmetry()

                    apt_event = self._get_steps_f_test("anterior_pelvic_tilt_range", l_step_blocks,
                                                                              r_step_blocks, time_block)

                    if apt_event is not None:
                        time_block_obj.anterior_pelvic_tilt.left = apt_event.left_median
                        time_block_obj.anterior_pelvic_tilt.right = apt_event.right_median
                        time_block_obj.anterior_pelvic_tilt.significant = apt_event.significant

                    ankle_pitch_event = self._get_steps_f_test("ankle_pitch_range", l_step_blocks,
                                                                              r_step_blocks, time_block, threshold=1.03)
                    if ankle_pitch_event is not None:
                        time_block_obj.ankle_pitch.left = ankle_pitch_event.left_median
                        time_block_obj.ankle_pitch.right = ankle_pitch_event.right_median
                        time_block_obj.ankle_pitch.significant = ankle_pitch_event.significant

                    hip_drop_event = self._get_steps_f_test("hip_drop", l_step_blocks, r_step_blocks, time_block)

                    if hip_drop_event is not None:
                        time_block_obj.hip_drop.left = hip_drop_event.left_median
                        time_block_obj.hip_drop.right = hip_drop_event.right_median
                        time_block_obj.hip_drop.significant = hip_drop_event.significant

                    # if apt_event is None:
                    #     apt_event = AsymmetryDistribution()
                    #     apt_event.start_time = block_start_time
                    #     apt_event.end_time = block_end_time
                    #     apt_event.time_block = time_block
                    events.append(time_block_obj)
                    time_block += 1
            last_unit_block_time = max(end_time, last_unit_block_time)
        # if seconds_duration > last_unit_block_time and (seconds_duration - last_unit_block_time) > 10:
        #     seconds_between_blocks = seconds_duration - last_unit_block_time
        #     gap_intervals = ceil(seconds_between_blocks / float(seconds))
        #     for g in range(0, gap_intervals):
        #         # time_block += 1
        #         #gap_event = AsymmetryDistribution()
        #         gap_event = TimeBlock()
        #         gap_event.start_time = last_unit_block_time + (g * seconds)
        #         gap_end_time = min(last_unit_block_time + ((g + 1) * seconds), seconds_duration)
        #         gap_event.end_time = gap_end_time
        #         gap_event.time_block = time_block
        #         events.append(gap_event)
        #         time_block += 1

        return events

    @staticmethod
    def _get_steps_f_test(attribute, step_list_x, step_list_y, time_block, threshold=1.15):
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
                if len(value_list_x) > 0:
                    left_median = statistics.median(value_list_x)
                else:
                    left_median = 0
                if len(value_list_y) > 0:
                    right_median = statistics.median(value_list_y)
                else:
                    right_median = 0

                all_values = []
                all_values.extend(step_list_x)
                all_values.extend(step_list_y)

                times = list(x.cumulative_end_time for x in all_values)
                start_time = min(times)
                end_time = max(times)

                if p <= .05:

                    dist = AsymmetryDistribution()

                    dist.time_block = time_block
                    dist.start_time = start_time
                    dist.end_time = end_time
                    dist.attribute_label = attribute

                    dist.r_value = r
                    dist.left_median = left_median
                    dist.right_median = right_median
                    #if abs(left_median - right_median) > 1:
                    if left_median > right_median > 0:
                        if left_median / right_median > threshold:
                            dist.significant = True
                    elif right_median > left_median > 0:
                        if right_median / left_median > threshold:
                            dist.significant = True
                    #ignore if one is zero
                    # elif (left_median == 0 or right_median == 0) and left_median != right_median:
                    #         dist.significant = True
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
                    dist = AsymmetryDistribution()
                    dist.time_block = time_block
                    dist.left_median = left_median
                    dist.right_median = right_median
                    dist.start_time = start_time
                    dist.end_time = end_time
                    return dist
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

    def write_movement_pattern(self, movement_pattern, environment):

        mongo_collection = get_mongo_collection('MOVEMENTPATTERN')
        plans_api_version = self.datastore.get_metadatum('plans_api_version', '4_4')

        # end_date = self.datastore.get_metadatum('end_date', None)
        event_date = self.datastore.get_metadatum('event_date', None)

        seconds_duration = (parse_datetime(self.active_time_end) - parse_datetime(self.active_time_start)).seconds

        user_id = self.datastore.get_metadatum('user_id', None)

        plans_factory = PlansFactory(plans_api_version, environment, user_id, event_date, self.datastore.session_id, seconds_duration)
        plans = plans_factory.get_plans()
        record_out = plans.get_mongo_movement_pattern_record(movement_pattern)

        query = {'session_id': self.datastore.session_id, 'user_id': user_id}
        mongo_collection.replace_one(query, record_out, upsert=True)

        _logger.info("Wrote movement pattern record for " + self.datastore.session_id)

        if plans_api_version != plans_factory.latest_plans_version:
            latest_plans_factory = PlansFactory(plans_factory.latest_plans_version, environment, user_id, event_date, self.datastore.session_id, seconds_duration)
            latest_plans = latest_plans_factory.get_plans()
            latest_record_out = latest_plans.get_mongo_movement_pattern_record(movement_pattern)
            latest_record_out["plans_version"] = plans_factory.latest_plans_version
            latest_mongo_collection = get_mongo_collection('MOVEMENTPATTERNRESERVE')
            latest_mongo_collection.replace_one(query, latest_record_out, upsert=True)

            _logger.info("Wrote movement pattern reserve record for " + self.datastore.session_id)

    def write_movement_asymmetry(self, movement_events, asymmetry_events, environment):

        mongo_collection = get_mongo_collection('ASYMMETRY')
        plans_api_version = self.datastore.get_metadatum('plans_api_version', '4_4')

        # end_date = self.datastore.get_metadatum('end_date', None)
        event_date = self.datastore.get_metadatum('event_date', None)

        seconds_duration = (parse_datetime(self.active_time_end) - parse_datetime(self.active_time_start)).seconds

        user_id = self.datastore.get_metadatum('user_id', None)

        plans_factory = PlansFactory(plans_api_version, environment, user_id, event_date, self.datastore.session_id, seconds_duration)
        plans = plans_factory.get_plans()
        record_out = plans.get_mongo_asymmetry_record(asymmetry_events, movement_events)

        query = {'session_id': self.datastore.session_id, 'user_id': user_id}
        mongo_collection.replace_one(query, record_out, upsert=True)

        _logger.info("Wrote asymmetry record for " + self.datastore.session_id)

        if plans_api_version != plans_factory.latest_plans_version:
            latest_plans_factory = PlansFactory(plans_factory.latest_plans_version, environment, user_id, event_date, self.datastore.session_id, seconds_duration)
            latest_plans = latest_plans_factory.get_plans()
            latest_record_out = latest_plans.get_mongo_asymmetry_record(asymmetry_events, movement_events)
            latest_record_out["plans_version"] = plans_factory.latest_plans_version
            latest_mongo_collection = get_mongo_collection('ASYMMETRYRESERVE')
            latest_mongo_collection.replace_one(query, latest_record_out, upsert=True)

            _logger.info("Wrote asymmetryReserve record for " + self.datastore.session_id)

        # record_out = OrderedDict()
        # record_out['user_id'] = user_id
        # record_out['event_date'] = event_date
        # record_out['seconds_duration'] = seconds_duration
        # record_out['session_id'] = self.datastore.session_id
        #
        # # sym_count = [m for m in movement_events if not m.significant and (m.left_median > 0 or m.right_median > 0)]
        # # asym_count = [m for m in movement_events if m.significant and (m.left_median > 0 or m.right_median > 0)]
        #
        # anterior_pelivic_tilt = OrderedDict()
        # anterior_pelivic_tilt['left'] = asymmetry_events.anterior_pelvic_tilt_summary.left
        # anterior_pelivic_tilt['right'] = asymmetry_events.anterior_pelvic_tilt_summary.right
        # anterior_pelivic_tilt['symmetric_events'] = asymmetry_events.anterior_pelvic_tilt_summary.symmetric_events
        # anterior_pelivic_tilt['asymmetric_events'] = asymmetry_events.anterior_pelvic_tilt_summary.asymmetric_events
        # anterior_pelivic_tilt['percent_events_asymmetric'] = asymmetry_events.anterior_pelvic_tilt_summary.percent_events_asymmetric
        #
        # record_out['apt'] = anterior_pelivic_tilt
        #
        # ankle_pitch = OrderedDict()
        # ankle_pitch['left'] = asymmetry_events.ankle_pitch_summary.left
        # ankle_pitch['right'] = asymmetry_events.ankle_pitch_summary.right
        # ankle_pitch['symmetric_events'] = asymmetry_events.ankle_pitch_summary.symmetric_events
        # ankle_pitch['asymmetric_events'] = asymmetry_events.ankle_pitch_summary.asymmetric_events
        # ankle_pitch['percent_events_asymmetric'] = asymmetry_events.ankle_pitch_summary.percent_events_asymmetric
        #
        # record_out['ankle_pitch'] = ankle_pitch
        #
        # record_asymmetries = []
        #
        # for m in movement_events:
        #     event_record = OrderedDict()
        #     event_record['time_block'] = m.time_block
        #     event_record['start_time'] = m.start_time
        #     event_record['end_time'] = m.end_time
        #
        #     apt_time_block = OrderedDict()
        #     apt_time_block['left'] = m.anterior_pelvic_tilt.left
        #     apt_time_block['right'] = m.anterior_pelvic_tilt.right
        #     apt_time_block['significant'] = m.anterior_pelvic_tilt.significant
        #
        #     event_record['apt'] = apt_time_block
        #
        #     ankle_pitch_time_block = OrderedDict()
        #     ankle_pitch_time_block['left'] = m.ankle_pitch.left
        #     ankle_pitch_time_block['right'] = m.ankle_pitch.right
        #     ankle_pitch_time_block['significant'] = m.ankle_pitch.significant
        #
        #     event_record['ankle_pitch'] = ankle_pitch_time_block
        #
        #     record_asymmetries.append(event_record)
        #
        # record_out['time_blocks'] = record_asymmetries

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
