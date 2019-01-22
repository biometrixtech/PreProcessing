# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 11:57:32 2016

@author: Gautam
"""

from __future__ import division

import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt


def prepare_data(data_in, sc, sl=False):
    """Subsets and transforms the training data as well as define features
    to be used
    Args:
        data_in: pandas dataframe or RawFrame object with the acceleration, euler
        sc: scaler model to scale data
        sl: whether is single-leg
    Returns:
        X : Predictors
        Y : Reponse (only if training)
    """

    data = pd.DataFrame()
    data['LaX'] = np.array(data_in.LaX.reshape(-1,))
    data['LaY'] = np.array(data_in.LaY)
    data['LaZ'] = np.array(data_in.LaZ)
    data['LeX'] = np.array(data_in.LeX)
    data['LeY'] = np.array(data_in.LeY)
    data['LeZ'] = np.array(data_in.LeZ)
    data['phase_lf'] = np.array(data_in.phase_lf)
    data['RaX'] = np.array(data_in.RaX)
    data['RaY'] = np.array(data_in.RaY)
    data['RaZ'] = np.array(data_in.RaZ)
    data['ReX'] = np.array(data_in.ReX)
    data['ReY'] = np.array(data_in.ReY)
    data['ReZ'] = np.array(data_in.ReZ)
    data['phase_rf'] = np.array(data_in.phase_rf)
    data['HaX'] = np.array(data_in.HaX)
    data['HaY'] = np.array(data_in.HaY)
    data['HaZ'] = np.array(data_in.HaZ)
    data['HeX'] = np.array(data_in.HeX)
    data['HeY'] = np.array(data_in.HeY)
    data['HeZ'] = np.array(data_in.HeZ)
    data['mass'] = np.array(data_in.mass)

    # create dummy variables for phase
    data.phase_lf = data.phase_lf.astype(float)
    data.phase_rf = data.phase_rf.astype(float)

    dum_phase_lf = pd.get_dummies(data.phase_lf, prefix='phase_lf').astype(float)
    dum_phase_rf = pd.get_dummies(data.phase_rf, prefix='phase_rf').astype(float)
    data = pd.concat([data, dum_phase_lf, dum_phase_rf], axis=1)
    phase_cols = {'phase_lf_0', 'phase_lf_1', 'phase_lf_2',
                  'phase_rf_0', 'phase_rf_1', 'phase_rf_2'}
    missing_cols = phase_cols - set(data.columns)
    for col in missing_cols:
        data[col] = 0

    data.loc[data.phase_lf_0 == 0, 'phase_lf_0'] = -1
    data.loc[data.phase_lf_1 == 0, 'phase_lf_1'] = -1
    data.loc[data.phase_lf_2 == 0, 'phase_lf_2'] = -1
    data.loc[data.phase_rf_0 == 0, 'phase_rf_0'] = -1
    data.loc[data.phase_rf_1 == 0, 'phase_rf_1'] = -1
    data.loc[data.phase_rf_2 == 0, 'phase_rf_2'] = -1

    # Variable for change in euler angle
    for sensor in ['L', 'H', 'R']:
        for orientation in ['X', 'Y', 'Z']:
            var1 = sensor+'e'+orientation
            var2 = sensor+'a'+orientation
            var1_d = var1+'_d'
            var2_d = var2+'_d'
            data[var1_d] = np.ediff1d(data[var1], to_begin=np.nan)
            data.loc[np.abs(data[var1_d]) > 3.00, var1_d] = 0
            data[var2_d] = np.ediff1d(data[var2], to_begin=np.nan)

    # Add variables for total acceleration in all sensors and the changes
    data['left_accel'] = np.sqrt(data.LaX**2+data.LaY**2+data.LaZ**2)
    data['hip_accel'] = np.sqrt(data.HaX**2+data.HaY**2+data.HaZ**2)
    data['right_accel'] = np.sqrt(data.RaX**2+data.RaY**2+data.RaZ**2)

    for var in ['left_accel', 'hip_accel', 'right_accel']:
        var_d = var+'_d'
        data[var_d] = np.ediff1d(data[var], to_begin=np.nan)

    # Define set of predictors to use
    if not sl:
        predictors = ['LaX', 'LaY', 'LaZ',
                      'RaX', 'RaY', 'RaZ',
                      'HaX', 'HaY', 'HaZ',
                      'LeX_d', 'LeY_d', 'LeZ_d',
                      'ReX_d', 'ReY_d', 'ReZ_d',
                      'HeX_d', 'HeY_d', 'HeZ_d',
                      'LaX_d', 'LaY_d', 'LaZ_d',
                      'RaX_d', 'RaY_d', 'RaZ_d',
                      'HaX_d', 'HaY_d', 'HaZ_d',
                      'hip_accel', 'right_accel', 'left_accel',
                      'left_accel_d', 'right_accel_d', 'hip_accel_d',
                      'mass',
                      'phase_lf_0', 'phase_lf_1', 'phase_lf_2',
                      'phase_rf_0', 'phase_rf_1', 'phase_rf_2']
    else:
        predictors = ['LaX', 'LaY', 'LaZ',
                      'RaX', 'RaY', 'RaZ',
                      'HaX', 'HaY', 'HaZ',
                      'LeX_d', 'LeY_d', 'LeZ_d',
                      'ReX_d', 'ReY_d', 'ReZ_d',
                      'HeX_d', 'HeY_d', 'HeZ_d',
                      'LaX_d', 'LaY_d', 'LaZ_d',
                      'RaX_d', 'RaY_d', 'RaZ_d',
                      'HaX_d', 'HaY_d', 'HaZ_d',
                      'hip_accel', 'right_accel', 'left_accel',
                      'left_accel_d', 'right_accel_d', 'hip_accel_d',
                      'mass']

    x = data[predictors].values

    # check for missing data in any of the predictors and mark those rows
    missing_data = False
    nan_row = []
    if np.isnan(x).any():
        missing_data = True
    if missing_data:
        nan_row = np.unique(np.where(np.isnan(x))[0])
        x = np.delete(x, nan_row, axis=0)

    # pass the data through a low pass butterworth filter
    # filtering has to be done after subsetting for nan
    x1 = x[:, 0:33]
    x2 = x[:, 33:]
    x1 = _filter_data(x1, )
    x = np.append(x1, x2, 1)
    # scale the data
    x = sc.transform(x)
    return x, nan_row


def _filter_data(x, cutoff=6, fs=100, order=4):
    """forward-backward lowpass butterworth filter
    defaults:
        cutoff freq: 12hz
        sampling rage: 100hz
        order: 4"""
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return filtfilt(b, a, x, axis=0)
