from datetime import datetime

import pandas
from scipy import stats
from app.advancedStats.models.variable import CategorizationVariable
from advancedStats.models.unit_block import UnitBlock
from advancedStats.summary_analysis import get_unit_blocks
from app.advancedStats.models.asymmetry import MovementAsymmetry, LoadingAsymmetry, LoadingAsymmetrySummary, SessionAsymmetry


class AsymmetryProcessor(object):
    def __init__(self, user_id, event_date, session_id, single_complexity_matrix, double_complexity_matrix):
        self.user_id = user_id
        self.event_date = event_date
        self.session_id = session_id
        self.single_complexity_matrix = single_complexity_matrix
        self.double_complexity_matrix = double_complexity_matrix

    def get_session_asymmetry(self):

        asym = SessionAsymmetry(self.user_id, self.event_date, self.session_id)
        asym.loading_asymmetries = self.get_loading_asymmetries()
        asym.movement_asymmetries = self.get_movement_asymmetries()

        # relative magnitude
        var_list = []
        var_list.append(CategorizationVariable("peak_grf_perc_diff_lf", 0, 5, 5, 10, 10, 100, False))
        var_list.append(CategorizationVariable("peak_grf_perc_diff_rf", 0, 5, 5, 10, 10, 100, False))
        var_list.append(CategorizationVariable("gct_perc_diff_lf", 0, 5, 5, 10, 10, 100, False))
        var_list.append(CategorizationVariable("gct_perc_diff_rf", 0, 5, 5, 10, 10, 100, False))
        
        # var_list.append(CategorizationVariable("peak_grf_gct_left", 0, 5, 5, 10, 10, 100, False))
        # var_list.append(CategorizationVariable("peak_grf_gct_right", 0, 5, 5, 10, 10, 100, False))
        var_list.append(CategorizationVariable("peak_grf_gct_left_over", 0, 2.5, 2.5, 5, 5, 100, False))
        var_list.append(CategorizationVariable("peak_grf_gct_left_under", 0, 2.5, 2.5, 5, 5, 10, False))
        var_list.append(CategorizationVariable("peak_grf_gct_right_over", 0, 2.5, 2.5, 5, 5, 100, False))
        var_list.append(CategorizationVariable("peak_grf_gct_right_under", 0, 2.5, 2.5, 5, 5, 10, False))

        asym.loading_asymmetry_summaries = self.get_variable_asymmetry_summaries(self.user_id, self.event_date, var_list)

        return asym

    def get_loading_asymmetries(self):

        events = []

        for keys, mcsl in self.single_complexity_matrix.items():
            event = self.get_loading_asymmetry("total_grf", mcsl, mcsl.complexity_level, mcsl.cma_level, mcsl.grf_level,
                                               "Single")

            events.append(event)

        for keys, mcdl in self.double_complexity_matrix.items():
            event = self.get_loading_asymmetry("total_grf", mcdl, mcdl.complexity_level, mcdl.cma_level, mcdl.grf_level,
                                               "Double")

            events.append(event)

        return events

    def get_loading_asymmetry(self, attribute, complexity_matrix_cell, complexity_level, cma_level, grf_level, stance):

        asym = LoadingAsymmetry(complexity_level, cma_level, grf_level, stance)
        left_sum = complexity_matrix_cell.get_steps_sum(attribute, complexity_matrix_cell.left_steps)
        right_sum = complexity_matrix_cell.get_steps_sum(attribute, complexity_matrix_cell.right_steps)
        asym.total_left_right_sum = left_sum + right_sum

        if len(complexity_matrix_cell.left_steps) == 0 or len(complexity_matrix_cell.right_steps) == 0:
            asym.training_asymmetry = left_sum - right_sum
        else:
            asym.kinematic_asymmetry = left_sum - right_sum
        asym.total_asymmetry = asym.training_asymmetry + asym.kinematic_asymmetry
        if asym.total_left_right_sum > 0:
            asym.total_percent_asymmetry = (asym.total_asymmetry / asym.total_left_right_sum) * 100

        complexity_matrix_summary = complexity_matrix_cell.get_summary()

        asym.left_step_count = complexity_matrix_summary.left_step_count
        asym.right_step_count = complexity_matrix_summary.right_step_count
        asym.total_steps = complexity_matrix_summary.total_steps
        asym.step_asymmetry = asym.left_step_count - asym.right_step_count
        if asym.total_steps > 0:
            asym.step_count_percent_asymmetry = (asym.step_asymmetry / float(asym.total_steps)) * 100

        asym.ground_contact_time_left = complexity_matrix_summary.left_duration
        asym.ground_contact_time_right = complexity_matrix_summary.right_duration
        asym.total_ground_contact_time = complexity_matrix_summary.total_duration
        asym.ground_contact_time_asymmetry = asym.ground_contact_time_left - asym.ground_contact_time_right
        if asym.total_ground_contact_time > 0:
            asym.ground_contact_time_percent_asymmetry = (asym.ground_contact_time_asymmetry / float(asym.total_ground_contact_time)) * 100

        asym.left_avg_accumulated_grf_sec = complexity_matrix_summary.left_avg_accumulated_grf_sec
        asym.right_avg_accumulated_grf_sec = complexity_matrix_summary.right_avg_accumulated_grf_sec
        asym.accumulated_grf_sec_asymmetry = asym.left_avg_accumulated_grf_sec - asym.right_avg_accumulated_grf_sec
        if asym.right_avg_accumulated_grf_sec > 0:
            asym.accumulated_grf_sec_percent_asymmetry = (asym.left_avg_accumulated_grf_sec /
                                                          float(asym.right_avg_accumulated_grf_sec)) * 100

        return asym

    def get_movement_asymmetries(self):

        events = []

        for keys, mcsl in self.single_complexity_matrix.items():
            event = self.get_movement_asymmetry(mcsl.complexity_level, mcsl.cma_level, mcsl.grf_level, "Single",
                                                mcsl.left_steps, mcsl.right_steps)

            events.append(event)

        for keys, mcdl in self.double_complexity_matrix.items():
            event = self.get_movement_asymmetry(mcdl.complexity_level, mcdl.cma_level, mcdl.grf_level, "Double",
                                                mcdl.left_steps, mcdl.right_steps)

            events.append(event)

        return events

    def get_movement_asymmetry(self, complexity_level, cma_level, grf_level, stance, left_steps, right_steps):

        event = MovementAsymmetry(complexity_level, cma_level, grf_level, stance)
        event.adduc_ROM = self.get_steps_f_test("adduc_ROM", left_steps, right_steps)
        event.adduc_motion_covered = self.get_steps_f_test("adduc_motion_covered", left_steps, right_steps)
        event.flex_ROM = self.get_steps_f_test("flex_ROM", left_steps, right_steps)
        event.flex_motion_covered = self.get_steps_f_test("flex_motion_covered", left_steps, right_steps)

        event.adduc_ROM_hip = self.get_steps_f_test("adduc_ROM_hip", left_steps, right_steps)
        event.adduc_motion_covered_hip = self.get_steps_f_test("adduc_motion_covered_hip", left_steps, right_steps)
        event.flex_ROM_hip = self.get_steps_f_test("flex_ROM_hip", left_steps, right_steps)
        event.flex_motion_covered_hip = self.get_steps_f_test("flex_motion_covered_hip", left_steps, right_steps)

        return event

    def get_steps_f_test(self, attribute, step_list_x, step_list_y):
        value_list_x = []
        value_list_y = []
        for item in step_list_x:
            if(getattr(item,attribute) is not None):
                value_list_x.append(getattr(item,attribute))
        for item in step_list_y:
            if(getattr(item,attribute) is not None):
                value_list_y.append(getattr(item,attribute))
        if(len(value_list_x)==0 or len(value_list_y)==0):
            return 0
        else:
            try:
                r,p = stats.kruskal(value_list_x, value_list_y)
                if(p<=.05):
                    #write out values for temp analysis
                    #x_frame = pandas.DataFrame(value_list_x)
                    #y_frame = pandas.DataFrame(value_list_y)
                    #x_frame.to_csv('C:\\UNC\\v6\\f_test_x_'+self.complexity_level+'_'+self.grf_level+'_'+self.cma_level+'_'+attribute+'.csv',sep=',')
                    #y_frame.to_csv('C:\\UNC\\v6\\f_test_y_'+self.complexity_level+'_'+self.grf_level+'_'+self.cma_level+'_'+attribute+'.csv',sep=',')
                    return r
                else:
                    return None
            except ValueError:
                return None

    def get_variable_asymmetry_summaries(self, user, date, variable_list):

        mongo_unit_blocks = get_unit_blocks(user, date)

        cumulative_end_time = 0

        variable_matrix = {}

        for cat_variable in variable_list:
            variable_matrix[cat_variable.name] = LoadingAsymmetrySummary()

        if len(mongo_unit_blocks) > 0:

            sessionTimeStart = mongo_unit_blocks[0].get('unitBlocks')[0].get('timeStart')
            try:
                sessionTimeStart_object = datetime.strptime(sessionTimeStart, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                sessionTimeStart_object = datetime.strptime(sessionTimeStart, '%Y-%m-%d %H:%M:%S')

            for ub in mongo_unit_blocks:
                if len(ub) > 0:

                    unit_bock_count = len(ub.get('unitBlocks'))

                    for n in range(0, unit_bock_count):
                        ubData = ub.get('unitBlocks')[n]
                        ub_rec = UnitBlock(ubData)

                        timeEnd = ub.get('unitBlocks')[n].get('timeEnd')

                        try:
                            timeEnd_object = datetime.strptime(timeEnd, '%Y-%m-%d %H:%M:%S.%f')
                        except ValueError:
                            timeEnd_object = datetime.strptime(timeEnd, '%Y-%m-%d %H:%M:%S')

                        cumulative_end_time = (timeEnd_object - sessionTimeStart_object).seconds

                        for variable, summary in variable_matrix.items():
                            variable_matrix[variable] = self.calc_loading_asymmetry_summary(summary, variable, variable_list, ub_rec)

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

    def calc_loading_asymmetry_summary(self, summary, variable, variable_list, unit_block_data):

        # summary = LoadingAsymmetrySummary()

        cat_variable = None

        for v in range(0, len(variable_list)):
            if variable_list[v].name == variable:
                cat_variable = variable_list[v]

        variable_value = getattr(unit_block_data, cat_variable.name)

        summary.variable_name = cat_variable.name

        if variable_value is not None:
            if cat_variable.invereted == False:
                if variable_value > cat_variable.yellow_high:
                    summary.red_time += unit_block_data.duration
                    summary.red_grf += unit_block_data.total_grf
                    summary.red_cma += unit_block_data.total_accel
                if variable_value > cat_variable.green_high and variable_value <=cat_variable.yellow_high:
                    summary.yellow_time += unit_block_data.duration
                    summary.yellow_grf += unit_block_data.total_grf
                    summary.yellow_cma += unit_block_data.total_accel
                if variable_value >= cat_variable.green_low and variable_value <= cat_variable.green_high:
                    summary.green_time += unit_block_data.duration
                    summary.green_grf += unit_block_data.total_grf
                    summary.green_cma += unit_block_data.total_accel
            else:
                if variable_value > cat_variable.yellow_high:
                    summary.green_time += unit_block_data.duration
                    summary.green_grf += unit_block_data.total_grf
                    summary.green_cma += unit_block_data.total_accel
                if variable_value > cat_variable.red_high and variable_value <=cat_variable.yellow_high:
                    summary.yellow_time += unit_block_data.duration
                    summary.yellow_grf += unit_block_data.total_grf
                    summary.yellow_cma += unit_block_data.total_accel
                if variable_value >= cat_variable.red_low and variable_value <= cat_variable.red_high:
                    summary.red_time += unit_block_data.duration
                    summary.red_grf += unit_block_data.total_grf
                    summary.red_cma += unit_block_data.total_accel

        summary.total_time += unit_block_data.duration
        summary.total_grf += unit_block_data.total_grf
        summary.total_cma += unit_block_data.total_accel

        return summary