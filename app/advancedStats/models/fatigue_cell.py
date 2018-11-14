import step
import numpy as np
from scipy import stats 
from asymmetry import LoadingAsymmetry
from complexity_matrix_summary import ComplexityMatrixSummary
from descriptive_stats_cell import DescriptiveStatsCell


class FatigueCell(object):
    """description of class"""
    def __init__(self, complexity_level="Low", fatigue_level="Low"):
        self.fatigue_level = fatigue_level
        self.complexity_level = complexity_level
        self.left_steps = []
        self.right_steps = []

    
    def add_step(self, step):
        if(step.orientation=="Left"):
            self.left_steps.append(step)
        else:
            self.right_steps.append(step)
    
    def get_summary(self):
        summary = ComplexityMatrixSummary()
        summary.left_step_count = len(self.left_steps)
        summary.right_step_count = len(self.right_steps)
        summary.total_steps = summary.left_step_count + summary.right_step_count
        summary.left_duration = self.get_steps_sum("duration", self.left_steps)
        summary.right_duration = self.get_steps_sum("duration", self.right_steps)
        summary.total_duration = summary.left_duration + summary.right_duration
        summary.left_avg_accumulated_grf_sec = self.get_steps_mean("accumulated_grf_per_sec",self.left_steps)
        summary.right_avg_accumulated_grf_sec = self.get_steps_mean("accumulated_grf_per_sec",self.right_steps)
        return summary
    
    def get_asymmetry(self, attribute):
        asym = LoadingAsymmetry()
        left_sum = self.get_steps_sum(attribute, self.left_steps)
        right_sum = self.get_steps_sum(attribute, self.right_steps)
        asym.total_sum = left_sum + right_sum
        
        if(len(self.left_steps)==0 or len(self.right_steps)==0):
            asym.training_asymmetry = left_sum-right_sum
        else:
            asym.kinematic_asymmetry = left_sum-right_sum
        asym.total_asymmetry = asym.training_asymmetry + asym.kinematic_asymmetry
        return asym

    def get_descriptive_stats(self):
        stats = DescriptiveStatsCell()
        stats.left_adduc_ROM_mean = self.get_steps_mean("adduc_ROM", self.left_steps)
        stats.left_adduc_ROM_stddev = self.get_steps_stddev("adduc_ROM", self.left_steps)
        stats.left_adduc_motion_covered_mean = self.get_steps_mean("adduc_motion_covered", self.left_steps)
        stats.left_adduc_motion_covered_stddev = self.get_steps_stddev("adduc_motion_covered", self.left_steps)       
        stats.left_flex_ROM_mean = self.get_steps_mean("flex_ROM", self.left_steps)
        stats.left_flex_ROM_stddev = self.get_steps_stddev("flex_ROM", self.left_steps)
        stats.left_flex_motion_covered_mean = self.get_steps_mean("flex_motion_covered", self.left_steps)
        stats.left_flex_motion_covered_stddev = self.get_steps_stddev("flex_motion_covered", self.left_steps)          
 
        stats.left_adduc_ROM_hip_mean = self.get_steps_mean("adduc_ROM_hip", self.left_steps)
        stats.left_adduc_ROM_hip_stddev = self.get_steps_stddev("adduc_ROM_hip", self.left_steps)
        stats.left_adduc_motion_covered_hip_mean = self.get_steps_mean("adduc_motion_covered_hip", self.left_steps)
        stats.left_adduc_motion_covered_hip_stddev = self.get_steps_stddev("adduc_motion_covered_hip", self.left_steps)       
        stats.left_flex_ROM_hip_mean = self.get_steps_mean("flex_ROM_hip", self.left_steps)
        stats.left_flex_ROM_hip_stddev = self.get_steps_stddev("flex_ROM_hip", self.left_steps)
        stats.left_flex_motion_covered_hip_mean = self.get_steps_mean("flex_motion_covered_hip", self.left_steps)
        stats.left_flex_motion_covered_hip_stddev = self.get_steps_stddev("flex_motion_covered_hip", self.left_steps)  

        stats.right_adduc_ROM_mean = self.get_steps_mean("adduc_ROM", self.right_steps)
        stats.right_adduc_ROM_stddev = self.get_steps_stddev("adduc_ROM", self.right_steps)
        stats.right_adduc_motion_covered_mean = self.get_steps_mean("adduc_motion_covered", self.right_steps)
        stats.right_adduc_motion_covered_stddev = self.get_steps_stddev("adduc_motion_covered", self.right_steps)       
        stats.right_flex_ROM_mean = self.get_steps_mean("flex_ROM", self.right_steps)
        stats.right_flex_ROM_stddev = self.get_steps_stddev("flex_ROM", self.right_steps)
        stats.right_flex_motion_covered_mean = self.get_steps_mean("flex_motion_covered", self.right_steps)
        stats.right_flex_motion_covered_stddev = self.get_steps_stddev("flex_motion_covered", self.right_steps) 

        stats.right_adduc_ROM_hip_mean = self.get_steps_mean("adduc_ROM_hip", self.right_steps)
        stats.right_adduc_ROM_hip_stddev = self.get_steps_stddev("adduc_ROM_hip", self.right_steps)
        stats.right_adduc_motion_covered_hip_mean = self.get_steps_mean("adduc_motion_covered_hip", self.right_steps)
        stats.right_adduc_motion_covered_hip_stddev = self.get_steps_stddev("adduc_motion_covered_hip", self.right_steps)       
        stats.right_flex_ROM_hip_mean = self.get_steps_mean("flex_ROM_hip", self.right_steps)
        stats.right_flex_ROM_hip_stddev = self.get_steps_stddev("flex_ROM_hip", self.right_steps)
        stats.right_flex_motion_covered_hip_mean = self.get_steps_mean("flex_motion_covered_hip", self.right_steps)
        stats.right_flex_motion_covered_hip_stddev = self.get_steps_stddev("flex_motion_covered_hip", self.right_steps) 

        stats.left_adduc_ROM_time_corr = self.get_steps_correlation("adduc_ROM","accumulated_grf_per_sec", self.left_steps)
        stats.right_adduc_ROM_time_corr = self.get_steps_correlation("adduc_ROM","accumulated_grf_per_sec", self.right_steps)
        stats.left_adduc_motion_covered_time_corr = self.get_steps_correlation("adduc_motion_covered","accumulated_grf_per_sec", self.left_steps)
        stats.right_adduc_motion_covered_time_corr = self.get_steps_correlation("adduc_motion_covered","accumulated_grf_per_sec", self.right_steps)



        return stats
    
    def get_steps_correlation(self, attribute_x, attribute_y, step_list):
        value_list_x = []
        value_list_y = []
        for item in step_list:
            if(getattr(item,attribute_x) is not None):
                value_list_x.append(getattr(item,attribute_x))
            if(getattr(item,attribute_y) is not None):
                value_list_y.append(getattr(item,attribute_y))
        if(len(value_list_x)==0 or len(value_list_y)==0):
            return 0
        else:
            r,p = stats.pearsonr(value_list_x, value_list_y)
            if(p<=.05):
                return r
            else:
                return None
            
    
    
    def get_steps_sum(self, attribute, step_list):
        value_list = []
        for item in step_list:
            if(getattr(item,attribute) is not None):
                value_list.append(getattr(item,attribute))
        if(len(value_list)==0):
            return 0
        else:
            return np.sum(value_list)
    
    def get_steps_stddev(self, attribute, step_list):
        value_list = []
        for item in step_list:
            if(getattr(item,attribute) is not None):
                value_list.append(getattr(item,attribute))
        if(len(value_list)==0):
            return 0
        else:
            return np.std(value_list)
    
    def get_steps_mean(self, attribute, step_list):
        value_list = []
        for item in step_list:
            if(getattr(item,attribute) is not None):
                value_list.append(getattr(item,attribute))
        if(len(value_list)==0):
            return 0
        else:
            return np.mean(value_list)
