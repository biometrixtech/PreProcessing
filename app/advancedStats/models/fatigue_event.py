class FatigueEvent(object):
    def __init__(self, grf_level, cma_level):
        self.stance = ""
        self.active_block_id = ""
        self.complexity_level = ""
        self.grf_level = grf_level.replace("Grf", "")
        self.cma_level = cma_level.replace("CMA", "")
        self.attribute_name = ""
        self.attribute_label = ""
        self.orientation = ""
        self.cumulative_end_time = None
        self.z_score = 0.0
        self.raw_value = 0.0


