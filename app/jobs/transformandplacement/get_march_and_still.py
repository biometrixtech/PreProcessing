import numpy as np
# import pandas as pd
from .exceptions import StillDetectionException, MarchDetectionException

from utils import get_ranges
from utils.quaternion_conversions import quat_to_euler
# from utils.quaternion_operations import quat_conjugate, hamilton_product
import utils.quaternion_operations as qo

from .body_frame_transformation import body_frame_tran

from scipy.signal import find_peaks

from .transform_calculation import compute_transform
from .heading_calculation import heading_foot_finder
from jobs.driftcorrection.heading_correction import heading_correction


def detect_march_and_still(data):
    # get candidate windows
    try:
        print('trying with sensor0')
        return get_march_and_still(data, 0)
    except MarchDetectionException:
        try:
            print('trying with sensor2')
            return get_march_and_still(data, 2)
        except MarchDetectionException:
            raise
        

def get_march_and_still(data, sensor):
    static = data[f"static_{sensor}"]
    static = _fix_short_static(static)
    ranges, lengths = get_ranges(static, 1, True)
    for r, length in zip(ranges, lengths):
        if length >= 400 and r[0] > 150:
            start = r[0]
            end = min(r[1], r[0] + int(600))
            if is_valid_march(data, start, end):
                (start_still_0, end_still_0, start_still_hip, end_still_hip, start_still_2, end_still_2) = get_still_all(data, start)
                return (start, end, start_still_0, end_still_0,
                        start, end, start_still_hip, end_still_hip,
                        start, end, start_still_2, end_still_2)
            else:
                continue
    raise MarchDetectionException("could not detect marching+still")


def is_valid_march(data, start, end):
    print(f"candidate start and end of march {start}, {end}")

    # validate march based on acceleration
    acc_lf = data.loc[start:end, ['acc_0_x', 'acc_0_y', 'acc_0_z']].values
    acc_rf = data.loc[start:end, ['acc_2_x', 'acc_2_y', 'acc_2_z']].values
    left_valid = validate_march_acc(acc_lf)
    right_valid = validate_march_acc(acc_rf)

    if left_valid and right_valid:
        # find static right before marching
        try:
            samples_before_march = min([250, start])
            start_still_0, end_still_0 = _detect_still(data[start - samples_before_march:start], sensor=0)
            start_still_0 += start - samples_before_march
            end_still_0 += start - samples_before_march
            start_still_2, end_still_2 = _detect_still(data[start - samples_before_march:start], sensor=2)
            start_still_2 += start - samples_before_march
            end_still_2 += start - samples_before_march
            start_still_hip = start_still_0
            end_still_hip = end_still_0
            start = min([end_still_0, end_still_2])
        except StillDetectionException:
            print(f"STILL DETECTION FAILED {start, end}")
            return False
        else:
            # transform and heading correct the data
            ref_quats = compute_transform(data,
                                          start_still_0,
                                          end_still_0,
                                          start_still_hip,
                                          end_still_hip,
                                          start_still_2,
                                          end_still_2
                                          )
            data_c = body_frame_tran(data, ref_quats[0], ref_quats[1], ref_quats[2])
            print("data transformed")
            qHH = ref_quats[3]
            try:
                qH0, qH2 = heading_foot_finder(data_c[start:end, 5:9], data_c[start:end, 21:25])
                data_hc = heading_correction(data_c, qH0, qHH, qH2)
                print("heading corrected, checking euler")
            except:
                print(f"HEADING DETECTION FAILED {start, end}")
                return False
            else:
                # euler angle checks
                quats_lf = data_hc[start:end, 5:9]
                quats_rf = data_hc[start:end, 21:25]
                if validate_pitch(quats_lf) and validate_pitch(quats_rf):
                    print(f"PITCH VALIDATED")
                    return True
                else:
                    print(f"PITCH VALIDATION FAILED {start, end}")
                    return False


def get_still_all(data, start):
    samples_before_march = min([250, start])
    start_still_0, end_still_0 = _detect_still(data[start - samples_before_march:start], sensor=0)
    start_still_0 += start - samples_before_march
    end_still_0 += start - samples_before_march
    start_still_2, end_still_2 = _detect_still(data[start - samples_before_march:start], sensor=2)
    start_still_2 += start - samples_before_march
    end_still_2 += start - samples_before_march
    start_still_hip = start_still_0
    end_still_hip = end_still_0

    return (start_still_0, end_still_0,
            start_still_hip, end_still_hip,
            start_still_2, end_still_2)


def validate_pitch(quats):
    """
    Validate:
        - We have pitch change in good range
        - Pitch change is uni-directional
        - Motion is mostly in pitch and roll change is minimal
    """
    valid_pitch = False
    euler_x, euler_y = extract_geometry(quats)

    euler_x = euler_x[0:400] * 180 / np.pi
    euler_y *= 180 / np.pi

    init_pitch = euler_y[0]
    pitch_diff = euler_y - init_pitch
    peaks, peak_heights = find_peaks(pitch_diff, height=20, distance=50)
    has_good_peaks = len(peaks) >= 3
    if has_good_peaks:
        # # make sure pich change is uni-directional (exclude walking)
        # if np.any(pitch_diff[peaks] >= 75):
        #     # exclude march with very high pitch change (e.g. buttkicks) as this introduces error in heading detection
        #     return False
        # # make sure there's no walking
        for i in range(1, len(peaks)):
            if np.all(pitch_diff[peaks[i-1]:peaks[i]] > -10):
                if i >= 2:
                    valid_pitch = True
            else:
                break
    if valid_pitch:
        # validate that after heading correction, most of the motion is in pitch
        if min(euler_x) < -25 or max(euler_x) > 25:
            valid_pitch = False
            print(f"min and max roll: {min(euler_x), max(euler_x)}")

    return valid_pitch


def validate_march_acc(acc):
    """Validate that the window has some peaks in acceleration associated with marching
    Note: this will validate walking as well, which will be rejected in a later step
    """

    marching_found = False
    acc_norm = np.linalg.norm(acc, axis=1) - 1000
    peak_pos, _ = find_peaks(acc_norm, height=1000, distance=50)
    if peak_pos.size >= 3:
        marching_found = True
    return marching_found


def _fix_short_static(static):
    ranges, length = get_ranges(static, 0, True)
    for r, l in zip(ranges, length):
        if l < 15:
            static[r[0]: r[1]] = 1
    return static


def _detect_still(data, sensor=0):
    """Detect part of data without activity for neutral reference
    """
    len(data)
    euler = quat_to_euler(
        data[f'quat_{sensor}_w'],
        data[f'quat_{sensor}_x'],
        data[f'quat_{sensor}_y'],
        data[f'quat_{sensor}_z'],
    )
    euler_x = euler[:, 0] * 180 / np.pi
    euler_y = euler[:, 1] * 180 / np.pi
    static = data[f'static_{sensor}'].values
    # x_diff = max(euler_x) - min(euler_x)
    # y_diff = max(euler_y) - min(euler_y)
#    max_diff_all = max(x_diff, y_diff)
#    if max_diff_all > 20:  # too much movement/drift in the second prior
#        raise StillDetectionException(f'could not detect still for sensor{sensor}', sensor)

    for i in np.arange(len(data) - 1, 25, -1):
        start = i - 25
        end = i
        # get the greatest change in angle in the window
        x_diff = max(euler_x[start:end]) - min(euler_x[start:end])
        y_diff = max(euler_y[start:end]) - min(euler_y[start:end])
        max_diff = max(x_diff, y_diff)

        # check the number of static samples in the window
        static_present = static[start:end] == 0
        static_count = sum(static_present)

        # if either is good, use the window
        if static_count >= 20 or max_diff < .75:
            return start, end
    raise StillDetectionException(f'could not detect still for sensor{sensor}', sensor)


def extract_geometry(quats):
    """
    Function to interpret quaternion data geometrically.
    Explanation given here: https://sites.google.com/a/biometrixtech.com/wiki/home/preprocessing/anatomical/methods-tried/general-math-methods/geometry-extraction

    Args:
        quats = quaternions

    Returns:
        adduction: tilt about x axis in radians
        flexion: tilt about y axis in radians
    """

    k_v = np.array([0, 0, 0, 1]).reshape(-1, 4)
    v_k = qo.quat_prod(qo.quat_prod(quats.reshape(-1, 4), k_v),
                       qo.quat_conj(quats.reshape(-1, 4)))
    j_v = np.array([0, 0, 1, 0]).reshape(-1, 4)
    v_j = qo.quat_prod(qo.quat_prod(quats.reshape(-1, 4), j_v),
                       qo.quat_conj(quats.reshape(-1, 4)))
    i_v = np.array([0, 1, 0, 0]).reshape(-1, 4)
    v_i = qo.quat_prod(qo.quat_prod(quats.reshape(-1, 4), i_v),
                       qo.quat_conj(quats.reshape(-1, 4)))
    n = len(quats)
    z_cross = np.zeros((n, 1))
    z_cross[v_k[:, 3] < 0] = 1
    
    flexion = np.arctan2(v_i[:, 3], (np.sqrt(v_i[:, 1] ** 2 + v_i[:, 2] ** 2))) * 180 / np.pi
    adduction = np.arctan2(v_j[:, 3], np.sqrt(v_j[:, 1]**2 + v_j[:, 2]**2)) * 180 / np.pi
    
    for i in range(n - 1):
        # Left foot
        if z_cross[i] == 1 and z_cross[i - 1] == 0:
            # Found a window - search for the values at the boundaries
            bound2_index = i
            while z_cross[bound2_index] == 1 and z_cross[bound2_index + 1] == 1 and bound2_index < (len(z_cross) - 2):
                    bound2_index = bound2_index + 1
            if flexion[i] < 0:
                if flexion[i - 1] < flexion[bound2_index + 1]:
                    mirroring_value = flexion[i - 1]
                else:
                    mirroring_value = flexion[bound2_index + 1]
            else:
                if flexion[i - 1] > flexion[bound2_index + 1]:
                    mirroring_value = flexion[i - 1]
                else:
                    mirroring_value = flexion[bound2_index + 1]
            for k in range(i, bound2_index):
                flexion[k] = mirroring_value - (flexion[k] - mirroring_value)

    flexion = -flexion / 180 * np.pi
    adduction = adduction / 180 * np.pi
    
    return adduction, flexion
