
import quatConvs as qc
from .extract_geometry import extract_geometry
from .movement_attributes import get_total_accel, standing_or_not
from .unit_blocks import define_unit_blocks
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
    quats = data.loc[:, ['quat_hip_w', 'quat_hip_x', 'quat_hip_y', 'quat_hip_z']].values
    euls = qc.quat_to_euler(quats)
    data['euler_hip_z'] = euls[:, 2].reshape(-1, 1)

    (
        data['euler_hip_x'],
        data['euler_hip_y']
    ) = extract_geometry(quats)

    data['total_accel'] = get_total_accel(data.loc[:, ['acc_hip_x', 'acc_hip_y', 'acc_hip_z']].values)

    data['standing'] = standing_or_not(data.loc[:, ['euler_hip_x', 'euler_hip_y', 'euler_hip_z']].values, sampl_freq)

    data['active'] = define_unit_blocks(data.total_accel)

    return data
