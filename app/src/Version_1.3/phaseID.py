# -*- coding: utf-8 -*-
"""
Created on Sun Jul 10 10:55:04 2016

@author: Ankur
"""

from enum import Enum

class phase_id(Enum):
    
    rflf_ground = 0
    lf_ground = 1
    rf_ground = 2
    rflf_offground = 3
    lf_imp = 4
    rf_imp = 5