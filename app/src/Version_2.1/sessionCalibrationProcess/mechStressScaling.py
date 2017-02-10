# -*- coding: utf-8 -*-
"""
Created on Fri Feb 10 09:13:42 2017

@author: Gautam
"""
import boto3
import pickle
import numpy as np
import pandas as pd

import coordinateFrameTransformation as coord
from mechStressTraining import prepare_data


def calc_ms_scale(data, hip_bf_transform, lf_bf_transform, rf_bf_transform,
                  lf_n_transform, rf_n_transform, hip_n_transform):
    """Calculates the scale factor for mechanical stress using calibration data
    as baseline. Taking ~7s of data and scaling up to 30m
    Args
        data: processed data from session anatomical calibration
        
    """
    # use transform values to adjust coordinate frame of session_calib data
    data.epoch_time = data.index
    _transformed_data, neutral_data =\
            coord.transform_data(data, hip_bf_transform, lf_bf_transform,
                                 rf_bf_transform, lf_n_transform,
                                 rf_n_transform, hip_n_transform)
    # reshape left foot body transformed data
    data.LaX = _transformed_data[:, 1].reshape(-1, 1)
    data.LaY = _transformed_data[:, 2].reshape(-1, 1)
    data.LaZ = _transformed_data[:, 3].reshape(-1, 1)
    data.LeX = _transformed_data[:, 4].reshape(-1, 1)
    data.LeY = _transformed_data[:, 5].reshape(-1, 1)
    data.LeZ = _transformed_data[:, 6].reshape(-1, 1)
    data.LqW = _transformed_data[:, 7].reshape(-1, 1)
    data.LqX = _transformed_data[:, 8].reshape(-1, 1)
    data.LqY = _transformed_data[:, 9].reshape(-1, 1)
    data.LqZ = _transformed_data[:, 10].reshape(-1, 1)
    # reshape hip body transformed data
    data.HaX = _transformed_data[:, 11].reshape(-1, 1)
    data.HaY = _transformed_data[:, 12].reshape(-1, 1)
    data.HaZ = _transformed_data[:, 13].reshape(-1, 1)
    data.HeX = _transformed_data[:, 14].reshape(-1, 1)
    data.HeY = _transformed_data[:, 15].reshape(-1, 1)
    data.HeZ = _transformed_data[:, 16].reshape(-1, 1)
    data.HqW = _transformed_data[:, 17].reshape(-1, 1)
    data.HqX = _transformed_data[:, 18].reshape(-1, 1)
    data.HqY = _transformed_data[:, 19].reshape(-1, 1)
    data.HqZ = _transformed_data[:, 20].reshape(-1, 1)
    # reshape right foot body transformed data
    data.RaX = _transformed_data[:, 21].reshape(-1, 1)
    data.RaY = _transformed_data[:, 22].reshape(-1, 1)
    data.RaZ = _transformed_data[:, 23].reshape(-1, 1)
    data.ReX = _transformed_data[:, 24].reshape(-1, 1)
    data.ReY = _transformed_data[:, 25].reshape(-1, 1)
    data.ReZ = _transformed_data[:, 26].reshape(-1, 1)
    data.RqW = _transformed_data[:, 27].reshape(-1, 1)
    data.RqX = _transformed_data[:, 28].reshape(-1, 1)
    data.RqY = _transformed_data[:, 29].reshape(-1, 1)
    data.RqZ = _transformed_data[:, 30].reshape(-1, 1)

    # Load mech_stress model
    s3 = boto3.resource('s3')
    cont_models = 'biometrix-globalmodels'
    ms_obj = s3.Bucket(cont_models).Object('ms_trainmodel.pkl')
    ms_fileobj = ms_obj.get()
    ms_body = ms_fileobj["Body"].read()
    mstress_fit = pickle.loads(ms_body)
    del ms_body, ms_fileobj, ms_obj

    # Prepare data to match data used in mech stress training
    ms_data, nan_row = prepare_data(data, False)
   
    # calculate mechanical stress
    mech_stress = np.abs(mstress_fit.predict(ms_data).reshape(-1, 1))

    # calculate the scaling factor
    mech_stress_avg = np.mean(mech_stress)
    print mech_stress_avg
    mech_stress_scale = mech_stress_avg*30*60*100

    return mech_stress_scale


