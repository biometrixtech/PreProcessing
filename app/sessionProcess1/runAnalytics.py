

import pandas as pd


import quatConvs as qc
from extractGeometry import extract_geometry
from movementAttributes import get_total_accel, standing_or_not
from unit_blocks import define_unit_blocks
from .convert_time import get_times



def run_session(data):
    """Creates object attributes according to session analysis process.

    Args:
        data: raw data object with attributes of:
            epoch_time, magn, corrupt, aX, aY, aZ, qW, qX, qY, qZ
    Returns:
        pandas dataframe
        
    """
    sampl_freq = 100
    data['time_stamp'], data['ms_elapsed'] = get_times(data['epoch_time'].values)
    # Compute euler angles, geometric interpretation of data as appropriate
    quats = data.loc[:, ['qW', 'qX', 'qY', 'qZ']].values
    euls = qc.quat_to_euler(quats)
    data['eZ'] = euls[:, 2].reshape(-1, 1)

    (
        data['eX'],
        data['eY']
    ) = extract_geometry(quats)
    

    data['total_accel'] = get_total_accel(data.loc[:, ['aX', 'aY', 'aZ']].values)

    data['standing'] = standing_or_not(data.loc[:, ['eX', 'eY', 'eZ']].values, sampl_freq)

    data['active'] = define_unit_blocks(data.total_accel)
    
    return data