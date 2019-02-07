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
        self.total_left_sum = 0
        self.total_right_sum = 0
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
