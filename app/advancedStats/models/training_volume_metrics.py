class SessionTrainingVolume(object):
    def __init__(self):
        self.accumulated_grf = 0.0
        self.cma = 0.0
        self.average_peak_vertical_grf_lf = 0.0
        self.average_peak_vertical_grf_rf = 0.0
        self.average_peak_acceleration = 0.0
        self.average_total_GRF = 0.0
        self.active_time = 0.0
        self.ground_contact_time_left = 0.0
        self.ground_contact_time_right = 0.0
        self.intensity_bands = None
        self.grf_bands = None
        self.stance_bands = None
        self.left_right_bands = None


class CombinedReportingBand(object):
    def __init__(self, descriptor):
        self.descriptor = descriptor
        self.seconds = 0
        self.seconds_percentage = 0.0
        self.accumulated_grf = 0.0
        self.accumulated_grf_percentage = 0.0
        self.cma = 0.0
        self.cma_percentage = 0.0


class SideReportingBand(object):
    def __init__(self, descriptor, orientation):
        self.descriptor = descriptor
        self.orientation = orientation
        self.average_peak_vGRF = 0.0
        self.low_average_GRF = 0.0
        self.low_average_accel = 0.0
        self.low_gct = 0.0
        self.low_gct_percentage = 0.0


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

        # avg_peak_vertical_grf by low, mod, high bands
        self.low_average_peak_vGRF_lf = 0.0
        self.moderate_average_peak_vGRF_lf = 0.0
        self.high_average_peak_vGRF_lf = 0.0
        self.total_average_peak_vGRF_lf = 0.0

        self.low_average_peak_vGRF_rf = 0.0
        self.moderate_average_peak_vGRF_rf = 0.0
        self.high_average_peak_vGRF_rf = 0.0
        self.total_average_peak_vGRF_rf = 0.0

        # avg_grf by low, mod, high bands
        self.low_average_GRF_lf = 0.0
        self.moderate_average_GRF_lf = 0.0
        self.high_average_GRF_lf = 0.0
        self.total_average_GRF_lf = 0.0

        self.low_average_GRF_rf = 0.0
        self.moderate_average_GRF_rf = 0.0
        self.high_average_GRF_rf = 0.0
        self.total_average_GRF_rf = 0.0

        # avg_accel by low, mod, high bands
        self.low_average_accel_lf = 0.0
        self.moderate_average_accel_lf = 0.0
        self.high_average_accel_lf = 0.0
        self.total_average_accel_lf = 0.0

        self.low_average_accel_rf = 0.0
        self.moderate_average_accel_rf = 0.0
        self.high_average_accel_rf = 0.0
        self.total_average_accel_rf = 0.0

        # cma by low, mod, high bands
        self.low_gct_left = 0.0
        self.low_gct_left_percentage = 0.0
        self.moderate_gct_left = 0.0
        self.moderate_gct_left_percentage = 0.0
        self.high_gct_left = 0.0
        self.high_gct_left_percentage = 0.0
        self.low_gct_right = 0.0
        self.low_gct_right_percentage = 0.0
        self.moderate_gct_right = 0.0
        self.moderate_gct_right_percentage = 0.0
        self.high_gct_right = 0.0
        self.high_gct_right_percentage = 0.0
        self.gct_total_left = 0.0
        self.gct_total_right = 0.0


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
        self.single_average_peak_vGRF_lf = 0.0
        self.double_average_peak_vGRF_lf = 0.0
        self.single_average_peak_vGRF_rf = 0.0
        self.double_average_peak_vGRF_rf = 0.0

        # gcr by single, double bands
        self.single_gct_left = 0.0
        self.single_gct_left_percentage = 0.0
        self.double_gct_left = 0.0
        self.double_gct_left_percentage = 0.0
        self.single_gct_right = 0.0
        self.single_gct_right_percentage = 0.0
        self.double_gct_right = 0.0
        self.double_gct_right_percentage = 0.0
        self.gct_total_left = 0.0
        self.gct_total_right = 0.0


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
        self.left_average_peak_vGRF = 0.0
        self.right_average_peak_vGRF = 0.0

        # gct by left/right bands
        self.left_gct = 0.0
        self.right_gct = 0.0

