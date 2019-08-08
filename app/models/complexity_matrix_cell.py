from scipy import stats
import math
import numpy as np

from .fatigue_event import FatigueEvent


class ComplexityMatrixCell(object):
    """
    Description of class
    """

    def __init__(self, row_name="Row", column_name="Column", complexity_level="Low"):
        self.grf_level = row_name
        self.cma_level = column_name
        self.complexity_level = complexity_level
        self.left_steps = []
        self.right_steps = []

    @property
    def left_step_count(self):
        return len(self.left_steps)

    @property
    def right_step_count(self):
        return len(self.right_steps)

    @property
    def left_duration(self):
        return self.get_steps_sum("duration", self.left_steps)

    @property
    def right_duration(self):
        return self.get_steps_sum("duration", self.right_steps)

    @property
    def left_avg_accumulated_grf_sec(self):
        return self.get_steps_mean("accumulated_grf_per_sec", self.left_steps)

    @property
    def right_avg_accumulated_grf_sec(self):
        return self.get_steps_mean("accumulated_grf_per_sec", self.right_steps)

    def get_steps_correlation(self, attribute_x, attribute_y, step_list):
        value_list_x = []
        value_list_y = []
        for item in step_list:
            if getattr(item, attribute_x) is not None:
                value_list_x.append(getattr(item, attribute_x))
            if getattr(item, attribute_y) is not None:
                value_list_y.append(getattr(item, attribute_y))
        if len(value_list_x) == 0 or len(value_list_y) == 0:
            return 0
        else:
            r, p = stats.pearsonr(value_list_x, value_list_y)
            if p <= .05:
                return r
            else:
                return None

    def get_decay_outliers(self, attribute, label, orientation, unit_block_list, step_list):

        seconds = 420.0
        abs_list = {}
        abs_value_list = []
        abs_outlier_list = []
        active_block_count = -1
        interval = 0
        decay = []
        decay_mean = None
        last_t0 = None
        t = None
        for unit_block_number in unit_block_list:

            active_block_count += 1
            if len(decay) > 0:
                decay_mean = np.mean(decay)
            if decay_mean is not None:
                abs_list[interval] = {
                    'start_time': last_t0,
                    'end_time': t,
                    'time_block': interval,
                    'raw_value': decay_mean
                }
                abs_value_list.append(decay_mean)
            steps = list(x for x in step_list if x.unit_block_number == unit_block_number)
            decay = []
            y0 = None
            t0 = None
            decay_mean = None
            last_t0 = None
            cnt = 1
            yt = 0
            for item in steps:
                if getattr(item, attribute) is not None:

                    if last_t0 is None:
                        t0 = getattr(item, "cumulative_end_time")
                        y0 = math.fabs(getattr(item, attribute))
                        last_t0 = t0

                    t = getattr(item, "cumulative_end_time")
                    if last_t0 <= t <= (last_t0 + seconds):

                        yt += math.fabs(getattr(item, attribute))
                        yt_average = float(yt) / float(cnt)
                        if cnt > 4:

                            decay.append((math.log(yt_average / y0)) / (t - last_t0))
                        cnt += 1
                    else:

                        if len(decay) > 0:
                            decay_mean = np.mean(decay)
                        if decay_mean is not None:
                            abs_list[interval] = {
                                'start_time': last_t0,
                                'end_time': t,
                                'time_block': interval,
                                'raw_value': decay_mean
                            }
                            abs_value_list.append(decay_mean)
                        decay = []
                        last_t0 = t
                        t0 = t
                        cnt = 1
                        y0 = math.fabs(getattr(item, attribute))
                        yt = math.fabs(getattr(item, attribute))
                        yt_average = float(yt) / float(cnt)

                        interval += 1

            if len(decay) > 0:
                decay_mean = np.mean(decay)
            if decay_mean is not None:
                abs_list[interval] = {
                    'start_time': last_t0,
                    'end_time': t,
                    'time_block': interval,
                    'raw_value': decay_mean
                }
                abs_value_list.append(decay_mean)

            # t = None
            # cnt = 0
            # for item in steps:
            #     if getattr(item, attribute) is not None:
            #         yt = math.fabs(getattr(item, attribute))
            #         t = getattr(item, "cumulative_end_time")
            #
            #         if cnt > 4:
            #             decay.append((math.log(yt / y0)) / (t - t0))
            #         cnt = cnt + 1
            # if len(decay) > 0:
            #     decay_mean = np.mean(decay)
            # if decay_mean is not None:
            #     abs_list[key] = {
            #         'end_time': t,
            #         'time_block': self.get_time_block(steps[0].active_block_number, len(active_block_list), 4),
            #         'raw_value': decay_mean
            #     }
            #     abs_value_list.append(decay_mean)

        # what is the mean of the mean?

        abs_mean = np.mean(abs_value_list)
        abs_stddev = np.std(abs_value_list)

        # now loop back through and find outliers!
        for key, value in abs_list.items():
            z_score = (value['raw_value'] - abs_mean) / abs_stddev
            outlier = FatigueEvent(self.cma_level, self.grf_level)
            outlier.active_block_id = key
            outlier.attribute_label = label
            outlier.attribute_name = attribute
            outlier.complexity_level = self.complexity_level
            outlier.cumulative_end_time = value["end_time"]
            outlier.orientation = orientation
            outlier.raw_value = value['raw_value']
            outlier.time_block = value["time_block"]
            outlier.z_score = z_score
            if math.fabs(z_score) > 2:
                outlier.significant = 1

            abs_outlier_list.append(outlier)

        return abs_outlier_list

    def get_time_block(self, active_block_number, active_block_length, category_count):
        category_width = active_block_length / float(category_count)
        block = math.ceil(float(active_block_number) / category_width)
        block = min(block, category_count)
        return block

    def get_steps_sum(self, attribute, step_list):
        value_list = []
        for item in step_list:
            if getattr(item, attribute) is not None:
                value_list.append(getattr(item, attribute))
        if len(value_list) == 0:
            return 0
        else:
            return np.sum(value_list)

    def get_steps_stddev(self, attribute, step_list):
        value_list = []
        for item in step_list:
            if getattr(item, attribute) is not None:
                value_list.append(getattr(item, attribute))
        if len(value_list) == 0:
            return 0
        else:
            return np.std(value_list)

    def get_steps_mean(self, attribute, step_list):
        value_list = []
        for item in step_list:
            if getattr(item, attribute) is not None:
                value_list.append(getattr(item, attribute))
        if len(value_list) == 0:
            return 0
        else:
            return np.mean(value_list)

    def add_step(self, step):
        if step.orientation == "Left":
            self.left_steps.append(step)
        else:
            self.right_steps.append(step)

    def get_decay_parameters(self):

        outlier_list = []

        active_block_list_lf = {x.active_block_id for x in self.left_steps}
        active_block_list_rf = {x.active_block_id for x in self.right_steps}
        active_block_list = list(set(active_block_list_lf).union(active_block_list_rf))
        active_block_list.sort()

        unit_block_list_lf = {x.unit_block_number for x in self.left_steps}
        unit_block_list_rf = {x.unit_block_number for x in self.right_steps}
        unit_block_list = list(set(unit_block_list_lf).union(unit_block_list_rf))
        unit_block_list.sort()

        # outlier_list.extend(self.get_decay_outliers("adduc_ROM_hip", "adduc_rom_hip", "Left", active_block_list, self.left_steps))
        # outlier_list.extend(self.get_decay_outliers("flex_ROM_hip", "flex_rom_hip", "Left", active_block_list, self.left_steps))
        # outlier_list.extend(self.get_decay_outliers("adduc_ROM_hip", "adduc_rom_hip", "Right", active_block_list, self.right_steps))
        # outlier_list.extend(self.get_decay_outliers("flex_ROM_hip", "flex_rom_hip", "Right", active_block_list, self.right_steps))
        outlier_list.extend(self.get_decay_outliers("anterior_pelvic_tilt_range", "anterior_pelvic_tilt_range", "Left", unit_block_list, self.left_steps))
        outlier_list.extend(self.get_decay_outliers("anterior_pelvic_tilt_rate", "anterior_pelvic_tilt_rate", "Left", unit_block_list, self.left_steps))
        outlier_list.extend(self.get_decay_outliers("anterior_pelvic_tilt_range", "anterior_pelvic_tilt_range", "Right", unit_block_list, self.right_steps))
        outlier_list.extend(self.get_decay_outliers("anterior_pelvic_tilt_rate", "anterior_pelvic_tilt_rate", "Right", unit_block_list, self.right_steps))


        adduc_pos_hip_steps_lf = list(x for x in self.left_steps if x.adduc_motion_covered_pos_hip > 0)

        adduc_neg_hip_steps_rf = list(x for x in self.right_steps if x.adduc_motion_covered_neg_hip < 0)
        adduc_pos_hip_steps_rf = list(x for x in self.right_steps if x.adduc_motion_covered_pos_hip > 0)
        adduc_neg_hip_steps_lf = list(x for x in self.left_steps if x.adduc_motion_covered_neg_hip < 0)

        flex_pos_hip_steps_rf = list(x for x in self.right_steps if x.flex_motion_covered_pos_hip > 0)
        flex_pos_hip_steps_lf = list(x for x in self.left_steps if x.flex_motion_covered_pos_hip > 0)

        flex_neg_hip_steps_rf = list(x for x in self.right_steps if x.flex_motion_covered_neg_hip < 0)
        flex_neg_hip_steps_lf = list(x for x in self.left_steps if x.flex_motion_covered_neg_hip < 0)

        outlier_list.extend(
            self.get_decay_outliers("adduc_motion_covered_pos_hip", "adduc_pos_hip", "Left", active_block_list,
                                    adduc_pos_hip_steps_lf))
        outlier_list.extend(
            self.get_decay_outliers("flex_motion_covered_pos_hip", "flex_pos_hip", "Left", active_block_list,
                                    flex_pos_hip_steps_lf))

        outlier_list.extend(
            self.get_decay_outliers("adduc_motion_covered_pos_hip", "adduc_pos_hip", "Right", active_block_list,
                                    adduc_pos_hip_steps_rf))
        outlier_list.extend(
            self.get_decay_outliers("flex_motion_covered_pos_hip", "flex_pos_hip", "Right", active_block_list,
                                    flex_pos_hip_steps_rf))

        outlier_list.extend(
            self.get_decay_outliers("adduc_motion_covered_neg_hip", "adduc_neg_hip", "Left", active_block_list,
                                    adduc_neg_hip_steps_lf))
        outlier_list.extend(
            self.get_decay_outliers("flex_motion_covered_neg_hip", "flex_neg_hip", "Left", active_block_list,
                                    flex_neg_hip_steps_lf))

        outlier_list.extend(
            self.get_decay_outliers("adduc_motion_covered_neg_hip", "adduc_neg_hip", "Right", active_block_list,
                                    adduc_neg_hip_steps_rf))
        outlier_list.extend(
            self.get_decay_outliers("flex_motion_covered_neg_hip", "flex_neg_hip", "Right", active_block_list,
                                    flex_neg_hip_steps_rf))

        return outlier_list
