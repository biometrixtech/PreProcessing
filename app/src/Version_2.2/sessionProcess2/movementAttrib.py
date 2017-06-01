# -*- coding: utf-8 -*-
"""
Created on Thu Oct 13 08:13:38 2016

@author: court
"""

import numpy as np


""""Calculate Movement Attributes and Performance Variables.
    Performance Variables:
        total acceleration
    Movement Attributes:
        [plane]
            -horizontal
            -lateral
            -vertical
            -rotational
            -stationary
        [stance]
            -feet eliminated
            -double leg
            -single leg
                -stationary
                -dynamic
                
"""

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
    
#     # instantaneous calculation
#    for i in range(len(hip_acc_aif)):
#        AccelMag[i]=np.sqrt(hip_acc_aif[i][0]**2+hip_acc_aif[i][1]**2 \
#                            +hip_acc_aif[i][2]**2)

    return accel_mag
    
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
    motion_proportion = hip_acc/accel_mag
    del hip_acc  # not used in further computations
    lat = motion_proportion[:, 0].reshape(-1, 1)
    vert = motion_proportion[:, 1].reshape(-1, 1)
    horz = motion_proportion[:, 2].reshape(-1, 1)
    del motion_proportion  # not used in further computations

    # give binaries value according to instantaneous percentages of each
        # plane of motion
    stationary_binary[(accel_mag<0.75)] = 1
    lat_binary[(lat>0.15) & (stationary_binary==0)] = 1
    vert_binary[(vert>0.15) & (stationary_binary==0)] = 1
    horz_binary[(horz>0.15) & (stationary_binary==0)] = 1
    rot_binary[(rot>0.2) & (stationary_binary==0)] = 1
    
    return lat, vert, horz, rot, lat_binary, vert_binary, horz_binary,\
            rot_binary, stationary_binary, accel_mag.reshape(-1, 1)
    
    
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

    # make copy of relevant data
    hip_y = np.copy(hip_eul)
    del hip_eul  # not used in further computations
    hip_y = hip_y[:,1][:].reshape(-1, 1)

    # set threshold for standing
    _standing_thresh = np.pi/4

    # create binary array based on elements' relation to threshold
    hip_y[np.where(hip_y > _standing_thresh)] = 0
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
    
    
def double_or_single_leg(lf_ph, rf_ph, stand, hz):
    
    """Determine when the subject is standing on a single leg vs. both legs.
    Heavily dependent on phase data.
    
    Args:
        lf_phase: left foot phase
        rf_phase: right foot phase
        standing: string of binaries where 1 indicates standing position, 0
            indicates not standing position
        hz: an int, sampling rate of sensor
    
    Returns:
        double_leg: string of binaries where 1 indicates standing on both legs,
            0 indicates other position
        single_leg: string of binaries where 1 indicates standing on one leg,
            0 indicates other position
        feet_eliminated: string of binaries where 1 indicates no feet on ground,
            0 indicates some contact with ground
    
    """
    
    # reshape inputs from flats to multidimensional arrays
    lf_phase = np.copy(lf_ph.reshape(-1,))
    rf_phase = np.copy(rf_ph.reshape(-1,))
    standing = np.copy(stand.reshape(-1,))
    
    # delete variables that are not being used in further computations
    del lf_ph, rf_ph, stand
    
    # isolate only phases for acceleration measured standing
    _lf_phase_iso_stand = (lf_phase + 1)*standing
    _lf_phase_iso_stand = _lf_phase_iso_stand.astype(int) - 1
    _rf_phase_iso_stand = (rf_phase + 1)*standing
    _rf_phase_iso_stand = _rf_phase_iso_stand.astype(int) - 1
    del _rf_phase_iso_stand  # not used in further computations
    
    # create storage for variables
    double_leg = np.zeros((len(lf_phase), 1))
    single_leg = np.zeros((len(lf_phase), 1))
    feet_eliminated = np.zeros((len(lf_phase), 1))
    
    # delete variables that are not being used in further computations
    del lf_phase, rf_phase
    
    # define window to be classified as particular stance
    _double_win = int(0.5 * hz)
    _feet_elim_win = int(0.3 * hz)

    # find lengths of stretches where phase = 0 is true
    zero_indices = _num_runs(_lf_phase_iso_stand, 0)
    diff_0s = zero_indices[:, 1] - zero_indices[:, 0]

    # isolate periods of phase = 0 which are significant in length, save as
        # double leg standing
    sig_diff_0s = zero_indices[np.where(diff_0s>_double_win), :]
    del zero_indices, diff_0s  # not used in further computations
    sig_diff_0s = sig_diff_0s.reshape(len(sig_diff_0s[0]), 2)

    for i in range(len(sig_diff_0s)):
        double_leg[sig_diff_0s[i][0]:sig_diff_0s[i][1]] = 1
    del sig_diff_0s  # not used in further computations

    # find lengths of stretches where phase = 3 is true
    three_indices = _num_runs(_lf_phase_iso_stand, 3)
    del _lf_phase_iso_stand  # not used in further computations
    diff_3s = three_indices[:, 1] - three_indices[:, 0]

    # isolate periods of phase = 0 which are significant in length, save as
        # feet eliminated
    sig_diff_3s = three_indices[np.where(diff_3s>_feet_elim_win), :]
    del three_indices, diff_3s  # not used in further computations
    sig_diff_3s = sig_diff_3s.reshape(len(sig_diff_3s[0]), 2)

    for i in range(len(sig_diff_3s)):
        feet_eliminated[sig_diff_3s[i][0]:sig_diff_3s[i][1]] = 1
    del sig_diff_3s  # not used in further computations

    # where double leg standing and feet_eliminated are false, assume
        # single leg standing
    single_leg[(double_leg==0) & (feet_eliminated==0)] = 1

    return double_leg, single_leg, feet_eliminated
    
    
def stationary_or_dynamic(lf_ph, rf_ph, sing_leg, hz):
    
    """Determine when the subject is stationary or dynamic while standing on
    one leg.
    Heavily dependent on phase data.
    
    Args:
        lf_phase: left foot phase
        rf_phase: right foot phase
        single_leg: string of binaries where 1 indicates standing on a single
            leg, 0 indicates not standing position
        hz: an int, sampling rate of sensor
    
    Returns:
        stationary: string of binaries where 1 indicates stationary stance on
            one leg, 0 indicates other position
        dynamic: string of binaries where 1 indicates dynamic stance on one
            leg, 0 indicates other position
    
    """
    
    # reshape inputs from flats to multidimensional arrays
    lf_phase = np.copy(lf_ph.reshape(-1,))
    rf_phase = np.copy(rf_ph.reshape(-1,))
    single_leg = np.copy(sing_leg.reshape(-1,))
    
    # delete variables that are not being used in further computations
    del lf_ph, rf_ph, sing_leg
    
    # isolate only phases for single leg standing
    _lf_phase_iso_sing = (lf_phase + 1)*single_leg
    _lf_phase_iso_sing = _lf_phase_iso_sing.astype(int) - 1
    _rf_phase_iso_sing = (rf_phase + 1)*single_leg
    _rf_phase_iso_sing = _rf_phase_iso_sing.astype(int) - 1
    
    # create storage for variables
    stationary = np.zeros((len(lf_phase), 1))
    dynamic = np.ones((len(lf_phase), 1))
    
    # delete variables that are not being used in further computations
    del lf_phase, rf_phase, _rf_phase_iso_sing
    
    # define minimum window for "standing still"
    _stationary_win=int(0.75 * hz)

    # find lengths of stretches where right foot single leg standing is true
    one_indices = _num_runs(_lf_phase_iso_sing, 1)
    diff_1s = one_indices[:, 1] - one_indices[:, 0]

    # isolate periods of right foot single leg standing which are significant
        # in length, save as stationary
    sig_diff_1s = one_indices[np.where(diff_1s>_stationary_win), :]
    del one_indices, diff_1s  # not used in further computations
    sig_diff_1s = sig_diff_1s.reshape(len(sig_diff_1s[0]), 2)

    for i in range(len(sig_diff_1s)):
        stationary[sig_diff_1s[i][0]:sig_diff_1s[i][1]] = 1
    del sig_diff_1s  # not used in further computations

    # find lengths of stretches where left foot single leg standing is true
    two_indices = _num_runs(_lf_phase_iso_sing, 2)
    diff_2s = two_indices[:, 1] - two_indices[:, 0]

    # isolate periods of left foot single leg standing which are significant
        # in length, save as stationary
    sig_diff_2s = two_indices[np.where(diff_2s>_stationary_win), :]
    del two_indices, diff_2s  # not used in further computations
    sig_diff_2s = sig_diff_2s.reshape(len(sig_diff_2s[0]), 2)

    for i in range(len(sig_diff_2s)):
        stationary[sig_diff_2s[i][0]:sig_diff_2s[i][1]] = 1
    del sig_diff_2s  # not used in further computations

    # dynamic single leg stance is false where stationary is true or single
        # leg standing is false
    dynamic[(stationary==1)] = 0
    dynamic[(single_leg==0)] = 0

    return stationary, dynamic.reshape(-1, 1) # singleLegStat and singleLegDyn


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
