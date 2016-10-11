# -*- coding: utf-8 -*-
"""
Created on Sun Jul 10 10:55:04 2016

@author: Ankur
"""

from enum import Enum

class phase_id(Enum):
    
    """Enumeration class. Assign phase values for each foot.
    
    Members:
        GROUND: left/right foot in balance phase
        IN_AIR: left/right foot in the air
        IMPACT: left/right foot impacts the ground
        
    """
    
    GROUND = 0  # right/left foot on the ground
    IN_AIR = 1  # right/left foot in the air
    IMPACT = 2  # right/left foot impact