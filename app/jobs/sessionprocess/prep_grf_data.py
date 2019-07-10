# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 11:57:32 2016

@author: Gautam
"""

from __future__ import division
from aws_xray_sdk.core import xray_recorder
import numpy as np
import pandas as pd

from utils import filter_data


@xray_recorder.capture('app.jobs.sessionprocess.prep_grf_data.prepare_data')
def prepare_data(data_in, scaler_model, user_mass):
    """Subsets and transforms the training data as well as define features
    to be used
    Args:
        data_in: pandas dataframe or RawFrame object with the acceleration, euler
        scaler_model: scaler model to scale data
        user_mass: the user's mass
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
    data['acc_rf_x'] = np.array(data_in.acc_rf_x)
    data['acc_rf_y'] = np.array(data_in.acc_rf_y)
    data['acc_rf_z'] = np.array(data_in.acc_rf_z)
    data['euler_rf_x'] = np.array(data_in.euler_rf_x)
    data['euler_rf_y'] = np.array(data_in.euler_rf_y)
    data['euler_rf_z'] = np.array(data_in.euler_rf_z)
    data['acc_hip_x'] = np.array(data_in.acc_hip_x)
    data['acc_hip_y'] = np.array(data_in.acc_hip_y)
    data['acc_hip_z'] = np.array(data_in.acc_hip_z)
    data['euler_hip_x'] = np.array(data_in.euler_hip_x)
    data['euler_hip_y'] = np.array(data_in.euler_hip_y)
    data['euler_hip_z'] = np.array(data_in.euler_hip_z)
    data['mass'] = np.ones(len(data_in)) * user_mass

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
    data['acc_lf'] = np.sqrt(data.acc_lf_x**2 + data.acc_lf_y**2 + data.acc_lf_z**2)
    data['acc_hip'] = np.sqrt(data.acc_hip_x**2 + data.acc_hip_y**2 + data.acc_hip_z**2)
    data['acc_rf'] = np.sqrt(data.acc_rf_x**2 + data.acc_rf_y**2 + data.acc_rf_z**2)

    for var in ['acc_lf', 'acc_hip', 'acc_rf']:
        var_d = var+'_d'
        data[var_d] = np.ediff1d(data[var], to_begin=np.nan)

    # Define set of predictors to use
    predictors = [
                  'acc_lf_z',
                  'acc_hip_x', 'acc_hip_y', 'acc_hip_z',
                  'acc_rf_z',
                  'euler_lf_x', 'euler_lf_y', 
                  'euler_hip_x', 'euler_hip_y', 
                  'euler_rf_x', 'euler_rf_y',
                  'euler_lf_x_d', 'euler_lf_y_d', 'euler_lf_z_d',
                  'euler_hip_x_d', 'euler_hip_y_d', 'euler_hip_z_d',
                  'euler_rf_x_d', 'euler_rf_y_d', 'euler_rf_z_d',
                  'acc_lf_z_d',
                  'acc_hip_x_d', 'acc_hip_y_d', 'acc_hip_z_d',
                  'acc_rf_z_d',
                  'acc_lf', 'acc_hip', 'acc_rf',
                  'acc_lf_d', 'acc_hip_d', 'acc_rf_d',
                  'mass'
                 ]

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
    x1 = x[:, 0:len(predictors) - 1]
    x2 = x[:, len(predictors) - 1:]
    x1 = filter_data(x1, filt='low', fs=97.5, highcut=6, order=4)
    x = np.append(x1, x2, 1)
    # scale the data
    x = scaler_model.transform(x)
    return x, nan_row
