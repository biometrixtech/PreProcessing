from enum import Enum


class MovementPatternStats(object):
    def __init__(self, side, cadence):
        self.side = side
        self.cadence = cadence
        self.elasticity = 0.0
        self.elasticity_t = 0.0
        self.elasticity_se = 0.0
        self.obs = 0.0
        self.adf = 0.0
        self.adf_critical = 0.0


class MovementPatternType(Enum):
    apt_ankle_pitch = 0
    hip_drop_apt = 1
    hip_drop_pva = 2
    knee_valgus_hip_drop = 3
    knee_valgus_pva = 4
    knee_valgus_apt = 5


class MovementPatterns(object):
    def __init__(self):
        self.user_id = ""
        self.session_id = ""
        self.apt_ankle_pitch_stats = []
        self.hip_drop_apt_stats = []
        self.hip_drop_pva_stats = []
        self.knee_valgus_hip_drop_stats = []
        self.knee_valgus_pva_stats = []
        self.knee_valgus_apt_stats = []

    def get_elasticity(self, side, movement_pattern_type):

        stats = []

        if movement_pattern_type == MovementPatternType.apt_ankle_pitch:

            stats = [s.elasticity for s in self.apt_ankle_pitch_stats if s.side == side and abs(s.elasticity_t) >= 2.0 and s.obs >= 100]

        elif movement_pattern_type == MovementPatternType.hip_drop_apt:

            stats = [s.elasticity for s in self.hip_drop_apt_stats if s.side == side and abs(s.elasticity_t) >= 2.0 and s.obs >= 100]

        elif movement_pattern_type == MovementPatternType.hip_drop_pva:

            stats = [s.elasticity for s in self.hip_drop_pva_stats if
                     s.side == side and abs(s.elasticity_t) >= 2.0 and s.obs >= 100]

        elif movement_pattern_type == MovementPatternType.knee_valgus_hip_drop:

            stats = [s.elasticity for s in self.knee_valgus_hip_drop_stats if
                     s.side == side and abs(s.elasticity_t) >= 2.0 and s.obs >= 100]

        elif movement_pattern_type == MovementPatternType.knee_valgus_pva:

            stats = [s.elasticity for s in self.knee_valgus_pva_stats if
                     s.side == side and abs(s.elasticity_t) >= 2.0 and s.obs >= 100]

        elif movement_pattern_type == MovementPatternType.knee_valgus_apt:

            stats = [s.elasticity for s in self.knee_valgus_apt_stats if
                     s.side == side and abs(s.elasticity_t) >= 2.0 and s.obs >= 100]

        if len(stats) > 0:
            stats = sorted(stats, key=lambda x: abs(x), reverse=True)
            return stats[0]
        else:
            return 0.0

    def get_adf(self, side, movement_pattern_type):

        stats = []

        if movement_pattern_type == MovementPatternType.apt_ankle_pitch:

            stats = [s.adf for s in self.apt_ankle_pitch_stats if s.side == side and s.adf <= s.adf_critical and s.obs >= 100]

        if len(stats) > 0:
            stats = sorted(stats, key=lambda x: x)
            return stats[0]
        else:
            return 0.0


