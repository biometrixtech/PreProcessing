import logging
from utils.quaternion_operations import quat_avg
from .heading_calculation import heading_hip_finder

_logger = logging.getLogger(__name__)


def compute_transform(data, start_still_0, end_still_0, start_still_hip, end_still_hip, start_still_2, end_still_2):
    data.reset_index(inplace=True, drop=True)
    quat0 = data.loc[start_still_0:end_still_0, ['quat_0_w', 'quat_0_x', 'quat_0_y', 'quat_0_z']].values.reshape(-1, 4)
    quat1 = data.loc[start_still_hip:end_still_hip, ['quat_1_w', 'quat_1_x', 'quat_1_y', 'quat_1_z']].values.reshape(-1, 4)
    quat2 = data.loc[start_still_2:end_still_2, ['quat_2_w', 'quat_2_x', 'quat_2_y', 'quat_2_z']].values.reshape(-1, 4)

    left_reference_quaternion = quat_avg(quat0)
    hip_reference_quaternion = quat_avg(quat1)
    right_reference_quaternion = quat_avg(quat2)
    hip_heading_quaternion = heading_hip_finder(quat_avg(quat1))

    return (left_reference_quaternion.tolist()[0],
            hip_reference_quaternion.tolist()[0],
            right_reference_quaternion.tolist()[0],
            hip_heading_quaternion.tolist()[0])
