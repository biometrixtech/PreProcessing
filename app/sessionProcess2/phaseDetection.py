# -*- coding: utf-8 -*-
"""
Created on Mon Dec 12 10:02:11 2016

@author: ankurmanikandan
"""

import logging

import numpy as np
from scipy.signal import butter, filtfilt

from phaseID import phase_id
import const_thres_phase as ct

logger = logging.getLogger()


def combine_phase(laz, raz, la_magn, ra_magn, pitch_lf, pitch_rf, hz):
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
    laz = laz.reshape(-1,)
    raz = raz.reshape(-1,)
    la_magn = la_magn.reshape(-1,)
    ra_magn = ra_magn.reshape(-1,)
    pitch_lf = pitch_lf.reshape(-1,)
    pitch_rf = pitch_rf.reshape(-1,)

    # Check and mark rows with missing data
    length = len(laz)
    missing_data = False
    nan_row = []
    if np.isnan(laz).any() or np.isnan(raz).any():
        missing_data = True
    if missing_data:
        nan_row = np.where(np.isnan(laz)|np.isnan(raz))[0]
        finite_row = np.array(list(set(range(length)) - set(nan_row)))
        laz = np.delete(laz, (nan_row),)
        raz = np.delete(raz, (nan_row),)
        la_magn = np.delete(la_magn, (nan_row),)
        ra_magn = np.delete(ra_magn, (nan_row),)
        pitch_lf = np.delete(pitch_lf, (nan_row),)
        pitch_rf = np.delete(pitch_rf, (nan_row),)

    # Filter through low-pass(or band-pass) filter
    laz = _filter_data(laz, filt='low', highcut=ct.cutoff_acc)
    raz = _filter_data(raz, filt='low', highcut=ct.cutoff_acc)

    la_magn = _filter_data(la_magn, filt='low', highcut=ct.cutoff_magn)
    ra_magn = _filter_data(ra_magn, filt='low', highcut=ct.cutoff_magn)

    pitch_lf = _filter_data(pitch_lf, filt='band', lowcut=ct.lowcut_pitch, highcut=ct.highcut_pitch)
    pitch_rf = _filter_data(pitch_rf, filt='band', lowcut=ct.lowcut_pitch, highcut=ct.highcut_pitch)

    # Get balance/movement phase and start and end of movement phase for both
    # right and left feet
    ph, lf_sm, lf_em, rf_sm, rf_em = _body_phase(raz=ra_magn,
                                                 laz=la_magn, hz=hz)
#    del laz_body, raz_body
    lf_ph = list(ph)
    rf_ph = list(ph)
    del ph

    lf_imp = _impact_detect(start_move=lf_sm, end_move=lf_em, 
                            az=laz, pitch=pitch_lf, hz=hz)  # starting and ending
                            # point of the impact phase for the left foot
    del lf_sm, lf_em # no use in further computations

    rf_imp = _impact_detect(start_move=rf_sm, end_move=rf_em,
                            az=raz, pitch=pitch_rf, hz=hz)  # starting and ending
                            # points of the impact phase for the right foot
    del rf_sm, rf_em, raz  # no use in further computations

    if len(lf_imp) > 0:  # condition to check whether impacts exist in the
                         # left foot data
        for i, j in zip(lf_imp[:, 0], lf_imp[:, 1]):
            if j==len(lf_ph):
                lf_ph[i:j] = [phase_id.lf_imp.value]*int(j-i)
            else:
                lf_ph[i:j+1] = [phase_id.lf_imp.value]*int(j-i+1) # decide impact
                                                      # phase for the left foot

    del lf_imp  # no use in further computation

    if len(rf_imp) > 0:  # condition to check whether impacts exist in the
                         # right foot data
        for x, y in zip(rf_imp[:, 0], rf_imp[:, 1]):
            if y == len(rf_ph):
                rf_ph[x:y] = [phase_id.rf_imp.value]*int(y-x)
            else:
                rf_ph[x:y+1] = [phase_id.rf_imp.value]*int(y-x+1) # decide impact
                                                     # phase for the right foot
    del rf_imp  # no use in further computation

    lf_ph, rf_ph = _final_phases(rf_ph, lf_ph)

    #Insert previous value for phase where data needed to predict was missing
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

    rf_ph = np.array(rf_ph1).reshape(-1, 1)
    lf_ph = np.array(lf_ph1).reshape(-1, 1)


    return lf_ph, rf_ph


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
    sm_r = np.where(r_ch==1)[0]
    em_r = np.where(r_ch==-1)[0]

    # if data ends with movement, assign final point as end of movement
    if len(sm_r) != len(em_r):
        em_r = np.append(em_r, len(raz))
    del raz  # delete raz, no use in further computations

    l = _phase_detect(acc=laz, hz=hz)  # run phase detect on left foot

    # Determing start and end of movement phase for right foot
    l_ch = np.ediff1d(l, to_begin=0)
    sm_l = np.where(l_ch==1)[0]
    em_l = np.where(l_ch==-1)[0]

    # if data ends with movement, assign final point as end of movementß
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
    #TODO(Dipesh) Change this to actually have take-off phase
    tf_win = int(0.06*hz) # window for take_off
    for i in sm_r:
        r[i:i+tf_win] = [0]*len(r[i:i+tf_win])
    for j in sm_l:
        l[j:j+tf_win] = [0]*len(l[j:j+tf_win])

    phase = []  # store body phase decisions
    for i in range(len(r)):
        if r[i] == 0 and l[i] == 0:  # decide in balance phase
            phase.append(phase_id.rflf_ground.value)  # append to list
        elif r[i] == 1 and l[i] == 0:  # decide left foot on the ground
            phase.append(phase_id.lf_ground.value)  # append to list
        elif r[i] == 0 and l[i] == 1:  # decide right foot on the ground
            phase.append(phase_id.rf_ground.value)  # append to list
        elif r[i] == 1 and l[i] == 1:  # decide both feet off ground
            phase.append(phase_id.rflf_offground.value)  # append to list
        
    return np.array(phase), sm_l, em_l, sm_r, em_r


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
    min_thresh_mov = ct.min_thresh_mov # threshold for min number of samples 
                        # required to be classified as false movement phase
    for i in range(len(start_bal) - 1):
        diff = start_bal[i+1] - start_bal[i]
        if 1 < diff <= min_thresh_mov:
            for j in range(1, diff+1):
                start_bal.append(start_bal[i]+j)

    # create balance phase array
    bal_phase = np.ones(len_acc).astype(int)  # 1=movement phase
    bal_phase[start_bal] = 0  # 0=balance phase

    return bal_phase


def _impact_detect(start_move, end_move, az, pitch, hz):
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
    neg_thresh = ct.neg_thresh # negative threshold
    pos_thresh = ct.pos_thresh # positive threshold
    jump_thresh = ct.jump_thresh
    drop_thresh = ct.drop_thresh # Min change required after peak accel
    win = ct.win  # sampling window
    imp_len = ct.imp_len  # smallest impact window
    end_imp_thresh = ct.end_imp_thresh
    
    drop_win = ct.drop_win
    acc = 0
    start_imp = []
    end_imp = []

    detected_with_euler = 0
    for i,j in zip(start_move, end_move):
        acc = az[i:j]  # acceleration values of corresponding movement phase
        pit = pitch[i:j]

        k = min_air_time # minimum time in air before you can impact
        if k >= len(acc):
            continue
        in_air = True
        while in_air:
            max_imp = False
            if acc[k] <= neg_thresh:  # check if AccZ[k] is lesser than thresh
                if np.any(acc[k+1:k+win+1] >= acc[k] + jump_thresh):
                    # Find the max acc point in potential impact (if impact is detected, this point will be the impact start point)
                    m = np.where(acc[k+1:k+win+1] == np.nanmax(acc[k+1:k+win+1]))[0][0]
                    # Check if the acc drops by defined threshold within drop_win
                    # it's detected as impact if this condition satisfies
                    # This check is in place to rule out false impact detections 
                    # as most true impacts do have immediate downward turn
                    #TODO needs to be tuned for get better balance of  false positives vs false negatives
                    drop_win = min([drop_win, len(az[i+k+m+2:])]) # make sure that drop_win is contained within end of movement phase
                    diff = [az[i+k+m+1]]*drop_win - az[i+k+m+2:i+k+m+2+drop_win]
                    if any(diff>=drop_thresh) and acc[k+m+1] > pos_thresh:
                        start_imp_ind = i + k + m - 1
                        # if impact is detected, first check if it's end of movement phase
                        end_imp_ind = start_imp_ind + imp_len
                        if j-end_imp_ind <= end_imp_thresh:
                            start_imp.append(start_imp_ind)
                            end_imp.append(j)
                            in_air = False
                        # if not look for takeoff following the impact
                        else:
                            t = imp_len # minimum window between start of impact and start of takeoff
                            in_ground = True
                            # check if any data within a range can be detected as take_off point
                            while in_ground and t < end_imp_thresh:
                                # check if AccZ[k + t] is greater than thres
                                if acc[k + m + t] >= ct.pos_thres_takeoff:
                                    if np.any(acc[k + m + t + 1: k + m + t + win - 1] <= acc[k+m+t] - ct.jump_thres_takeoff):
                                        end_imp_ind = start_imp_ind + t + 3
                                        if np.any(acc[k+m+t] - acc[k+m+t-1] >= 2 * 9.80665):
                                            end_imp_ind = start_imp_ind + int(t/2)
                                        elif len(np.where(acc[k+m+int(t/2):k+m+t] <= - 9.80665)[0]) > 0:
                                            for l in np.where(acc[k+m+int(t/2):k+m+t] <= - 9.80665)[0]:
                                                if np.any(acc[k+m+int(t/2)+l+1:k+m+int(t/2)+l+win] > acc[k+m+int(t/2)+l] + jump_thresh):
                                                    end_imp_ind = start_imp_ind + int(t/2)
                                        in_ground = False
                                    else:
                                        t += 1
                                else:
                                    t += 1
                            # If impact is not determined by acceleration based test, try pitch based test
                            t = imp_len # reset t
                            while in_ground and t < end_imp_thresh:
                                if np.abs(pit[k + m + t]) < 5 and pit[k+m+t] - pit[k+m+t-2] > 0.:
#                                    print('detected with eulers: '+ str(end_imp_ind))
                                    detected_with_euler += 1
                                    end_imp_ind = start_imp_ind + t + 3
                                    in_ground = False
                                else:
                                    t += 1
                            # if both fail, assign the maximum threshold as end of impact
                            if in_ground and t == end_imp_thresh:
                                # check if there's a second impact somewhere
                                for l in np.arange(k + 10, k + end_imp_thresh, 1):
                                    if acc[l] <= neg_thresh:
                                        if np.any(acc[l+1:l+win+1] >= acc[l] + jump_thresh):
                                            end_imp_ind = start_imp_ind + int(1*end_imp_thresh/2)
                                    else:
                                        end_imp_ind = start_imp_ind + end_imp_thresh
                                        max_imp = True

                            # finally append the detected start and end of impact points
                            start_imp.append(start_imp_ind)
                            end_imp.append(end_imp_ind)
                            if max_imp:
                                k = end_imp_ind - i + 1
                            else:
                                k = end_imp_ind - i + 6 # TODO can't have impact start within the minimum threshold for air time
                                
                    else:
                        k += 1
                else:
                    k += 1
            else:
                k += 1
            if i + k >= j-1:
                in_air = False
        # check if there is impact at the end of movement phase,
        # if not, assign last imp_len points as impact, make sure in_air always ends with impact
        # This is used to handle low intensity activity where the threshold might not be achieved
        if j not in end_imp:
            start_imp.append(j - imp_len)
            end_imp.append(j)

    print('{} takeoffs detected with euler'.format(detected_with_euler))
    imp = [[i,j] for i,j in zip(start_imp, end_imp)]

    return np.array(imp)    


def _final_phases(rf_ph, lf_ph):
    """
    Determine the final phases of right and left feet.

    Args:
        rf_ph: a list, right foot phase
        lf_ph: a list, left foot phase

    Returns:
        lf_ph: a list, left foot final phase
        rf_ph: a list, right foot final phase
    """

    if len(rf_ph) != len(lf_ph):
        logger.warning("Rf phase and lf phase array lengths are different!")
    else:
        for i in enumerate(rf_ph):
            if rf_ph[i[0]] == phase_id.rf_imp.value and \
            lf_ph[i[0]] == phase_id.rflf_offground.value:
                lf_ph[i[0]] = phase_id.rf_ground.value
            elif lf_ph[i[0]] == phase_id.lf_imp.value and \
            rf_ph[i[0]] == phase_id.rflf_offground.value:
                rf_ph[i[0]] = phase_id.lf_ground.value

    return lf_ph, rf_ph


def _filter_data(X, filt='band', lowcut=0.1, highcut=40, fs=100, order=4):
    """forward-backward bandpass butterworth filter
    defaults:
        lowcut freq: 0.1
        hicut freq: 20
        sampling rage: 100hz
        order: 4"""
    nyq = 0.5 * fs
    low = lowcut/nyq
    high = highcut/nyq
    if filt == 'low':
        b, a = butter(order, high, btype='low', analog=False)
    elif filt == 'band':
        b, a = butter(order, [low, high], btype='band', analog=False)
    X_filt = filtfilt(b, a, X, axis=0)
    return X_filt
