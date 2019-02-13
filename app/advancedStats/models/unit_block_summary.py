class unit_block_summary(object):
    """description of class"""
    def __init__(self,active_block_id='', unit_block_number=0):
        self.active_block_id=active_block_id
        self.unit_block_number = unit_block_number
        self.peak_grf_symmetry = None
        self.accumulated_grf_symmetry = None
        self.ground_contact_time_symmetry = None
        self.load_rate_symmetry = None
        self.contralateral_hip_drop_symmetry = 0
        self.pronation_symmetry = 0
        self.supination_symmetry = 0
        self.land_time_symmetry = 0


