# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 11:57:32 2016

@author: Gautam
"""

from __future__ import division

import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt


def prepare_data(data_in, scaler_model, user_mass, is_single_leg=False):
    """Subsets and transforms the training data as well as define features
    to be used
    Args:
        data_in: pandas dataframe or RawFrame object with the acceleration, euler
        scaler_model: scaler model to scale data
        user_mass: the user's mass
        is_single_leg: whether is single-leg
    Returns:
        X : Predictors
        Y : Reponse (only if training)
    """

    data = pd.DataFrame()
    data['acc_lf_x'] = np.array(data_in.acc_lf_x.values.reshape(-1,))
    data['acc_lf_y'] = np.array(data_in.acc_lf_y)
    data['acc_lf_z'] = np.array(data_in.acc_lf_z)
    data['euler_lf_x'] = np.array(data_in.euler_lf_x)
    data['euler_lf_y'] = np.array(data_in.euler_lf_y)
    data['euler_lf_z'] = np.array(data_in.euler_lf_z)
    data['phase_lf'] = np.array(data_in.phase_lf)
    data['acc_rf_x'] = np.array(data_in.acc_rf_x)
    data['acc_rf_y'] = np.array(data_in.acc_rf_y)
    data['acc_rf_z'] = np.array(data_in.acc_rf_z)
    data['euler_rf_x'] = np.array(data_in.euler_rf_x)
    data['euler_rf_y'] = np.array(data_in.euler_rf_y)
    data['euler_rf_z'] = np.array(data_in.euler_rf_z)
    data['phase_rf'] = np.array(data_in.phase_rf)
    data['acc_hip_x'] = np.array(data_in.acc_hip_x)
    data['acc_hip_y'] = np.array(data_in.acc_hip_y)
    data['acc_hip_z'] = np.array(data_in.acc_hip_z)
    data['euler_hip_x'] = np.array(data_in.euler_hip_x)
    data['euler_hip_y'] = np.array(data_in.euler_hip_y)
    data['euler_hip_z'] = np.array(data_in.euler_hip_z)
    data['mass'] = np.zeros(len(data_in)) * user_mass

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
    for sensor in ['lf', 'hip', 'rf']:
        for orientation in ['x', 'y', 'z']:
            var1 = 'euler_{}_{}'.format(sensor, orientation)
            var2 = 'acc_{}_{}'.format(sensor, orientation)
            var1_d = var1 + '_d'
            var2_d = var2 + '_d'
            data[var1_d] = np.ediff1d(data[var1], to_begin=np.nan)
            data.loc[np.abs(data[var1_d]) > 3.00, var1_d] = 0
            data[var2_d] = np.ediff1d(data[var2], to_begin=np.nan)

    # Add variables for total acceleration in all sensors and the changes
    data['left_accel'] = np.sqrt(data.acc_lf_x**2+data.acc_lf_y**2+data.acc_lf_z**2)
    data['hip_accel'] = np.sqrt(data.acc_hip_x**2+data.acc_hip_y**2+data.acc_hip_z**2)
    data['right_accel'] = np.sqrt(data.acc_rf_x**2+data.acc_rf_y**2+data.acc_rf_z**2)

    for var in ['left_accel', 'hip_accel', 'right_accel']:
        var_d = var+'_d'
        data[var_d] = np.ediff1d(data[var], to_begin=np.nan)

    # Define set of predictors to use
    if not is_single_leg:
        predictors = ['acc_lf_x', 'acc_lf_y', 'acc_lf_z',
                      'acc_rf_x', 'acc_rf_y', 'acc_rf_z',
                      'acc_hip_x', 'acc_hip_y', 'acc_hip_z',
                      'euler_lf_x_d', 'euler_lf_y_d', 'euler_lf_z_d',
                      'euler_rf_x_d', 'euler_rf_y_d', 'euler_rf_z_d',
                      'euler_hip_x_d', 'euler_hip_y_d', 'euler_hip_z_d',
                      'acc_lf_x_d', 'acc_lf_y_d', 'acc_lf_z_d',
                      'acc_rf_x_d', 'acc_rf_y_d', 'acc_rf_z_d',
                      'acc_hip_x_d', 'acc_hip_y_d', 'acc_hip_z_d',
                      'hip_accel', 'right_accel', 'left_accel',
                      'left_accel_d', 'right_accel_d', 'hip_accel_d',
                      'mass',
                      'phase_lf_0', 'phase_lf_1', 'phase_lf_2',
                      'phase_rf_0', 'phase_rf_1', 'phase_rf_2']
    else:
        predictors = ['acc_lf_x', 'acc_lf_y', 'acc_lf_z',
                      'acc_rf_x', 'acc_rf_y', 'acc_rf_z',
                      'acc_hip_x', 'acc_hip_y', 'acc_hip_z',
                      'euler_lf_x_d', 'euler_lf_y_d', 'euler_lf_z_d',
                      'euler_rf_x_d', 'euler_rf_y_d', 'euler_rf_z_d',
                      'euler_hip_x_d', 'euler_hip_y_d', 'euler_hip_z_d',
                      'acc_lf_x_d', 'acc_lf_y_d', 'acc_lf_z_d',
                      'acc_rf_x_d', 'acc_rf_y_d', 'acc_rf_z_d',
                      'acc_hip_x_d', 'acc_hip_y_d', 'acc_hip_z_d',
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
    x = scaler_model.transform(x)
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