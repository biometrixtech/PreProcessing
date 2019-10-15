class MovementPatternStats(object):
    def __init__(self, side, cadence):
        self.side = side
        self.cadence = cadence
        self.elasticity = 0.0
        self.elasticity_t = 0.0
        self.elasticity_se = 0.0
        self.elasticity_obs = 0.0
        self.elasticity_adf = 0.0
        self.elasticity_adf_critical = 0.0


class MovementPattern(object):
    def __init__(self):
        self.user_id = ""
        self.session_id = ""
        self.apt_ankle_pitch_stats = []
