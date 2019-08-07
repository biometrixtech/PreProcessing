from jobs.transformandplacement.body_frame_transformation import body_frame_tran
import numpy as np
import scipy.io
import pandas as pd


# def find_reset(op_cond):
#     """
#     Find a confident reset_index in a long enough static phase.
#
#     Parameters
#     ----------
#     op_cond : array_like
#         global op_cond, as or value of left, hip and right.
#
#     Returns
#     -------
#     reset_index : number
#         Confident static reset index.
#     """
#     op_cond = np.asanyarray(op_cond)
#     # Sampling frequency
#     fs = 100
#     # Set maximum lenght whithin search (MPh) from the beginning of the data (secs*Fs)
#     nsearch = 30*fs
#     # op_down counter and threshold for resetIndex
#     op_down_count = 0
#     op_down_th = 0.3*fs
#
#     for i in range(nsearch):
#         if op_cond[i] == 0:
#             op_down_count += 1
#             if op_down_count > op_down_th and i + 1 > 0.5*fs:
#                 return i
#         else:
#             op_down_count = 0
#     ## Reduce threshold in the extreme case that reset_found=false
#     if i==nsearch-1:
#         # op_down counter and threshold for resetIndex
#         op_down_count = 0
#         op_down_th = 0.2*fs
#         for i in range(nsearch):
#             if op_cond[i] == 0:
#                 op_down_count += 1
#                 if op_down_count > op_down_th and i + 1 > 0.5*fs:
#                     return i
#             else:
#                 op_down_count = 0
#
#     return -1


def test_match_221e():
    for i in [2, 3, 4, 6]:
        path = f'../../../files/data{i}/'

        data = scipy.io.loadmat(f"{path}data.mat").get("data")
        dataC_actual = scipy.io.loadmat(f"{path}dataC.mat").get("dataC")
        reset_index = scipy.io.loadmat(f"{path}resetIndex.mat").get("resetIndex")[0][0] - 1  # subtract one because matlab index starts at 1 not 0

        data = np.asanyarray(data)
        # # Creating pandas dataframe from numpy array
        df = pd.DataFrame({'epoch_time': data[:, 0], 'static_0': data[:, 1], 'acc_0_x': data[:, 2],
                                'acc_0_y': data[:, 3], 'acc_0_z': data[:, 4], 'quat_0_w': data[:, 5],
                                'quat_0_x': data[:, 6], 'quat_0_y': data[:, 7], 'quat_0_z': data[:, 8],
                                'static_1': data[:, 9], 'acc_1_x': data[:, 10], 'acc_1_y': data[:, 11],'acc_1_z': data[:, 12],
                                'quat_1_w': data[:, 13],'quat_1_x': data[:, 14], 'quat_1_y': data[:, 15], 'quat_1_z': data[:, 16],
                                'static_2': data[:, 17], 'acc_2_x': data[:, 18], 'acc_2_y': data[:, 19],
                                'acc_2_z': data[:, 20], 'quat_2_w': data[:, 21], 'quat_2_x': data[:, 22],
                                'quat_2_y': data[:, 23], 'quat_2_z': data[:, 24]})

        # # Find reset_index
        # op_cond_l = data[:, 1]
        # op_cond_h = data[:, 9]
        # op_cond_r = data[:, 17]
        # op_cond = np.logical_or(op_cond_h, np.logical_or(op_cond_l, op_cond_r))
        # reset_index = find_reset(op_cond)

        # Reset Orientation
        qCL = data[reset_index, 5: 9]
        qCH = data[reset_index,13:17]
        qCR = data[reset_index,21:25]

        dataC_observed = body_frame_tran(df, qCL, qCH, qCR)

        precision = 10**-4
        for a in range(0, 25):
            assert (np.abs(dataC_actual[:, a] - dataC_observed[:, a]) < precision).all()
