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
    ground = 0  # when the foot is on the ground
    air = 1  # when the foot is in the air
    impact = 2  # when the foot impacts the ground
    takeoff = 3  # when the foot is taking off from the ground (from impact or balance)
