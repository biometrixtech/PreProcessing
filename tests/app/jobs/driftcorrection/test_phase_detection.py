# from aws_xray_sdk.core import xray_recorder
# from jobs.driftcorrection.placement import get_placement_lateral_hip
#
# xray_recorder.configure(sampling=False)
# xray_recorder.begin_segment(name="test")
# import numpy as np
# import pandas as pd
# import os
# import matplotlib.pyplot as plt
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
# def plot_accel(left, right, hip):
#     left.reset_index(drop=True, inplace=True)
#     right.reset_index(drop=True, inplace=True)
#     hip.reset_index(drop=True, inplace=True)
#
#     s = 0
#     e = len(left)
#
#     plt.figure()
#     plt.subplot(311)
#     plt.plot(left[s:e])
#     plt.plot(right[s:e])
#     plt.plot(hip[s:e])
#     plt.legend()
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
# def test_lateral_hip_acceleration():
#     path = '../../../../testdata/calibration/'
#     correct_list = []
#     error_list = []
#     help_list = []
#     zero_list = []
#     file_nums = [1, 3, 5, 7, 9, 11, 13, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34]
#     file_starts = [920, 860, 900, 860, 840, 900, 890, 840, 840, 850, 890, 900, 790, 870, 820, 870, 880, 900]
#     file_ends = [1710, 1500, 1475, 1530, 1510, 1500, 1523, 1500, 1470, 1475, 1500, 1500, 1630, 1580, 1550, 1510, 1560, 1640]
#     index_num = 0
#     for file_num in file_nums:
#
#         test_file2 = 'capture'+str(file_num)+'_calibration.csv'
#         test_data2 = pd.read_csv(path + test_file2)
#         test_data2.columns = ['epoch_time', 'quat_0_w', 'quat_0_x', 'quat_0_y', 'quat_0_z', 'acc_0_x', 'acc_0_y',
#                               'acc_0_z', 'quat_1_w', 'quat_1_x', 'quat_1_y', 'quat_1_z', 'acc_1_x', 'acc_1_y',
#                               'acc_1_z', 'quat_2_w', 'quat_2_x', 'quat_2_y', 'quat_2_z', 'acc_2_x', 'acc_2_y', 'acc_2_z']
#
#         if index_num in [3, 4, 14]:
#             f=0
#         placement = get_placement_lateral_hip(test_data2, file_starts[index_num], file_ends[index_num])
#
#         if placement == [2, 1, 0]:
#             error_list.append(file_num)
#         #elif side_0 == 0:
#         #    zero_list.append(file_num)
#         else:
#             correct_list.append(file_num)
#
#         #if side_0 - side_2 == 1:
#         #    help_list.append(file_num)
#         index_num += 1
#
#     i=0
#
#
