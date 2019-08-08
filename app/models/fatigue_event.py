
class FatigueEvent(object):
    def __init__(self, cma_level, grf_level):
        self.active_block_id = ""
        self.attribute_label = ""
        self.attribute_name = ""
        self.cma_level = cma_level.replace("CMA", "")
        self.complexity_level = ""
        self.count = 1
        self.cumulative_end_time = None
        self.grf_level = grf_level.replace("Grf", "")
        self.orientation = ""
        self.raw_value = 0.0
        self.stance = ""
        self.time_block = ""
        self.z_score = 0.0
        self.significant = 0
