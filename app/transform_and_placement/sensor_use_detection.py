from __future__ import print_function

import numpy as np

from exceptions import PlacementDetectionException


def detect_single_sensor(data):
    """Use inactivity to detect if it's a single sensor use
    Output:
        placement list with [left, hip, right] placement only hip is true placement. Left and
        right are dummy placementes
    """
    sensor0 = np.sqrt(np.sum(data.loc[:, ['aX0', 'aY0', 'aZ0']].values ** 2, axis=1))
    sensor1 = np.sqrt(np.sum(data.loc[:, ['aX1', 'aY1', 'aZ1']].values ** 2, axis=1))
    sensor2 = np.sqrt(np.sum(data.loc[:, ['aX2', 'aY2', 'aZ2']].values ** 2, axis=1))

    placement = detect_hip_sensor([sensor0, sensor1, sensor2])

    return placement


def detect_hip_sensor(accel, win=100, thresh=1):
    """Check for long period of inactivity
    Output:
        placement list with [left, hip, right] placement only hip is true placement. Left and
        right are dummy placementes
        Note: Exception is raised and processing halted if hip sensor cannot be identified
    """
    sensor0 = accel[0]
    sensor1 = accel[1]
    sensor2 = accel[2]

    count_sensor0 = np.array([0, 0, 0])
    count_sensor1 = np.array([0, 0, 0])
    count_sensor2 = np.array([0, 0, 0])
    counts = 0
    i = 0
    while i < len(accel[0]) - win:
        active = check_active(sensor0[i:i+win], sensor1[i:i+win], sensor2[i:i+win], thresh)
        if active[0] == 1:
            count_sensor0 += active
        if active[1] == 1:
            count_sensor1 += active
        if active[2] == 1:
            count_sensor2 += active
        i += win
        counts += 1

    movement_perc = np.array([count_sensor0[0], count_sensor1[1], count_sensor2[2]]) / float(counts)
    ratio_sensor0 = np.array([count_sensor0[1], count_sensor0[2]])/ float(count_sensor0[0])
    ratio_sensor1 = np.array([count_sensor1[0], count_sensor1[2]])/ float(count_sensor1[1])
    ratio_sensor2 = np.array([count_sensor2[0], count_sensor2[1]])/ float(count_sensor2[2])

    if np.sum(movement_perc >= .2) == 1:
        # check if first sensor is hip
        if np.all(ratio_sensor0 <= 0.5) and movement_perc[0] >= .2:
            placement = [1, 0, 2]
        # check if second sensor is hip
        elif np.all(ratio_sensor1 <= 0.5) and movement_perc[1] >= .2:
            placement = [0, 1, 2]
        # check if third sensor is hip
        elif np.all(ratio_sensor2 <= 0.5) and movement_perc[2] >= .2:
            placement = [0, 2, 1]
        else:
            raise PlacementDetectionException('Failed placement and cannot detect hip sensor')
    else:
        raise PlacementDetectionException('Failed placement and cannot detect hip sensor')
    return placement


def check_active(sensor0, sensor1, sensor2, accel_thresh, perc=.2):
    """Check if the each of the sensor is active or not within the block
    """
    result = [0, 0, 0]
    mov_thresh = perc * len(sensor0)
    mean_sensor0 = np.mean(sensor0)
    mean_sensor1 = np.mean(sensor1)
    mean_sensor2 = np.mean(sensor2)

    sensor0 = np.abs(sensor0 - mean_sensor0)
    sensor1 = np.abs(sensor1 - mean_sensor1)
    sensor2 = np.abs(sensor2 - mean_sensor2)
    if np.sum(sensor0 > accel_thresh) > mov_thresh:
        result[0] = 1
    if np.sum(sensor1 > accel_thresh) > mov_thresh:
        result[1] = 1
    if np.sum(sensor2 > accel_thresh) > mov_thresh:
        result[2] = 1

    return result


def detect_data_truncation(data, placement):
    """Check accel values to see if truncation is necessary
    Inputs:
        data: pandas dataframe with the whole session
        placement: placement array [left, hip, right]
    Output:
        Tuple with values (truncate, single_sensor, truncation_index)
            truncate=True if truncation is required
            single_sensor=True if single sensor processing required
            truncation_index location to truncate if truncation required
    """
    sensor0 = np.sqrt(np.sum(data.loc[:, ['aX0', 'aY0', 'aZ0']].values ** 2, axis=1))
    sensor1 = np.sqrt(np.sum(data.loc[:, ['aX1', 'aY1', 'aZ1']].values ** 2, axis=1))
    sensor2 = np.sqrt(np.sum(data.loc[:, ['aX2', 'aY2', 'aZ2']].values ** 2, axis=1))

    left = sensor0 if placement[0] == 0 else sensor1 if placement[0] == 1 else sensor2
    hip = sensor0 if placement[1] == 0 else sensor1 if placement[1] == 1 else sensor2
    right = sensor0 if placement[2] == 0 else sensor1 if placement[2] == 1 else sensor2

    win = 500
    i = 0
    active_all = np.array([[0, 0, 0]])
    while i < len(data) - win:
        # active is defined as accel is outside 1m/s^2 window of average accel more than 10% of
        # the time within the block (defined as 5s). Need 50 points out of 500 to be outside the
        # range. This should cover squats or similar low intense activities
        active = np.array(check_active(left[i:i+win],
                                       hip[i:i+win],
                                       right[i:i+win],
                                       accel_thresh=1.,
                                       perc=.1))
        active_all = np.append(active_all, active.reshape(1, -1), axis=0)
        i += win
    left = active_all[:, 0]
    hip = active_all[:, 1]
    right = active_all[:, 2]

    missing_left = 0
    missing_hip = 0
    missing_right = 0

    counter = 0
    for l, h, r in zip(left, hip, right):
        if l == 1 or r == 1:
            # if there's no movement in hip when there's movement in one of the legs for 5 mins
            # truncate data
            if missing_hip > 60:
                print('Truncating data as movement in hip not detected for extended period')
                return (True, False, counter * win)
            elif h == 0:
                missing_hip += 1
            else:
                missing_hip = 0
        if h == 1:
            # If there's no movement in either of the legs for >5 mins when there's movement in hip
            # we're assuming user either took of the sensors or sensor fell of and processing as
            # single sensor
            if missing_left > 60 or missing_right > 60:
                print('No movement detected in feet for extended period. Moving to single sensor')
                return (False, True, None)
            else:
                if l == 0:
                    missing_left += 1
                else:
                    missing_left = 0
                if r == 0:
                    missing_right += 1
                else:
                    missing_right = 0
        counter += 1

    return (False, False, None)
