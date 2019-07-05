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
        placement = get_placement(test_data2, file_starts[index_num], file_ends[index_num])

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


def get_placement(data, window_start, window_end):
    hip_accel_data = data["acc_hip_y"][window_start:window_end]
    sensor_0_accel_data = data["acc_lf_z"][window_start:window_end]
    sensor_2_accel_data = data["acc_rf_z"][window_start:window_end]
    lf_euls = qc.quat_to_euler(
        data["quat_lf_w"][window_start:window_end],
        data["quat_lf_x"][window_start:window_end],
        data["quat_lf_y"][window_start:window_end],
        data["quat_lf_z"][window_start:window_end])
    sensor_0_euler_y_degrees = pd.Series(lf_euls[:, 1] * 180 / np.pi)
    rf_euls = qc.quat_to_euler(
        data["quat_rf_w"][window_start:window_end],
        data["quat_rf_x"][window_start:window_end],
        data["quat_rf_y"][window_start:window_end],
        data["quat_rf_z"][window_start:window_end])
    sensor_2_euler_y_degrees = pd.Series(rf_euls[:, 1] * 180 / np.pi)

    trough_mpd = 1
    trough_mph = 20
    trough_edge = 'rising'
    trough_thresh = 0
    sensor_0_peaks = detect_peaks(sensor_0_euler_y_degrees, mph=trough_mph, mpd=trough_mpd, threshold=trough_thresh,
                                  edge=trough_edge, kpsh=False, valley=False)
    sensor_2_peaks = detect_peaks(sensor_2_euler_y_degrees, mph=trough_mph, mpd=trough_mpd, threshold=trough_thresh,
                                  edge=trough_edge, kpsh=False, valley=False)
    troughs = []
    for s_0 in sensor_0_peaks:
        troughs.append(("0", s_0))  # we'll be using the same point in time with a diff data series
    for s_2 in sensor_2_peaks:
        troughs.append(("2", s_2))  # we'll be using the same point in time with a diff data series
    troughs = sorted(troughs, key=lambda x: x[1])
    crossing_zero = []
    crossing_zero = sorted(crossing_zero, key=lambda x: x[1])
    zero_cross = crossing_zero

    for p in range(0, len(troughs)):
        if troughs[p][0] == "0":
            if p == len(troughs) - 1:
                sensor_0_accel_short_data = sensor_0_accel_data.values[troughs[p][1]:]

            else:
                sensor_0_accel_short_data = sensor_0_accel_data.values[troughs[p][1]:troughs[p + 1][1]]

            zero_crossings = np.where(np.diff(np.sign(sensor_0_accel_short_data)))[0]
            if len(zero_crossings) > 0:
                crossing_zero.append(("0", zero_crossings[0] + 1 + troughs[p][1]))

        else:
            if p == len(troughs) - 1:

                sensor_2_accel_short_data = sensor_2_accel_data.values[troughs[p][1]:]
            else:

                sensor_2_accel_short_data = sensor_2_accel_data.values[troughs[p][1]:troughs[p + 1][1]]

            zero_crossings = np.where(np.diff(np.sign(sensor_2_accel_short_data)))[0]
            if len(zero_crossings) > 0:
                crossing_zero.append(("2", zero_crossings[0] + 1 + troughs[p][1]))

    sensor_dict = {}
    sensor_dict["0T"] = 0
    sensor_dict["0P"] = 0
    sensor_dict["2T"] = 0
    sensor_dict["2P"] = 0
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

        if crossing_zero[c][0] == "0":
            window_troughs_0 = detect_peaks(window_data.values, mph=mph, mpd=mpd, threshold=thresh, edge=edge,
                                            kpsh=False, valley=True)
            for w_0 in window_troughs_0:
                window_results.append(("0", "T", w_0))
            window_peaks_0 = detect_peaks(window_data.values, mph=mph, mpd=mpd, threshold=thresh, edge=edge, kpsh=False,
                                          valley=False)
            for w_0 in window_peaks_0:
                window_results.append(("0", "P", w_0))
        else:
            window_troughs_2 = detect_peaks(window_data.values, mph=mph, mpd=mpd, threshold=thresh, edge=edge,
                                            kpsh=False, valley=True)
            for w_2 in window_troughs_2:
                window_results.append(("2", "T", w_2))
            window_peaks_2 = detect_peaks(window_data.values, mph=mph, mpd=mpd, threshold=thresh, edge=edge, kpsh=False,
                                          valley=False)
            for w_2 in window_peaks_2:
                window_results.append(("2", "P", w_2))

        window_results = sorted(window_results, key=lambda x: x[2])

        if len(window_results) > 0:
            if window_results[0][0] == "0" and window_results[0][1] == "T":
                sensor_dict["0T"] += 1
            elif window_results[0][0] == "0" and window_results[0][1] == "P":
                sensor_dict["0P"] += 1
            elif window_results[0][0] == "2" and window_results[0][1] == "T":
                sensor_dict["2T"] += 1
            elif window_results[0][0] == "2" and window_results[0][1] == "P":
                sensor_dict["2P"] += 1
    side_0 = sensor_dict["0T"] + sensor_dict["2P"]
    side_2 = sensor_dict["0P"] + sensor_dict["2T"]

    if side_0 >= side_2:
        placement = [0, 1, 2]
    else:
        placement = [2, 1, 0]

    return placement


