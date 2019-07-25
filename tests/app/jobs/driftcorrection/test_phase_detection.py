from aws_xray_sdk.core import xray_recorder
from jobs.driftcorrection.placement import get_placement_lateral_hip

xray_recorder.configure(sampling=False)
xray_recorder.begin_segment(name="test")
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt

# Use theano backend for keras
os.environ['KERAS_BACKEND'] = 'theano'

from app.jobs.sessionprocess import phase_detection as phd


def test_combine_phase():
    pass


def test_body_phase():
    pass


def plot_accel(left, right, hip):
    left.reset_index(drop=True, inplace=True)
    right.reset_index(drop=True, inplace=True)
    hip.reset_index(drop=True, inplace=True)

    s = 0
    e = len(left)

    plt.figure()
    plt.subplot(311)
    plt.plot(left[s:e])
    plt.plot(right[s:e])
    plt.plot(hip[s:e])
    plt.legend()



def test_phase_detect():
    '''
    Tests included:
        -output appropriately formatted
        -output matches expectation given known input
            -smoothes false motion
            -does not smooth true motion
    '''



    #acc = np.ones((200, 1))
    acc = np.ones(200)
    acc[50] = 5
    acc[100:] = 5
    hz = 200
    bal = phd._phase_detect(acc)
    #targ = np.zeros((200, 1))
    targ = np.zeros(200)
    targ[100:] = 1
    targ[50:] = 1

    # output formatted appropriately
    assert 200 == len(bal)
    # output matches expectation given known input
    #assert True is np.allclose(bal, targ.reshape(1, -1))
    assert True is np.allclose(bal, targ)


def test_impact_detect():
    pass


def test_lateral_hip_acceleration():
    path = '../../../../testdata/calibration/'
    correct_list = []
    error_list = []
    help_list = []
    zero_list = []
    file_nums = [1, 3, 5, 7, 9, 11, 13, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34]
    file_starts = [920, 860, 900, 860, 840, 900, 890, 840, 840, 850, 890, 900, 790, 870, 820, 870, 880, 900]
    file_ends = [1710, 1500, 1475, 1530, 1510, 1500, 1523, 1500, 1470, 1475, 1500, 1500, 1630, 1580, 1550, 1510, 1560, 1640]
    index_num = 0
    for file_num in file_nums:

        test_file2 = 'capture'+str(file_num)+'_calibration.csv'
        test_data2 = pd.read_csv(path + test_file2)
        test_data2.columns = ['epoch_time', 'quat_0_w', 'quat_0_x', 'quat_0_y', 'quat_0_z', 'acc_0_x', 'acc_0_y',
                              'acc_0_z', 'quat_1_w', 'quat_1_x', 'quat_1_y', 'quat_1_z', 'acc_1_x', 'acc_1_y',
                              'acc_1_z', 'quat_2_w', 'quat_2_x', 'quat_2_y', 'quat_2_z', 'acc_2_x', 'acc_2_y', 'acc_2_z']

        if index_num in [3, 4, 14]:
            f=0
        placement, weak_placement = get_placement_lateral_hip(test_data2, file_starts[index_num], file_ends[index_num])

        if weak_placement:
            help_list.append(file_num)

        if placement == [2, 1, 0]:
            error_list.append(file_num)
        elif placement == [0, 0, 0]:
            zero_list.append(file_num)
        elif placement == [0, 1, 2]:
            correct_list.append(file_num)
        else:
            error_list.append(file_num)

        index_num += 1

    i=0

def test_lateral_hip_acceleration_2():
    path = '../../../../testdata/uncontrolled/'
    correct_list = []
    error_list = []
    help_list = []
    zero_list = []

    correct = [[0, 1, 2], [0, 1, 2], [0, 1, 2], [0, 1, 2],[0, 1, 2],[0, 1, 2],[0, 1, 2],[0, 1, 2],[2, 1, 0],[2, 1, 0],[0, 1, 2],[2, 1, 0],[2, 1, 0], [2, 1, 0],[2, 1, 0],[2, 1, 0],[2, 1, 0],[2, 1, 0],[2, 1, 0], [0, 1, 2]]
    file_names = ['b6b42d70_diagnostics_v3.csv','39f243c2_diagnostics_v2.csv','7bbff8e0_diagnostics_v3.csv', '958dba09_diagnostics_v3.csv','27ab9e93_diagnostics_v2.csv',
                  'e12e7da7_diagnostics_v2.csv','b2a95b1b_diagnostics_v3.csv','f78a9e26_diagnostics_v2.csv','15868b04_diagnostics_v2.csv','b1d4e15c_diagnostics_v2.csv',
                  'b6c0489b_diagnostics_v2.csv','b390e769_diagnostics_v2.csv','f7b46970_diagnostics_v2.csv','dc2277a6_diagnostics_v2.csv','dc0c6273_diagnostics_v2.csv',
                  '47f84e96_diagnostics_v2.csv','6988ba9b_diagnostics_v2.csv','e3223bf2_diagnostics_v2.csv',
                  'ad96ceb5_diagnostics_v2.csv','946864ae_diagnostics_v2.csv']
    index_num = 0
    for file_name in file_names:

        test_file2 = file_name
        # test_data2 = pd.read_csv(path + test_file2, usecols=['epoch_time',
        #                                                      'quat_lf_w', 'quat_lf_x', 'quat_lf_y', 'quat_lf_z',
        #                                                      'acc_lf_x', 'acc_lf_y', 'acc_lf_z',
        #                                                      'quat_hip_w', 'quat_hip_x', 'quat_hip_y', 'quat_hip_z',
        #                                                      'acc_hip_x', 'acc_hip_y', 'acc_hip_z',
        #                                                      'quat_rf_w', 'quat_rf_x', 'quat_rf_y', 'quat_rf_z',
        #                                                      'acc_rf_x', 'acc_rf_y', 'acc_rf_z',
        #                                                      'euler_lf_y', 'euler_rf_y', 'march_hip'], nrows=2000)
        test_data2 = pd.read_csv(path + test_file2, nrows=2000)
        # test_data2.columns = ['epoch_time',
        #                       'quat_0_w', 'quat_0_x', 'quat_0_y', 'quat_0_z',
        #                       'acc_0_x', 'acc_0_y', 'acc_0_z',
        #                       'quat_1_w', 'quat_1_x', 'quat_1_y', 'quat_1_z',
        #                       'acc_1_x', 'acc_1_y', 'acc_1_z',
        #                       'quat_2_w', 'quat_2_x', 'quat_2_y', 'quat_2_z',
        #                       'acc_2_x', 'acc_2_y', 'acc_2_z',
        #                       'euler_0_y', 'euler_2_y', 'march_hip']
        test_data2.columns = ['obs_index', 'static_lf',' static_hip', 'static_rf', 'time_stamp','epoch_time',
                             'ms_elapsed','active', 'phase_lf', 'phase_rf', 'candidate_troughs_lf', 'troughs_lf',
                             'correction_points_hip', 'candidate_troughs_rf', 'troughs_rf', 'grf', 'grf_lf', 'grf_rf',
                             'total_accel', 'euler_lf_x', 'euler_lf_y', 'euler_lf_z', 'euler_hip_x', 'euler_hip_y',
                             'euler_hip_z', 'euler_rf_x', 'euler_rf_y', 'euler_rf_z', 'quat_0_w', 'quat_0_x',
                             'quat_0_y', 'quat_0_z', 'quat_1_w', 'quat_1_x', 'quat_1_y', 'quat_1_z',
                             'quat_2_w', 'quat_2_x', 'quat_2_y', 'quat_2_z', 'acc_0_x', 'acc_0_y', 'acc_0_z',
                             'acc_1_x', 'acc_1_y', 'acc_1_z', 'acc_2_x', 'acc_2_y', 'acc_2_z',
                             'missing_troughs_lf', 'missing_troughs_rf', 'in_air_error', 'overlap_lf', 'overlap_rf',
                             'half_length', 'double_length', 'offsets_trough_lf', 'offsets_trough_rf',
                             'euler_out_of_range_lf', 'euler_out_of_range_hip', 'euler_out_of_range_rf',
                             'offsets_direction_lf', 'offsets_direction_rf', 'offsets_direction_hip', 'still_lf',
                             'still_hip', 'still_rf', 'march_lf', 'march_hip', 'march_rf']

        march_start = 2001
        march_end = 0

        for d in range(0, 2000):
            if test_data2['march_hip'][d] == 1:
                march_start = min(march_start, d)
                march_end = max(march_start, d)

        placement, weak_placement = get_placement_lateral_hip(test_data2, march_start, march_end)

        if weak_placement:
            help_list.append(file_name)
        if placement[1] != 0 and placement[0] != correct[index_num][0]:
            error_list.append(file_name)
        elif placement == [0, 0, 0]:
            zero_list.append(file_name)
        elif placement == correct[index_num]:
            correct_list.append(file_name)
        else:
            error_list.append(file_name)

        index_num += 1

    i=0


