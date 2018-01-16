# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 10:41:36 2016

@author: Gautam

Session execution script. Used by athletes during block processes. Takes raw
session data, processes, and returns analyzed data.

Input data called from 'biometrix-blockcontainer'

Output data collected in BlockEvent Table.
"""

import logging
import numpy as np
import pandas as pd

import dataObject as do

import columnNames as cols
import phaseDetection as phase
import quatConvs as qc
import prePreProcessing as ppp
from extractGeometry import extract_geometry



def save_file(data_in, file_name):
    """Creates object attributes according to session analysis process.

    Args:
        data_in: raw data object with attributes of:
            epoch_time, corrupt_magn, missing_type, LaX, LaY, LaZ, LqX, LqY,
            LqZ, HaX, HaY, HaZ, HqX, HqY, HqZ, RaX, RaY, RaZ, RqX, RqY, RqZ
        file_version: file format and type version (matching accessory sensor dev)
        mass: user's mass in kg
        grf_fit: keras fitted model for grf prediction
        sc: scaler model to scale data
        aws: Boolean indicator for whether we're running locally or on amazon
            aws
    
    Returns:
        result: string signifying success or failure.
        Note: In case of completion for local run, returns movement table.
    """
    columns = data_in.columns
    data_in = ppp.subset_data(old_data=data_in)
    data = do.RawFrame(data_in, columns)
    sampl_freq = 100

    # Compute euler angles, geometric interpretation of data as appropriate
    lf_quats = np.hstack([data.LqW, data.LqX, data.LqY,
                          data.LqZ]).reshape(-1, 4)
    lf_euls = qc.quat_to_euler(lf_quats)
    data.LeZ = lf_euls[:, 2].reshape(-1, 1)
    del(lf_euls)

    hip_quats = np.hstack([data.HqW, data.HqX, data.HqY, data.HqZ]).reshape(-1, 4)
    h_euls = qc.quat_to_euler(hip_quats)
    data.HeZ = h_euls[:, 2].reshape(-1, 1)
    del(h_euls)

    rf_quats = np.hstack([data.RqW, data.RqX, data.RqY, data.RqZ]).reshape(-1, 4)
    rf_euls = qc.quat_to_euler(rf_quats)
    data.ReZ = rf_euls[:, 2].reshape(-1, 1)
    del(rf_euls)

    adduction_L, flexion_L, adduction_H, flexion_H, adduction_R, flexion_R = extract_geometry(lf_quats, hip_quats, rf_quats)

    data.LeX = adduction_L.reshape(-1, 1)
    data.LeY = flexion_L.reshape(-1, 1)
    data.HeX = adduction_H.reshape(-1, 1)
    data.HeY = flexion_H.reshape(-1, 1)
    data.ReX = adduction_R.reshape(-1, 1)
    data.ReY = flexion_R.reshape(-1, 1)

    # data.la_magn = np.sqrt(data.LaX**2 + data.LaY**2 + data.LaZ**2)
    # data.ra_magn = np.sqrt(data.RaX**2 + data.RaY**2 + data.RaZ**2) 

    # PHASE DETECTION
    data.phase_lf, data.phase_rf = phase.combine_phase(data.LaZ, data.RaZ, 
                                                       data.LaZ,
                                                       data.RaZ ,
                                                       data.LeY,
                                                       data.ReY, 100)

    # logger.info('DONE WITH PHASE DETECTION!')

    # Output debug CSV
    import cStringIO
    import boto3
    columns = ['epoch_time', 'corrupt', 
               'magn_lf', 'corrupt_lf',
               'LaX', 'LaY', 'LaZ', 'LqX', 'LqY', 'LqZ', 'LqW',
               'magn_h', 'corrupt_h',
               'HaX', 'HaY', 'HaZ', 'HqX', 'HqY', 'HqZ', 'HqW', 
               'magn_rf', 'corrupt_rf',
               'RaX', 'RaY', 'RaZ', 'RqX', 'RqY', 'RqZ', 'RqW',
               'LeX', 'LeY', 'LeZ',
               'HeX', 'HeY', 'HeZ',
               'ReX', 'ReY', 'ReZ',
               'phase_lf', 'phase_rf']
    length = len(data.LaX)
    debug_data = pd.DataFrame(data={'epoch_time': data.epoch_time.reshape(-1,)})
    for var in columns[1:]:
       frame = pd.DataFrame(data={var: data.__dict__[var].reshape(-1, )}, index=debug_data.index)
       frames = [debug_data, frame]
       debug_data = pd.concat(frames, axis=1)
       # del frame, frames, data.__dict__[var]
    fileobj = cStringIO.StringIO()
    debug_data.to_csv(fileobj, index=False, na_rep='', columns=columns)
    del debug_data
    fileobj.seek(0)
    s3 = boto3.resource('s3')
    s3.Bucket('biometrix-decode').put_object(Key=file_name + '_transformed', Body=fileobj)
