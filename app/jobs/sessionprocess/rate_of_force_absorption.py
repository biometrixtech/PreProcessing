# -*- coding: utf-8 -*-
"""
Created on Wed Dec 21 08:01:53 2016

@author: ankurmanikandan
"""

import numpy as np


def detect_rate_of_force_absorption(lf_imp, rf_imp, grf, phase_lf, phase_rf, stance, hz):
    """
    Determine rate of force absorption.

    Args:
        lf_imp: 2d array, start and end indices of impact phase, left foot
        rf_imp: 2d array, start and end indices of impact phase, right foot
        phase_lf: left foot phase
        phase_rf: right foot phase
        stance: enumerated stance
                [0] Not standing
                [1] Feet eliminated
                [2] Single dyn balance
                [3] Single stat balance
                [4] Double dyn balance
                [5] Double stat balance
                [6] Single impact
                [7] Double impact
                [8] Single takeoff
                [9] Double takeoff
        hz: int, sampling rate

    Returns:
        lf_rofa: array, rate of force absorption left foot
        rf_rofa: array, rate of force absorption right foot
    """
    # change stance into single or doulbe leg
#    single_leg = np.array([i in [2, 3, 6, 8] for i in stance])
    double_leg = np.array([i in [3, 5] for i in stance])
    
    # determine rate of force absorption for left & right feet
    if len(lf_imp) != 0:
        lf_rofa = _det_lf_rf_rofa(grf=grf, s_imp=lf_imp[:, 0], 
                                  e_imp=lf_imp[:, 1], stance=double_leg, hz=hz)
        lf_rofa[double_leg] = lf_rofa[double_leg] / 2
    else:
        lf_rofa = np.zeros((len(grf), 1))

    if len(rf_imp) != 0:
        rf_rofa = _det_lf_rf_rofa(grf=grf, s_imp=rf_imp[:, 0], 
                                  e_imp=rf_imp[:, 1], stance=double_leg, hz=hz)
        rf_rofa[double_leg] = rf_rofa[double_leg] / 2
    else:
        rf_rofa = np.zeros((len(grf), 1))

    return lf_rofa, rf_rofa


def _det_lf_rf_rofa(grf, s_imp, e_imp, stance, hz):
    """
    Determine rate of force absorption.

    Args:
        grf: array, grf (total not separated for legs (ideally would be separated for right/left))
        s_imp: array, start of impact phases
        e_imp: array, end of impact phases
        stance: to separate single vs double leg stances
        hz: int, sampling rate

    Returns:
        rofa: array, rate of force absorption
    """
    
    rofa = np.zeros((len(grf), 1))
    count = 0
    for i, j in zip(s_imp, e_imp):
        try:
            # either pick the last zero point or the first point of detected impact phase as start
            start = i + np.where(grf[i:j]!=0)[0][0] - 1
            end = i + np.nanargmax(grf[i:j])
            if end < start:
                print('decreasing')
            length_subset_grf = abs(end-start)
        except IndexError:
            length_subset_grf = 0
        except ValueError:
            length_subset_grf = 0
        if length_subset_grf != 0:
            denom = float(length_subset_grf)/hz
            grf_change = grf[end] - grf[start]
        elif length_subset_grf == 0:
            grf_change = 0
            denom = 1.0/hz
        if grf_change > 0:
            count += 1
            rofa[i:j, 0] = grf_change/denom

    return rofa
