from utils import parse_datetime


class UnitBlock(object):
    
    def __init__(self, mongo_unit_block, accumulated_grf=0):
        time_start = parse_datetime(mongo_unit_block.get('timeStart'))
        time_end = parse_datetime(mongo_unit_block.get('timeEnd'))
        
        self.time_start = time_start.strftime("%H:%M:%S")
        self.time_end = time_end.strftime("%H:%M:%S")
        
        self.duration = mongo_unit_block.get('duration')
        self.contact_duration_lf = mongo_unit_block.get('contactDurationLF')
        # self.contact_duration_lf5 = mongo_unit_block.get('contactDurationLF5')
        # self.contact_duration_lf95 = mongo_unit_block.get('contactDurationLF95')
        # self.contact_duration_lf_std = mongo_unit_block.get('contactDurationLFStd')

        self.contact_duration_rf = mongo_unit_block.get('contactDurationRF')
        # self.contact_duration_rf5 = mongo_unit_block.get('contactDurationRF5')
        # self.contact_duration_rf95 = mongo_unit_block.get('contactDurationRF95')
        # self.contact_duration_rf_std = mongo_unit_block.get('contactDurationRFStd')                   

        self.peak_grf_lf = mongo_unit_block.get('peakGrfLF')
        # self.peak_grf_lf5 = mongo_unit_block.get('peakGrfLF5')
        # self.peak_grf_lf95 = mongo_unit_block.get('peakGrfLF95')
        # self.peak_grf_lf_std = mongo_unit_block.get('peakGrfLFStd')

        self.peak_grf_rf = mongo_unit_block.get('peakGrfRF')
        # self.peak_grf_rf5 = mongo_unit_block.get('peakGrfRF5')
        # self.peak_grf_rf95 = mongo_unit_block.get('peakGrfRF95')
        # self.peak_grf_rf_std = mongo_unit_block.get('peakGrfRFStd')

        # self.perc_optimal = mongo_unit_block.get('percOptimal')
        # self.control = mongo_unit_block.get('control')
        # self.hip_control = mongo_unit_block.get('hipControl')
        # self.ankle_control = mongo_unit_block.get('ankleControl')
        # self.control_lf = mongo_unit_block.get('controlLF')
        # self.control_rf = mongo_unit_block.get('controlRF')
                       
        # self.symmetry = mongo_unit_block.get('symmetry')
        # self.hip_symmetry = mongo_unit_block.get('hipSymmetry')
        # self.ankle_symmetry = mongo_unit_block.get('ankleSymmetry')
        # self.total_grf = mongo_unit_block.get('totalGRF')
        # self.total_grf_avg = mongo_unit_block.get('totalGRFAvg')
        # self.accumulated_grf = accumulated_grf+self.total_grf

        # self.optimal_grf = mongo_unit_block.get('optimalGRF')
        # self.irregular_grf = mongo_unit_block.get('irregularGRF')
        self.LF_grf = mongo_unit_block.get('LFgRF')
        self.RF_grf = mongo_unit_block.get('RFgRF')
        self.left_grf = mongo_unit_block.get('leftGRF')
        self.right_grf = mongo_unit_block.get('rightGRF')
        self.single_leg_grf = mongo_unit_block.get('singleLegGRF')
        self.perc_left_grf = mongo_unit_block.get('percLeftGRF')
        self.perc_right_grf = mongo_unit_block.get('percRightGRF')
        self.perc_LR_grf_diff = mongo_unit_block.get('percLRGRFDiff')
        self.total_accel = mongo_unit_block.get('totalAccel')
        # self.irregular_accel = mongo_unit_block.get('irregularAccel')
        self.total_accel_avg = mongo_unit_block.get('totalAccelAvg')

        self.peak_grf_contact_duration_lf = mongo_unit_block.get('peakGrfContactDurationLF')
        self.peak_grf_contact_duration_rf = mongo_unit_block.get('peakGrfContactDurationRF')

        # Derived variables
        if self.peak_grf_lf is not None and self.peak_grf_rf is not None:
            self.peak_grf_perc_left = self.peak_grf_lf / (self.peak_grf_rf + self.peak_grf_lf) * 100
            self.peak_grf_perc_right = self.peak_grf_rf / (self.peak_grf_rf + self.peak_grf_lf) * 100
            self.peak_grf_perc_diff = (self.peak_grf_perc_right - 50) / 50 * 100

            if self.peak_grf_perc_right >= 50:
                self.peak_grf_perc_diff_rf = (self.peak_grf_perc_right - 50) / 50 * 100
            else:
                self.peak_grf_perc_diff_rf = None

            if self.peak_grf_perc_left > 50:
                self.peak_grf_perc_diff_lf = (self.peak_grf_perc_left - 50) / 50 * 100
            else:
                self.peak_grf_perc_diff_lf = None

        else:
            self.peak_grf_perc_left = None
            self.peak_grf_perc_right = None
            self.peak_grf_perc_diff = None
            self.peak_grf_perc_diff_rf = None
            self.peak_grf_perc_diff_lf = None

        if self.contact_duration_lf is not None and self.contact_duration_rf is not None:
            self.gct_perc_left = self.contact_duration_lf / (self.contact_duration_rf + self.contact_duration_lf) * 100
            self.gct_perc_right = self.contact_duration_rf / (self.contact_duration_rf + self.contact_duration_lf) * 100
            self.gct_perc_diff = (self.gct_perc_right - 50) / 50 * 100

            if self.gct_perc_right >= 50:
                self.gct_perc_diff_rf = (self.gct_perc_right - 50) / 50 * 100
            else:
                self.gct_perc_diff_rf = None

            if self.gct_perc_left > 50:
                self.gct_perc_diff_lf = (self.gct_perc_left - 50) / 50 * 100
            else:
                self.gct_perc_diff_lf = None
        else:
            self.gct_perc_left = None
            self.gct_perc_right = None
            self.gct_perc_diff = None
            self.gct_perc_diff_lf = None
            self.gct_perc_diff_rf = None

        if self.peak_grf_contact_duration_lf is not None and self.peak_grf_contact_duration_rf is not None:
            self.peak_grf_gct_left_over = max(0, self.peak_grf_contact_duration_lf - 9.5)
            self.peak_grf_gct_left_under = max(0, 9.5 - self.peak_grf_contact_duration_lf)
            self.peak_grf_gct_right_over = max(0, self.peak_grf_contact_duration_rf - 9.5)
            self.peak_grf_gct_right_under = max(0, 9.5 - self.peak_grf_contact_duration_rf)
            
        else:
            self.peak_grf_gct_left_over = None
            self.peak_grf_gct_left_under = None
            self.peak_grf_gct_right_over = None
            self.peak_grf_gct_right_under = None
