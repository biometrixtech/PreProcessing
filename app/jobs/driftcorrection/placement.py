import logging
import pandas as pd
import numpy as np
from utils.detect_peaks import detect_peaks
import utils.quaternion_conversions as qc

_logger = logging.getLogger(__name__)


def get_placement_hip_correction(data):

    hip_window = 5

    hip_correction_data = data[["correction_points_1", "troughs_0", "troughs_2"]]

    corr_hip_indices = np.where(hip_correction_data.correction_points_1.values == 1)[0].astype(list)
    if len(corr_hip_indices) > 0:
        corr_point_padded = set(np.concatenate([np.arange(i - hip_window, i + hip_window) for i in corr_hip_indices]))

        window_data = hip_correction_data.loc[corr_point_padded, :]

        zero_sum = np.sum(window_data.troughs_0)
        two_sum = np.sum(window_data.troughs_2)
        test_sum = np.sum(window_data.correction_points_1)

        hip_correction_placement = [0, 1, 2]
        weak_placement = False

        if two_sum > zero_sum:
            hip_correction_placement = [2, 1, 0]
        elif two_sum == zero_sum:
            hip_correction_placement = [0, 0, 0]

        if abs(two_sum - zero_sum) <= 10:
            weak_placement = True
    else:
        hip_correction_placement = [0, 0, 0]
        weak_placement = True

    return hip_correction_placement, weak_placement


def get_placement_lateral_hip(data, window_start, window_end):

    weak_placement = False

    try:
        hip_accel_data = data["acc_1_y"][window_start:window_end]
        sensor_0_accel_data = data["acc_0_z"][window_start:window_end]
        sensor_2_accel_data = data["acc_2_z"][window_start:window_end]
        lf_euls = qc.quat_to_euler(
            data["quat_0_w"][window_start:window_end],
            data["quat_0_x"][window_start:window_end],
            data["quat_0_y"][window_start:window_end],
            data["quat_0_z"][window_start:window_end])
        sensor_0_euler_y_degrees = pd.Series(lf_euls[:, 1] * 180 / np.pi)
        rf_euls = qc.quat_to_euler(
            data["quat_2_w"][window_start:window_end],
            data["quat_2_x"][window_start:window_end],
            data["quat_2_y"][window_start:window_end],
            data["quat_2_z"][window_start:window_end])
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
        # zero_cross = crossing_zero

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

        if abs(side_0 - side_2) == 1 or (side_2 + side_0) <= 2 or (side_0 == side_2):
            weak_placement = True

        if side_0 > side_2:
            return [0, 1, 2], weak_placement
        elif side_2 > side_0:
            return [2, 1, 0], weak_placement
        else:
            return [0, 0, 0], weak_placement

    except Exception as e:
        print(e)
        _logger.error(e)
        raise(e)
