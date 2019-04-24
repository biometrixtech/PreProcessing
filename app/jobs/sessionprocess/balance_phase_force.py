# -*- coding: utf-8 -*-
"""
Created on Fri Dec 08 19:59:10 2017

@author: Administrator
"""
from aws_xray_sdk.core import xray_recorder
import numpy as np
from utils import get_ranges


@xray_recorder.capture('app.jobs.sessionprocess.balance_phase_force.calculate_balance_phase_force')
def calculate_balance_phase_force(data):
    accel_mag = np.sqrt(data.acc_hip_x**2 + data.acc_hip_y**2 + data.acc_hip_z**2)
    balance = np.array((data.phase_lf == 0) | data.phase_rf == 0).reshape(-1,)
#    balance = np.array([i in [2, 3, 4, 5] for i in data.stance])
    stance = np.array(data.stance)
    stance[balance] = 1
    stance[~balance] = 0
    grf = np.array(data.grf)
    grf[~balance] = np.nan
    accel_mag[~balance] = np.nan

    # start and end indices of impact phase for left and right foot
    range_bal = get_ranges(col_data=stance, value=1)
    
    # declaring variable to store the start and end of impact phase
    bal_start_stop = np.zeros(len(stance))*np.nan
    
    # assigning True when an impact phase appears
    magn_grf = np.zeros((len(grf), 1))
    for i in range(len(range_bal)):
        bal_start_stop[range_bal[i, 0]:range_bal[i, 1]] = i+1
    for s, e in zip(range_bal[:, 0], range_bal[:, 1]):
        len_bal_win = e - s
        if len_bal_win <= 50:
            grf_s = grf[s:e]
            finite_grf = grf_s[np.isfinite(grf_s)]
            if len(finite_grf) > 0:
                magn_grf[s:e, 0] = np.percentile(finite_grf, 97.5) - np.percentile(finite_grf, 2.5)
        else:
            ints = np.append(np.arange(s, e, 50), e)
            for i in range(len(ints)-1):
                start = ints[i]
                end = ints[i+1]
                grf_s = grf[start:end]
                finite_grf = grf_s[np.isfinite(grf_s)]
                if len(finite_grf) > 0:
                    magn_grf[start:end, 0] = np.percentile(finite_grf, 97.5) - np.percentile(finite_grf, 2.5)
    magn_grf[magn_grf < 30] = 0

    return magn_grf
