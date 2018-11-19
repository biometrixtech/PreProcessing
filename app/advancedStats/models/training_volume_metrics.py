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


class ReportingBand(object):
    def __init__(self, descriptor):
        self.descriptor = descriptor
        self.seconds = 0
        self.seconds_percentage = 0.0
        self.accumulated_grf = 0.0
        self.accumulated_grf_percentage = 0.0
        self.cma = 0.0
        self.cma_percentage = 0.0
        self.left = SideReportingBand("Left")
        self.right = SideReportingBand("Right")

    def update_side_calculations(self):

        total_gct = self.left.gct + self.right.gct
        total_cma =self.right.cma + self.right.cma
        total_seconds = self.left.seconds + self.right.seconds
        total_accum_grf = self.left.accumulated_grf + self.right.accumulated_grf

        if total_gct > 0:
            self.left.gct_percentage = (self.left.gct / float(total_gct)) * 100
            self.right.gct_percentage = (self.right.gct / float(total_gct)) * 100

        if total_cma > 0:
            self.left.cma_percentage = (self.left.cma / float(total_cma)) * 100
            self.right.cma_percentage = (self.right.cma / float(total_cma)) * 100

        if total_seconds > 0:
            self.left.seconds_percentage = (self.left.seconds / float(total_seconds)) * 100
            self.right.seconds_percentage = (self.right.seconds / float(total_seconds)) * 100

        if total_accum_grf > 0:
            self.left.accumulated_grf_percentage = (self.left.accumulated_grf / float(total_accum_grf)) * 100
            self.right.accumulated_grf_percentage = (self.right.accumulated_grf / float(total_accum_grf)) * 100

        self.left.update_cumulative_averages()
        self.right.update_cumulative_averages()


class SideReportingBand(object):
    def __init__(self, orientation):
        self.orientation = orientation
        self.average_peak_vGRF = AveragedValue()
        self.average_GRF = AveragedValue()
        self.average_accel = AveragedValue()
        self.gct = 0.0
        self.gct_percentage = 0.0
        self.cma = 0.0
        self.cma_percentage = 0.0
        self.cumulative_average_peak_vGRF = 0.0
        self.cumulative_average_GRF = 0.0
        self.cumulative_average_accel = 0.0
        self.seconds = 0
        self.seconds_percentage = 0.0
        self.accumulated_grf = 0.0
        self.accumulated_grf_percentage = 0.0

    def update_cumulative_averages(self):
        self.cumulative_average_peak_vGRF = self.average_peak_vGRF.get_average()
        self.cumulative_average_GRF = self.average_GRF.get_average()
        self.cumulative_average_accel = self.average_accel.get_average()


class AveragedValue(object):
    def __init__(self):
        self.value = 0.0
        self.count = 0

    def add_value(self, value, count):
        if value is not None:
            self.value += value
            self.count += count

    def get_average(self):

        if self.count > 0:

            return self.value / float(self.count)

        else:

            return None


class LowModHighBands(object):
    def __init__(self):
        self.low = ReportingBand("Low")
        self.moderate = ReportingBand("Moderate")
        self.high = ReportingBand("High")
        self.total = ReportingBand("Total")
        #self.left_low = SideReportingBand("Low", "Left")
        #self.left_moderate = SideReportingBand("Moderate", "Left")
        #self.left_high = SideReportingBand("High", "Left")
        #self.left_total = SideReportingBand("Total", "Left")
        #self.right_low = SideReportingBand("Low", "Right")
        #self.right_moderate = SideReportingBand("Moderate", "Right")
        #self.right_high = SideReportingBand("High", "Right")
        #self.right_total = SideReportingBand("Total", "Right")

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

    def update_band_calculations(self):

        self.low.seconds_percentage = (self.low.seconds / float(self.total.seconds)) * 100
        self.moderate.seconds_percentage = (self.moderate.seconds / float(self.total.seconds)) * 100
        self.high.seconds_percentage = (self.high.seconds / float(self.total.seconds)) * 100
        self.total.seconds_percentage = (self.total.seconds / float(self.total.seconds)) * 100

        self.low.accumulated_grf_percentage = (self.low.accumulated_grf / float(self.total.accumulated_grf)) * 100
        self.moderate.accumulated_grf_percentage = (self.moderate.accumulated_grf / float(self.total.accumulated_grf)) * 100
        self.high.accumulated_grf_percentage = (self.high.accumulated_grf / float(self.total.accumulated_grf)) * 100
        self.total.accumulated_grf_percentage = (self.total.accumulated_grf / float(self.total.accumulated_grf)) * 100

        self.low.cma_percentage = (self.low.cma / float(self.total.cma)) * 100
        self.moderate.cma_percentage = (self.moderate.cma / float(self.total.cma)) * 100
        self.high.cma_percentage = (self.high.cma / float(self.total.cma)) * 100
        self.total.cma_percentage = (self.total.cma / float(self.total.cma)) * 100

        self.low.update_side_calculations()
        self.moderate.update_side_calculations()
        self.high.update_side_calculations()
        self.total.update_side_calculations()


class StanceBands(object):
    def __init__(self):
        self.single = ReportingBand("Single")
        self.double = ReportingBand("Double")
        self.total = ReportingBand("Total")

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

    def update_band_calculations(self):
        self.single.seconds_percentage = (self.single.seconds / float(self.total.seconds)) * 100
        self.double.seconds_percentage = (self.double.seconds / float(self.total.seconds)) * 100
        self.total.seconds_percentage = (self.total.seconds / float(self.total.seconds)) * 100

        self.single.accumulated_grf_percentage = (self.single.accumulated_grf / float(self.total.accumulated_grf)) * 100
        self.double.accumulated_grf_percentage = (self.double.accumulated_grf / float(
            self.total.accumulated_grf)) * 100
        self.total.accumulated_grf_percentage = (self.total.accumulated_grf / float(
            self.total.accumulated_grf)) * 100

        self.single.cma_percentage = (self.single.cma / float(self.total.cma)) * 100
        self.double.cma_percentage = (self.double.cma / float(self.total.cma)) * 100
        self.total.cma_percentage = (self.total.cma / float(self.total.cma)) * 100

        self.single.update_side_calculations()
        self.double.update_side_calculations()
        self.total.update_side_calculations()


class LeftRightBands(object):
    def __init__(self):
        self.left = SideReportingBand("Left")
        self.right = SideReportingBand("Right")
        self.total = SideReportingBand("Total")
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

    def update_band_calculations(self):

        #total_seconds = self.left.seconds + self.right.seconds
        #total_accumulated_grf = self.left.accumulated_grf + self.right.accumulated_grf
        #total_cma = self.left.cma + self.right.cma
        self.left.seconds_percentage = (self.left.seconds / float(self.total.seconds)) * 100
        self.right.seconds_percentage = (self.right.seconds / float(self.total.seconds)) * 100
        self.total.seconds_percentage = (self.total.seconds / float(self.total.seconds)) * 100

        self.left.accumulated_grf_percentage = (self.left.accumulated_grf / float(self.total.accumulated_grf)) * 100
        self.right.accumulated_grf_percentage = (self.right.accumulated_grf / float(
            self.total.accumulated_grf)) * 100
        self.total.accumulated_grf_percentage = (self.total.accumulated_grf / float(
            self.total.accumulated_grf)) * 100

        self.left.cma_percentage = (self.left.cma / float(self.total.cma)) * 100
        self.right.cma_percentage = (self.right.cma / float(self.total.cma)) * 100
        self.total.cma_percentage = (self.total.cma / float(self.total.cma)) * 100

        self.left.update_cumulative_averages()
        self.right.update_cumulative_averages()
        self.total.update_cumulative_averages()