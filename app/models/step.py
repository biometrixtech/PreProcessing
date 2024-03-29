from datetime import datetime
from utils import parse_datetime


class Step(object):
    """
    A Step
    """

    def __init__(self, mongo_step=None, accumulated_grf=0, orientation="Left", active_block_id='', unit_block_number=0, session_position_number=0, session_start_time=datetime.now):
        self.active_block_id = active_block_id
        self.unit_block_number = unit_block_number
        self.session_position_number = session_position_number
        self.active_block_number = 0
        self.time_block = 0

        if mongo_step is None:
            self.orientation = orientation
            self.duration = 0
            self.total_grf = 0
            self.accumulated_grf = 0
            self.accumulated_grf_per_sec = 0
        
            self.total_grf_avg = 0
            self.total_accel = 0
            self.total_accel_avg = 0
            # self.control = 0
            # self.ankle_control = 0
            # self.hip_control = 0
            self.peak_grf = 0
            self.peak_grf_contact_duration = 0
            self.peak_grf_impact_duration = 0
            self.peak_grf_perc_impact_duration = 0
            self.adduc_ROM = 0
            self.adduc_motion_covered = 0
            self.flex_ROM = 0
            self.flex_motion_covered = 0
            self.contact_duration = 0
            # self.contralateral_hip_drop = 0
            # self.ankle_rotation = 0
            # self.land_pattern = 0
            self.adduc_ROM_hip = 0
            self.adduc_motion_covered_total_hip = 0
            self.adduc_motion_covered_neg_hip = 0
            self.adduc_motion_covered_pos_hip = 0
            self.flex_ROM_hip = 0
            self.flex_motion_covered_total_hip = 0
            self.flex_motion_covered_neg_hip = 0
            self.flex_motion_covered_pos_hip = 0

            # self.land_time = 0

            # new vars
            self.anterior_pelvic_tilt_range = 0
            self.anterior_pelvic_tilt_rate = 0
            self.ankle_pitch_range = 0
            self.hip_drop = 0
            self.cadence_zone = None
            self.knee_valgus = 0
            self.hip_rotation = 0
            self.peak_hip_vertical_accel = 0
            self.median_hip_vertical_accel = 0
            self.peak_hip_vertical_accel_95 = 0
            
        else:
            time_start = parse_datetime(mongo_step.get('startTime'))
            time_end = parse_datetime(mongo_step.get('endTime'))
        
            self.cumulative_end_time = (time_end - session_start_time).total_seconds()
            
            self.time_start = time_start.time().strftime("%H:%M:%S")
            self.time_end = time_end.time().strftime("%H:%M:%S")

            self.step_start_time = time_start
            self.step_end_time = time_end

            self.orientation = orientation
            self.duration = mongo_step.get('duration')
            self.total_grf = mongo_step.get('totalGRF')
            self.peak_grf = mongo_step.get('peakGRF') or 0

            if self.peak_grf is not None:
                self.accumulated_grf = accumulated_grf + self.peak_grf
            else:
                self.accumulated_grf = accumulated_grf
            self.accumulated_grf_per_sec = self.accumulated_grf / self.cumulative_end_time
        
            self.total_grf_avg = mongo_step.get('totalGRFAvg')
            self.total_accel = mongo_step.get('totalAccel')
            self.total_accel_avg = mongo_step.get('totalAccelAvg')
            # self.control = mongo_step.get('control')
            # self.ankle_control = mongo_step.get('ankleControl')
            # self.hip_control = mongo_step.get('hipControl')

            if orientation == "Left":
                self.peak_grf_contact_duration = mongo_step.get('peakGrfContactDurationLF')
                self.peak_grf_impact_duration = mongo_step.get('peakGrfImpactDurationLF')
                self.peak_grf_perc_impact_duration = mongo_step.get('peakGrfPercImpactDurationLF')
                self.adduc_ROM = mongo_step.get('adducROMLF')
                self.adduc_motion_covered = mongo_step.get('adducMotionCoveredLF')
                self.flex_ROM = mongo_step.get('flexROMLF')
                self.flex_motion_covered = mongo_step.get('flexMotionCoveredLF')
                self.contact_duration = mongo_step.get('contactDurationLF')
                # self.contralateral_hip_drop = mongo_step.get('contraHipDropLF')
                # self.ankle_rotation = mongo_step.get('ankleRotationLF')
                # self.land_pattern = mongo_step.get('landPatternLF')
            else:
                self.peak_grf_contact_duration = mongo_step.get('peakGrfContactDurationRF')
                self.peak_grf_impact_duration = mongo_step.get('peakGrfImpactDurationRF')
                self.peak_grf_perc_impact_duration = mongo_step.get('peakGrfPercImpactDurationRF')
                self.adduc_ROM = mongo_step.get('adducROMRF')
                self.adduc_motion_covered = mongo_step.get('adducMotionCoveredRF')
                self.flex_ROM = mongo_step.get('flexROMRF')
                self.flex_motion_covered = mongo_step.get('flexMotionCoveredRF')
                self.contact_duration = mongo_step.get('contactDurationRF')
                # self.contralateral_hip_drop = mongo_step.get('contraHipDropRF')
                # self.ankle_rotation = mongo_step.get('ankleRotationRF')
                # self.land_pattern = mongo_step.get('landPatternRF')

            self.adduc_ROM_hip = mongo_step.get('adducROMHip')
            self.adduc_motion_covered_total_hip = mongo_step.get('adducMotionCoveredTotalHip')
            self.adduc_motion_covered_neg_hip = mongo_step.get('adducMotionCoveredNegHip')
            self.adduc_motion_covered_pos_hip = mongo_step.get('adducMotionCoveredPosHip')
            self.flex_ROM_hip = mongo_step.get('flexROMHip')
            self.flex_motion_covered_total_hip = mongo_step.get('flexMotionCoveredTotalHip')
            self.flex_motion_covered_neg_hip = mongo_step.get('flexMotionCoveredNegHip')
            self.flex_motion_covered_pos_hip = mongo_step.get('flexMotionCoveredPosHip')

            # new vars
            self.anterior_pelvic_tilt_range = mongo_step.get('anteriorPelvicTiltRange')
            self.anterior_pelvic_tilt_rate = mongo_step.get('anteriorPelvicTiltRate')
            self.ankle_pitch_range = None
            self.ankle_pitch = mongo_step.get('anklePitchRange')
            self.hip_drop = mongo_step.get('hipDrop')
            self.cadence_zone = mongo_step.get('cadence_zone')
            self.knee_valgus = mongo_step.get('kneeValgus')
            self.hip_rotation = mongo_step.get('hipMedialRotation')
            self.peak_hip_vertical_accel = mongo_step.get('peakHipVerticalAccel')
            self.median_hip_vertical_accel = mongo_step.get('medianHipVerticalAccel')
            self.peak_hip_vertical_accel_95 = mongo_step.get('peakHipVerticalAccel95')
            self.max_ankle_pitch_time = mongo_step.get('maxAnklePitchTime')

            # self.land_time = mongo_step.get('landTime')
            self.stance = mongo_step.get('stance')
            self.stance_calc = self.get_stance()

    def get_stance(self):
        try:
            if self.stance.count(2) + self.stance.count(4) > self.stance.count(3) + self.stance.count(5):
                return 2
            elif self.stance.count(2) + self.stance.count(4) < self.stance.count(3) + self.stance.count(5):
                return 4
            else:
                return 4
        except:
            return 0
