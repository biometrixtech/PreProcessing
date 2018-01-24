# -*- coding: utf-8 -*-
"""
Created on Tue Dec 05 14:40:57 201

@author: court
"""

import numpy as np
import copy


def plane_analysis(hip_acc, hip_eul, ms_elapsed):
    """Define planes in which movement is occurring at a point in time.
    
    Args:
        hip_acc: hip acceleration data after coordinate frame transformation
        hip_eul: hip orientation data after coordinate frame transformation
        hz: sampling frequency
        
    Returns:
        instantaneous values and characterizing binary values for planes of
        motion:
            lat,
            vert,
            horz,
            rot,
            lat_binary,
            vert_binary,
            horz_binary,
            rot_binary,
            stationary_binary,
            accel_mag
    """

    # create storage for variables
    len_hip_acc = len(hip_acc)
    sampling_rate = 1000/ms_elapsed
    del ms_elapsed  # not used in further computations
    lat = np.empty((len_hip_acc, 1))
    vert = np.empty((len_hip_acc, 1))
    horz = np.empty((len_hip_acc, 1))
    _ang_vel = np.zeros_like(hip_eul)
    _ang_acc = np.zeros_like(hip_eul)
    _rot_mag = np.zeros((len(hip_eul), 1))
    rot = np.empty((len(hip_eul), 1))
    lat_binary = np.zeros((len_hip_acc, 1))
    vert_binary = np.zeros((len_hip_acc, 1))
    horz_binary = np.zeros((len_hip_acc, 1))
    rot_binary = np.zeros((len_hip_acc, 1))
    stationary_binary = np.zeros((len_hip_acc, 1))
    
    # define 'radius' of body to relate angular acceleration to linear accel
    RADIUS = 0.1524 # 6 inches conv. to meters
    
    # find magnitude of linear acceleration
    accel_mag = total_accel(hip_acc).reshape((len_hip_acc, 1))
    
    # calculate angular velocity
    _pos_diff = np.vstack((np.array([[0, 0, 0]]), np.diff(hip_eul, axis=0)))
    del hip_eul  # not used in further computations
    _pos_diff = np.nan_to_num(_pos_diff)
    _ang_vel = _pos_diff*sampling_rate
    del _pos_diff  # not used in further computations
    _ang_vel = np.nan_to_num(_ang_vel)
        
    # calculate angular acceleration
    _vel_diff = np.vstack((np.array([[0, 0, 0]]), np.diff(_ang_vel, axis=0)))
    del _ang_vel  # not used in further computations
    _vel_diff = np.nan_to_num(_vel_diff)
    _ang_acc = _vel_diff*sampling_rate
    del _vel_diff  # not used in further computations
    _ang_acc = np.nan_to_num(_ang_acc)

    # calculate magnitude of angular acceleration
    _rot_mag = np.sqrt(_ang_acc[:, 0]**2 + _ang_acc[:, 1]**2 +
               _ang_acc[:, 2]**2)
    del _ang_acc  # not used in further computations
        
    # relate angular acceleration to tangential linear acceleration
    rot = RADIUS/_rot_mag
    rot[(_rot_mag==0)] = 0.0
    del _rot_mag  # not used in further computations
    rot = rot.reshape(-1, 1)

    # Characterize proportion of motion of each type
    motion_proportion = np.abs(hip_acc**2/accel_mag**2)
    del hip_acc  # not used in further computations
    lat = motion_proportion[:, 0].reshape(-1, 1)
    horz = motion_proportion[:, 1].reshape(-1, 1)
    vert = motion_proportion[:, 2].reshape(-1, 1)
    del motion_proportion  # not used in further computations

    # give binaries value according to instantaneous percentages of each
        # plane of motion
    stationary_binary[(np.abs(accel_mag)<0.75)] = 1
    lat_binary[(np.abs(lat)>0.15) & (stationary_binary==0)] = 1
    vert_binary[(np.abs(vert)>0.15) & (stationary_binary==0)] = 1
    horz_binary[(np.abs(horz)>0.15) & (stationary_binary==0)] = 1
    rot_binary[(np.abs(rot)>0.2) & (stationary_binary==0)] = 1
    
    return lat, vert, horz, rot, lat_binary, vert_binary, horz_binary,\
           rot_binary, stationary_binary, accel_mag.reshape(-1, 1)


def run_stance_analysis(data):
    """Determine the subject's stance.
    
    Args:
        data: data frame including orientation and acceleration columns, phase
        
    Returns:
        stance: column of enumerated stance values, such that
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
        
    """

    # get eul data, hz, hip acc, phases from data frame
    LeX = data.LeX.reshape(-1, 1)
    LeY = data.LeY.reshape(-1, 1)
    LeZ = data.LeZ.reshape(-1, 1)

    HeX = data.HeX.reshape(-1, 1)
    HeY = data.HeY.reshape(-1, 1)
    HeZ = data.HeZ.reshape(-1, 1)

    ReX = data.ReX.reshape(-1, 1)
    ReY = data.ReY.reshape(-1, 1)
    ReZ = data.ReZ.reshape(-1, 1)

    leuls = np.hstack((LeX, LeY))
    leuls = np.hstack((leuls, LeZ))

    heuls = np.hstack((HeX, HeY))
    heuls = np.hstack((heuls, HeZ))

    reuls = np.hstack((ReX, ReY))
    reuls = np.hstack((reuls, ReZ))

    hz = 100

    HaX = data.HaX.reshape(-1, 1)
    HaY = data.HaY.reshape(-1, 1)
    HaZ = data.HaZ.reshape(-1, 1)

    hacc = np.hstack((HaX, HaY))
    hacc = np.hstack((hacc, HaZ))

    lf_ph = data.phase_lf.reshape(-1, 1)
    rf_ph = data.phase_rf.reshape(-1, 1)

    # find total accel
    hip_tot_acc = total_accel(hacc)

    # determine if standing or not
    standing, not_standing = standing_or_not(heuls, hz)

    # sort by phase
    left_dyn_balance, right_dyn_balance, double_dyn_balance, \
        left_stat_balance, right_stat_balance, double_stat_balance, \
        left_impact, right_impact, double_impact, left_takeoff, right_takeoff,\
        double_takeoff, feet_eliminated = sort_phases(lf_ph, rf_ph, not_standing, hz, hip_tot_acc)


    # enumerate stance
    stance = enumerate_stance(left_dyn_balance, right_dyn_balance, double_dyn_balance, \
        left_stat_balance, right_stat_balance, double_stat_balance, \
        left_impact, right_impact, double_impact, left_takeoff, right_takeoff,\
        double_takeoff, feet_eliminated)
    
    return stance
    
#%%
def standing_or_not(hip_eul, hz):
    """Determine when the subject is standing or not.
    
    Args:
        hip_eul: body frame euler angle position data at hip        
        hz: an int, sampling rate of sensor
        
    Returns:
        2 binary lists characterizing position:
            standing
            not_standing
    """
    
    # create storage for variables
    standing = np.zeros((len(hip_eul), 1))
    
    # define minimum window to be characterized as standing
    _standing_win=int(0.5*hz)

    # make copy of relevant data so as not to overwrite old
    hip_y = copy.deepcopy(hip_eul)
    del hip_eul  # not used in further computations
    hip_y = hip_y[:,1][:].reshape(-1, 1)

    # set threshold for standing
    _forward_standing_thresh = np.pi/2
    _backward_standing_thresh = -np.pi/4

    # create binary array based on elements' relation to threshold
    hip_y[np.where(hip_y == 0)] = 1
    hip_y[np.where(hip_y > _forward_standing_thresh)] = 0
    hip_y[np.where(hip_y < _backward_standing_thresh)] = 0
    hip_y[np.where(hip_y != 0)] = 1

    # find lengths of stretches where standing is true
    one_indices = _num_runs(hip_y, 1)
    diff_1s = one_indices[:, 1] - one_indices[:, 0]

    # isolate periods of standing which are significant in length, then mark=2
    sig_diff_1s = one_indices[np.where(diff_1s>_standing_win), :]
    del one_indices, diff_1s  # not used in further computations
    sig_diff_1s = sig_diff_1s.reshape(len(sig_diff_1s[0]), 2)

    for i in range(len(sig_diff_1s)):
        hip_y[sig_diff_1s[i][0]:sig_diff_1s[i][1]] = 2
    del sig_diff_1s  # not used in further computations

    # reset binary array to only record periods of significant standing
    hip_y[np.where(hip_y != 2)] = 0
    hip_y[np.where(hip_y != 0)] = 1

    # eliminate periods of insignificant 'not standing' by repeating method
    zero_indices = _num_runs(hip_y, 0)
    diff_0s = zero_indices[:, 1] - zero_indices[:, 0]

    sig_diff_0s = zero_indices[np.where(diff_0s<4*_standing_win), :]
    del zero_indices, diff_0s  # not used in further computations
    sig_diff_0s = sig_diff_0s.reshape(len(sig_diff_0s[0]), 2)

    for i in range(len(sig_diff_0s)):
        hip_y[sig_diff_0s[i][0]:sig_diff_0s[i][1]] = 1

    standing = hip_y
    del sig_diff_0s, hip_y  # not used in further computations
    
    # define not_standing as the points in time where subject is not standing
    not_standing = [1]*len(standing)
    not_standing = np.asarray(not_standing).reshape((len(standing), 1))
    not_standing = not_standing - standing
            
    return standing, not_standing

#%%
def sort_phases(lf_ph, rf_ph, not_standing, hz, hacc):
    '''
    Function to identify true stances according to user's position and motion.
    
    Args:
        lf_ph: left foot phase
        rf_ph: right foot phase
        not_standing: binary column of indices indicating where a user was not
            standing, according to the function standing_or_not()
        hz: frequency, expected to be 100 Hz for V2 system
        hacc: total hip acceleration magnitude across all 3 axes, according to
            the function total_accel()

    Returns:
        left_dyn_balance: binary column identifying when user is balancing on
            their left leg while in motion
        right_dyn_balance: binary column identifying when user is balancing on
            their right leg while in motio
        double_dyn_balance: binary column identifying when user is standing on
            both legs while moving (at the hips)
        left_stat_balance: binary column identifying when user is standing
            stationarily on their left leg
        right_stat_balance: binary column identifying when user is standing
            stationarily on their right leg
        double_stat_balance: binary column identifying when user is standing
            stationarily on both feet
        left_impact: binary column identifying when user is impacting the
            ground with their left foot
        right_impact: binary column identifying when user is impacting the
            ground with their right foot
        double_impact: binary column identifying when user is impacting the
            ground with both feet
        left_takeoff: binary column identifying when user is accelerating
            off of the ground from their left foot
        right_takeoff: binary column identifying when user is accelerating off
            of the ground from their right foot
        double_takeoff: binary column identifying when user is accelerating off
            of the ground from both feet
        feet_eliminated: binary column identifying when user does not have
            either foot on the ground

        
    '''

    # initialize variables
    left_dyn_balance= np.zeros((len(lf_ph), 1))
    right_dyn_balance = np.zeros((len(lf_ph), 1))
    double_dyn_balance = np.zeros((len(lf_ph), 1))

    left_stat_balance= np.zeros((len(lf_ph), 1))
    right_stat_balance = np.zeros((len(lf_ph), 1))
    double_stat_balance = np.zeros((len(lf_ph), 1))

    left_impact = np.zeros((len(lf_ph), 1))
    right_impact = np.zeros((len(lf_ph), 1))
    double_impact = np.zeros((len(lf_ph), 1))
    left_takeoff = np.zeros((len(lf_ph), 1))
    right_takeoff = np.zeros((len(lf_ph), 1))
    double_takeoff = np.zeros((len(lf_ph), 1))
    
    feet_eliminated = np.zeros((len(lf_ph), 1))

    # set single leg dynamic values according to their pure phase definitions
    left_dyn_balance[lf_ph == 1] = 1
    left_dyn_balance[rf_ph == 1] = 1
    right_dyn_balance[lf_ph == 2] = 1
    right_dyn_balance[rf_ph == 2] = 1

    left_impact[lf_ph == 4] = 1
    right_impact[rf_ph == 5] = 1

    left_takeoff[lf_ph == 6] = 1
    right_takeoff[rf_ph == 7] = 1


    # smooth dynamic balance where gaps of less than 3 ind show phase changes
#    zero_indices = _num_runs(left_dyn_balance, 0)
#    diff_0s = zero_indices[:, 1] - zero_indices[:, 0]
#
#    sig_diff_0s = zero_indices[np.where(diff_0s<3), :]
#    del zero_indices, diff_0s  # not used in further computations
#    sig_diff_0s = sig_diff_0s.reshape(len(sig_diff_0s[0]), 2)
#
#    for i in range(len(sig_diff_0s)):
#        left_dyn_balance[sig_diff_0s[i][0]:sig_diff_0s[i][1]] = 1
#    del sig_diff_0s # not used in further computations
#    
#    zero_indices = _num_runs(right_dyn_balance, 0)
#    diff_0s = zero_indices[:, 1] - zero_indices[:, 0]
#
#    sig_diff_0s = zero_indices[np.where(diff_0s<3), :]
#    del zero_indices, diff_0s  # not used in further computations
#    sig_diff_0s = sig_diff_0s.reshape(len(sig_diff_0s[0]), 2)
#
#    for i in range(len(sig_diff_0s)):
#        right_dyn_balance[sig_diff_0s[i][0]:sig_diff_0s[i][1]] = 1
#    del sig_diff_0s # not used in further computations
#    
#    one_indices = _num_runs(left_dyn_balance, 1)
#    diff_1s = one_indices[:, 1] - one_indices[:, 0]
#
#    sig_diff_1s = one_indices[np.where(diff_1s<3), :]
#    del one_indices, diff_1s  # not used in further computations
#    sig_diff_1s = sig_diff_1s.reshape(len(sig_diff_1s[0]), 2)
#
#    for i in range(len(sig_diff_1s)):
#        left_dyn_balance[sig_diff_1s[i][0]:sig_diff_1s[i][1]] = 1
#    del sig_diff_1s # not used in further computations
# 
#    one_indices = _num_runs(right_dyn_balance, 1)
#    diff_1s = one_indices[:, 1] - one_indices[:, 0]
#
#    sig_diff_1s = one_indices[np.where(diff_1s<3), :]
#    del one_indices, diff_1s  # not used in further computations
#    sig_diff_1s = sig_diff_1s.reshape(len(sig_diff_1s[0]), 2)
#
#    for i in range(len(sig_diff_1s)):        
#        right_dyn_balance[sig_diff_1s[i][0]:sig_diff_1s[i][1]] = 1
#    del sig_diff_1s # not used in further computations


    # differentiate between static and dynamic balance phases
    _acc_thresh = 2.5
    _dyn_win = int(0.5 * hz) # half a second window

    one_indices = _num_runs(left_dyn_balance, 1)
    diff_1s = one_indices[:, 1] - one_indices[:, 0]

    sig_diff_1s = one_indices[np.where(diff_1s > _dyn_win), :]
    del one_indices, diff_1s  # not used in further computations
    sig_diff_1s = sig_diff_1s.reshape(len(sig_diff_1s[0]), 2)

    for i in range(len(sig_diff_1s)):
        left_stat_balance[sig_diff_1s[i][0]:sig_diff_1s[i][1]] = 1
    del sig_diff_1s # not used in further computations

    one_indices = _num_runs(right_dyn_balance, 1)
    diff_1s = one_indices[:, 1] - one_indices[:, 0]

    sig_diff_1s = one_indices[np.where(diff_1s > _dyn_win), :]
    del one_indices, diff_1s  # not used in further computations
    sig_diff_1s = sig_diff_1s.reshape(len(sig_diff_1s[0]), 2)

    for i in range(len(sig_diff_1s)):
        right_stat_balance[sig_diff_1s[i][0]:sig_diff_1s[i][1]] = 1
    del sig_diff_1s # not used in further computations

    # remove data with acceleration from 'stationary'
    left_stat_balance[hacc > _acc_thresh] = 0
    right_stat_balance[hacc > _acc_thresh] = 0

    # clear dynamic balance where stationary balance is true
    left_dyn_balance[left_stat_balance == 1] = 0
    right_dyn_balance[right_stat_balance == 1] = 0

    # determine where double leg stance applicable

    # where single leg things overlap, assign double leg
    double_dyn_balance[(lf_ph == 1) & (rf_ph == 2)] = 1
    double_dyn_balance[(lf_ph == 0) | (rf_ph == 0)] = 1
    double_stat_balance[(left_stat_balance == 1)
                        & (right_stat_balance == 1)] = 1

    one_indices = _num_runs(double_dyn_balance, 1)
    diff_1s = one_indices[:, 1] - one_indices[:, 0]

    sig_diff_1s = one_indices[np.where(diff_1s > _dyn_win), :]
    del one_indices, diff_1s  # not used in further computations
    sig_diff_1s = sig_diff_1s.reshape(len(sig_diff_1s[0]), 2)

    for i in range(len(sig_diff_1s)):
        double_stat_balance[sig_diff_1s[i][0]:sig_diff_1s[i][1]] = 1
    del sig_diff_1s # not used in further computations

    double_stat_balance[hacc > _acc_thresh] = 0

    # where single leg things start very close to each other, assign double leg
    doub_range = 3 # radius for features to begin in for left + right to = doub

#    r_one_indices = _num_runs(right_dyn_balance, 1)
#    l_one_indices = _num_runs(left_dyn_balance, 1)
#    all_l_one_indices = np.array([])
#
#    for k in range(int(l_one_indices.shape[0])):
#
#        all_l_one_indices = np.hstack((all_l_one_indices,
#                                       np.asarray(range(l_one_indices[k, 0] 
#                                       - doub_range, l_one_indices[k, 0]
#                                       + doub_range))))
#
#    set_all_l_one_indices = set(all_l_one_indices)
#
#    for k in range(int(r_one_indices.shape[0])):
#        r_run = range(r_one_indices[k, 0] - doub_range, r_one_indices[k, 0]
#                      + doub_range)
#        r_win = set(r_run)
#        intersect = set_all_l_one_indices.intersection(r_win)
#        if len(intersect) != 0: # there are close impacts
#            # assign full value of windows containing that index to be doub leg
#            double_dyn_balance[range(r_one_indices[k, 0],
#                                     r_one_indices[k, 1])] = 1
#            for r in range(int(l_one_indices.shape[0])):
#                l_run = range(l_one_indices[r, 0], l_one_indices[r, 1])
#                l_win = set(l_run)
#                intersect2 = r_win.intersection(l_win)
#                if len(intersect2) != 0:
#                    double_dyn_balance[l_run] = 1
#                del l_run, l_win
#        del r_run, r_win
#    del r_one_indices, l_one_indices, all_l_one_indices, set_all_l_one_indices

    r_one_indices = _num_runs(right_impact, 1)

    l_one_indices = _num_runs(left_impact, 1)
    all_l_one_indices = np.array([])

    for k in range(int(l_one_indices.shape[0])):

        all_l_one_indices = np.hstack((all_l_one_indices,
                                       np.asarray(range(l_one_indices[k, 0]
                                       - doub_range, l_one_indices[k, 0]
                                       + doub_range))))

    set_all_l_one_indices = set(all_l_one_indices)

    for k in range(int(r_one_indices.shape[0])):
        r_run = range(r_one_indices[k, 0] - doub_range, r_one_indices[k, 0]
                      + doub_range)
        r_win = set(r_run)
        intersect = set_all_l_one_indices.intersection(r_win)
        if len(intersect) != 0: # there are close impacts
            # assign full value of windows containing that index to be doub leg
            double_impact[range(r_one_indices[k, 0], r_one_indices[k, 1])] = 1
            for r in range(int(l_one_indices.shape[0])):
                l_run = range(l_one_indices[r, 0], l_one_indices[r, 1])
                l_win = set(l_run)
                intersect2 = r_win.intersection(l_win)
                if len(intersect2) != 0:
                    double_impact[l_run] = 1
                del l_run, l_win
        del r_run, r_win
    del r_one_indices, l_one_indices, all_l_one_indices, set_all_l_one_indices

    r_one_indices = _num_runs(right_takeoff, 1)

    l_one_indices = _num_runs(left_takeoff, 1)
    all_l_one_indices = np.array([])

    for k in range(int(l_one_indices.shape[0])):

        all_l_one_indices = np.hstack((all_l_one_indices,
                                       np.asarray(range(l_one_indices[k, 0]
                                       - doub_range, l_one_indices[k, 0]
                                       + doub_range))))

    set_all_l_one_indices = set(all_l_one_indices)
    for k in range(int(r_one_indices.shape[0])):
        r_run = range(r_one_indices[k, 0] - doub_range, r_one_indices[k, 0]
                      + doub_range)
        r_win = set(r_run)
        intersect = set_all_l_one_indices.intersection(r_win)
        if len(intersect) != 0: # there are close impacts
            # assign full value of windows containing that index to be doub leg
            double_takeoff[range(r_one_indices[k, 0], r_one_indices[k, 1])] = 1
            for r in range(int(l_one_indices.shape[0])):
                l_run = range(l_one_indices[r, 0], l_one_indices[r, 1])
                l_win = set(l_run)
                intersect2 = r_win.intersection(l_win)
                if len(intersect2) != 0:
                    double_takeoff[l_run] = 1
                del l_run, l_win
        del r_run, r_win
    del r_one_indices, l_one_indices, all_l_one_indices, set_all_l_one_indices

    # remove data where user was not standing
    left_dyn_balance[not_standing == 1] = 0
    right_dyn_balance[not_standing == 1] = 0
    double_dyn_balance[not_standing == 1] = 0
    left_stat_balance[not_standing == 1] = 0
    right_stat_balance[not_standing == 1] = 0
    double_stat_balance[not_standing == 1] = 0
    left_impact[not_standing == 1] = 0
    right_impact[not_standing == 1] = 0
    double_impact[not_standing == 1] = 0
    left_takeoff[not_standing == 1] = 0
    right_takeoff[not_standing == 1] = 0
    double_takeoff[not_standing == 1] = 0

    # remove data where neither foot is on ground
    left_dyn_balance[lf_ph == 3] = 0
    right_dyn_balance[lf_ph == 3] = 0
    double_dyn_balance[lf_ph == 3] = 0
    left_stat_balance[lf_ph == 3] = 0
    right_stat_balance[lf_ph == 3] = 0
    double_stat_balance[lf_ph == 3] = 0
    left_impact[lf_ph == 3] = 0
    right_impact[lf_ph == 3] = 0
    double_impact[lf_ph == 3] = 0
    left_takeoff[lf_ph == 3] = 0
    right_takeoff[lf_ph == 3] = 0
    double_takeoff[lf_ph == 3] = 0
    
    feet_eliminated[lf_ph == 3] = 1

    return left_dyn_balance, right_dyn_balance, double_dyn_balance, \
           left_stat_balance, right_stat_balance, double_stat_balance, \
           left_impact, right_impact, double_impact, left_takeoff, \
           right_takeoff, double_takeoff, feet_eliminated
    


#%% helper functions

def _num_runs(arr, num):
    """
    Function that determines the beginning and end indices of stretches of
    of the same value in an array.

    Args:
        arr: array to be analyzed for runs of a value
        num: number to searched for in the array arr

    Returns:
        ranges: nx2 np.array, with each row containing start and stop + 1
            indices of runs of the value num

    Example:
    >> arr = np.array([1, 1, 2, 3, 2, 0, 0, 1, 3, 1, 1, 1, 6])
    >> _num_runs(arr, 1)
    Out:
    array([[ 0,  2],
           [ 7,  8],
           [ 9, 12]], dtype=int64)
    >> _num_runs(arr, 0)
    Out:
    array([[5, 7]], dtype=int64)

    """

    # Create an array that is 1 where a=num, and pad each end with an extra 0.
    
    iszero = np.concatenate(([0], np.equal(arr.reshape(-1,), num), [0]))
    del arr, num  # not used in further computations
    absdiff = np.abs(np.diff(iszero))
    del iszero  # not used in further computations

    # Runs start and end where absdiff is 1.
    ranges = np.where(absdiff == 1)[0].reshape(-1, 2)

    return ranges


def total_accel(hip_acc_aif):

    """Take magnitude of acceleration at each point in time.

    Arg:
        hip_acc_aif: hip acceleration in the adjusted inertial frame
        (post-coordinate frame transform) for all times in recording
    Return:
        Column of the magnitude of total acceleration for each point in time
    """
    
    accel_mag = np.empty((len(hip_acc_aif), 1))
    accel_mag = np.sqrt(hip_acc_aif[:, 0]**2 + hip_acc_aif[:, 1]**2 \
                        + hip_acc_aif[:, 2]**2)

    return accel_mag


def enumerate_stance(left_dyn_balance, right_dyn_balance, double_dyn_balance, \
        left_stat_balance, right_stat_balance, double_stat_balance, \
        left_impact, right_impact, double_impact, left_takeoff, right_takeoff,\
        double_takeoff, feet_eliminated):

    '''
    Function that takes binary columns indicating where specific stances are
    true, according to the function sort_phases(), and combines them into a
    single enumerated column

    Args:
        left_dyn_balance: binary column identifying when user is balancing on
            their left leg while in motion
        right_dyn_balance: binary column identifying when user is balancing on
            their right leg while in motion
        double_dyn_balance: binary column identifying when user is standing on
            both legs while moving (at the hips)
        left_stat_balance: binary column identifying when user is standing
            stationarily on their left leg
        right_stat_balance: binary column identifying when user is standing
            stationarily on their right leg
        double_stat_balance: binary column identifying when user is standing
            stationarily on both feet
        left_impact: binary column identifying when user is impacting the
            ground with their left foot
        right_impact: binary column identifying when user is impacting the
            ground with their right foot
        double_impact: binary column identifying when user is impacting the
            ground with both feet
        left_takeoff: binary column identifying when user is accelerating
            off of the ground from their left foot
        right_takeoff: binary column identifying when user is accelerating off
            of the ground from their right foot
        double_takeoff: binary column identifying when user is accelerating off
            of the ground from both feet
        feet_eliminated: binary column identifying when user does not have
            either foot on the ground

    Returns:
        stance: column of enumerated stance values, such that
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
    '''

    stance = np.zeros((len(left_dyn_balance), 1))

    # use order of enumeration assignment to favor later values
    # 0 is not_standing data
    stance[left_stat_balance == 1] = 3
    stance[right_stat_balance == 1] = 3
    stance[left_dyn_balance == 1] = 2
    stance[right_dyn_balance == 1] = 2
    stance[double_dyn_balance == 1] = 4
    stance[double_stat_balance == 1] = 5
    stance[left_impact == 1] = 6
    stance[right_impact == 1] = 6
    stance[double_impact == 1] = 7
    stance[left_takeoff == 1] = 8
    stance[right_takeoff == 1] = 8
    stance[double_takeoff == 1] = 9
    stance[feet_eliminated == 1] = 1

    return stance



##%% Run the data
#if __name__ == '__main__':
#    import pandas as pd
#
#    '''
#    run this on data which has been transformed and which has proper phase detection
#    
#    code flow:
#        run_stance_analysis -- 
#        pulls data from frame
#        finds total acceleration (identical to v1 version)
#        determines if data is from user standing or not (identical to v1 method)
#        sorts data into stance subcategories by phase
#        enumerates stance        
#    '''
#
#    data = 'phase_transformed_f03d706b-75cc-49db-a4ae-ca1eecca789f'
#    data = data + '.csv'
#
#    sdata = pd.read_csv(data)
#
#    stance = run_stance_analysis(sdata)
