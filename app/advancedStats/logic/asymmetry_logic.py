from scipy import stats
from app.advancedStats.models.asymmetry import MovementAsymmetry, LoadingAsymmetry, SessionAsymmetry


class AsymmetryProcessor(object):
    def __init__(self, user_id, event_date, session_id, single_complexity_matrix, double_complexity_matrix):
        self.user_id = user_id
        self.event_date = event_date
        self.session_id = session_id
        self.single_complexity_matrix = single_complexity_matrix
        self.double_complexity_matrix = double_complexity_matrix

    def get_session_asymmetry(self, user_id, event_date, session_id):

        asym = SessionAsymmetry(user_id, event_date, session_id)
        asym.loading_asymmetries = self.get_loading_asymmetries()
        asym.movement_asymmetries = self.get_movement_asymmetries()
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
        asym.total_sum = left_sum + right_sum

        if len(complexity_matrix_cell.left_steps) == 0 or len(complexity_matrix_cell.right_steps) == 0:
            asym.training_asymmetry = left_sum - right_sum
        else:
            asym.kinematic_asymmetry = left_sum - right_sum
        asym.total_asymmetry = asym.training_asymmetry + asym.kinematic_asymmetry
        if asym.total_sum > 0:
            asym.total_percent_asymmetry = (asym.total_asymmetry / asym.total_sum) * 100

        complexity_matrix_summary = complexity_matrix_cell.get_summary()

        asym.left_step_count = complexity_matrix_summary.left_step_count
        asym.right_step_count = complexity_matrix_summary.right_step_count
        asym.total_steps = complexity_matrix_summary.total_steps
        asym.step_asymmetry = asym.left_step_count - asym.right_step_count
        if asym.total_steps > 0:
            asym.step_count_percent_asymmetry = (asym.step_asymmetry / asym.total_steps) * 100

        asym.left_duration = complexity_matrix_summary.left_duration
        asym.right_duration = complexity_matrix_summary.right_duration
        asym.total_duration = complexity_matrix_summary.total_duration
        asym.duration_asymmetry = asym.left_duration = asym.right_duration
        if asym.total_duration > 0:
            asym.duration_percent_asymmetry = (asym.duration_asymmetry / asym.total_duration) * 100

        asym.left_avg_accumulated_grf_sec = complexity_matrix_summary.left_avg_accumulated_grf_sec
        asym.right_avg_accumulated_grf_sec = complexity_matrix_summary.right_avg_accumulated_grf_sec
        asym.accumulated_grf_sec_asymmetry = asym.left_avg_accumulated_grf_sec - asym.right_avg_accumulated_grf_sec
        if asym.right_avg_accumulated_grf_sec > 0:
            asym.accumulated_grf_sec_percent_asymmetry = (asym.left_avg_accumulated_grf_sec /
                                                          asym.right_avg_accumulated_grf_sec) * 100

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