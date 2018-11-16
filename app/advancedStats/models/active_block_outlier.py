class ActiveBlockOutlier(object):
    def __init__(self, id=None):
        self.active_block_id = id
        self.attribute_name = ""
        self.label = ""
        self.complexity_level = ""
        self.orientation = ""
        self.start_time = None
        self.end_time = None
        #self.grf_level = ""
        #self.cma_level = ""
        self.z_score = 0
        self.raw_value = 0
        self.time_block = 0


