from aws_xray_sdk.core import xray_recorder
from jobs.driftcorrection.placement import get_placement_lateral_hip

xray_recorder.configure(sampling=False)
xray_recorder.begin_segment(name="test")
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
#
# # Use theano backend for keras
# os.environ['KERAS_BACKEND'] = 'theano'
#
# from app.jobs.sessionprocess import phase_detection as phd
#
#
# def test_combine_phase():
#     pass
#
#
# def test_body_phase():
#     pass
#
#
def plot_accel(left, right, hip):

    #left.reset_index(drop=True, inplace=True)
    #right.reset_index(drop=True, inplace=True)
    #hip.reset_index(drop=True, inplace=True)

    s = 0
    e = len(left)

    plt.figure()
    plt.subplot(311)
    plt.plot(left[s:e])
    plt.plot(right[s:e])
    plt.plot(hip[s:e])
    plt.legend()

def plot_stomp(left, right):

    #left.reset_index(drop=True, inplace=True)
    #right.reset_index(drop=True, inplace=True)
    #hip.reset_index(drop=True, inplace=True)

    s = 0
    e = len(left)

    plt.figure()
    plt.subplot(311)
    plt.plot(left[s:e])
    #plt.plot(right[s:e])
    plt.legend()
#
#
#
# def test_phase_detect():
#     '''
#     Tests included:
#         -output appropriately formatted
#         -output matches expectation given known input
#             -smoothes false motion
#             -does not smooth true motion
#     '''
#
#
#
#     #acc = np.ones((200, 1))
#     acc = np.ones(200)
#     acc[50] = 5
#     acc[100:] = 5
#     hz = 200
#     bal = phd._phase_detect(acc)
#     #targ = np.zeros((200, 1))
#     targ = np.zeros(200)
#     targ[100:] = 1
#     targ[50:] = 1
#
#     # output formatted appropriately
#     assert 200 == len(bal)
#     # output matches expectation given known input
#     #assert True is np.allclose(bal, targ.reshape(1, -1))
#     assert True is np.allclose(bal, targ)
#
#
# def test_impact_detect():
#     pass
#
#

_output_columns = [
    'obs_index',
    'static_lf',
    'static_hip',
    'static_rf',
    'time_stamp',
    'epoch_time',
    'ms_elapsed',
    'active',
    'phase_lf',
    'phase_rf',
    'candidate_troughs_lf', 'troughs_lf',
    'correction_points_hip',
    'candidate_troughs_rf', 'troughs_rf',
    'grf',
    'grf_lf',
    'grf_rf',
    'total_accel',
    'euler_lf_x', 'euler_lf_y', 'euler_lf_z',
    'euler_hip_x', 'euler_hip_y', 'euler_hip_z',
    'euler_rf_x', 'euler_rf_y', 'euler_rf_z',
    'acc_lf_x', 'acc_lf_y', 'acc_lf_z',
    'acc_hip_x', 'acc_hip_y', 'acc_hip_z',
    'acc_rf_x', 'acc_rf_y', 'acc_rf_z',
    'quat_lf_w','quat_lf_x', 'quat_lf_y', 'quat_lf_z',
    'quat_hip_w', 'quat_hip_x', 'quat_hip_y', 'quat_hip_z',
    'quat_rf_w', 'quat_rf_x', 'quat_rf_y', 'quat_rf_z',
    'stance',
    'adduc_motion_covered_abs_lf', 'adduc_motion_covered_pos_lf', 'adduc_motion_covered_neg_lf',
    'adduc_range_of_motion_lf',
    'flex_motion_covered_abs_lf', 'flex_motion_covered_pos_lf', 'flex_motion_covered_neg_lf',
    'flex_range_of_motion_lf',
    'contact_duration_lf',
    'adduc_motion_covered_abs_h', 'adduc_motion_covered_pos_h', 'adduc_motion_covered_neg_h',
    'adduc_range_of_motion_h',
    'flex_motion_covered_abs_h', 'flex_motion_covered_pos_h', 'flex_motion_covered_neg_h',
    'flex_range_of_motion_h',
    'contact_duration_h',
    'adduc_motion_covered_abs_rf', 'adduc_motion_covered_pos_rf', 'adduc_motion_covered_neg_rf',
    'adduc_range_of_motion_rf',
    'flex_motion_covered_abs_rf', 'flex_motion_covered_pos_rf', 'flex_motion_covered_neg_rf',
    'flex_range_of_motion_rf',
    'contact_duration_rf']

_renamed_columns = [
    'obs_index',
    'static_0',
    'static_1',
    'static_2',
    'time_stamp',
    'epoch_time',
    'ms_elapsed',
    'active',
    'phase_0',
    'phase_2',
    'candidate_troughs_0', 'troughs_0',
    'correction_points_1',
    'candidate_troughs_2', 'troughs_2',
    'grf',
    'grf_0',
    'grf_2',
    'total_accel',
    'euler_0_x', 'euler_0_y', 'euler_0_z',
    'euler_1_x', 'euler_1_y', 'euler_1_z',
    'euler_2_x', 'euler_2_y', 'euler_2_z',
    'acc_0_x', 'acc_0_y', 'acc_0_z',
    'acc_1_x', 'acc_1_y', 'acc_1_z',
    'acc_2_x', 'acc_2_y', 'acc_2_z',
    'quat_0_w','quat_0_x', 'quat_0_y', 'quat_0_z',
    'quat_1_w', 'quat_1_x', 'quat_1_y', 'quat_1_z',
    'quat_2_w', 'quat_2_x', 'quat_2_y', 'quat_2_z',
    'stance',
    'adduc_motion_covered_abs_0', 'adduc_motion_covered_pos_0', 'adduc_motion_covered_neg_0',
    'adduc_range_of_motion_0',
    'flex_motion_covered_abs_0', 'flex_motion_covered_pos_0', 'flex_motion_covered_neg_0',
    'flex_range_of_motion_0',
    'contact_duration_0',
    'adduc_motion_covered_abs_1', 'adduc_motion_covered_pos_1', 'adduc_motion_covered_neg_1',
    'adduc_range_of_motion_1',
    'flex_motion_covered_abs_1', 'flex_motion_covered_pos_1', 'flex_motion_covered_neg_1',
    'flex_range_of_motion_1',
    'contact_duration_1',
    'adduc_motion_covered_abs_2', 'adduc_motion_covered_pos_2', 'adduc_motion_covered_neg_2',
    'adduc_range_of_motion_2',
    'flex_motion_covered_abs_2', 'flex_motion_covered_pos_2', 'flex_motion_covered_neg_2',
    'flex_range_of_motion_2',
    'contact_duration_2']

def test_lateral_hip_acceleration():
    path = '../../../../testdata/failed_placements_completed/'
    correct_list = []
    error_list = []
    help_list = []
    zero_list = []

    session_id = "2f26eee8-455a-5678-a384-ed5a14c6e54a"

    test_file2 = session_id + '_processed'
    test_data2 = pd.read_csv(path + test_file2, usecols=_output_columns)
    test_data2.columns = _renamed_columns

    start = 827
    end = 1409

    hip_accel_data = test_data2["acc_1_y"][start:end]
    sensor_0_accel_data = test_data2["acc_0_z"][start:end]
    sensor_2_accel_data = test_data2["acc_2_z"][start:end]

    #plot_accel(sensor_0_accel_data, sensor_2_accel_data, hip_accel_data)

    sensor_0_accel_stomp_data = test_data2["acc_0_z"][end:end+1000]
    sensor_2_accel_stomp_data = test_data2["acc_2_z"][end:end+1000]

    plot_stomp(sensor_0_accel_stomp_data, sensor_2_accel_stomp_data)

    placement = get_placement_lateral_hip(test_data2, start, end)

    if placement == [2, 1, 0]:
        error_list.append(file_num)
    #elif side_0 == 0:
    #    zero_list.append(file_num)
    else:
        correct_list.append(file_num)

    #if side_0 - side_2 == 1:
    #    help_list.append(file_num)
    index_num += 1

    i=0


