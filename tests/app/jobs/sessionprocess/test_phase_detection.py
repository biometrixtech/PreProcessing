from aws_xray_sdk.core import xray_recorder
xray_recorder.configure(sampling=False)
xray_recorder.begin_segment(name="test")
import numpy as np
import pandas as pd
import os
from app.utils.detect_peaks import detect_peaks
import matplotlib.pyplot as plt
import utils.quaternion_conversions as qc
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
        hip_accel_data = test_data2["acc_hip_y"][file_starts[index_num]:file_ends[index_num]]
        sensor_0_accel_data = test_data2["acc_lf_z"][file_starts[index_num]:file_ends[index_num]]
        sensor_2_accel_data = test_data2["acc_rf_z"][file_starts[index_num]:file_ends[index_num]]
        lf_euls = qc.quat_to_euler(
            test_data2["quat_lf_w"][file_starts[index_num]:file_ends[index_num]],
            test_data2["quat_lf_x"][file_starts[index_num]:file_ends[index_num]],
            test_data2["quat_lf_y"][file_starts[index_num]:file_ends[index_num]],
            test_data2["quat_lf_z"][file_starts[index_num]:file_ends[index_num]])
        sensor_0_euler_y_degrees = pd.Series(lf_euls[:, 1] * 180/ np.pi)
        rf_euls = qc.quat_to_euler(
            test_data2["quat_rf_w"][file_starts[index_num]:file_ends[index_num]],
            test_data2["quat_rf_x"][file_starts[index_num]:file_ends[index_num]],
            test_data2["quat_rf_y"][file_starts[index_num]:file_ends[index_num]],
            test_data2["quat_rf_z"][file_starts[index_num]:file_ends[index_num]])
        sensor_2_euler_y_degrees = pd.Series(rf_euls[:, 1] * 180 / np.pi)
        #if file_num in [3, 13, 16, 32]:
        #    plot_accel(sensor_0_accel_data, sensor_2_accel_data, hip_accel_data)
        trough_mpd = 1
        trough_mph = 20
        trough_edge = 'rising'
        trough_thresh = 0
        sensor_0_peaks = detect_peaks(sensor_0_euler_y_degrees,mph=trough_mph, mpd=trough_mpd,threshold=trough_thresh,edge=trough_edge,kpsh=False,valley=False)
        sensor_2_peaks = detect_peaks(sensor_2_euler_y_degrees,mph=trough_mph, mpd=trough_mpd, threshold=trough_thresh, edge=trough_edge, kpsh=False, valley=False)
        troughs = []
        for lf in sensor_0_peaks:
            troughs.append(("L", lf))  # we'll be using the same point in time with a diff data series

        for rf in sensor_2_peaks:
            troughs.append(("R", rf))  # we'll be using the same point in time with a diff data series

        troughs = sorted(troughs, key=lambda x: x[1])

        crossing_zero = []

        crossing_zero = sorted(crossing_zero, key=lambda x: x[1])
        zero_cross = crossing_zero

        # if file_num in [3, 13, 16, 32]:
        #     i = 9
        #     pass

        for p in range(0, len(troughs)):
            if troughs[p][0] == "L":
                if p == len(troughs) - 1:
                    sensor_0_accel_short_data = sensor_0_accel_data.values[troughs[p][1]:]

                else:
                    sensor_0_accel_short_data = sensor_0_accel_data.values[troughs[p][1]:troughs[p+1][1]]

                zero_crossings = np.where(np.diff(np.sign(sensor_0_accel_short_data)))[0]
                if len(zero_crossings) > 0:
                    crossing_zero.append(("L", zero_crossings[0]+1 + troughs[p][1]))

            else:
                if p == len(troughs) - 1:

                    sensor_2_accel_short_data = sensor_2_accel_data.values[troughs[p][1]:]
                else:

                    sensor_2_accel_short_data = sensor_2_accel_data.values[troughs[p][1]:troughs[p + 1][1]]

                zero_crossings = np.where(np.diff(np.sign(sensor_2_accel_short_data)))[0]
                if len(zero_crossings) > 0:
                    crossing_zero.append(("R", zero_crossings[0]+1 + troughs[p][1]))

        sensor_dict = {}
        sensor_dict["LT"] = 0
        sensor_dict["LP"] = 0
        sensor_dict["RT"] = 0
        sensor_dict["RP"] = 0

        for c in range(0, len(crossing_zero) - 1):

            if c < len(crossing_zero) - 1:
                window_data = hip_accel_data[crossing_zero[c][1]:crossing_zero[c + 1][1]]
            else:
                window_data = hip_accel_data[crossing_zero[c][1]:]

            window_results = []
            mpd = 1
            mph = 5.0
            thresh = 0
            edge = None  # has no impact on detection

            if crossing_zero[c][0] == "L":
                left_window_troughs = detect_peaks(window_data.values, mph=mph, mpd=mpd, threshold=thresh, edge=edge, kpsh=False, valley=True)
                for lf in left_window_troughs:
                    window_results.append(("L", "T", lf))
                left_window_peaks = detect_peaks(window_data.values, mph=mph, mpd=mpd, threshold=thresh, edge=edge, kpsh=False, valley=False)
                for lf in left_window_peaks:
                    window_results.append(("L", "P", lf))
            else:
                right_window_troughs = detect_peaks(window_data.values, mph=mph,mpd=mpd, threshold=thresh, edge=edge, kpsh=False, valley=True)
                for rf in right_window_troughs:
                    window_results.append(("R", "T", rf))
                right_window_peaks = detect_peaks(window_data.values, mph=mph,mpd=mpd, threshold=thresh, edge=edge, kpsh=False, valley=False)
                for rf in right_window_peaks:
                    window_results.append(("R", "P", rf))

            window_results = sorted(window_results, key=lambda x: x[2])

            if len(window_results) > 0:
                if window_results[0][0] == "L" and window_results[0][1] == "T":
                    sensor_dict["LT"] += 1
                elif window_results[0][0] == "L" and window_results[0][1] == "P":
                    sensor_dict["LP"] += 1
                elif window_results[0][0] == "R" and window_results[0][1] == "T":
                    sensor_dict["RT"] += 1
                elif window_results[0][0] == "R" and window_results[0][1] == "P":
                    sensor_dict["RP"] += 1

        left_side = sensor_dict["LT"] + sensor_dict["RP"]
        right_side = sensor_dict["LP"] + sensor_dict["RT"]

        if right_side > left_side:
            error_list.append(file_num)
        elif left_side == 0:
            zero_list.append(file_num)
        else:
            correct_list.append(file_num)

        if left_side - right_side == 1:
            help_list.append(file_num)
        index_num += 1

    i=0


