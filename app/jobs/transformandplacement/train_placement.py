import os
from os.path import isfile, join
import pickle

from .column_vector import Condition
from jobs.downloadandchunk.decode_data import read_file
from .placement_detection import shift_accel, get_eulers


def train(input_dir, output_dir):
    condition_list = []

    bce_bce_012 = Condition('bce_bce_012', 'g1', 'g4', True)
    bce_bce_210 = Condition('bce_bce_210', 'g1', 'g4', False)
    bde_bde_012 = Condition('bde_bde_012', 'g1', 'g4', True)
    bde_bde_210 = Condition('bde_bde_210', 'g1', 'g4', False)
    ace_ace_012 = Condition('ace_ace_012', 'g2', 'g3', True)
    ace_ace_210 = Condition('ace_ace_210', 'g2', 'g3', False)
    ade_ade_012 = Condition('ade_ade_012', 'g2', 'g3', True)
    ade_ade_210 = Condition('ade_ade_210', 'g2', 'g3', False)
    acf_acf_012 = Condition('acf_acf_012', 'g3', 'g2', True)
    acf_acf_210 = Condition('acf_acf_210', 'g3', 'g2', False)
    adf_adf_012 = Condition('adf_adf_012', 'g3', 'g2', True)
    adf_adf_210 = Condition('adf_adf_210', 'g3', 'g2', False)
    bcf_bcf_012 = Condition('bcf_bcf_012', 'g4', 'g1', True)
    bcf_bcf_210 = Condition('bcf_bcf_210', 'g4', 'g1', False)
    bdf_bdf_012 = Condition('bdf_bdf_012', 'g4', 'g1', True)
    bdf_bdf_210 = Condition('bdf_bdf_210', 'g4', 'g1', False)
    ade_ace_012 = Condition('ade_ace_012', 'g4', 'g1', True)
    ade_ace_210 = Condition('ade_ace_210', 'g4', 'g1', False)

    training_files = [t for t in os.listdir(input_dir) if isfile(join(input_dir, t))]
    training_files = [t for t in training_files if '.DS_Store' not in t]
    for file_name in training_files:
        tap_data = read_file(os.path.join(input_dir, file_name))
        shift_accel(tap_data)
        get_eulers(tap_data)

        ax0_list = list(tap_data.acc_0_x_original)[0:1000]
        ay0_list = list(tap_data.acc_0_y_original)[0:1000]
        az0_list = list(tap_data.acc_0_z_original)[0:1000]
        ax2_list = list(tap_data.acc_2_x_original)[0:1000]
        ay2_list = list(tap_data.acc_2_y_original)[0:1000]
        az2_list = list(tap_data.acc_2_z_original)[0:1000]
        ex0_list = list(tap_data.euler_0_x)[0:1000]
        ey0_list = list(tap_data.euler_0_y)[0:1000]
        ex2_list = list(tap_data.euler_2_x)[0:1000]
        ey2_list = list(tap_data.euler_2_y)[0:1000]

        if file_name == 'both_optimal_orientation':

            ace_ace_210.add_training_data(ax0_list, ay0_list, az0_list, ex0_list, ey0_list, ax2_list, ay2_list, az2_list, ex2_list, ey2_list)
            ace_ace_012.add_training_data(ax2_list, ay2_list, az2_list, ex2_list, ey2_list, ax0_list, ay0_list, az0_list, ex0_list, ey0_list)

        if file_name == 'both_up_strap' or 'ACE' in file_name:
            ace_ace_012.add_training_data(ax0_list, ay0_list, az0_list, ex0_list, ey0_list, ax2_list, ay2_list, az2_list, ex2_list, ey2_list)
            ace_ace_210.add_training_data(ax2_list, ay2_list, az2_list, ex2_list, ey2_list, ax0_list, ay0_list, az0_list, ex0_list, ey0_list)

        if file_name == 'both_led_skin_side_strap' or 'BCE' in file_name:
            bce_bce_012.add_training_data(ax0_list, ay0_list, az0_list, ex0_list, ey0_list, ax2_list, ay2_list, az2_list, ex2_list, ey2_list)
            bce_bce_210.add_training_data(ax2_list, ay2_list, az2_list, ex2_list, ey2_list, ax0_list, ay0_list, az0_list, ex0_list, ey0_list)

        if file_name == 'both_inside_ankle_strap' or 'ACF' in file_name:
            acf_acf_012.add_training_data(ax0_list, ay0_list, az0_list, ex0_list, ey0_list, ax2_list, ay2_list, az2_list, ex2_list, ey2_list)
            acf_acf_210.add_training_data(ax2_list, ay2_list, az2_list, ex2_list, ey2_list, ax0_list, ay0_list, az0_list, ex0_list, ey0_list)

        if file_name == 'both_down_strap':
            ade_ade_012.add_training_data(ax0_list, ay0_list, az0_list, ex0_list, ey0_list, ax2_list, ay2_list, az2_list, ex2_list, ey2_list)
            ade_ade_210.add_training_data(ax2_list, ay2_list, az2_list, ex2_list, ey2_list, ax0_list, ay0_list, az0_list, ex0_list, ey0_list)

        if 'ADE' in file_name:
            ade_ade_210.add_training_data(ax0_list, ay0_list, az0_list, ex0_list, ey0_list, ax2_list, ay2_list, az2_list, ex2_list, ey2_list)
            ade_ade_012.add_training_data(ax2_list, ay2_list, az2_list, ex2_list, ey2_list, ax0_list, ay0_list, az0_list, ex0_list, ey0_list)

        if file_name == 'right_up_left_down':

            ade_ace_012.add_training_data(ax0_list, ay0_list, az0_list, ex0_list, ey0_list, ax2_list, ay2_list, az2_list, ex2_list, ey2_list)
            ade_ace_210.add_training_data(ax2_list, ay2_list, az2_list, ex2_list, ey2_list, ax0_list, ay0_list, az0_list, ex0_list, ey0_list)

        if 'ADF' in file_name:
            adf_adf_210.add_training_data(ax0_list, ay0_list, az0_list, ex0_list, ey0_list, ax2_list, ay2_list, az2_list, ex2_list, ey2_list)
            adf_adf_012.add_training_data(ax2_list, ay2_list, az2_list, ex2_list, ey2_list, ax0_list, ay0_list, az0_list, ex0_list, ey0_list)

        if 'BCF' in file_name:
            bcf_bcf_012.add_training_data(ax0_list, ay0_list, az0_list, ex0_list, ey0_list, ax2_list, ay2_list, az2_list, ex2_list, ey2_list)
            bcf_bcf_210.add_training_data(ax2_list, ay2_list, az2_list, ex2_list, ey2_list, ax0_list, ay0_list, az0_list, ex0_list, ey0_list)

        if 'BDF' in file_name:
            bdf_bdf_210.add_training_data(ax0_list, ay0_list, az0_list, ex0_list, ey0_list, ax2_list, ay2_list, az2_list, ex2_list, ey2_list)
            bdf_bdf_012.add_training_data(ax2_list, ay2_list, az2_list, ex2_list, ey2_list, ax0_list, ay0_list, az0_list, ex0_list, ey0_list)
        if 'BDE' in file_name:
            bde_bde_210.add_training_data(ax0_list, ay0_list, az0_list, ex0_list, ey0_list, ax2_list, ay2_list, az2_list, ex2_list, ey2_list)
            bde_bde_012.add_training_data(ax2_list, ay2_list, az2_list, ex2_list, ey2_list, ax0_list, ay0_list, az0_list, ex0_list, ey0_list)

    condition_list.append(bce_bce_012)
    condition_list.append(bce_bce_210)
    condition_list.append(bde_bde_012)
    condition_list.append(bde_bde_210)
    condition_list.append(ace_ace_012)
    condition_list.append(ace_ace_210)
    condition_list.append(ade_ade_012)
    condition_list.append(ade_ade_210)
    condition_list.append(acf_acf_012)
    condition_list.append(acf_acf_210)
    condition_list.append(adf_adf_012)
    condition_list.append(adf_adf_210)
    condition_list.append(bcf_bcf_012)
    condition_list.append(bcf_bcf_210)
    condition_list.append(bdf_bdf_012)
    condition_list.append(bdf_bdf_210)
    condition_list.append(ade_ace_012)
    condition_list.append(ade_ace_210)

    for cn in condition_list:
        cn.calc_raw_percentages()

    condition_list = [cn.json_serialise() for cn in condition_list]
    with open(f'{output_dir}/placement_model_v1_0.pkl', 'wb') as file_path:
        pickle.dump(condition_list, file_path)
