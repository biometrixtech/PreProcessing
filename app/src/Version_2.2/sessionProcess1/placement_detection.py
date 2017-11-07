from __future__ import print_function

import numpy as np
import quatConvs as qc



def detect_placement(data):
    """Detect placement of sensors using accleration and pitch
    """
    data = shift_accel(data)
    walking = detect_activity(data)
    data = data.loc[walking[0]:walking[1], :]
    data.reset_index(inplace=True)
    hip = hips_vs_feet(data)
    if hip == 0:
        qW1 = data.qW1.values.reshape(-1, 1)
        qX1 = data.qX1.values.reshape(-1, 1)
        qY1 = data.qY1.values.reshape(-1, 1)
        qZ1 = data.qZ1.values.reshape(-1, 1)

        qW2 = data.qW2.values.reshape(-1, 1)
        qX2 = data.qX2.values.reshape(-1, 1)
        qY2 = data.qY2.values.reshape(-1, 1)
        qZ2 = data.qZ2.values.reshape(-1, 1)

        quats_1 = np.concatenate((qW1, qX1, qY1, qZ1), axis=1)
        quats_2 = np.concatenate((qW2, qX2, qY2, qZ2), axis=1)

        euls_1 = qc.quat_to_euler(quats_1)
        euls_2 = qc.quat_to_euler(quats_2)

        pitch_foot1 = euls_1[:, 1]
        pitch_foot2 = euls_2[:, 1]

        right_0, left_0 = left_vs_right(pitch_foot1, pitch_foot2)
        right = right_0
        left = left_0

    elif hip == 1:
        qW1 = data.qW0.values.reshape(-1, 1)
        qX1 = data.qX0.values.reshape(-1, 1)
        qY1 = data.qY0.values.reshape(-1, 1)
        qZ1 = data.qZ0.values.reshape(-1, 1)

        qW2 = data.qW2.values.reshape(-1, 1)
        qX2 = data.qX2.values.reshape(-1, 1)
        qY2 = data.qY2.values.reshape(-1, 1)
        qZ2 = data.qZ2.values.reshape(-1, 1)

        quats_1 = np.concatenate((qW1, qX1, qY1, qZ1), axis=1)
        quats_2 = np.concatenate((qW2, qX2, qY2, qZ2), axis=1)

        euls_1 = qc.quat_to_euler(quats_1)
        euls_2 = qc.quat_to_euler(quats_2)

        pitch_foot1 = euls_1[:, 1]
        pitch_foot2 = euls_2[:, 1]

        right_0, left_0 = left_vs_right(pitch_foot1, pitch_foot2)
        if right_0 == 1:
            right = 0
            left = 2
        else:
            right = 2
            left = 0

    elif hip == 2:
        qW1 = data.qW0.values.reshape(-1, 1)
        qX1 = data.qX0.values.reshape(-1, 1)
        qY1 = data.qY0.values.reshape(-1, 1)
        qZ1 = data.qZ0.values.reshape(-1, 1)

        qW2 = data.qW1.values.reshape(-1, 1)
        qX2 = data.qX1.values.reshape(-1, 1)
        qY2 = data.qY1.values.reshape(-1, 1)
        qZ2 = data.qZ1.values.reshape(-1, 1)

        quats_1 = np.concatenate((qW1, qX1, qY1, qZ1), axis=1)
        quats_2 = np.concatenate((qW2, qX2, qY2, qZ2), axis=1)

        euls_1 = qc.quat_to_euler(quats_1)
        euls_2 = qc.quat_to_euler(quats_2)

        pitch_foot1 = euls_1[:, 1]
        pitch_foot2 = euls_2[:, 1]

        right_0, left_0 = left_vs_right(pitch_foot1, pitch_foot2)
        if right_0 == 1:
            right = 0
            left = 1
        else:
            right = 1
            left = 0

    return str(left) + str(hip) + str(right)


def detect_activity(data):
    """Detect part of data with activity for placement detection
    """
    thresh = 5.  # threshold to detect balance phase
    bal_win = 100 # sampling window to determine balance phase
    min_mov = 100
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
    change = np.where(np.ediff1d(start_bal) > min_mov)[0]

    start = start_bal[change[0]] - 200
    end = start + 1700

    return start, end


def shift_accel(data):
    """Adjust acceleration so that all axes are centered around 0
    """
    data.aX0 = data.aX0 - np.nanmean(data.aX0)
    data.aX0 = data.aX0 - np.nanmean(data.aX0)
    data.aZ0 = data.aZ0 - np.nanmean(data.aZ0)

    data.aX1 = data.aX1 - np.nanmean(data.aX1)
    data.aY1 = data.aY1 - np.nanmean(data.aY1)
    data.aZ1 = data.aZ1 - np.nanmean(data.aZ1)

    data.aX2 = data.aX2 - np.nanmean(data.aX2)
    data.aY2 = data.aY2 - np.nanmean(data.aY2)
    data.aZ2 = data.aZ2 - np.nanmean(data.aZ2)

    return data


def hips_vs_feet(data):
    """use sum of square of acceleration during movement to detect hips from feet
    """
    sum_sq_0 = np.sum(data.aX0**2 + data.aY0**2 + data.aZ0**2) / 1000
    sum_sq_1 = np.sum(data.aX1**2 + data.aY1**2 + data.aZ1**2) / 1000
    sum_sq_2 = np.sum(data.aX2**2 + data.aY2**2 + data.aZ2**2) / 1000

    ratio = [0, 0, 0]
    ratio[0] = np.min([sum_sq_1, sum_sq_2]) / sum_sq_0
    ratio[1] = np.min([sum_sq_0, sum_sq_2]) / sum_sq_1
    ratio[2] = np.min([sum_sq_0, sum_sq_1]) / sum_sq_2
    print(ratio)

    if np.max(ratio) == ratio[0] and ratio[0] >= 1.5:
        hip = 0
    elif np.max(ratio) == ratio[1] and ratio[1] >= 1.5:
        hip = 1
    elif np.max(ratio) == ratio[2] and ratio[2] >= 1.5:
        hip = 2
    else:
        raise(ValueError)

    return hip


def left_vs_right(pitch_foot1, pitch_foot2):
    """Use raw pitch value and the direction of change to detect left vs right foot
    """
    mean1 = np.nanmean(pitch_foot1[0:100])
    mean2 = np.nanmean(pitch_foot2[0:100])

    diff1 = np.nansum(pitch_foot1 - mean1)
    diff2 = np.nansum(pitch_foot2 - mean2)

    if diff2 > diff1:
        right = 2
        left = 1
    else:
        right = 1
        left = 2
    return left, right
