# -*- coding: utf-8 -*-
"""
Created on Wed Jun 22 12:11:52 2016

@author: Ankur
"""

import logging

import numpy as np

from phaseID import phase_id


logger = logging.getLogger()
    
    
def sync_time(imp_rf, imp_lf, sampl_rate):

    """Determine the land time on impact for right and left feet.
    
    Args:
        imp_rf: right foot phase
        imp_lf: left foot phase
        sampl_rate: int, sampling rate of sensor

    Returns:
        diff: array, time difference between right and left feet impacts
        ltime_index: array, index when land time is determined
        lf_rf_imp_indicator: array, indicate whether right/left foot impacted
        the ground first
    """
        
    rf_start = _zero_runs(imp_time=imp_rf, rf_or_lf='rf')  # obtaining the first instant 
    # of the impact phases of the right foot
    lf_start = _zero_runs(imp_time=imp_lf, rf_or_lf='lf')  # obtaining the first instant 
    # of the impact phases of the left foot
    
    # delete phase variables
    del imp_rf, imp_lf

    # initialize variables
    diff = []  # initialize list to store the difference in impact times
    ltime_index = []  # initialize list to store index for land time
    lf_rf_imp_indicator = []  # initialize list to indicate whether right/left
    # foot impacted the ground first

    # determine false impacts
    for i in enumerate(rf_start):
        for j in enumerate(lf_start):
            if abs(lf_start[j[0]] - rf_start[i[0]]) <= 0.3*sampl_rate:
            # checking for false impact phases
                if lf_start[j[0]] < rf_start[i[0]]:  # check if left foot
                # impacts first
                    diff.append(-(lf_start[j[0]] - rf_start[i[0]])\
                    /float(sampl_rate)*1000)
                    # appending the difference of time of impact between
                    # left and right feet, dividing by the sampling rate to
                    # convert the time difference to milli seconds
                    ltime_index.append(int(j[1]))
                    lf_rf_imp_indicator.append('l')
                elif lf_start[j[0]] > rf_start[i[0]]:  # check if right foot
                # impacts first
                    diff.append((rf_start[i[0]] - lf_start[j[0]])\
                    /float(sampl_rate)*1000)
                    ltime_index.append(int(i[1]))
                    lf_rf_imp_indicator.append('r')
                elif lf_start[j[0]] == rf_start[i[0]]:  # check impact time of
                # right foot equals left foot
                    diff.append(0.0)
                    ltime_index.append(int(i[1]))
                    lf_rf_imp_indicator.append('n')
          
    return np.array(diff).reshape(-1, 1), \
    np.array(ltime_index).reshape(-1, 1), \
    np.array(lf_rf_imp_indicator).reshape(-1, 1)
    
    
#def _imp_start_time(imp_time):
#    """Determine the beginning of each impact.
#    
#    Args:
#        imp_time: right/left foot phase
#        
#    Returns:
#        first_instance_imp: a list containing the first instance of impact for
#        right/left foot
#    """
#    
#    first_instance_imp = []  # initializing a list
#    count = 0  # initializing a count variable
#    for i in enumerate(imp_time):
#        if imp_time[i[0]] == phase_id.lf_imp.value \
#        or imp_time[i[0]] == phase_id.rf_imp.value:  # checking if an impact
#        # phase exists (4 for left foot; 5 for right foot)
#            if count < 1:
#                first_instance_imp.append(i[0])  # appending the first instance
#                # of an impact phase
#                count = count + 1
#        elif imp_time[i[0]] == phase_id.rflf_ground.value \
#        or imp_time[i[0]] == phase_id.lf_ground.value \
#        or imp_time[i[0]] == phase_id.rf_ground.value \
#        or imp_time[i[0]] == phase_id.rflf_offground.value:
#            count = 0
#                        
#    return first_instance_imp
    
    
def _zero_runs(imp_time, rf_or_lf):

    """
    Determine the beginning of each impact.
    Args:
        imp_time: array, right/left foot phase
        rf_or_lf: string, indicator for right/left foot
    Returns:
        ranges: array, first instance of impact for right/left foot
    """
    
    if 'r' in rf_or_lf:
        imp_value = phase_id.rf_imp.value
    elif 'l' in rf_or_lf:
        imp_value = phase_id.lf_imp.value

    # determine where column data is NaN
    isnan = np.array(np.array(imp_time==imp_value).astype(int)).reshape(-1, 1)
    del imp_time  # not used in further computations
#    isnan = isnan[miss_type != intentional_missing_data]  # subsetting for when
    # missing value is an intentional blank
#    del miss_type  # not used in further computations
    
    if isnan[0] == 1:
        t_b = 1
    else:
        t_b = 0
        
    # mark where column data changes to and from NaN
    absdiff = np.abs(np.ediff1d(isnan, to_begin=t_b))
    if isnan[-1] == 1:
        absdiff = np.concatenate([absdiff, [1]], 0)
    del isnan  # not used in further computations

    # determine the number of consecutive NaNs
    ranges = np.where(absdiff == 1)[0].reshape((-1, 2))

    return ranges[:,0]


def landing_pattern(rf_euly, lf_euly, land_time_index, l_r_imp_ind, sampl_rate,
                    land_time):
    
    """Determine the pitch angle of the right and left feet on impact.
    
    Args:
        rf_euly: right foot pitch angles
        lf_euly: left foot pitch angles
        land_time_index: right and left landing times indexes
        l_r_imp_indicator: an array, indicator for right/left impacting the 
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
            out_pattern.append([np.rad2deg(rf_euly[int(i)]),
                                np.rad2deg(lf_euly[i+\
                                int(abs(k)/1000*sampl_rate)])])
        elif j == 'r':
            out_pattern.append([np.rad2deg(rf_euly[int(i)]),
                                np.rad2deg(lf_euly[i-\
                                int(abs(k)/1000*sampl_rate)])])
        elif j == 'n':
            out_pattern.append([np.rad2deg(rf_euly[int(i)]),
                                np.rad2deg(lf_euly[int(i)])])

    return np.array(out_pattern).reshape(-1, 2)


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
    

if __name__ == '__main__':
    
    import matplotlib.pyplot as plt
    from phaseDetection import combine_phase
    import time
    
    file_name = '250to125_Ivonna_Combined_Sensor_Transformed_Data.csv'
    data = np.genfromtxt(file_name, names=True, delimiter=',', dtype=float)
    
    hz = 125
    
    lf_ph, rf_ph = combine_phase(data['LaZ'], data['RaZ'], hz)
    
    start_time = time.time()
    n_landtime, ltime_index, lf_rf_imp_indicator = sync_time(rf_ph, lf_ph, hz)
    
    n_landpattern = landing_pattern(data['RaZ'], data['LaZ'],
                                    land_time_index=ltime_index,
                                    l_r_imp_ind=lf_rf_imp_indicator,
                                    sampl_rate=hz, land_time=n_landtime)
    land_time, land_pattern = continuous_values(n_landpattern, n_landtime,
                                                len(data), ltime_index)

    print time.time() - start_time
    
#    plt.figure(1)
#    plt.title('left foot')
#    plt.plot(data['LaZ'])
#    plt.plot(lf_ph)
#    plt.show()
#    
#    plt.figure(2)
#    plt.title('right foot')
#    plt.plot(data['RaZ'])
#    plt.plot(rf_ph)
#    plt.show()
