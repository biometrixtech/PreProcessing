# -*- coding: utf-8 -*-
"""
Created on Mon Dec 12 10:02:11 2016

@author: ankurmanikandan
"""
from aws_xray_sdk.core import xray_recorder
from enum import Enum
import logging
import pandas as pd
import numpy as np

from .constants import constants as ct
from utils import filter_data, get_ranges

logger = logging.getLogger()


class PhaseId(Enum):
    """
    ID values for phase
    """
    ground = 0  # when the foot is on the ground
    air = 1  # when the foot is in the air
    impact = 2  # when the foot impacts the ground
    takeoff = 3  # when the foot is taking off from the ground (from impact or balance)


@xray_recorder.capture('app.jobs.sessionprocess.phase_detection.combine_phase')
def combine_phase(laz, raz, grf_lf_ind, grf_rf_ind, hz, acc_hip_z, acc_hip_x, total_accel):
    """
    Combines balance, foot in the air and impact phases for left and
    right feet.

    Args:
        laz: left foot vertical acceleration
        raz: right foot vertical acceleration
        grf_lf_ind: indicator for non-zero grf for left foot
        grf_rf_ind: indicator for non-zero grf for right foot
        hz: an int, sampling rate
        acc_hip_z: hip vertical acceleration
        acc_hip_x: hip x acceleration
        total_accel: total center of mass acceleration

    Returns:
        phase_lf: an array, different phases of left foot
        phase_rf: an array, different phases of right foot
    """
    # reshape for faster computation
    laz = laz.values.reshape(-1, )
    raz = raz.values.reshape(-1, )

    # Check and mark rows with missing data
    length = len(laz)
    missing_data = False
    nan_row = []
    if np.isnan(laz).any() or np.isnan(raz).any():
        missing_data = True
    if missing_data:
        nan_row = np.where(np.isnan(laz) | np.isnan(raz))[0]
        finite_row = np.array(list(set(range(length)) - set(nan_row)))
        laz = np.delete(laz, nan_row, )
        raz = np.delete(raz, nan_row, )

    # Filter through low-pass filter
    la_magn = filter_data(laz, filt='low', highcut=ct.cutoff_magn, fs=hz)
    ra_magn = filter_data(raz, filt='low', highcut=ct.cutoff_magn, fs=hz)

    acc_hip_z = filter_data(acc_hip_z, filt='low', highcut=6)
    acc_hip_x = filter_data(acc_hip_x, filt='low', highcut=40)
    acc_hip = filter_data(total_accel, filt='low', highcut=15)

    # Get balance/movement phase and start and end of movement phase for both
    # right and left foot
    lf_ph, lf_sm, lf_em = _body_phase(la_magn, hz)
    rf_ph, rf_sm, rf_em = _body_phase(ra_magn, hz)

    _impact_detect(phase=lf_ph,
                   start_move=lf_sm,
                   end_move=lf_em,
                   grf=grf_lf_ind,
                   acc_hip_z=acc_hip_z,
                   acc_hip_x=acc_hip_x,
                   acc_hip=acc_hip)  # detect and add impacts
    del lf_sm, lf_em  # no use in further computations

    _impact_detect(phase=rf_ph,
                   start_move=rf_sm,
                   end_move=rf_em,
                   grf=grf_rf_ind,
                   acc_hip_z=acc_hip_z,
                   acc_hip_x=acc_hip_x,
                   acc_hip=acc_hip)  # detect and add impacts
    del rf_sm, rf_em, raz  # no use in further computations

    # Insert previous value for phase where data needed to predict was missing
    if missing_data:
        phase_lf = np.ones(length).astype(int)
        phase_lf[finite_row] = lf_ph
        phase_rf = np.ones(length).astype(int)
        phase_rf[finite_row] = rf_ph
        for i in nan_row:
            phase_lf[i] = phase_lf[i - 1]
            phase_rf[i] = phase_rf[i - 1]
    else:
        phase_lf, phase_rf = lf_ph, rf_ph

    return phase_lf, phase_rf


@xray_recorder.capture('app.jobs.sessionprocess.phase_detection._body_phase')
def _body_phase(acc_z, hz):
    """
    Get movement vs static phase.

    Args:
        acc_z: an array, vertical acceleration for given foot
        hz: an int, sampling rate of sensor

    Returns:
        phase: an array, different phases (ground/air) of given foot
        start_mov: start of movement phase
        end_mov: end of movement phase
    """
    phase = _phase_detect(acc_z)

    # Determing start and end of movement phase for right foot
    change = np.ediff1d(phase, to_begin=0)
    start_mov = np.where(change == 1)[0]
    end_mov = np.where(change == -1)[0]

    # if data ends with movement, assign final point as end of movement
    if len(start_mov) != len(end_mov):
        end_mov = np.append(end_mov, len(acc_z))
    del acc_z  # delete acc_z, no use in further computations

    start_mov = list(start_mov)
    end_mov = list(end_mov)
    if phase[0] == 1:
        start_mov.insert(0, 0)
    # Assign first 10 data points of movement phase as balance (take_off)
    # TODO Change this to actually have take-off phase
    tf_win = int(0.30 * hz)  # window for take_off
    for i in start_mov:
        phase[i:i + tf_win] = [0] * len(phase[i:i + tf_win])
    for j in end_mov:
        phase[j - tf_win:j] = [0] * len(phase[j - tf_win:j])
    return np.array(phase), start_mov, end_mov


@xray_recorder.capture('app.jobs.sessionprocess.phase_detection._phase_detect')
def _phase_detect(acc_z):
    """detect movement vs balance phase
    """
    acc_mag_sd = pd.Series(acc_z).rolling(100).std(center=True)
    min_sd = 1.5
    mov = np.where(acc_mag_sd >= min_sd)[0]
    phase = np.zeros(len(acc_z)).astype(int)
    phase[mov] = 1

    return phase


@xray_recorder.capture('app.jobs.sessionprocess.phase_detection._impact_detect')
def _impact_detect(phase, start_move, end_move, grf, acc_hip_z, acc_hip_x, acc_hip):
    """
    Update phase with impacts and takeoffs

    Args:
        phase: array, with ground/air phases
        start_move: an array, indexes when 'foot in the air' phase begins for 
        left/right foot
        end_move: an array, indexes when 'foot in the air' phase ends for 
        left/right foot

    Returns:
        None
    """
    min_air_time = ct.min_air_time
    imp_len = ct.imp_len  # smallest impact window
    for i, j in zip(start_move, end_move):
        if j - i < min_air_time:
            phase[i:j] = 0
        else:
            grf_sub = grf[i:j]
            ranges, lengths = get_ranges(grf_sub, 1, True)
            for imp, length in zip(ranges, lengths):
                imp += i
                if (imp[0] != i and  # can't impact from start
                        # length >= imp_len and  # make sure impact is of enough length
                        phase[imp[0] - 1] == PhaseId.air.value):  # has to be in air right before impact
                    if imp[1] == len(phase):
                        imp[1] -= 1
                    if imp[1] - imp[0] < 50:
                        acc_hip_z_step = acc_hip_z[imp[0]:imp[1]]
                        acc_hip_x_step = acc_hip_x[imp[0]:imp[1]]
                        _update_impact_start_jog(imp, acc_hip_z_step, acc_hip_x_step)
                        acc_hip_step = acc_hip[imp[0]:imp[1] + 5]
                        _update_impact_end_jog(imp, acc_hip_step)
                    if imp[1] - imp[0] > imp_len:
                        phase[imp[0]: imp[1]] = PhaseId.impact.value

    _detect_takeoff(phase)


def _update_impact_end_jog(imp, acc_hip):
    search_start_index = int(3 * len(acc_hip) / 4)
    max_index = np.where(acc_hip[search_start_index:] == max(acc_hip[search_start_index:]))[0][0] + search_start_index
    imp[1] = imp[0] + max_index
    
    # hip_acc_cross = None
    # for l in range(int(len(acc_hip) / 2), len(acc_hip) - 1):
    #     if acc_hip[l] >= 10 and acc_hip[l - 1] < 10:
    #         hip_acc_cross = l + imp[0]
    #         # break
    # if hip_acc_cross is not None:
    #     imp[1] = hip_acc_cross


def _update_impact_start_jog(imp, acc_hip_z, acc_hip_x):
    hip_x_trough = None
    hip_z_cross = None
    trough = np.where(acc_hip_x == min(acc_hip_x))[0]
    if len(trough) > 0:
        hip_x_trough = trough[0] + imp[0]
    for k in range(1, len(acc_hip_z) - 1):
        if acc_hip_z[k] >= 0 and acc_hip_z[k - 1] < 0:
            hip_z_cross = k + imp[0]
            break
    if hip_z_cross is not None and hip_x_trough is not None:
        if np.abs(hip_z_cross - hip_x_trough) <= 10:
            imp[0] = int((hip_z_cross + hip_x_trough) / 2)
        else:
            imp[0] = hip_x_trough
    elif hip_z_cross is not None and hip_x_trough is None:
        imp[0] = hip_z_cross
    elif hip_z_cross is None and hip_x_trough is not None:
        imp[0] = hip_x_trough


@xray_recorder.capture('app.jobs.sessionprocess.phase_detection._detect_takeoff')
def _detect_takeoff(phase):
    """
    Update phase with takeoffs

    Args:
        phase: array, with ground/air/impact phases
    Returns:
        None
    """
    imp_range, imp_len = get_ranges(phase, 2, True)
    takeoff = []

    # takeoffs from impact
    air = np.array([i == 1 for i in phase]).astype(int)
    air[np.where(phase == 2)[0]] = 3
    impact_to_air = np.where(np.ediff1d(air, to_begin=0) == -2)[0]
    for i in impact_to_air:
        # find when this impact started
        try:
            impact_start = imp_range[np.where(imp_range[:, 1] == i)[0], 0]
            takeoff_len = int((i - impact_start[0]) / 2)
            takeoff.append(np.arange(i - takeoff_len, i))
        except IndexError:
            print('error')
            pass
    if len(takeoff) > 0:
        takeoff_all = np.concatenate(takeoff).ravel()
        phase[takeoff_all] = 3
