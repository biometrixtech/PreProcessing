from numpy import pi
from scipy import stats


class Threshold(object):
    def __init__(self, label, min_value, max_value):
        self.label = label
        self.min = min_value
        self.max = max_value

    def json_serialise(self):
        return {'label': self.label,
                'min': self.min,
                'max': self.max}

    @classmethod
    def json_deserialise(cls, input_dict):
        return cls(input_dict['label'], input_dict['min'], input_dict['max'])


class PiVector(object):
    def __init__(self):
        self.categories = {}
        self.sum = 0.0
        self.categories[Threshold('00', -pi, -pi / float(1.10))] = Category()
        self.categories[Threshold('01', -pi / float(1.10), -pi / float(1.15))] = Category()
        self.categories[Threshold('02', -pi / float(1.15), -pi / float(1.25))] = Category()
        self.categories[Threshold('03', -pi / float(1.25), -pi / float(1.5))] = Category()
        self.categories[Threshold('04', -pi / float(1.5), -pi / float(1.75))] = Category()
        self.categories[Threshold('05', -pi / float(1.75), -pi / float(2.0))] = Category()
        self.categories[Threshold('06', -pi / float(2.0), -pi / float(2.25))] = Category()
        self.categories[Threshold('07', -pi / float(2.25), -pi / float(2.5))] = Category()
        self.categories[Threshold('08', -pi / float(2.5), -pi / float(3.75))] = Category()
        self.categories[Threshold('09', -pi / float(3.75), -pi / float(5.0))] = Category()
        self.categories[Threshold('10', -pi / float(5.0), -pi / float(6.75))] = Category()
        self.categories[Threshold('11', -pi / float(6.75), 0.0)] = Category()
        self.categories[Threshold('12', 0.0, pi / float(6.75))] = Category()
        self.categories[Threshold('13', pi / float(6.75), pi / float(5.0))] = Category()
        self.categories[Threshold('14', pi / float(5.0), pi / float(3.75))] = Category()
        self.categories[Threshold('15', pi / float(3.75), pi / float(2.5))] = Category()
        self.categories[Threshold('16', pi / float(2.5), pi / float(2.25))] = Category()
        self.categories[Threshold('17', pi / float(2.25), pi / float(2.0))] = Category()
        self.categories[Threshold('18', pi / float(2.0), pi / float(1.75))] = Category()
        self.categories[Threshold('19', pi / float(1.75), pi / float(1.5))] = Category()
        self.categories[Threshold('20', pi / float(1.5),  pi / float(1.25))] = Category()
        self.categories[Threshold('21', pi / float(1.25), pi / float(1.15))] = Category()
        self.categories[Threshold('22', pi / float(1.15), pi / float(1.10))] = Category()
        self.categories[Threshold('23', pi / float(1.10), pi)] = Category()

    def json_serialise(self):
        return {
            'sum': self.sum,
            'categories': {frozenset(key.json_serialise().items()): frozenset(value.json_serialise().items()) for key, value in self.categories.items()}
        }

    @classmethod
    def json_deserialise(cls, input_dict):
        column_vector = cls()
        column_vector.categories = {}
        column_vector.sum = input_dict['sum']
        for key, value in input_dict['categories'].items():
            column_vector.categories[Threshold.json_deserialise(dict(key))] = Category.json_deserialise(dict(value))
        return column_vector

    def add(self, value_list):

        for v in value_list:
            for c in self.categories.keys():
                if c.min is None:
                    if v <= c.max:
                        self.categories[c].count += 1
                elif c.max is None:
                    if v > c.min:
                        self.categories[c].count += 1
                else:
                    if c.min < v <= c.max:
                        self.categories[c].count += 1

            self.sum += 1

    def calc_percentages(self, sum):

        for c in self.categories.keys():
            if sum > 0:
                self.categories[c].percentage = (float(self.categories[c].count) / float(sum)) * 100
            else:
                self.categories[c].percentage = 0.0

    def calc_raw_percentages(self):

        for c in self.categories.keys():
            if self.sum > 0:
                self.categories[c].percentage = (float(self.categories[c].count) / float(self.sum)) * 100
            else:
                self.categories[c].percentage = 0.0

    def get_percentage(self, test_value):

        for c in self.categories.keys():
            if ((c.min is None and test_value <= c.max) or (c.min < test_value <= c.max) or
                    (c.max is None and test_value > c.min)):
                return self.categories[c].percentage

        return None


class ColumnVector(object):
    def __init__(self):
        self.categories = {}
        self.sum = 0.0
        self.raw_values = []

        self.categories[Threshold('00', None, -15.0)] = Category()
        self.categories[Threshold('01', -15.0,  -9.0)] = Category()
        self.categories[Threshold('02', -9.0,  -4.5)] = Category()
        self.categories[Threshold('03b', -4.5, -2.5)] = Category()
        self.categories[Threshold('03c', -2.5, -2.0)] = Category()
        self.categories[Threshold('04', -2.0, -1.5)] = Category()
        self.categories[Threshold('05', -1.5, -1.0)] = Category()
        self.categories[Threshold('06', -1.0, -0.50)] = Category()
        self.categories[Threshold('09', -0.50, -0.25)] = Category()
        self.categories[Threshold('09c', -0.25, 0.0)] = Category()
        self.categories[Threshold('10', 0.0, 0.25)] = Category()
        self.categories[Threshold('10c', 0.25, 0.50)] = Category()
        self.categories[Threshold('12', 0.50, 1.0)] = Category()
        self.categories[Threshold('14', 1.0, 1.5)] = Category()
        self.categories[Threshold('15', 1.5, 2.0)] = Category()
        self.categories[Threshold('15b', 2.0, 2.5)] = Category()
        self.categories[Threshold('16', 2.5, 4.5)] = Category()
        self.categories[Threshold('17', 4.5, 9.0)] = Category()
        self.categories[Threshold('18', 9.0, 15.0)] = Category()
        self.categories[Threshold('19', 15.0, None)] = Category()

    def json_serialise(self):
        return {
            'sum': self.sum,
            # 'raw_values': self.raw_values,
            'categories': {frozenset(key.json_serialise().items()): frozenset(value.json_serialise().items()) for key, value in self.categories.items()}
        }

    @classmethod
    def json_deserialise(cls, input_dict):
        column_vector = cls()
        column_vector.categories = {}
        column_vector.sum = input_dict['sum']
        # column_vector.raw_values = input_dict['raw_values']
        for key, value in input_dict['categories'].items():
            threshold = Threshold.json_deserialise(dict(key))
            category = Category.json_deserialise(dict(value))
            column_vector.categories[threshold] = category
        return column_vector

    def add(self, value_list):

        for v in value_list:
            for c in self.categories.keys():
                if c.min is None:
                    if v <= c.max:
                        self.categories[c].count += 1
                elif c.max is None:
                    if v > c.min:
                        self.categories[c].count += 1
                else:
                    if c.min < v <= c.max:
                        self.categories[c].count += 1

            self.raw_values.append(v)
            self.sum += 1

    def calc_percentages(self, sum):

        for c in self.categories.keys():
            if sum > 0:
                self.categories[c].percentage = (float(self.categories[c].count) / float(sum)) * 100
            else:
                self.categories[c].percentage = 0.0

    def calc_raw_percentages(self):

        for c in self.categories.keys():
            if self.sum > 0:
                self.categories[c].percentage = (float(self.categories[c].count) / float(self.sum)) * 100
            else:
                self.categories[c].percentage = 0.0

    def get_percentage(self, test_value):

        for c in self.categories.keys():
            if ((c.min is None and test_value <= c.max) or (c.min < test_value <= c.max) or
                    (c.max is None and test_value > c.min)):
                return self.categories[c].percentage

        return None


class Category(object):
    def __init__(self, label=None):
        self.label = label
        self.count = 0.0
        self.percentage = 0.0

    def json_serialise(self):
        return {
            'label': self.label,
            'count': self.count,
            'percentage': self.percentage
        }

    @classmethod
    def json_deserialise(cls, input_dict):
        category = cls(input_dict['label'])
        category.count = input_dict['count']
        category.percentage = input_dict['percentage']
        return category


class Condition(object):
    def __init__(self, label, group_0, group_1, is_group_0_left):
        self.label = label
        self.group_0 = group_0
        self.group_1 = group_1
        self.is_group_0_left = is_group_0_left
        self.ax_0 = ColumnVector()
        self.ay_0 = ColumnVector()
        self.az_0 = ColumnVector()
        self.ex_0 = PiVector()
        self.ey_0 = PiVector()
        self.ax_1 = ColumnVector()
        self.ay_1 = ColumnVector()
        self.az_1 = ColumnVector()
        self.ex_1 = PiVector()
        self.ey_1 = PiVector()

    def json_serialise(self):
        return {
            'label': self.label,
            'group_0': self.group_0,
            'group_1': self.group_1,
            'is_group_0_left': self.is_group_0_left,
            'ax_0': self.ax_0.json_serialise(),
            'ay_0': self.ay_0.json_serialise(),
            'az_0': self.az_0.json_serialise(),
            'ex_0': self.ex_0.json_serialise(),
            'ey_0': self.ey_0.json_serialise(),
            'ax_1': self.ax_1.json_serialise(),
            'ay_1': self.ay_1.json_serialise(),
            'az_1': self.az_1.json_serialise(),
            'ex_1': self.ex_1.json_serialise(),
            'ey_1': self.ey_1.json_serialise()
        }

    @classmethod
    def json_deserialise(cls, input_dict):
        condition = cls(input_dict['label'], input_dict['group_0'], input_dict['group_1'], input_dict['is_group_0_left'])
        condition.ax_0 = ColumnVector.json_deserialise(input_dict['ax_0'])
        condition.ay_0 = ColumnVector.json_deserialise(input_dict['ay_0'])
        condition.az_0 = ColumnVector.json_deserialise(input_dict['az_0'])
        condition.ex_0 = PiVector.json_deserialise(input_dict['ex_0'])
        condition.ey_0 = PiVector.json_deserialise(input_dict['ey_0'])
        condition.ax_1 = ColumnVector.json_deserialise(input_dict['ax_1'])
        condition.ay_1 = ColumnVector.json_deserialise(input_dict['ay_1'])
        condition.az_1 = ColumnVector.json_deserialise(input_dict['az_1'])
        condition.ex_1 = PiVector.json_deserialise(input_dict['ex_1'])
        condition.ey_1 = PiVector.json_deserialise(input_dict['ey_1'])

        return condition

    def total_sum(self):

        total_0 = (self.ax_0.sum + self.ay_0.sum + self.az_0.sum + self.ex_0.sum + self.ey_0.sum)
        total_1 = (self.ax_1.sum + self.ay_1.sum + self.az_1.sum + self.ex_1.sum + self.ey_1.sum)

        return total_0, total_1

    def total_sum_a(self):
        total_0 = (self.ax_0.sum + self.ay_0.sum + self.az_0.sum)
        total_1 = (self.ax_1.sum + self.ay_1.sum + self.az_1.sum)

        return total_0, total_1

    def total_sum_e(self):

        total_0 = (self.ex_0.sum + self.ey_0.sum)
        total_1 = (self.ex_1.sum + self.ey_1.sum)

        return total_0, total_1

    def add_training_data(self, ax_0_data, ay_0_data, az_0_data, ex_0_data, ey_0_data, ax_1_data, ay_1_data, az_1_data, ex_1_data, ey_1_data):

        self.ax_0.add(ax_0_data)
        self.ay_0.add(ay_0_data)
        self.az_0.add(az_0_data)
        self.ex_0.add(ex_0_data)
        self.ey_0.add(ey_0_data)

        self.ax_1.add(ax_1_data)
        self.ay_1.add(ay_1_data)
        self.az_1.add(az_1_data)
        self.ex_1.add(ex_1_data)
        self.ey_1.add(ey_1_data)

    def calc_percentages(self):

        # total_0, total_1 = self.total_sum()
        total_0a, total_1a = self.total_sum_a()
        total_0e, total_1e = self.total_sum_e()

        self.ax_0.calc_percentages(total_0a)
        self.ay_0.calc_percentages(total_0a)
        self.az_0.calc_percentages(total_0a)
        self.ex_0.calc_percentages(total_0e)
        self.ey_0.calc_percentages(total_0e)

        self.ax_1.calc_percentages(total_1a)
        self.ay_1.calc_percentages(total_1a)
        self.az_1.calc_percentages(total_1a)
        self.ex_1.calc_percentages(total_1e)
        self.ey_1.calc_percentages(total_1e)

    def calc_raw_percentages(self):

        self.ax_0.calc_raw_percentages()
        self.ay_0.calc_raw_percentages()
        self.az_0.calc_raw_percentages()
        self.ex_0.calc_raw_percentages()
        self.ey_0.calc_raw_percentages()

        self.ax_1.calc_raw_percentages()
        self.ay_1.calc_raw_percentages()
        self.az_1.calc_raw_percentages()
        self.ex_1.calc_raw_percentages()
        self.ey_1.calc_raw_percentages()


class Ranking(object):
    def __init__(self):
        self.rank = -1
        self.score = 100.0


class MatchProbability(object):
    def __init__(self, trained_conditions):

        self.ax_0 = ColumnVector()
        self.ay_0 = ColumnVector()
        self.az_0 = ColumnVector()
        self.ex_0 = PiVector()
        self.ey_0 = PiVector()

        self.ax_1 = ColumnVector()
        self.ay_1 = ColumnVector()
        self.az_1 = ColumnVector()
        self.ex_1 = PiVector()
        self.ey_1 = PiVector()
        self.trained_conditions = trained_conditions
        self.condition_ranking = {}

        for t in self.trained_conditions:
            self.condition_ranking[t.label] = Ranking()

    def calc_rankings(self, test_0_ax, test_0_ay, test_0_az, test_0_ex, test_0_ey, test_1_ax, test_1_ay, test_1_az, test_1_ex, test_1_ey):

        self.ax_0.add(test_0_ax)
        self.ay_0.add(test_0_ay)
        self.az_0.add(test_0_az)
        self.ex_0.add(test_0_ex)
        self.ey_0.add(test_0_ey)

        self.ax_1.add(test_1_ax)
        self.ay_1.add(test_1_ay)
        self.az_1.add(test_1_az)
        self.ex_1.add(test_1_ex)
        self.ey_1.add(test_1_ey)

        self.ax_0.calc_raw_percentages()
        self.ay_0.calc_raw_percentages()
        self.az_0.calc_raw_percentages()
        self.ex_0.calc_raw_percentages()
        self.ey_0.calc_raw_percentages()

        self.ax_1.calc_raw_percentages()
        self.ay_1.calc_raw_percentages()
        self.az_1.calc_raw_percentages()
        self.ex_1.calc_raw_percentages()
        self.ey_1.calc_raw_percentages()

        initial_rankings = {}
        full_total = 0
        sr_ax0_list = {}
        sr_ay0_list = {}
        sr_az0_list = {}
        sr_ex0_list = {}
        sr_ey0_list = {}
        sr_ax1_list = {}
        sr_ay1_list = {}
        sr_az1_list = {}
        sr_ex1_list = {}
        sr_ey1_list = {}
        sr_tot_list = {}

        for t in self.trained_conditions:
            sr_ax0_list[t.label] = self.get_spearman_rank(self.ax_0, t.ax_0)
            sr_ay0_list[t.label] = self.get_spearman_rank(self.ay_0, t.ay_0)
            sr_az0_list[t.label] = self.get_spearman_rank(self.az_0, t.az_0)
            sr_ex0_list[t.label] = self.get_spearman_rank(self.ex_0, t.ex_0)
            sr_ey0_list[t.label] = self.get_spearman_rank(self.ey_0, t.ey_0)
            sr_ax1_list[t.label] = self.get_spearman_rank(self.ax_1, t.ax_1)
            sr_ay1_list[t.label] = self.get_spearman_rank(self.ay_1, t.ay_1)
            sr_az1_list[t.label] = self.get_spearman_rank(self.az_1, t.az_1)
            sr_ex1_list[t.label] = self.get_spearman_rank(self.ex_1, t.ex_1)
            sr_ey1_list[t.label] = self.get_spearman_rank(self.ey_1, t.ey_1)

            sr_tot_list[t.label] = (sr_ax0_list[t.label][0] + sr_ay0_list[t.label][0] +
                                    sr_az0_list[t.label][0] + sr_ex0_list[t.label][0] +
                                    (2.0 * sr_ey0_list[t.label][0]) + sr_ax1_list[t.label][0] +
                                    sr_ay1_list[t.label][0] + sr_az1_list[t.label][0] +
                                    sr_ex1_list[t.label][0] + (2.0 * sr_ey1_list[t.label][0])) * 8.33  # if perfectly correlated, will be 100.00

        for rl, tl in initial_rankings.items():
            if full_total > 0:
                if tl == 0:
                    initial_rankings[rl] = 100.00
                else:
                    initial_rankings[rl] = (tl / full_total) * 100
            else:
                initial_rankings[rl] = 0.00

        sorted_rankings = sorted(sr_tot_list, key=sr_tot_list.__getitem__, reverse=True)

        rk = 0
        for c in sorted_rankings:
            self.condition_ranking[c].rank = rk
            self.condition_ranking[c].score = sr_tot_list[c]
            rk += 1

    @staticmethod
    def get_total_diff(cv, tcv):

        total_diff = 0.0

        for tc, v in tcv.categories.items():
            cv_perc = 0.00
            for cc, vc in cv.categories.items():
                if cc.max == tc.max and cc.min == tc.min:
                    cv_perc = vc.percentage
            total_diff += ((v.percentage / 100) * abs(v.percentage - cv_perc))

        return total_diff

    @staticmethod
    def get_spearman_rank(cv, tcv):

        c_list = []
        t_list = []

        for tc in sorted(tcv.categories.keys(), key=lambda x: x.label):
            t_list.append(tcv.categories[tc].percentage)

        for c in sorted(cv.categories.keys(), key=lambda x: x.label):
            c_list.append(cv.categories[c].percentage)

        spearman_result = stats.spearmanr(c_list, t_list)

        return spearman_result


class MatchResult(object):
    def __init__(self, file_name, expected_value, actual_value, correct):
        self.file_name = file_name
        self.expected_value = expected_value
        self.actual_value = actual_value
        self.correct = correct


class MatchAggregation(object):
    def __init__(self):
        self.group_1_results = []
        self.group_2_results = []
        self.group_3_results = []
        self.group_4_results = []
        self.correct_results = []
        self.incorrect_results = []
        self.groups = []
        self.group_1 = ['BCF', 'BCH', 'ACE', 'ACG']
        self.group_2 = ['BDF', 'BDH', 'ADE', 'ADG']
        self.group_3 = ['ACF', 'ACH', 'BCE', 'BCG']
        self.group_4 = ['ADF', 'ADH', 'BDE', 'BDG']
        self.group_1_correct_percent = 0.0
        self.group_2_correct_percent = 0.0
        self.group_3_correct_percent = 0.0
        self.group_4_correct_percent = 0.0
        self.group_1_count = 0.0
        self.group_2_count = 0.0
        self.group_3_count = 0.0
        self.group_4_count = 0.0
        self.code_accuracy_dictionary = {}
        self.code_count_dictionary = {}

    def get_accuracy_for_code(self, code):

        total = 0
        incorrect = 0

        for c in range(0, len(self.group_1_results)):
            if code in self.group_1_results[c].file_name:
                total += 1
                if (not self.group_1_results[c].correct or not self.group_2_results[c].correct or
                    not self.group_3_results[c].correct or not self.group_4_results[c].correct):
                    incorrect += 1

        return (float(total - incorrect) / float(total)) * 100

    def grade_results(self):
        for gr in self.groups:
            correct = list(g for g in self.correct_results if g.expected_value == gr)
            incorrect = list(g for g in self.incorrect_results if g.expected_value == gr)
            correct_percent = float(len(correct) / float(len(correct) + len(incorrect)))
            count = len(correct) + len(incorrect)
            self.code_accuracy_dictionary[gr] = correct_percent * 100
            self.code_count_dictionary[gr] = count

    def add_ranking(self, file_name, condition_ranking_list):
        for c in condition_ranking_list:
            if condition_ranking_list[c].rank == 0:
                grp = self.get_group_combo(file_name)

                if grp not in self.groups:
                    self.groups.append(grp)

                if grp == c:
                    self.correct_results.append(MatchResult(file_name, grp, c, True))
                else:
                    self.incorrect_results.append(MatchResult(file_name, grp, c, False))

    def name_in_group_1(self, name):

        if name in self.group_1:
            return True
        else:
            return False

    def name_in_group_2(self, name):

        if name in self.group_2:
            return True
        else:
            return False

    def name_in_group_3(self, name):

        if name in self.group_3:
            return True
        else:
            return False

    def name_in_group_4(self, name):

        if name in self.group_4:
            return True
        else:
            return False

    def group_1_in_name(self, name):

        for g in self.group_1:
            if g in name:
                return True
        return False

    def group_2_in_name(self, name):

        for g in self.group_2:
            if g in name:
                return True
        return False

    def group_3_in_name(self, name):

        for g in self.group_3:
            if g in name:
                return True
        return False

    def group_4_in_name(self, name):

        for g in self.group_4:
            if g in name:
                return True
        return False

    @staticmethod
    def get_group_combo(name):
        if 'both_down_strap' in name:
                return 'ade_ade_210'

        if 'ADE' in name:
            return 'ade_ade_210'

        if 'right_up_left_down' in name:
            return 'ade_ace_012'

        if 'both_optimal_orientation' in name:
            return 'ace_ace_210'

        if 'both_up_strap' in name or 'ACE' in name:
            return 'ace_ace_012'

        if 'both_led_skin_side_strap' in name or 'BCE' in name:
            return 'bce_bce_012'

        if 'both_side_ankle_strap' in name:
            return 'ace_ace_210'

        if 'ACG' in name:
            return 'ace_ace_012'

        if 'both_inside_ankle_strap' in name or 'ACF' in name:
            return 'acf_acf_012'

        if 'BCG' in name:
            return 'bce_bce_012'

        if 'BCH' in name:
            return 'bcf_bcf_012'

        if 'BDH' in name:
            return 'bdf_bdf_210'

        if 'BDG' in name:
            return 'bde_bde_210'

        if 'ADG' in name:
            return 'ade_ade_210'

        if 'BDE' in name:
            return 'bde_bde_210'

        if 'ADF' in name:
            return 'adf_adf_210'

        if 'BCF' in name:
            return 'bcf_bcf_012'

        if 'BDF' in name:
            return 'bdf_bdf_210'

        if 'ACH' in name:
            return 'acf_acf_012'

        if 'ADH' in name:
            return 'adf_adf_210'

        return ''
