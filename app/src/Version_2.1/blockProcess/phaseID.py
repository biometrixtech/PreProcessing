# -*- coding: utf-8 -*-
"""
Created on Sun Jul 10 10:55:04 2016

@author: Ankur
"""

from enum import Enum

class phase_id(Enum):
    
    """
    ID values for phase
    
    """
    
    rflf_ground = 0  # when both feet are on the ground
    lf_ground = 1  # when the left foot is on the ground and the right foot is in the air
    rf_ground = 2  # when the right foot is on the ground and the left foot is in the air
    rflf_offground = 3  # when both the left and the right feet are in the air
    lf_imp = 4  # when the left foot impacts the ground
    rf_imp = 5  # when the right foot impacts the ground