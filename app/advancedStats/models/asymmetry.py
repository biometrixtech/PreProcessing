class LoadingAsymmetry(object):
    """description of class"""
    def __init__(self, complexity_level, cma_level, grf_level, stance, training_asymmetry=0, kinematic_asymmetry=0):
        self.variable = ""
        self.complexity_level = complexity_level
        self.cma_level = cma_level.replace("CMA", "")
        self.grf_level = grf_level.replace("Grf", "")
        self.stance = stance
        self.training_asymmetry = 0
        self.kinematic_asymmetry = 0
        self.total_asymmetry = self.training_asymmetry+self.kinematic_asymmetry
        self.total_left_right_sum = 0
        self.total_percent_asymmetry = None
        self.left_step_count = 0
        self.right_step_count = 0
        self.total_steps = 0
        self.step_asymmetry = 0.0
        self.step_count_percent_asymmetry = None
        self.ground_contact_time_left = 0
        self.ground_contact_time_right = 0
        self.total_ground_contact_time = 0
        self.ground_contact_time_asymmetry = 0.0
        self.ground_contact_time_percent_asymmetry = None
        self.left_avg_accumulated_grf_sec = 0
        self.right_avg_accumulated_grf_sec = 0
        self.accumulated_grf_sec_asymmetry = 0.0
        self.accumulated_grf_sec_percent_asymmetry = None


class LoadingAsymmetrySummary(object):
    def __init__(self):
        self.variable_name = ""
        self.red_grf = 0.0
        self.red_grf_percent = 0.0
        self.red_cma = 0.0
        self.red_cma_percent = 0.0
        self.red_time = 0.0
        self.red_time_percent = 0.0
        self.yellow_grf = 0.0
        self.yellow_grf_percent = 0.0
        self.yellow_cma = 0.0
        self.yellow_cma_percent = 0.0
        self.yellow_time = 0.0
        self.yellow_time_percent = 0.0
        self.green_grf = 0.0
        self.green_grf_percent = 0.0
        self.green_cma = 0.0
        self.green_cma_percent = 0.0
        self.green_time = 0.0
        self.green_time_percent = 0.0
        self.total_grf = 0.0
        self.total_cma = 0.0
        self.total_time = 0.0
        self.total_session_time = 0.0


class MovementAsymmetry(object):
    def __init__(self, complexity_level, cma_level, grf_level, stance):
        self.complexity_level = complexity_level
        self.stance = stance
        self.cma_level = cma_level.replace("CMA", "")
        self.grf_level = grf_level.replace("Grf", "")
        self.adduc_rom = 0.0
        self.adduc_motion_covered = 0.0
        self.flex_rom = 0.0
        self.flex_motion_covered = 0.0
        self.adduc_rom_hip = 0.0
        self.adduc_motion_covered_hip = 0.0
        self.flex_rom_hip = 0.0
        self.flex_motion_covered_hip = 0.0


class SessionAsymmetry(object):
    def __init__(self, user_id, event_date, session_id):
        self.user_id = user_id
        self.event_date = event_date
        self.session_id = session_id
        self.movement_asymmetries = None
        self.loading_asymmetries = None

        # Relative Magnitude
        self.loading_asymmetry_summaries = None


