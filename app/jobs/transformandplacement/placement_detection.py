from __future__ import print_function
import logging
import numpy as np
import pandas as pd
from scipy.stats import skew


import utils.quaternion_operations as qo

from utils import quaternion_conversions as qc
from jobs.transformandplacement.exceptions import PlacementDetectionException
from jobs.transformandplacement.column_vector import MatchProbability


_logger = logging.getLogger(__name__)


def detect_placement(data):
    """Detect placement of sensors using accleration and pitch
    """
    data.reset_index(inplace=True, drop=True)
    start, end = detect_activity(data)
    for i in range(len(start)):
        try:
            data_sub = data.loc[start[i]:end[i], :]
            data_sub.reset_index(inplace=True, drop=True)

            # prepare foot1 data
            pitch_foot1 = qc.quat_to_euler(
                data_sub['quat_0_w'],
                data_sub['quat_0_x'],
                data_sub['quat_0_y'],
                data_sub['quat_0_z'],
            )[100:, 1] * 180 / np.pi
            # # rotate if the placement is at too high angle creating the weird divets in pitch data
            # # TODO: This seems to work but unsure how need to make sure math works
            # if np.nanmean(pitch_foot1[0:100]) > 35:
            #     pitch_foot1 = extract_geometry(quats_1, -np.pi/2)
            # elif np.nanmean(pitch_foot1[0:100]) < -35:
            #     pitch_foot1 = extract_geometry(quats_1, np.pi/2)

            if np.nanmean(data_sub.acc_0_y_original.values[0:100]) < -4.9:  # the sensor was upside down
                pitch_foot1 = -pitch_foot1

            # prepare foot2 data
            pitch_foot2 = qc.quat_to_euler(
                data_sub['quat_2_w'],
                data_sub['quat_2_x'],
                data_sub['quat_2_y'],
                data_sub['quat_2_z'],
            )[100:, 1] * 180 / np.pi
            # # rotate if the placement is at too high angle creating the weird divets in pitch data
            # # TODO: This seems to work but unsure how need to make sure math works
            # if np.nanmean(pitch_foot2[0:100]) > 35:
            #     pitch_foot2 = extract_geometry(quats_2, -np.pi/2)
            # elif np.nanmean(pitch_foot2[0:100]) < -35:
            #     pitch_foot2 = extract_geometry(quats_2, np.pi/2)

            if np.nanmean(data_sub.acc_2_y_original.values[0:100]) < -4.9:  # the sensor was upside down
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
    acc_mag_0 = np.sqrt(data.acc_0_x**2 + data.acc_0_y**2 + data.acc_0_z**2)
    acc_mag_1 = np.sqrt(data.acc_1_x**2 + data.acc_1_y**2 + data.acc_1_z**2)
    acc_mag_2 = np.sqrt(data.acc_2_x**2 + data.acc_2_y**2 + data.acc_2_z**2)
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
    data.loc[:, 'acc_0_x_original'] = data.acc_0_x.values
    data.loc[:, 'acc_0_y_original'] = data.acc_0_y.values
    data.loc[:, 'acc_0_z_original'] = data.acc_0_z.values
    data.acc_0_x = data.acc_0_x - np.nanmean(data.acc_0_x[0:100])
    data.acc_0_y = data.acc_0_y - np.nanmean(data.acc_0_y[0:100])
    data.acc_0_z = data.acc_0_z - np.nanmean(data.acc_0_z[0:100])

    data.loc[:, 'acc_1_x_original'] = data.acc_1_x.values
    data.loc[:, 'acc_1_y_original'] = data.acc_1_y.values
    data.loc[:, 'acc_1_z_original'] = data.acc_1_z.values
    data.acc_1_x = data.acc_1_x - np.nanmean(data.acc_1_x[0:100])
    data.acc_1_y = data.acc_1_y - np.nanmean(data.acc_1_y[0:100])
    data.acc_1_z = data.acc_1_z - np.nanmean(data.acc_1_z[0:100])

    data.loc[:, 'acc_2_x_original'] = data.acc_2_x.values
    data.loc[:, 'acc_2_y_original'] = data.acc_2_y.values
    data.loc[:, 'acc_2_z_original'] = data.acc_2_z.values
    data.acc_2_x = data.acc_2_x - np.nanmean(data.acc_2_x[0:100])
    data.acc_2_y = data.acc_2_y - np.nanmean(data.acc_2_y[0:100])
    data.acc_2_z = data.acc_2_z - np.nanmean(data.acc_2_z[0:100])


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


def get_eulers(data):
    euls_0 = qc.quat_to_euler(
                    data['quat_0_w'],
                    data['quat_0_x'],
                    data['quat_0_y'],
                    data['quat_0_z'],)
    data['euler_0_x'] = euls_0[:, 0].reshape(-1, 1)
    data['euler_0_y'] = euls_0[:, 1].reshape(-1, 1)

    euls_2 = qc.quat_to_euler(
                    data['quat_2_w'],
                    data['quat_2_x'],
                    data['quat_2_y'],
                    data['quat_2_z'],)
    data['euler_2_x'] = euls_2[:, 0].reshape(-1, 1)
    data['euler_2_y'] = euls_2[:, 1].reshape(-1, 1)


def predict_placement(data, condition_list):
    get_eulers(data)

    ax0_list = list(data.acc_0_x_original)
    ay0_list = list(data.acc_0_y_original)
    az0_list = list(data.acc_0_z_original)
    ax2_list = list(data.acc_2_x_original)
    ay2_list = list(data.acc_2_y_original)
    az2_list = list(data.acc_2_z_original)
    ex0_list = list(data.euler_0_x)
    ey0_list = list(data.euler_0_y)
    ex2_list = list(data.euler_2_x)
    ey2_list = list(data.euler_2_y)

    mp = MatchProbability(condition_list)

    mp.calc_rankings(ax0_list, ay0_list, az0_list, ex0_list, ey0_list, ax2_list, ay2_list, az2_list, ex2_list, ey2_list)
    for condition, ranking in mp.condition_ranking.items():
        if ranking.rank == 0:
            result = condition.split("_")
            placement = [int(i) for i in result[2]]
            return placement, {'left': result[0].upper(), 'right': result[1].upper()}


