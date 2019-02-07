# -*- coding: utf-8 -*-
"""
Created on Wed Jun 22 12:11:52 2016

@author: Ankur
"""
from aws_xray_sdk.core import xray_recorder
import logging
import numpy as np


logger = logging.getLogger()
    

@xray_recorder.capture('app.jobs.sessionprocess.impact_cme.sync_time')
def sync_time(rf_start, lf_start, sampl_rate):
    """
    Determine the land time on impact for right and left feet.
    
    Args:
        rf_start: array, left foot impact phase start indices
        lf_start: array, right foot impact phase start indices
        sampl_rate: float, sampling rate of sensor

    Returns:
        diff: array, time difference between right and left feet impacts
        ltime_index: array, index when land time is determined
        lf_rf_imp_indicator: array, indicate whether right/left foot impacted
        the ground first
    """

    # initialize variables
    diff = []  # initialize list to store the difference in impact times
    ltime_index = []  # initialize list to store index for land time
    lf_rf_imp_indicator = []  # initialize list to indicate whether right/left
    # foot impacted the ground first
    list_rf_start = list(rf_start)  # converted array to list
    list_lf_start = list(lf_start)  # converted array to list

    # determine false impacts
    for i in list_rf_start:
        for j in list_lf_start:
            if abs(j-i) <= 0.3*sampl_rate:
                # comparing correct impacts (pairs) of right and left feet
                if j < i:  # check if left foot
                    # impacts first
                    diff.append(-(j-i)/sampl_rate*1000)
                    # appending the difference of time of impact between
                    # left and right feet, dividing by the sampling rate to
                    # convert the time difference to milli seconds
                    ltime_index.append(int(j))
                    lf_rf_imp_indicator.append('l')
                elif j > i:  # check if right foot impacts first
                    diff.append((i-j)/sampl_rate*1000)
                    ltime_index.append(int(i))
                    lf_rf_imp_indicator.append('r')
                elif j == i:  # check impact time of right foot equals left foot
                    diff.append(0.0)
                    ltime_index.append(int(i))
                    lf_rf_imp_indicator.append('n')
          
    return np.array(diff).reshape(-1, 1), np.array(ltime_index).reshape(-1, 1), np.array(lf_rf_imp_indicator).reshape(-1, 1)


@xray_recorder.capture('app.jobs.sessionprocess.impact_cme.landing_pattern')
def landing_pattern(rf_euly, lf_euly, land_time_index, l_r_imp_ind, sampl_rate,
                    land_time):
    
    """Determine the pitch angle of the right and left feet on impact.
    
    Args:
        rf_euly: right foot pitch angles
        lf_euly: left foot pitch angles
        land_time_index: right and left landing times indexes
        l_r_imp_ind: an array, indicator for right/left impacting the
        ground first
        sampl_rate: an int, sampling rate
        land_time: an array, landing time
        
    Returns:
        out_pattern: 2D array, right and left feet pitch angles on impact
    
    """
        
    out_pattern = []
    # right and left feet pitch angles on impact
    for i, j, k in zip(land_time_index, l_r_imp_ind, land_time):
        if j == 'l':
            out_pattern.append([np.rad2deg(rf_euly[int(i)]), np.rad2deg(lf_euly[i + int(abs(k)/1000*sampl_rate)])])
        elif j == 'r':
            out_pattern.append([np.rad2deg(rf_euly[int(i)]), np.rad2deg(lf_euly[i - int(abs(k)/1000*sampl_rate)])])
        elif j == 'n':
            out_pattern.append([np.rad2deg(rf_euly[int(i)]), np.rad2deg(lf_euly[int(i)])])

    return np.array(out_pattern).reshape(-1, 2)


@xray_recorder.capture('app.jobs.sessionprocess.impact_cme.continuous_values')
def continuous_values(land_pattern, land_time, data_length, landtime_index):
    
    """Make the length of land time and land pattern variables the same
    as that of the data.
    
    Args:
        land_pattern: pitch angle on impact
        land_time: time difference between left and right feet impacts
        data_length: array, length of the sensor data read from s3 bucket
        landtime_index: array, indexes when landtime is not NaN
        
    Returns:
        final_landtime: array, time difference between right and left feet
        impacts
        final_landpattern: 2D array, pitch angle on impact; right,left
    """
    
    # initialize variables
    rf_quick_pattern = []  # to store right foot euler angles
    lf_quick_pattern = []  # to store left foot euler angles
    final_landtime = []  # to store the land time difference between right
    # and left feet

    # ensure right foot land pattern variable is the same length as the
    # sensor data
    count = 0
    for i in range(data_length):
        if i in landtime_index[:, 0]:
            rf_quick_pattern.append(land_pattern[count, 0])
            count = count + 1
        else:
            rf_quick_pattern.append(np.nan)
    
    # ensure left foot land pattern variable is the same length as the
    # sensor data
    count = 0
    for i in range(data_length):
        if i in landtime_index[:, 0]:
            lf_quick_pattern.append(land_pattern[count, 1])
            count = count + 1
        else:
            lf_quick_pattern.append(np.nan)
            
    # delete variables that are not required for computation after this point
    del land_pattern
     
    # ensure land time variable is the same length as the
    # sensor data
    count = 0
    for i in range(data_length):
        if i in landtime_index[:, 0]:
            final_landtime.append(land_time[count, 0])
            count = count + 1
        else:
            final_landtime.append(np.nan)

    # delete variables that are not equired for computation after this point
    del land_time, landtime_index
    
    # merge right foot and left foot land patterns into a single variable
    final_landpattern = []
    for i, j in zip(lf_quick_pattern, rf_quick_pattern):
        final_landpattern.append([j, i])
        
    # delete variables that are not required for computation after this point
    del lf_quick_pattern, rf_quick_pattern
        
    if len(final_landpattern) != len(final_landtime):
        logger.warning('Length of land pattern and land time are not equal.')
            
    return np.array(final_landtime), np.array(final_landpattern)
