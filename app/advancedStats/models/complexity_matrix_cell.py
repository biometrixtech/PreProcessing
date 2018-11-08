import step
import numpy as np
from scipy import stats 
from scipy.integrate import odeint
from asymmetry import Asymmetry
from complexity_matrix_summary import ComplexityMatrixSummary
from descriptive_stats_cell import DescriptiveStatsCell
from matrix_kruskal import MatrixKruskal
import pandas
import math
#import matrix_decay_parameters
from active_block_summary import ActiveBlockSummary
from active_block_outlier import ActiveBlockOutlier


class ComplexityMatrixCell(object):
    """description of class"""
    def __init__(self,row_name="Row",column_name="Column", complexity_level="Low"):
        self.row_name = row_name
        self.column_name = column_name
        self.complexity_level = complexity_level
        self.left_steps = []
        self.right_steps = []

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
        asym = Asymmetry()
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
            
    def get_steps_f_test(self, attribute, step_list_x, step_list_y):
        value_list_x = []
        value_list_y = []
        for item in step_list_x:
            if(getattr(item,attribute) is not None):
                value_list_x.append(getattr(item,attribute))
        for item in step_list_y:    
            if(getattr(item,attribute) is not None):
                value_list_y.append(getattr(item,attribute))
        if(len(value_list_x)==0 or len(value_list_y)==0):
            return 0
        else:
            try:
                r,p = stats.kruskal(value_list_x, value_list_y)
                if(p<=.05):
                    #write out values for temp analysis
                    #x_frame = pandas.DataFrame(value_list_x)
                    #y_frame = pandas.DataFrame(value_list_y)
                    #x_frame.to_csv('C:\\UNC\\v6\\f_test_x_'+self.complexity_level+'_'+self.row_name+'_'+self.column_name+'_'+attribute+'.csv',sep=',')
                    #y_frame.to_csv('C:\\UNC\\v6\\f_test_y_'+self.complexity_level+'_'+self.row_name+'_'+self.column_name+'_'+attribute+'.csv',sep=',')
                    return r
                else:
                    return None
            except ValueError:
                return None   

    def get_decay_outliers(self, attribute, label, orientation,active_block_list, step_list):
        
        abs_list = {}
        abs_value_list = []
        abs_outlier_list = []

        for key in active_block_list:
        
            steps = list(x for x in step_list if x.active_block_id == key)
            decay = []
            y0 = None
            t0= None
            decay_mean = None
            #accum_grf_per_sec0 = None
            for item in steps:
                if(getattr(item,attribute) is not None):
                    #accum_grf_per_sec0 = getattr(item,"accumulated_grf_per_sec")
                    y0 = math.fabs(getattr(item,attribute))
                    t0 = getattr(item,"cumulative_end_time")
                
                    break

            yt = None
            t = None
            cnt = 0
            #accum_grf_per_sect = None
            for item in steps:
                if(getattr(item,attribute) is not None):
                    #accum_grf_per_sect = getattr(item,"accumulated_grf_per_sec")
                    yt =  math.fabs(getattr(item,attribute)) 
                    t = getattr(item,"cumulative_end_time")

                    if(cnt>4):
                        decay.append((math.log(yt/y0))/(t-t0))
                    cnt = cnt + 1
            if(len(decay)>0):
                decay_mean = np.mean(decay)
            if(decay_mean is not None):
                abs = ActiveBlockSummary(key)
                setattr(abs, attribute, decay_mean)
                setattr(abs, "end_time", t)
                abs_list[key] = abs
                abs_value_list.append(decay_mean)
                
        

        #what is the mean of the mean?
        
        abs_mean = np.mean(abs_value_list)
        abs_stddev = np.std(abs_value_list)

        #now loop back through and find outliers!
        for key, value in abs_list.items():
            z_score = (getattr(value,attribute) - abs_mean) / abs_stddev
            if(math.fabs(z_score)>2):
                outlier = ActiveBlockOutlier(key)
                outlier.raw_value = getattr(value,attribute)
                outlier.z_score = z_score
                outlier.attribute_name = attribute
                outlier.complexity_level = self.complexity_level
                outlier.label = label
                outlier.orientation = orientation
                outlier.end_time = getattr(value,"end_time")
                
                abs_outlier_list.append(outlier)

        return abs_outlier_list
            
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
    
    def add_step(self, step):
        if(step.orientation=="Left"):
            self.left_steps.append(step)
        else:
            self.right_steps.append(step)

    def get_kruskal_calculations(self):
        calcs = MatrixKruskal()
        calcs.adduc_ROM = self.get_steps_f_test("adduc_ROM", self.left_steps, self.right_steps)
        calcs.adduc_motion_covered = self.get_steps_f_test("adduc_motion_covered", self.left_steps, self.right_steps)
        calcs.flex_ROM = self.get_steps_f_test("flex_ROM", self.left_steps, self.right_steps)
        calcs.flex_motion_covered = self.get_steps_f_test("flex_motion_covered", self.left_steps, self.right_steps)

        calcs.adduc_ROM_hip = self.get_steps_f_test("adduc_ROM_hip", self.left_steps, self.right_steps)
        calcs.adduc_motion_covered_hip = self.get_steps_f_test("adduc_motion_covered_hip", self.left_steps, self.right_steps)
        calcs.flex_ROM_hip = self.get_steps_f_test("flex_ROM_hip", self.left_steps, self.right_steps)
        calcs.flex_motion_covered_hip = self.get_steps_f_test("flex_motion_covered_hip", self.left_steps, self.right_steps)

        return calcs

    def get_decay_parameters(self):
        
        outlier_list = []
        
        active_block_list_LF = {x.active_block_id for x in self.left_steps}
        active_block_list_RF = {x.active_block_id for x in self.right_steps}
        active_block_list = list(set(active_block_list_LF).union(active_block_list_RF))


        #for key in active_block_list:
        #abs = ActiveBlockSummary.ActiveBlockSummary(key)
        #abs.adduc_ROM_LF = self.get_decay_outliers("adduc_ROM", key, self.left_steps)
        #abs.flex_ROM_LF = self.get_decay_outliers("flex_ROM",  key, self.left_steps)
        #abs.adduc_ROM_RF = self.get_decay_outliers("adduc_ROM",  key, self.right_steps)
        #abs.flex_ROM_RF = self.get_decay_outliers("flex_ROM",  key, self.right_steps)
        #abs.adduc_ROM_hip_LF = self.get_decay_outliers("adduc_ROM_hip",  key, self.left_steps)
        #abs.flex_ROM_hip_LF = self.get_decay_outliers("flex_ROM_hip", key,  self.left_steps)
        #abs.adduc_ROM_hip_RF = self.get_decay_outliers("adduc_ROM_hip",  key, self.right_steps)
        #abs.flex_ROM_hip_RF = self.get_decay_outliers("flex_ROM_hip", key,  self.right_steps)
        
        outlier_list.extend(self.get_decay_outliers("adduc_ROM","adduc_ROM","Left", active_block_list, self.left_steps))
        outlier_list.extend(self.get_decay_outliers("flex_ROM","flex_ROM","Left",  active_block_list, self.left_steps))
        outlier_list.extend(self.get_decay_outliers("adduc_ROM","adduc_ROM","Right",  active_block_list, self.right_steps))
        outlier_list.extend(self.get_decay_outliers("flex_ROM", "flex_ROM","Right", active_block_list, self.right_steps))
        outlier_list.extend(self.get_decay_outliers("adduc_ROM_hip","adduc_ROM_hip","Left",  active_block_list, self.left_steps))
        outlier_list.extend(self.get_decay_outliers("flex_ROM_hip","flex_ROM_hip","Left", active_block_list,  self.left_steps))
        outlier_list.extend(self.get_decay_outliers("adduc_ROM_hip","adduc_ROM_hip","Right",  active_block_list, self.right_steps))
        outlier_list.extend(self.get_decay_outliers("flex_ROM_hip","flex_ROM_hip","Right", active_block_list,  self.right_steps))
        

        pronating_steps_RF = list(x for x in self.right_steps if x.adduc_motion_covered >=0)
        supinating_steps_LF = list(x for x in self.left_steps if x.adduc_motion_covered  >=0)
        
        pronating_steps_LF = list(x for x in self.left_steps if x.adduc_motion_covered <0)
        supinating_steps_RF = list(x for x in self.right_steps if x.adduc_motion_covered <0)

        dorsi_steps_RF = list(x for x in self.right_steps if x.flex_motion_covered >=0)
        dorsi_steps_LF = list(x for x in self.left_steps if x.flex_motion_covered  >=0)
        
        plantar_steps_RF = list(x for x in self.right_steps if x.flex_motion_covered  <0)
        plantar_steps_LF = list(x for x in self.left_steps if x.flex_motion_covered  <0)
        
        adduc_pos_hip_steps_LF = list(x for x in self.left_steps if x.adduc_motion_covered_hip  >=0)
       
        adduc_neg_hip_steps_RF = list(x for x in self.right_steps if x.adduc_motion_covered_hip <0)
        adduc_pos_hip_steps_RF = list(x for x in self.right_steps if x.adduc_motion_covered_hip >=0)
        adduc_neg_hip_steps_LF = list(x for x in self.left_steps if x.adduc_motion_covered_hip  <0)

        flex_pos_hip_steps_RF = list(x for x in self.right_steps if x.flex_motion_covered_hip  >=0)
        flex_pos_hip_steps_LF = list(x for x in self.left_steps if x.flex_motion_covered_hip  >=0)
        
        flex_neg_hip_steps_RF = list(x for x in self.right_steps if x.flex_motion_covered_hip  <0)
        flex_neg_hip_steps_LF = list(x for x in self.left_steps if x.flex_motion_covered_hip  <0)


        #abs.adduc_pronation_LF = self.get_decay_outliers("adduc_motion_covered",  key, pronating_steps_LF)
        #abs.adduc_supination_LF = self.get_decay_outliers("adduc_motion_covered", key,  supinating_steps_LF)
        #abs.adduc_pronation_RF = self.get_decay_outliers("adduc_motion_covered",  key, pronating_steps_RF)
        #abs.adduc_supination_RF = self.get_decay_outliers("adduc_motion_covered", key,  supinating_steps_RF)

        #abs.dorsiflexion_LF = self.get_decay_outliers("flex_motion_covered",  key, dorsi_steps_LF)
        #abs.dorsiflexion_RF = self.get_decay_outliers("flex_motion_covered",  key, dorsi_steps_RF)
        #abs.plantarflexion_LF = self.get_decay_outliers("flex_motion_covered",  key, plantar_steps_LF)
        #abs.plantarflexion_RF = self.get_decay_outliers("flex_motion_covered", key,  plantar_steps_RF)
        
        #abs.adduc_positive_hip_LF = self.get_decay_outliers("adduc_motion_covered_hip",  key, adduc_pos_hip_steps_LF)
        #abs.flex_positive_hip_LF = self.get_decay_outliers("flex_motion_covered_hip", key,  flex_pos_hip_steps_LF)
        
        #abs.adduc_positive_hip_RF = self.get_decay_outliers("adduc_motion_covered_hip", key,  adduc_pos_hip_steps_RF)
        #abs.flex_positive_hip_RF = self.get_decay_outliers("flex_motion_covered_hip", key,  flex_pos_hip_steps_RF)

        #abs.adduc_negative_hip_LF = self.get_decay_outliers("adduc_motion_covered_hip", key,  adduc_neg_hip_steps_LF)
        #abs.flex_negative_hip_LF = self.get_decay_outliers("flex_motion_covered_hip", key,  flex_neg_hip_steps_LF)
        
        #abs.adduc_negative_hip_RF = self.get_decay_outliers("adduc_motion_covered_hip", key,  adduc_neg_hip_steps_RF)
        #abs.flex_negative_hip_RF = self.get_decay_outliers("flex_motion_covered_hip",  key, flex_neg_hip_steps_RF)


        outlier_list.extend(self.get_decay_outliers("adduc_motion_covered","Pronation","Left",  active_block_list, pronating_steps_LF))
        outlier_list.extend(self.get_decay_outliers("adduc_motion_covered","Supination", "Left", active_block_list,  supinating_steps_LF))
        outlier_list.extend(self.get_decay_outliers("adduc_motion_covered", "Pronation","Right", active_block_list, pronating_steps_RF))
        outlier_list.extend(self.get_decay_outliers("adduc_motion_covered","Supination","Right", active_block_list,  supinating_steps_RF))

        outlier_list.extend(self.get_decay_outliers("flex_motion_covered", "Dorsiflexion","Left", active_block_list, dorsi_steps_LF))
        outlier_list.extend(self.get_decay_outliers("flex_motion_covered", "Dorsiflexion","Right",  active_block_list, dorsi_steps_RF))
        outlier_list.extend(self.get_decay_outliers("flex_motion_covered", "Plantarflexion","Left", active_block_list, plantar_steps_LF))
        outlier_list.extend(self.get_decay_outliers("flex_motion_covered", "Plantarflexion","Right",active_block_list,  plantar_steps_RF))
        
        outlier_list.extend(self.get_decay_outliers("adduc_motion_covered_hip",  "adduc_pos_hip","Left", active_block_list, adduc_pos_hip_steps_LF))
        outlier_list.extend(self.get_decay_outliers("flex_motion_covered_hip",  "flex_pos_hip","Left",active_block_list,  flex_pos_hip_steps_LF))
        
        outlier_list.extend(self.get_decay_outliers("adduc_motion_covered_hip",  "adduc_pos_hip","Right",active_block_list,  adduc_pos_hip_steps_RF))
        outlier_list.extend(self.get_decay_outliers("flex_motion_covered_hip", "flex_pos_hip","Right",active_block_list,  flex_pos_hip_steps_RF))

        outlier_list.extend(self.get_decay_outliers("adduc_motion_covered_hip",  "adduc_neg_hip","Left",active_block_list,  adduc_neg_hip_steps_LF))
        outlier_list.extend(self.get_decay_outliers("flex_motion_covered_hip",  "flex_neg_hip","Left",active_block_list,  flex_neg_hip_steps_LF))
        
        outlier_list.extend(self.get_decay_outliers("adduc_motion_covered_hip", "adduc_neg_hip","Right",active_block_list,  adduc_neg_hip_steps_RF))
        outlier_list.extend(self.get_decay_outliers("flex_motion_covered_hip", "flex_neg_hip","Right", active_block_list, flex_neg_hip_steps_RF))

        #abs_list.append(abs)
        return outlier_list