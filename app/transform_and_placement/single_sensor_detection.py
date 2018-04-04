from __future__ import print_function

import numpy as np
from scipy.signal import butter, filtfilt


from exceptions import PlacementDetectionException

def detect_used_sensor(data):
    """Use inactivity to detect if it's a single sensor use
    """

    accel0 = np.sqrt(data.aX0**2 + data.aY0**2 + data.aZ0**2)
    accel1 = np.sqrt(data.aX1**2 + data.aY1**2 + data.aZ1**2)
    accel2 = np.sqrt(data.aX2**2 + data.aY2**2 + data.aZ2**2)

    sensor0, mov0 = check_long_inactivity(accel0)
    sensor1, mov1 = check_long_inactivity(accel1)
    sensor2, mov2 = check_long_inactivity(accel2)
    mov_perc = [mov0, mov1, mov2]
    print(sensor0, sensor1, sensor2)
    print(mov0, mov1, mov2)

    if not sensor0 and sensor1 and sensor2:
        placement = [1, 0, 2]
    elif not sensor1 and sensor0 and sensor2:
        placement = [0, 1, 2]
    elif not sensor2 and sensor0 and sensor1:
        placement = [0, 2, 1]
    else:
        if np.sum(mov_perc < .1) == 2:
            if mov_perc[0] > .2:
                placement = [1, 0, 2]
            elif mov_perc[1] > .2:
                placement = [0, 1, 2]
            elif mov_perc[2] > .2:
                placement = [1, 2, 0]
            else:
                raise PlacementDetectionException('Placement Detection Failed and cannot detect single sensor in use')
        else:
            raise PlacementDetectionException('Placement Detection Failed and cannot detect single sensor in use')

    return placement

def check_long_inactivity(values, win=36000, thresh=1):
    """Check for long period of inactivity
    """
    values = _filter_data(values)
    i = 0
    inactive = False
    while i < len(values) - win  and not inactive:
        current = np.mean(values[i:i+100])
        window_diff = np.abs(values[i:i+win] - current)
        if np.all(window_diff < thresh):
            inactive = True
        else:
            i += 1000
    average = np.mean(values[0:100])
    perc_movement = len(np.where(np.abs(values - average) > 1)[0]) / float(len(values))
    return inactive, perc_movement


def _filter_data(X, cutoff=6, fs=100, order=4):
    """forward-backward lowpass butterworth filter
    defaults:
        cutoff freq: 12hz
        sampling rage: 100hz
        order: 4"""
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    X_filt = filtfilt(b, a, X, axis=0)
    return X_filt
