# -*- coding: utf-8 -*-
"""
Created on Thu Oct 27 17:59:58 2016

@author: Gautam
"""

from enum import Enum


class ErrorId(Enum):
    
    no_error = 0
    corrupt_magn = 1
    all_sensors = 2
    hip_left = 3
    hip_right = 4
    hip = 5
    left_right = 6
    left = 7
    right = 8
    movement = 9
    missing = 10


class ErrorMessageBase(object):
    def __init__(self, error_id):
        if error_id == 0:
            self.error_message = ""
        elif error_id == 1:
            self.error_message = "Sensor is uncalibrated, please redo setup or remove magnetic devices"
        elif error_id == 2:
            self.error_message = "All three sensors are placed incorrectly, please redo placement"
        elif error_id == 3:
            self.error_message = "Hip and Left foot sensors are placed incorrectly, please redo placement"
        elif error_id == 4:
            self.error_message = "Hip and Right foot sensors are placed incorrectly, please redo placement"
        elif error_id == 5:
            self.error_message = "Hip sensor is placed incorrectly, please redo placement"
        elif error_id == 6:
            self.error_message = "Left and right feet sensors are placed incorrectly, please redo placement"
        elif error_id == 7:
            self.error_message = "Left foot sensor is placed incorrectly, please redo placement"
        elif error_id == 8:
            self.error_message = "Right foot sensor is placed incorrectly, please redo placement"
        elif error_id == 9:
            self.error_message = "Hold position and remain motionless, please try again"
        elif error_id == 10:
            self.error_message = "Calibration failed, please try again"


class ErrorMessageSession(object):
    def __init__(self, error_id):
        if error_id == 0:
            self.error_message = ""
        elif error_id == 1:
            self.error_message = "Sensor is uncalibrated, please redo setup or remove magnetic devices"
        elif error_id == 2:
            self.error_message = "All three sensors are placed incorrectly, please redo placement"
        elif error_id == 3:
            self.error_message = "Hip and Left foot sensors are placed incorrectly, please redo placement"
        elif error_id == 4:
            self.error_message = "Hip and Right foot sensors are placed incorrectly, please redo placement"
        elif error_id == 5:
            self.error_message = "Hip sensor is placed incorrectly, please redo placement"
        elif error_id == 6:
            self.error_message = "Left and right feet sensors are placed incorrectly, please redo placement"
        elif error_id == 7:
            self.error_message = "Left foot sensor is placed incorrectly, please redo placement"
        elif error_id == 8:
            self.error_message = "Right foot sensor is placed incorrectly, please redo placement"
        elif error_id == 9:
            self.error_message = "Hold position and remain motionless before bowing, please try again"
        elif error_id == 10:
            self.error_message = "Calibration failed, please try again"


            
class RPushDataBase(object):
    def __init__(self, error_id):
        if error_id == 0:
            self.value = {"action":"run_ression_calibration"}
        elif error_id == 1:
            self.value = {"action":"run_magn_calibration"}
        elif error_id == 2:
            self.value = {"action":"run_hip_placement"}
        elif error_id == 3:
            self.value = {"action":"run_hip_placement"}
        elif error_id == 4:
            self.value = {"action":"run_hip_placement"}
        elif error_id == 5:
            self.value = {"action":"run_hip_placement"}
        elif error_id == 6:
            self.value = {"action":"run_left_placement"}
        elif error_id == 7:
            self.value = {"action":"run_left_placement"}
        elif error_id == 8:
            self.value = {"action":"run_right_placement"}
        elif error_id == 9:
            self.value = {"action":"run_base_calibration"}
        elif error_id == 10:
            self.value = {"action":"run_base_calibration"}
            
            
class RPushDataSession(object):
    def __init__(self, error_id):
        if error_id == 0:
            self.value = {"action":"select_regimen"}
        elif error_id == 1:
            self.value = {"action":"run_magn_calibration"}
        elif error_id == 2:
            self.value = {"action":"run_hip_placement"}
        elif error_id == 3:
            self.value = {"action":"run_hip_placement"}
        elif error_id == 4:
            self.value = {"action":"run_hip_placement"}
        elif error_id == 5:
            self.value = {"action":"run_hip_placement"}
        elif error_id == 6:
            self.value = {"action":"run_left_placement"}
        elif error_id == 7:
            self.value = {"action":"run_left_placement"}
        elif error_id == 8:
            self.value = {"action":"run_right_placement"}
        elif error_id == 9:
            self.value = {"action":"run_session_calibration"}
        elif error_id == 10:
            self.value = {"action":"run_session_calibration"}
            
class ErrorMessageTraining(object):
    def __init__(self, error_id):
        if error_id == 0:
            self.error_message = ""
        elif error_id == 1:
            self.error_message = "Sensor is uncalibrated, please redo setup or remove magnetic devices"
        elif error_id == 10:
            self.error_message = "Training failed, please try again"

class RPushDataTraining(object):
    def __init__(self, error_id):
        if error_id ==0:
            self.value = {"action":"train_system"}
        if error_id == 1:
            self.value = {"action":"run_magn_calibration"}
        elif error_id == 10:
            self.value = {"action":"capture_exercise"}
            
            