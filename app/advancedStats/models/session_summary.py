class session_summary(object):
    """description of class"""
    def __init__(self, load_descriptor=""):
        self.load_descriptor = load_descriptor
        self.peak_grf_symmetry = None
        self.accumulated_grf_symmetry = None
        self.ground_contact_time_symmetry = None
        self.load_rate_symmetry = None
        self.contralateral_hip_drop_symmetry = 0
        self.pronation_symmetry = 0
        self.supination_symmetry = 0
        self.land_time_symmetry = 0


