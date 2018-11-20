from datetime import datetime
import numpy as np


class Step(object):
    """description of class"""

    def __init__(self,mongo_step=None, accumulated_grf=0, orientation="Left", active_block_id='', unit_block_number=0, session_position_number=0, sessionTimeStart_object=datetime.now):
        self.active_block_id = active_block_id
        self.unit_block_number = unit_block_number
        self.session_position_number = session_position_number
        self.active_block_number = 0
        self.time_block = 0
        if(mongo_step==None):
            self.orientation = orientation
            self.duration = 0
            self.total_grf = 0
            self.accumulated_grf = 0
            self.accumulated_grf_per_sec = 0
        
            self.total_grf_avg = 0
            self.total_accel = 0
            self.total_accel_avg = 0
            self.control = 0
            self.ankle_control = 0
            self.hip_control = 0
            self.peak_grf = 0
            self.peak_grf_contact_duration = 0
            self.peak_grf_impact_duration = 0
            self.peak_grf_perc_impact_duration = 0
            self.adduc_ROM =0
            self.adduc_motion_covered = 0
            self.flex_ROM = 0
            self.flex_motion_covered = 0
            self.contact_duration = 0
            self.contralateral_hip_drop = 0
            self.ankle_rotation = 0
            self.land_pattern = 0
            self.adduc_ROM_hip = 0
            self.adduc_motion_covered_hip = 0
            self.flex_ROM_hip = 0
            self.flex_motion_covered_hip =0

            self.land_time = 0
            
        else:
            time_start = mongo_step.get('startTime')
            time_end = mongo_step.get('endTime')
            try:
                timeStart_object = datetime.strptime(time_start, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                timeStart_object = datetime.strptime(time_start, '%Y-%m-%d %H:%M:%S')
            try:
                timeEnd_object = datetime.strptime(time_end, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                timeEnd_object = datetime.strptime(time_end, '%Y-%m-%d %H:%M:%S')
        
        
            cumulative_start_time = (timeStart_object- sessionTimeStart_object).seconds
            self.cumulative_end_time = (timeEnd_object- sessionTimeStart_object).total_seconds()    
            
            self.time_start = timeStart_object.time().strftime("%H:%M:%S")
            self.time_end = timeEnd_object.time().strftime("%H:%M:%S")

            self.orientation = orientation
            self.duration = mongo_step.get('duration')
            self.total_grf = mongo_step.get('totalGRF')
            self.peak_grf = mongo_step.get('peakGRF')
            #self.accumulated_grf = accumulated_grf+self.total_grf
            if self.peak_grf is not None:
                self.accumulated_grf = accumulated_grf + self.peak_grf
            else:
                self.accumulated_grf = accumulated_grf
            self.accumulated_grf_per_sec = self.accumulated_grf/self.cumulative_end_time
        
            self.total_grf_avg = mongo_step.get('totalGRFAvg')
            self.total_accel = mongo_step.get('totalAccel')
            self.total_accel_avg = mongo_step.get('totalAccelAvg')
            self.control = mongo_step.get('control')
            self.ankle_control = mongo_step.get('ankleControl')
            self.hip_control = mongo_step.get('hipControl')


            if(orientation=="Left"):
                self.peak_grf_contact_duration = mongo_step.get('peakGrfContactDurationLF')
                self.peak_grf_impact_duration = mongo_step.get('peakGrfImpactDurationLF')
                self.peak_grf_perc_impact_duration = mongo_step.get('peakGrfPercImpactDurationLF')
                self.adduc_ROM = mongo_step.get('adducROMLF')
                self.adduc_motion_covered = mongo_step.get('adducMotionCoveredLF')
                self.flex_ROM = mongo_step.get('flexROMLF')
                self.flex_motion_covered = mongo_step.get('flexMotionCoveredLF')
                self.contact_duration = mongo_step.get('contactDurationLF')
                self.contralateral_hip_drop = mongo_step.get('contraHipDropLF')
                self.ankle_rotation = mongo_step.get('ankleRotationLF')
                self.land_pattern = mongo_step.get('landPatternLF')
            else:
                self.peak_grf_contact_duration = mongo_step.get('peakGrfContactDurationRF')
                self.peak_grf_impact_duration = mongo_step.get('peakGrfImpactDurationRF')
                self.peak_grf_perc_impact_duration = mongo_step.get('peakGrfPercImpactDurationRF')
                self.adduc_ROM = mongo_step.get('adducROMRF')
                self.adduc_motion_covered = mongo_step.get('adducMotionCoveredRF')
                self.flex_ROM = mongo_step.get('flexROMRF')
                self.flex_motion_covered = mongo_step.get('flexMotionCoveredRF')
                self.contact_duration = mongo_step.get('contactDurationRF')
                self.contralateral_hip_drop = mongo_step.get('contraHipDropRF')
                self.ankle_rotation = mongo_step.get('ankleRotationRF')
                self.land_pattern = mongo_step.get('landPatternRF')

            self.adduc_ROM_hip = mongo_step.get('adducROMHip')
            self.adduc_motion_covered_hip = mongo_step.get('adducMotionCoveredHip')
            self.flex_ROM_hip = mongo_step.get('flexROMHip')
            self.flex_motion_covered_hip =mongo_step.get('flexMotionCoveredHip')

            self.land_time = mongo_step.get('landTime')
            self.stance = mongo_step.get('stance')
            self.stance_calc = self.get_stance()

    def get_stance(self):
        try:
            if(self.stance.count(8)+self.stance.count(6)+self.stance.count(2)+self.stance.count(3) >
                self.stance.count(9)+self.stance.count(7)+self.stance.count(4)+self.stance.count(5)):
                return 2
            elif(self.stance.count(8)+self.stance.count(6)+self.stance.count(2)+self.stance.count(3) <
                self.stance.count(9)+self.stance.count(7)+self.stance.count(4)+self.stance.count(5)):
                return 4
            else:
                return 4
        except:
            return 0

