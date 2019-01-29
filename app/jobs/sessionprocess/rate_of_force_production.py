# -*- coding: utf-8 -*-
"""
Created on Wed Dec 21 08:01:53 2016

@author: ankurmanikandan
"""
from aws_xray_sdk.core import xray_recorder
import numpy as np


@xray_recorder.capture('app.jobs.sessionprocess.rate_of_force_production.detect_rate_of_force_production')
def detect_rate_of_force_production(lf_takeoff, rf_takeoff, grf, phase_lf, phase_rf, stance, hz):
    """
    Determine rate of force production.

    Args:
        lf_takeoff: 2d array, start and end indices of takeoff phase, left foot
        rf_takeoff: 2d array, start and end indices of takeoff phase, right foot
        grf: ground reaction force
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
        lf_rofp: array, rate of force absorption left foot
        rf_rofp: array, rate of force absorption right foot
    """
    double_leg = np.array([i in [3, 5] for i in stance])
    
    # determine rate of force absorption for left & right feet
    if len(lf_takeoff) != 0:
        lf_rofp = _det_lf_rf_rofp(grf=grf, s_takeoff=lf_takeoff[:, 0],
                                  e_takeoff=lf_takeoff[:, 1], stance=double_leg, hz=hz)
        lf_rofp[double_leg] = lf_rofp[double_leg] / 2
    else:
        lf_rofp = np.zeros((len(grf), 1))

    if len(rf_takeoff) != 0:
        rf_rofp = _det_lf_rf_rofp(grf=grf, s_takeoff=rf_takeoff[:, 0], 
                                  e_takeoff=rf_takeoff[:, 1], stance=double_leg, hz=hz)
        rf_rofp[double_leg] = rf_rofp[double_leg] / 2
    else:
        rf_rofp = np.zeros((len(grf), 1))
    
    return lf_rofp, rf_rofp
    

@xray_recorder.capture('app.jobs.sessionprocess.rate_of_force_production._det_lf_rf_rofp')
def _det_lf_rf_rofp(grf, s_takeoff, e_takeoff, stance, hz):
    """
    Determine rate of force absorption.

    Args:
        grf: array, grf (total not separated for legs (ideally would be separated for right/left))
        s_takeoff: array, start of takeoff phases
        e_takeoff: array, end of takeoff phases
        stance: to separate single vs double leg stances
        hz: int, sampling rate

    Returns:
        rofp: array, rate of force absorption
    """
    rofp = np.zeros((len(grf), 1))
    count = 0
    for i, j in zip(s_takeoff, e_takeoff):
        try:
            start = i + np.nanargmax(grf[i:j])
        except ValueError:
            continue
        try:
            end = start + np.where(grf[start:10] == 0)[0][0]
        except IndexError:
            end = start + np.nanargmin(grf[start:j]) + 1
        if end <= start:
            count += 1
            continue
        else:
            if end == len(grf):
                end = len(grf) - 1
            length_subset_grf = abs(end-start)
            if length_subset_grf != 0:
                denom = float(length_subset_grf)/hz
                grf_change = grf[end] - grf[start]
                if grf_change == 0:
                    count += 1
                elif grf_change < 0:
                    rofp[i:j, 0] = abs(grf_change/denom)
                elif grf_change > 0:
                    rofp[i:j, 0] = grf_change/denom
                
    return rofp
