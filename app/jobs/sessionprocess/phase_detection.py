# -*- coding: utf-8 -*-
"""
Created on Mon Dec 12 10:02:11 2016

@author: ankurmanikandan
"""
from aws_xray_sdk.core import xray_recorder
from enum import Enum
import logging
import copy

import numpy as np
from scipy.signal import butter, filtfilt

from .constants import constants as ct
from utils.detect_peaks import detect_peaks

logger = logging.getLogger()


class phase_id(Enum):
    """
    ID values for phase
    """
    ground = 0  # when the foot is on the ground
    air = 1  # when the foot is in the air
    impact = 2  # when the foot impacts the ground
    takeoff = 3  # when the foot is taking off from the ground (from impact or balance)


@xray_recorder.capture('app.jobs.sessionprocess.phase_detection.combine_phase')
def combine_phase(laz, raz, la_magn, ra_magn, grf_lf_ind, grf_rf_ind, hz):
    """
    Combines balance, foot in the air and impact phases for left and 
    right feet.
    
    Args:
        laz: an array, left foot vertical acceleration
        raz: an array, right foot vertical acceleration
        la_magn: magnitude of acceleration in left foot
        ra_magn: magnitude of acceleration in right foot
        pitch_lf: pitch for left foot
        pitch_rf: pitch for right foot
        hz: an int, sampling rate
        
    Returns:
        lf_ph: an array, different phases of left foot
        rf_ph: an array, different phases of right foot
    """
    # reshape for faster computation
    laz = laz.values.reshape(-1,)
    raz = raz.values.reshape(-1,)
    la_magn = la_magn.values.reshape(-1, )
    ra_magn = ra_magn.values.reshape(-1, )

    # Check and mark rows with missing data
    length = len(laz)
    missing_data = False
    nan_row = []
    if np.isnan(laz).any() or np.isnan(raz).any():
        missing_data = True
    if missing_data:
        nan_row = np.where(np.isnan(laz) | np.isnan(raz))[0]
        finite_row = np.array(list(set(range(length)) - set(nan_row)))
        laz = np.delete(laz, nan_row,)
        raz = np.delete(raz, nan_row,)
        la_magn = np.delete(la_magn, nan_row,)
        ra_magn = np.delete(ra_magn, nan_row,)

    # Filter through low-pass(or band-pass) filter
    laz = _filter_data(laz, filt='low', highcut=ct.cutoff_acc)
    raz = _filter_data(raz, filt='low', highcut=ct.cutoff_acc)

    la_magn = _filter_data(la_magn, filt='low', highcut=ct.cutoff_magn)
    ra_magn = _filter_data(ra_magn, filt='low', highcut=ct.cutoff_magn)


    # Get balance/movement phase and start and end of movement phase for both
    # right and left feet
    lf_ph, rf_ph, lf_sm, lf_em, rf_sm, rf_em = _body_phase(raz=ra_magn, laz=la_magn, hz=hz)


    lf_imp = _impact_detect(start_move=lf_sm, end_move=lf_em, az=laz, grf=grf_lf_ind, hz=hz)  # starting and ending point of the impact phase for the left foot
    del lf_sm, lf_em  # no use in further computations

    rf_imp = _impact_detect(start_move=rf_sm, end_move=rf_em, az=raz, grf=grf_rf_ind, hz=hz)  # starting and ending points of the impact phase for the right foot
    del rf_sm, rf_em, raz  # no use in further computations

    if len(lf_imp) > 0:  # condition to check whether impacts exist in the left foot data
        for i, j in zip(lf_imp[:, 0], lf_imp[:, 1]):
            if j == len(lf_ph):
                lf_ph[i:j] = [phase_id.impact.value]*int(j-i)
            else:
                # print(i, j)
                lf_ph[i:j+1] = [phase_id.impact.value]*int(j-i+1)  # decide impact phase for the left foot

    del lf_imp  # no use in further computation

    if len(rf_imp) > 0:  # condition to check whether impacts exist in the right foot data
        for x, y in zip(rf_imp[:, 0], rf_imp[:, 1]):
            if y == len(rf_ph):
                rf_ph[x:y] = [phase_id.impact.value]*int(y-x)
            else:
                rf_ph[x:y+1] = [phase_id.impact.value]*int(y-x+1)  # decide impact phase for the right foot
    del rf_imp  # no use in further computation

    # Insert previous value for phase where data needed to predict was missing
    if missing_data:
        lf_ph1 = np.ones(length).astype(int)
        lf_ph1[finite_row] = lf_ph
        rf_ph1 = np.ones(length).astype(int)
        rf_ph1[finite_row] = rf_ph
        for i in nan_row:
            lf_ph1[i] = lf_ph1[i-1]
            rf_ph1[i] = rf_ph1[i-1]
    else:
        lf_ph1, rf_ph1 = lf_ph, rf_ph


    phase_lf = _detect_takeoff(lf_ph)
    phase_rf = _detect_takeoff(rf_ph)

    return phase_lf, phase_rf


@xray_recorder.capture('app.jobs.sessionprocess.phase_detection._body_phase')
def _body_phase(raz, laz, hz):
    """
    Combining phases of both left and right feet.

    Args:
        raz: an array, right foot vertical acceleration
        laz: an array, left foot vertical acceleration
        hz: an int, sampling rate of sensor

    Returns:
        phase: an array, different phases of both feet
        sm_l: start of movement phase for left foot
        em_l: end of movement phase for left foot
        sm_r: start of movement phase for right foot
        em_r: end of movement phase for right foot
    """

    r = _phase_detect(acc=raz, hz=hz)  # run phase detect on right foot

    # Determing start and end of movement phase for right foot
    r_ch = np.ediff1d(r, to_begin=0)
    sm_r = np.where(r_ch == 1)[0]
    em_r = np.where(r_ch == -1)[0]

    # if data ends with movement, assign final point as end of movement
    if len(sm_r) != len(em_r):
        em_r = np.append(em_r, len(raz))
    del raz  # delete raz, no use in further computations

    l = _phase_detect(acc=laz, hz=hz)  # run phase detect on left foot

    # Determing start and end of movement phase for left foot
    l_ch = np.ediff1d(l, to_begin=0)
    sm_l = np.where(l_ch == 1)[0]
    em_l = np.where(l_ch == -1)[0]

    # if data ends with movement, assign final point as end of movement
    if len(sm_l) != len(em_l):
        em_l = np.append(em_l, len(laz))

    del laz  # delete laz, no use in further computations

    sm_l = list(sm_l)
    em_l = list(em_l)
    sm_r = list(sm_r)
    em_r = list(em_r)
    if l[0] == 1:
        sm_l.insert(0, 0)
    if r[0] == 1:
        sm_r.insert(0, 0)
    # Assign first 10 data points of movement phase as balance (take_off)  
    # TODO(Dipesh) Change this to actually have take-off phase
    tf_win = int(0.06*hz)  # window for take_off
    for i in sm_r:
        r[i:i+tf_win] = [0]*len(r[i:i+tf_win])
    for j in sm_l:
        l[j:j+tf_win] = [0]*len(l[j:j+tf_win])

    return np.array(l), np.array(r), sm_l, em_l, sm_r, em_r


@xray_recorder.capture('app.jobs.sessionprocess.phase_detection._phase_detect')
def _phase_detect(acc, hz):
    """
    Detect when foot is on the ground vs. when foot is in the air
    
    Args:
        acc: an array, foot acceleration in the adjusted inertial frame
        hz: an int, sampling rate of sensor
        
    Returns:
        bal_phase: an array, returns 1's and 0's for foot in the air
        and foot on the ground respectively
    """

    thresh = ct.thresh  # threshold to detect balance phase
    bal_win = ct.bal_win  # sampling window to determine balance phase

    dummy_balphase = []  # dummy variable to store indexes of balance phase

    abs_acc = abs(acc)  # creating an array of absolute acceleration values
    len_acc = len(acc)  # length of acceleration value

    for i in range(len_acc-bal_win):
        # check if all the points within bal_win of current point are within
        # movement threshold
        if len(np.where(abs_acc[i:i+bal_win] <= thresh)[0]) == bal_win:
            dummy_balphase += range(i, i+bal_win)
  
    # delete variables that are of no use in further compuations
    del acc, abs_acc

    # determine the unique indexes in the dummy list
    start_bal = []    
    start_bal = np.unique(dummy_balphase)
    start_bal = np.sort(start_bal)
    start_bal = start_bal.tolist()  # convert from numpy array to list
    # delete variables that are of no use in further compuations
    del dummy_balphase

    # eliminate false movement phases 
    min_thresh_mov = ct.min_thresh_mov  # threshold for min number of samples required to be classified as false movement phase
    for i in range(len(start_bal) - 1):
        diff = start_bal[i+1] - start_bal[i]
        if 1 < diff <= min_thresh_mov:
            for j in range(1, diff+1):
                start_bal.append(start_bal[i]+j)

    # create balance phase array
    bal_phase = np.ones(len_acc).astype(int)  # 1=movement phase
    bal_phase[start_bal] = 0  # 0=balance phase

    return bal_phase


@xray_recorder.capture('app.jobs.sessionprocess.phase_detection._impact_detect')
def _impact_detect(start_move, end_move, az, grf, hz):
    """
    Detect when impact occurs.

    Args:
        start_move: an array, indexes when 'foot in the air' phase begins for 
        left/right foot
        end_move: an array, indexes when 'foot in the air' phase ends for 
        left/right foot
        az: an array, vertical acceleration of left/right foot
        hz: an int, sampling rate of sensor

    Returns:
        imp: 2d array,indexes of impact phase for left/right foot
    """
    min_air_time = ct.min_air_time
    imp_len = ct.imp_len  # smallest impact window
    end_imp_thresh = ct.end_imp_thresh

    impacts = np.empty((0, 2))
    for i, j in zip(start_move, end_move):
        grf_sub = grf[i:j]
        ranges, lengths = _zero_runs(grf_sub, 1)
        for imp, length in zip(ranges, lengths):
            imp += i
            if imp[0] != i and length >= imp_len:
                imp[1] -= 1
                impacts = np.append(impacts, imp.reshape(-1, 2), axis=0)

    return impacts.astype(int)


@xray_recorder.capture('app.jobs.sessionprocess.phase_detection._detect_takeoff')
def _detect_takeoff(phase):
    imp_range, imp_len = _zero_runs(col_dat=phase, static=2)
    phase_copy = copy.copy(phase)
    takeoff = []

    # takeoffs from impact
    air_lf = np.array([i == 1 for i in phase_copy]).astype(int)
    air_lf[np.where(phase == 2)[0]] = 3
    impact_to_air = np.where(np.ediff1d(air_lf, to_begin=0) == -2)[0]

    for i in impact_to_air:
        # find when this impact started
        try:
            impact_start = imp_range[np.where(imp_range[:, 1] == i)[0], 0]
            takeoff_len = int((i - impact_start[0])/2)
            takeoff.append(np.arange(i - takeoff_len, i))
        except IndexError:
            pass
            # print(i)
            # print(impact_start)
    if len(takeoff) > 0:
        takeoff_all = np.concatenate(takeoff).ravel()
        phase[takeoff_all] = 3

    return phase


@xray_recorder.capture('app.jobs.sessionprocess.phase_detection._filter_data')
def _filter_data(x, filt='band', lowcut=0.1, highcut=40, fs=97.5, order=4):
    """forward-backward bandpass butterworth filter
    defaults:
        lowcut freq: 0.1
        hicut freq: 20
        sampling rage: 100hz
        order: 4"""
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    if filt == 'low':
        b, a = butter(order, high, btype='low', analog=False)
    elif filt == 'band':
        b, a = butter(order, [low, high], btype='band', analog=False)
    return filtfilt(b, a, x, axis=0)


@xray_recorder.capture('app.jobs.sessionprocess.phase_detection._zero_runs')
def _zero_runs(col_dat, static):
    """
    Determine the start and end of each impact.

    Args:
        col_dat: array, algorithm indicator
        static: int, indicator for static algorithm
    Returns:
        ranges: 2d array, start and end of each static algorithm use
        length: length of
    """

    # determine where column data is the relevant impact phase value
    isnan = np.array(np.array(col_dat == static).astype(int)).reshape(-1, 1)

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
    length = ranges[:, 1] - ranges[:, 0]

    return ranges, length
    