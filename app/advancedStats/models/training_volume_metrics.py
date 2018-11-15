class SessionTrainingVolume(object):
    def __init__(self):
        self.accumulated_grf = 0.0
        self.cma = 0.0
        self.accumulated_peak_vertical_grf = 0.0
        self.active_time = 0.0
        self.ground_contact_time = 0.0
        self.intensity_bands = None
        self.grf_bands = None
        self.stance_bands = None
        self.left_right_bands = None


class LowModHighBands(object):
    def __init__(self):
        # seconds (active time) by low, mod, high bands
        self.low_seconds = 0
        self.low_seconds_percentage = 0.0
        self.moderate_seconds = 0
        self.moderate_seconds_percentage = 0.0
        self.high_seconds = 0
        self.high_seconds_percentage = 0.0
        self.total_seconds = 0

        # accumulated grf by low, mod, high bands
        self.low_accumulated_grf = 0.0
        self.low_accumulated_grf_percentage = 0.0
        self.moderate_accumulated_grf = 0.0
        self.moderate_accumulated_grf_percentage = 0.0
        self.high_accumulated_grf = 0.0
        self.high_accumulated_grf_percentage = 0.0
        self.total_accumulated_grf = 0.0

        # cma by low, mod, high bands
        self.low_cma = 0.0
        self.low_cma_percentage = 0.0
        self.moderate_cma = 0.0
        self.moderate_cma_percentage = 0.0
        self.high_cma = 0.0
        self.high_cma_percentage = 0.0
        self.total_cma = 0.0

        # accumulated_peak_vertical_grf by low, mod, high bands
        self.low_accumulated_peak_vGRF = 0.0
        self.low_accumulated_peak_vGRF_percentage = 0.0
        self.moderate_accumulated_peak_vGRF = 0.0
        self.moderate_accumulated_peak_vGRF_percentage = 0.0
        self.high_accumulated_peak_vGRF = 0.0
        self.high_accumulated_peak_vGRF_percentage = 0.0
        self.total_accumulated_peak_vGRF = 0.0

        # cma by low, mod, high bands
        self.low_gct = 0.0
        self.low_gct_percentage = 0.0
        self.moderate_gct = 0.0
        self.moderate_gct_percentage = 0.0
        self.high_gct = 0.0
        self.high_gct_percentage = 0.0
        self.total_gct = 0.0


class StanceBands(object):
    def __init__(self):
        # seconds (active time) by single, double bands
        self.single_seconds = 0
        self.single_seconds_percentage = 0.0
        self.double_seconds = 0
        self.double_seconds_percentage = 0.0
        self.total_seconds = 0

        # accumulated grf by single, double bands
        self.single_accumulated_grf = 0.0
        self.single_accumulated_grf_percentage = 0.0
        self.double_accumulated_grf = 0.0
        self.double_accumulated_grf_percentage = 0.0
        self.total_accumulated_grf = 0.0

        # cma by single, double bands
        self.single_cma = 0.0
        self.single_cma_percentage = 0.0
        self.double_cma = 0.0
        self.double_cma_percentage = 0.0
        self.total_cma = 0.0

        # accumulated_peak_vertical_grf by single, double bands
        self.single_accumulated_peak_vGRF = 0.0
        self.single_accumulated_peak_vGRF_percentage = 0.0
        self.double_accumulated_peak_vGRF = 0.0
        self.double_accumulated_peak_vGRF_percentage = 0.0
        self.total_accumulated_peak_vGRF = 0.0

        # cma by single, double bands
        self.single_gct = 0.0
        self.single_gct_percentage = 0.0
        self.double_gct = 0.0
        self.double_gct_percentage = 0.0
        self.total_gct = 0.0


class LeftRightBands(object):
    def __init__(self):
        # seconds (active time) by left/right bands
        self.left_seconds = 0
        self.left_seconds_percentage = 0.0
        self.right_seconds = 0
        self.right_seconds_percentage = 0.0
        self.total_seconds = 0

        # accumulated grf by left/right bands
        self.left_accumulated_grf = 0.0
        self.left_accumulated_grf_percentage = 0.0
        self.right_accumulated_grf = 0.0
        self.right_accumulated_grf_percentage = 0.0
        self.total_accumulated_grf = 0.0

        # cma by left/right bands
        self.left_cma = 0.0
        self.left_cma_percentage = 0.0
        self.right_cma = 0.0
        self.right_cma_percentage = 0.0
        self.total_cma = 0.0

        # accumulated_peak_vertical_grf by left/right bands
        self.left_accumulated_peak_vGRF = 0.0
        self.left_accumulated_peak_vGRF_percentage = 0.0
        self.right_accumulated_peak_vGRF = 0.0
        self.right_accumulated_peak_vGRF_percentage = 0.0
        self.total_accumulated_peak_vGRF = 0.0

        # cma by left/right bands
        self.left_gct = 0.0
        self.left_gct_percentage = 0.0
        self.right_gct = 0.0
        self.right_gct_percentage = 0.0
        self.total_gct = 0.0
