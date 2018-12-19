from complexity_matrix_cell import ComplexityMatrixCell
from motion_complexity import MotionComplexity
from step import Step
import numpy as np
import bisect


class ComplexityMatrix(object):
    """description of class"""
    def __init__(self, stance = "Double Leg"):
        self.cells = {}
        self.stance = stance

        if(stance=="Double Leg"):
            self.cells["LowGrf_LowCMA"] = ComplexityMatrixCell("LowGrf", "LowCMA", "Low")
            self.cells["ModGrf_LowCMA"] = ComplexityMatrixCell("ModGrf", "LowCMA", "Low")
            self.cells["HighGrf_LowCMA"] = ComplexityMatrixCell("HighGrf", "LowCMA", "Moderate")
            self.cells["LowGrf_ModCMA"] = ComplexityMatrixCell("LowGrf", "ModCMA", "Low")
            self.cells["ModGrf_ModCMA"] = ComplexityMatrixCell("ModGrf", "ModCMA", "Low")
            self.cells["HighGrf_ModCMA"] = ComplexityMatrixCell("HighGrf", "ModCMA", "Moderate")
            self.cells["LowGrf_HighCMA"] = ComplexityMatrixCell("LowGrf", "HighCMA", "Moderate")
            self.cells["ModGrf_HighCMA"] = ComplexityMatrixCell("ModGrf", "HighCMA", "Moderate")
            self.cells["HighGrf_HighCMA"] = ComplexityMatrixCell("HighGrf", "HighCMA", "Moderate")
        elif(stance=="Single Leg"):
            self.cells["LowGrf_LowCMA"] =ComplexityMatrixCell("LowGrf", "LowCMA", "Low")
            self.cells["ModGrf_LowCMA"] =ComplexityMatrixCell("ModGrf", "LowCMA", "Moderate")
            self.cells["HighGrf_LowCMA"] = ComplexityMatrixCell("HighGrf", "LowCMA", "High")
            self.cells["LowGrf_ModCMA"] =ComplexityMatrixCell("LowGrf", "ModCMA", "Moderate")
            self.cells["ModGrf_ModCMA"] =ComplexityMatrixCell("ModGrf", "ModCMA", "Moderate")
            self.cells["HighGrf_ModCMA"] = ComplexityMatrixCell("HighGrf", "ModCMA", "High")
            self.cells["LowGrf_HighCMA"] = ComplexityMatrixCell("LowGrf", "HighCMA", "High")
            self.cells["ModGrf_HighCMA"] = ComplexityMatrixCell("ModGrf", "HighCMA", "High")
            self.cells["HighGrf_HighCMA"]= ComplexityMatrixCell("HighGrf", "HighCMA", "High")

    def add_step(self, step):
        if(step.total_accel_avg is not None and step.total_accel_avg >0 and step.peak_grf is not None):
            if(step.total_accel_avg < 45 and step.peak_grf <2):
               self.cells["LowGrf_LowCMA"].add_step(step)
            
            elif(step.total_accel_avg < 45 and step.peak_grf >=2 and step.peak_grf<3):
                self.cells["ModGrf_LowCMA"].add_step(step)
            
            elif(step.total_accel_avg < 45 and step.peak_grf >=3):
                self.cells["HighGrf_LowCMA"].add_step(step)
            
            elif(step.total_accel_avg >= 45 and step.total_accel_avg <105 and step.peak_grf<2):
                self.cells["LowGrf_ModCMA"].add_step(step)
          
            elif(step.total_accel_avg >= 45 and step.total_accel_avg <105 and step.peak_grf >=2 and step.peak_grf<3):
                self.cells["ModGrf_ModCMA"].add_step(step)
          
            elif(step.total_accel_avg >= 45 and step.total_accel_avg <105 and step.peak_grf >=3):
                self.cells["HighGrf_ModCMA"].add_step(step)

            elif(step.total_accel_avg >105 and step.peak_grf<2):
                self.cells["LowGrf_HighCMA"].add_step(step)
 
            elif(step.total_accel_avg >105 and step.peak_grf >=2 and step.peak_grf<3):
                self.cells["ModGrf_HighCMA"].add_step(step)
 
            elif(step.total_accel_avg >105 and step.peak_grf >=3):
                self.cells["HighGrf_HighCMA"].add_step(step)

    def get_motion_complexity(self, complexity_level, interpolate_steps=False):
        complexity = MotionComplexity(complexity_level, self.stance)
        for c,k in self.cells.items():
            if(k.complexity_level == complexity_level):
                #add interpolation of steps if requested
                if(interpolate_steps==True):
                    if(len(k.left_steps)>0 and len(k.right_steps)>0):
                        if(len(k.left_steps)>len(k.right_steps)):
                            diff = len(k.left_steps)-len(k.right_steps)
                            k.right_steps = self.interpolate_steps(k.right_steps, diff, "Right", self.stance)
                        
                        elif(len(k.right_steps)>len(k.left_steps)):
                            diff = len(k.right_steps)-len(k.left_steps)
                            k.left_steps = self.interpolate_steps(k.left_steps, diff, "Left", self.stance)
                for left in k.left_steps:
                    complexity.add_step(left)
                for right in k.right_steps:
                    complexity.add_step(right)
        return complexity

    def create_interpolated_step(self, step_list, orientation, diff_index,max_diff):
        new_step = Step(orientation=orientation)
        cumul_end_time_list = list(x.cumulative_end_time for x in step_list if x.cumulative_end_time is not None)
        cumul_seconds_marker = step_list[diff_index-1].cumulative_end_time + (max_diff/2)

        property_list = [
            "adduc_ROM",
            "adduc_motion_covered",
            "flex_ROM",
            "flex_motion_covered",
            "adduc_ROM_hip",
            "adduc_motion_covered_total_hip",
            "flex_ROM_hip",
            "flex_motion_covered_total_hip",
            ]

        for p in property_list:
            value_list = []
            for item in step_list:
                if(getattr(item,p) is not None):
                    value_list.append(getattr(item,p))
            setattr(new_step,p,np.interp(cumul_seconds_marker, cumul_end_time_list, value_list))
            new_step.cumulative_end_time = cumul_seconds_marker

        return new_step


    def interpolate_steps(self, step_list, number_of_steps_to_add, new_step_orientation, stance):
        new_steps = []
        for s in range(0,number_of_steps_to_add):
            #first find the largest difference between two steps
            #assumes steps are ordered from earliest to latest
            max_diff =0
            diff_index = 0
            for st in range(1, len(step_list)): #start at second Step
                if(step_list[st].cumulative_end_time-step_list[st-1].cumulative_end_time > max_diff):
                    max_diff = step_list[st].cumulative_end_time-step_list[st-1].cumulative_end_time
                    diff_index = st

            
            #now, knowing the largest gap, let's interpolate a Step
            new_step = self.create_interpolated_step(step_list,new_step_orientation,diff_index, max_diff)
            new_step.stance = stance
            step_list.insert(diff_index,new_step) #adds new Step to step_list in the interpolated position
            
        return step_list
            

            

            