from __future__ import print_function

import numpy as np
from scipy.stats import skew

import utils.quaternion_conversions as qc
import utils.quaternion_operations as qo
from .exceptions import PlacementDetectionException


def detect_placement(data):
    """Detect placement of sensors using accleration and pitch
    """
    data.reset_index(inplace=True, drop=True)
    start, end = detect_activity(data)
    for i in range(len(start)):
        try:
            data_sub = data.loc[start[i]:end[i], :]
            data_sub.reset_index(inplace=True, drop=True)
            quats_1 = data_sub.loc[:, ['qW0', 'qX0', 'qY0', 'qZ0']].values.reshape(-1, 4)
            quats_2 = data_sub.loc[:, ['qW2', 'qX2', 'qY2', 'qZ2']].values.reshape(-1, 4)

            # prepare foot1 data
            pitch_foot1 = qc.quat_to_euler(quats_1)[100:, 1] * 180 / np.pi
            # # rotate if the placement is at too high angle creating the weird divets in pitch data
            # # TODO: This seems to work but unsure how need to make sure math works
            # if np.nanmean(pitch_foot1[0:100]) > 35:
            #     pitch_foot1 = extract_geometry(quats_1, -np.pi/2)
            # elif np.nanmean(pitch_foot1[0:100]) < -35:
            #     pitch_foot1 = extract_geometry(quats_1, np.pi/2)

            if np.nanmean(data_sub.aY0_original.values[0:100]) < -4.9:  # the sensor was upside down
                pitch_foot1 = -pitch_foot1

            # prepare foot2 data
            pitch_foot2 = qc.quat_to_euler(quats_2)[100:, 1] * 180 / np.pi
            # # rotate if the placement is at too high angle creating the weird divets in pitch data
            # # TODO: This seems to work but unsure how need to make sure math works
            # if np.nanmean(pitch_foot2[0:100]) > 35:
            #     pitch_foot2 = extract_geometry(quats_2, -np.pi/2)
            # elif np.nanmean(pitch_foot2[0:100]) < -35:
            #     pitch_foot2 = extract_geometry(quats_2, np.pi/2)

            if np.nanmean(data_sub.aY2_original.values[0:100]) < -4.9:  # the sensor was upside down
                pitch_foot2 = -pitch_foot2

            return [0, 1, 2] if is_foot1_left(pitch_foot1, pitch_foot2) else [2, 1, 0]

        except Exception as e:
            print(e)
            continue

    raise PlacementDetectionException('Could not detect placement using any of the movements')


def detect_activity(data):
    """Detect part of data with activity for placement detection
    """
    thresh = 5.  # threshold to detect balance phase
    bal_win = 100  # sampling window to determine balance phase
    acc_mag_0 = np.sqrt(data.aX0**2 + data.aY0**2 + data.aZ0**2)
    acc_mag_1 = np.sqrt(data.aX1**2 + data.aY1**2 + data.aZ1**2)
    acc_mag_2 = np.sqrt(data.aX2**2 + data.aY2**2 + data.aZ2**2)
    total_acc_mag = acc_mag_0 + acc_mag_1 + acc_mag_2

    dummy_balphase = []  # dummy variable to store indexes of balance phase

    abs_acc = total_acc_mag.values.reshape(-1, 1)  # creating an array of absolute acceleration values
    len_acc = len(total_acc_mag)  # length of acceleration value

    for i in range(len_acc-bal_win+1):
        # check if all the points within bal_win of current point are within
        # movement threshold
        if len(np.where(abs_acc[i:i+bal_win] <= thresh)[0]) == bal_win:
            dummy_balphase += range(i, i+bal_win)

    # determine the unique indexes in the dummy list
    start_bal = np.unique(dummy_balphase)
    start_bal = np.sort(start_bal)
    start_bal = start_bal.tolist()  # convert from numpy array to list
    # delete variables that are of no use in further compuations
    del dummy_balphase
    min_thresh_mov = 300  # threshold for min number of samples required to be classified as false movement phase
    for i in range(len(start_bal)):
        if i == 0:
            diff = start_bal[i]
            if 1 < diff <= min_thresh_mov:
                for j in range(0, diff):
                    start_bal.append(j)
        else:
            diff = start_bal[i] - start_bal[i-1]
            if 1 < diff <= min_thresh_mov:
                for j in range(1, diff+1):
                    start_bal.append(start_bal[i-1]+j)
    mov = np.ones(len(data))
    mov[start_bal] = 0
    change = np.ediff1d(mov, to_begin=0)
    start = np.where(change == 1)[0]
    end = np.where(change == -1)[0]

    # if data ends with movement, assign final point as end of movement
    if len(start) != len(end):
        end = np.append(end, len(data) - 1)
    start = start - 150

    if len(end) == 0: 
        # No moving portion was detected 
        raise PlacementDetectionException('Moving portion of data could not be detected') 

    # Return all detected section wehre motion is detected and are long enough
    start_final = []
    end_final = []
    for i in range(len(end)):
        end[i] = min([end[i], start[i] + 600])
        if end[i] - start[i] > 400:
            start_final.append(start[i])
            end_final.append(end[i])
    if len(end_final) == 0:
        # No moving portion was detected
        raise PlacementDetectionException('Moving portion with enough points could not be detected')
    else:
        return start_final, end_final


def shift_accel(data):
    """Adjust acceleration so that all axes are centered around 0
    """
    data.loc[:, 'aY0_original'] = data.aY0.values
    data.aX0 = data.aX0 - np.nanmean(data.aX0[0:100])
    data.aY0 = data.aY0 - np.nanmean(data.aY0[0:100])
    data.aZ0 = data.aZ0 - np.nanmean(data.aZ0[0:100])

    data.loc[:, 'aY1_original'] = data.aY1.values
    data.aX1 = data.aX1 - np.nanmean(data.aX1[0:100])
    data.aY1 = data.aY1 - np.nanmean(data.aY1[0:100])
    data.aZ1 = data.aZ1 - np.nanmean(data.aZ1[0:100])

    data.loc[:, 'aY2_original'] = data.aY2.values
    data.aX2 = data.aX2 - np.nanmean(data.aX2[0:100])
    data.aY2 = data.aY2 - np.nanmean(data.aY2[0:100])
    data.aZ2 = data.aZ2 - np.nanmean(data.aZ2[0:100])


def extract_geometry(quats, rot=None):

    i = np.array([0, 1, 0, 0]).reshape(1, 4)
    if rot is not None:
        rotation = qc.euler_to_quat(np.array([[0, 0, rot]]))
        quats = qo.quat_prod(quats, rotation)
    vi = qo.quat_prod(qo.quat_prod(quats, i), qo.quat_conj(quats))
    extension = np.arctan2(vi[:, 3], np.sqrt(vi[:, 1]**2+vi[:, 2]**2)) * 180 / np.pi

    return -extension.reshape(-1, 1)


def is_foot1_left(pitch_foot1, pitch_foot2):
    """Use raw pitch value and the direction of change to detect left vs right foot
    """
    skew1 = skew(pitch_foot1[np.isfinite(pitch_foot1)])
    skew2 = skew(pitch_foot2[np.isfinite(pitch_foot2)])
    threshold = 0.35

    if skew1 < -threshold and skew2 > threshold:
        return True  # foot1 is left, foot2 is right
    elif skew1 > threshold and skew2 < -threshold:
        return False  # foot2 is left, foot1 is right
    else:
        raise PlacementDetectionException('Could not detect left vs right from skew values 1={}, 2={}'.format(skew1, skew2))