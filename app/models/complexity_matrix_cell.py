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

    def get_decay_outliers(self, attribute, label, orientation, active_block_list, step_list):

        abs_list = {}
        abs_value_list = []
        abs_outlier_list = []
        active_block_count = -1

        for key in active_block_list:

            active_block_count += 1
            steps = list(x for x in step_list if x.active_block_id == key)
            decay = []
            y0 = None
            t0 = None
            decay_mean = None
            for item in steps:
                if getattr(item, attribute) is not None:
                    y0 = math.fabs(getattr(item, attribute))
                    t0 = getattr(item, "cumulative_end_time")

                    break

            t = None
            cnt = 0
            for item in steps:
                if getattr(item, attribute) is not None:
                    yt = math.fabs(getattr(item, attribute))
                    t = getattr(item, "cumulative_end_time")

                    if cnt > 4:
                        decay.append((math.log(yt / y0)) / (t - t0))
                    cnt = cnt + 1
            if len(decay) > 0:
                decay_mean = np.mean(decay)
            if decay_mean is not None:
                abs_list[key] = {
                    'end_time': t,
                    'time_block': self.get_time_block(steps[0].active_block_number, len(active_block_list), 4),
                    'raw_value': decay_mean
                }
                abs_value_list.append(decay_mean)

        # what is the mean of the mean?

        abs_mean = np.mean(abs_value_list)
        abs_stddev = np.std(abs_value_list)

        # now loop back through and find outliers!
        for key, value in abs_list.items():
            z_score = (value['raw_value'] - abs_mean) / abs_stddev
            if math.fabs(z_score) > 2:
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

        outlier_list.extend(self.get_decay_outliers("adduc_ROM_hip", "adduc_rom_hip", "Left", active_block_list, self.left_steps))
        outlier_list.extend(self.get_decay_outliers("flex_ROM_hip", "flex_rom_hip", "Left", active_block_list, self.left_steps))
        outlier_list.extend(self.get_decay_outliers("adduc_ROM_hip", "adduc_rom_hip", "Right", active_block_list, self.right_steps))
        outlier_list.extend(self.get_decay_outliers("flex_ROM_hip", "flex_rom_hip", "Right", active_block_list, self.right_steps))

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
