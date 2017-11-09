from __future__ import print_function

import numpy as np
import quatConvs as qc


def detect_placement(data):
    """Detect placement of sensors using accleration and pitch
    """
    data.reset_index(inplace=True)
    data = shift_accel(data)
    start, end = detect_activity(data)
    print(start, end)
    data = data.loc[start[0]:end[0], :]
    data.reset_index(inplace=True)
    hip_sensor_id = identify_hip_sensor(data)

    # based on the hip detected, assign other two sensors as foot1 and foot2
    if hip_sensor_id == 0:
        quat1_w = data.qW1.values.reshape(-1, 1)
        quat1_x = data.qX1.values.reshape(-1, 1)
        quat1_y = data.qY1.values.reshape(-1, 1)
        quat1_z = data.qZ1.values.reshape(-1, 1)

        quat2_w = data.qW2.values.reshape(-1, 1)
        quat2_x = data.qX2.values.reshape(-1, 1)
        quat2_y = data.qY2.values.reshape(-1, 1)
        quat2_z = data.qZ2.values.reshape(-1, 1)

        quats_1 = np.concatenate((quat1_w, quat1_x, quat1_y, quat1_z), axis=1)
        quats_2 = np.concatenate((quat2_w, quat2_x, quat2_y, quat2_z), axis=1)

        euls_1 = qc.quat_to_euler(quats_1)
        euls_2 = qc.quat_to_euler(quats_2)

        pitch_foot1 = euls_1[:, 1]
        pitch_foot2 = euls_2[:, 1]

        return [1, 0, 2] if is_foot1_left(pitch_foot1, pitch_foot2) else [2, 0, 1]

    elif hip_sensor_id == 1:
        quat1_w = data.qW0.values.reshape(-1, 1)
        quat1_x = data.qX0.values.reshape(-1, 1)
        quat1_y = data.qY0.values.reshape(-1, 1)
        quat1_z = data.qZ0.values.reshape(-1, 1)

        quat2_w = data.qW2.values.reshape(-1, 1)
        quat2_x = data.qX2.values.reshape(-1, 1)
        quat2_y = data.qY2.values.reshape(-1, 1)
        quat2_z = data.qZ2.values.reshape(-1, 1)

        quats_1 = np.concatenate((quat1_w, quat1_x, quat1_y, quat1_z), axis=1)
        quats_2 = np.concatenate((quat2_w, quat2_x, quat2_y, quat2_z), axis=1)

        euls_1 = qc.quat_to_euler(quats_1)
        euls_2 = qc.quat_to_euler(quats_2)

        pitch_foot1 = euls_1[:, 1]
        pitch_foot2 = euls_2[:, 1]

        return [0, 1, 2] if is_foot1_left(pitch_foot1, pitch_foot2) else [2, 1, 0]

    elif hip_sensor_id == 2:
        quat1_w = data.qW0.values.reshape(-1, 1)
        quat1_x = data.qX0.values.reshape(-1, 1)
        quat1_y = data.qY0.values.reshape(-1, 1)
        quat1_z = data.qZ0.values.reshape(-1, 1)

        quat2_w = data.qW1.values.reshape(-1, 1)
        quat2_x = data.qX1.values.reshape(-1, 1)
        quat2_y = data.qY1.values.reshape(-1, 1)
        quat2_z = data.qZ1.values.reshape(-1, 1)

        quats_1 = np.concatenate((quat1_w, quat1_x, quat1_y, quat1_z), axis=1)
        quats_2 = np.concatenate((quat2_w, quat2_x, quat2_y, quat2_z), axis=1)

        euls_1 = qc.quat_to_euler(quats_1)
        euls_2 = qc.quat_to_euler(quats_2)

        pitch_foot1 = euls_1[:, 1]
        pitch_foot2 = euls_2[:, 1]

        return [0, 2, 1] if is_foot1_left(pitch_foot1, pitch_foot2) else [1, 2, 0]

    else:
        raise Exception('Could not idenfity left from right')


def detect_activity(data):
    """Detect part of data with activity for placement detection
    """
    thresh = 5.  # threshold to detect balance phase
    bal_win = 100 # sampling window to determine balance phase
    acc_mag_0 = np.sqrt(data.aX0**2 + data.aY0**2 + data.aZ0**2)
    acc_mag_1 = np.sqrt(data.aX1**2 + data.aY1**2 + data.aZ1**2)
    acc_mag_2 = np.sqrt(data.aX2**2 + data.aY2**2 + data.aZ2**2)
    total_acc_mag = acc_mag_0 + acc_mag_1 + acc_mag_2

    dummy_balphase = []  # dummy variable to store indexes of balance phase

    abs_acc = total_acc_mag  # creating an array of absolute acceleration values
    len_acc = len(total_acc_mag)  # length of acceleration value
    

    for i in range(len_acc-bal_win):
        # check if all the points within bal_win of current point are within
        # movement threshold
        if len(np.where(abs_acc[i:i+bal_win] <= thresh)[0]) == bal_win:
            dummy_balphase += range(i, i+bal_win)

    # determine the unique indexes in the dummy list
    start_bal = []    
    start_bal = np.unique(dummy_balphase)
    start_bal = np.sort(start_bal)
    start_bal = start_bal.tolist()  # convert from numpy array to list
    # delete variables that are of no use in further compuations
    del dummy_balphase
    min_thresh_mov = 300 # threshold for min number of samples 
                        # required to be classified as false movement phase
    for i in range(len(start_bal) - 1):
        diff = start_bal[i+1] - start_bal[i]
        if 1 < diff <= min_thresh_mov:
            for j in range(1, diff+1):
                start_bal.append(start_bal[i]+j)
    mov = np.ones(len(data))
    mov[start_bal] = 0
    change = np.ediff1d(mov, to_begin=0)
    start = np.where(change==1)[0]
    end = np.where(change==-1)[0]

    # if data ends with movement, assign final point as end of movement
    if len(start) != len(end):
        end = np.append(end, len(data))

    start = start - 100
    for i in range(len(end)):
        end[i] = min([end[i], start[i] + 1100])

    return start, end


def shift_accel(data):
    """Adjust acceleration so that all axes are centered around 0
    """
    data.aX0 = data.aX0 - np.nanmean(data.aX0)
    data.aY0 = data.aY0 - np.nanmean(data.aY0)
    data.aZ0 = data.aZ0 - np.nanmean(data.aZ0)

    data.aX1 = data.aX1 - np.nanmean(data.aX1)
    data.aY1 = data.aY1 - np.nanmean(data.aY1)
    data.aZ1 = data.aZ1 - np.nanmean(data.aZ1)

    data.aX2 = data.aX2 - np.nanmean(data.aX2)
    data.aY2 = data.aY2 - np.nanmean(data.aY2)
    data.aZ2 = data.aZ2 - np.nanmean(data.aZ2)

    return data


def identify_hip_sensor(data):
    """use sum of square of acceleration during movement to detect hips from feet
    """
    sum_sq_0 = np.nansum(data.aX0**2 + data.aY0**2 + data.aZ0**2) / 1000
    sum_sq_1 = np.nansum(data.aX1**2 + data.aY1**2 + data.aZ1**2) / 1000
    sum_sq_2 = np.nansum(data.aX2**2 + data.aY2**2 + data.aZ2**2) / 1000

    ratio = [0, 0, 0]
    ratio[0] = np.min([sum_sq_1, sum_sq_2]) / sum_sq_0
    ratio[1] = np.min([sum_sq_0, sum_sq_2]) / sum_sq_1
    ratio[2] = np.min([sum_sq_0, sum_sq_1]) / sum_sq_2

    print(ratio)

    if np.max(ratio) == ratio[0] and ratio[0] >= 1.5:
        return 0
    elif np.max(ratio) == ratio[1] and ratio[1] >= 1.5:
        return 1
    elif np.max(ratio) == ratio[2] and ratio[2] >= 1.5:
        return 2
    else:
        raise(ValueError) # placeholder for inability to detect hips vs feet


def is_foot1_left(pitch_foot1, pitch_foot2):
    """Use raw pitch value and the direction of change to detect left vs right foot
    """
    # TODO: placeholder logic for now, needs update
    mean1 = np.nanmean(pitch_foot1[0:100])
    mean2 = np.nanmean(pitch_foot2[0:100])

    diff1 = np.nansum(pitch_foot1 - mean1)
    diff2 = np.nansum(pitch_foot2 - mean2)

    return diff2 > diff1
