from __future__ import print_function

import numpy as np

from .exceptions import PlacementDetectionException


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


def detect_hip_sensor(accel, win=100, thresh=2.):
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
        count_sensor0 = count_sensor0 + active if active[0] == 1 else count_sensor0
        count_sensor1 = count_sensor1 + active if active[1] == 1 else count_sensor1
        count_sensor2 = count_sensor2 + active if active[2] == 1 else count_sensor2
        i += win
        counts += 1

    movement_perc = np.array([count_sensor0[0], count_sensor1[1], count_sensor2[2]]) / float(counts)
    if count_sensor0[0] > 0:
        ratio_sensor0 = np.array([count_sensor0[1], count_sensor0[2]]) / float(count_sensor0[0])
    else:
        ratio_sensor0 = np.array([0., 0.])
    if count_sensor1[1] > 0:
        ratio_sensor1 = np.array([count_sensor1[0], count_sensor1[2]]) / float(count_sensor1[1])
    else:
        ratio_sensor1 = np.array([0., 0.])
    if count_sensor2[2] > 0:
        ratio_sensor2 = np.array([count_sensor2[0], count_sensor2[1]]) / float(count_sensor2[2])
    else:
        ratio_sensor2 = np.array([0., 0.])

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


def detect_data_truncation(data, placement, sensors=3):
    """Check accel values to see if truncation is necessary
    Inputs:
        data: pandas dataframe with the whole session
        placement: placement array [left, hip, right]
        sensors: number of sensors in use (1 or 3)
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

    win = 200
    i = 0
    seven_mins = 7 * 60 * 100. / win
    five_mins = 5 * 60 * 100. / win
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

    missing_left = missing_hip = missing_right = 0
    cont_missing_left = cont_missing_hip = cont_missing_right = 0
    if sensors == 3:
        counter = 0
        for l, h, r in zip(left, hip, right):
            cont_missing_left = cont_missing_left + 1 if l == 0 else 0
            # cont_missing_hip = cont_missing_hip + 1 if h == 0 else 0
            cont_missing_right = cont_missing_right + 1 if r == 0 else 0
            if l == 1 or r == 1:
                # if there's no movement in hip when there's movement in one of the legs for 5 mins
                # total or any continuous 7 mins, truncate data
                if missing_hip > five_mins or cont_missing_hip > seven_mins:
                    print('Truncating data as movement in hip not detected for extended period')
                    return (True, False, (counter - 60) * win)
                else:
                    missing_hip = missing_hip + 1 if h == 0 else 0
            if h == 1:
                missing_hip = 0
                # If there's no movement in either of the legs for >5 mins when there's movement
                # in hip or for a continuous 7 minutes without considering hips,
                # we're assuming user either took off the sensors or sensor fell off and
                # processing as single sensor
                if missing_left > five_mins or missing_right > five_mins \
                        or cont_missing_left > seven_mins or cont_missing_right > seven_mins:
                    print('Feet inactive for extended period. Moving to single sensor.')
                    return (False, True, None)
                else:
                    missing_left = missing_left + 1 if l == 0 else 0
                    missing_right = missing_right + 1 if r == 0 else 0

            counter += 1
    elif sensors == 1:
        # for single sensor, determine if it needs to be truncated single sensor
        # slightly longer threshold >7mins as we're looking at continous time
        # and to account for standing during breaks
        counter = 0
        missing_hip = 0
        for h in hip:
            if missing_hip >= seven_mins:
                print("Truncating data as movement in hip not detected for extended period")
                return (True, True, (counter - 84) * win)
            else:
                missing_hip = missing_hip + 1 if h == 0 else 0
            counter += 1

    # if turncation or single sensor is not required, return default
    return (False, False, None)
