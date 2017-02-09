# -*- coding: utf-8 -*-
"""
Created on Wed Dec 21 12:14:30 2016

@author: Gautam
"""

import numpy as np


def handle_processed(data):
    """Checks if quaternions are raw or processed. If processed, converts 
    imaginary components to raw.
    """
#    any_real = any([item in data.dtype.names for item in ['LqW', 'HqW', 'RqW']])
    # subset quaterion data for all three sensor
    quat_data = np.vstack([data['LqX'], data['LqY'], data['LqZ'],
                           data['HqX'], data['HqY'], data['HqZ'],
                           data['RqX'], data['RqY'], data['RqZ']])
    # check if all non-nan values are less than 1.
    processed = np.all(np.abs(quat_data[np.isfinite(quat_data)]) <= 1.01)
    
    if processed:
        data = _convert_to_raw(data)
    return data


def _convert_to_raw(data):
    """Reverts processed quaternion values to raw values.
    """
    data['LqX'] = data['LqX']*32767.0
    data['LqY'] = data['LqY']*32767.0
    data['LqZ'] = data['LqZ']*32767.0
    
    data['HqX'] = data['HqX']*32767.0
    data['HqY'] = data['HqY']*32767.0
    data['HqZ'] = data['HqZ']*32767.0
    
    data['RqX'] = data['RqX']*32767.0
    data['RqY'] = data['RqY']*32767.0
    data['RqZ'] = data['RqZ']*32767.0

    return data


if __name__ == "__main__":
    file_name = 'C:\\Users\\dipesh\\Desktop\\biometrix\\dataCapture\dipesh_calibration.csv'
    file_name = 'C:\\Users\\dipesh\\Downloads\\System_Response_Test\\ankur_moving.csv'    
    test_data = np.genfromtxt(file_name, delimiter=',', names=True)
    
    data = check_processed(test_data)