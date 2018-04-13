# -*- coding: utf-8 -*-
"""
Created on Wed Oct 12 11:16:55 2016

@author:Dipesh Gautam
"""

from __future__ import division

import copy
import numpy as np
#import pandas as pd


def score(data):
    """Average consistency, symmetry, control scores at sensor level,
    ankle/hip level and then average at body level
    Args:
        data : Pandas dataframe with the movement quality features, total_accel,
               grf, ms_elapsed, control score, session_type attributes
        grf_scale: scaling factor for ground reaction forces
        Returns:
        consistency, hip_consistency, ankle_consistency, consistency_lf,
        consistency_rf, symmetry, hip_symmetry, ankle_symmetry, destr_multiplier,
        dest_mech_stress, const_mech_stress, block_duration, session_duration,
        block_mech_stress_elapsed, session_mech_stress_elapsed

        Note: All symmetry and consistency scores are multiplied by grf
                for calculating weighted average while aggregating
    """
    control = copy.copy(data.control.values)

#    Calculate the destructive mechStress multiplier
    data['destr_multiplier'] = (1 - control/100)**2


#    Session duration
    ms_elapsed = np.array(data.ms_elapsed)
    data['session_duration'] = np.nan_to_num(ms_elapsed).cumsum()/np.nansum(ms_elapsed)

    return data
