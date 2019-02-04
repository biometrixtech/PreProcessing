
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
        self.adduc_motion_covered_tot_hip = 0.0
        self.adduc_motion_covered_pos_hip = 0.0
        self.adduc_motion_covered_neg_hip = 0.0
        self.flex_rom_hip = 0.0
        self.flex_motion_covered_tot_hip = 0.0
        self.flex_motion_covered_pos_hip = 0.0
        self.flex_motion_covered_neg_hip = 0.0