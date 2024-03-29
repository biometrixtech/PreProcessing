#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 25 13:45:44 2017

@author: dipeshgautam

"""

import numpy as np
import pandas as pd


incoming_from_accessory = [
    'epoch_time',
    'static_0',
    'acc_0_x', 'acc_0_y', 'acc_0_z', 'quat_0_w', 'quat_0_x', 'quat_0_y', 'quat_0_z',
    'static_1',
    'acc_1_x', 'acc_1_y', 'acc_1_z', 'quat_1_w', 'quat_1_x', 'quat_1_y', 'quat_1_z',
    'static_2',
    'acc_2_x', 'acc_2_y', 'acc_2_z', 'quat_2_w', 'quat_2_x', 'quat_2_y', 'quat_2_z',
]


# timestamp calculation from first 5 bytes
def _decode_timestamp(timestamp_data, nrows):
    timestamp = 0
    for i in range(5):
        temp = timestamp_data[:, i]
        shift = [8 * (4 - i)] * nrows  # shift ith value by 4-i bytes
        shifted = temp << shift

        timestamp = timestamp + shifted
    timestamp = timestamp + 1530000000000  # add fathom-origin (2017-06-19)
    return timestamp


# magn magnitude and corrupt enum calc
def _get_static_flag(flag, nrow):
    flag_temp = flag
    static = (flag_temp & 8 ) / 8
    return static.reshape(-1, 1)


def _get_corrupt_flag(flag, nrow):
    shift = [3] * nrow
    flag_temp = flag >> shift  # shift to right by 3
    corrupt = (flag_temp & 10)
    return corrupt.reshape(-1, 1)

# AXL temporary value for the axl.5 bytes are used to
# represent the 3 axes components of the accelerometer
def _decode_accel(axl_data, nrows, corrupt_data):
    corrupt = _get_corrupt_flag(corrupt_data, nrows) / 2
    axl_temp = 0
    for i in range(5):
        temp = axl_data[:, i]
        shift = [8 * (4 - i)] * nrows
        shifted = temp << shift
        axl_temp = axl_temp + shifted
    # Each AXL axis value is truncated from 16 bits to 13 bits. Therefore, the AXL temp
    # value must be shifted down by 26, 13 and 0 bits respectively for the 1st,
    # 2nd and 3rd axes. Then each axes value must be shifted up by 3 bits in
    # order to be interpreted as the original 16 bits signed integer value.
    axl = np.zeros((nrows, 3))
    for i in range(3):
        shift = [13 * (2 - i)] * nrows
        temp_value = axl_temp >> shift  # bitsra(axl_temp,(3-i)*13);
        temp_value = temp_value & int('1fff', 16)  # bitand(tempValue,hex2dec('1fff'));
        temp_value = temp_value << 3  # bitshift(tempValue,3);
        axl[:, i] = np.int16(temp_value)
    for i in range(len(corrupt)):
        if corrupt[i] == 1:
            axl[i, :] *= 4
    return axl


def _decode_quat(quat_data, nrows):
    # quaternion temporary value for the quaternion. 5 bytes are used to
    # represent the 3 imaginary components of the quaternion
    q_temp = 0
    for i in range(5):
        temp = quat_data[:, i]
        # Shift up temp value by 4,3,2,1 and 0 bytes for the 1st,2nd,3rd,4th and 5th byte.
        # Sum it up to the AXL temp value.
        shift = [8 * (4 - i)] * nrows
        shifted = temp << shift
        q_temp = q_temp + shifted

    # Each imaginary component converted from floating point to int16 by multiplying by 32767.
    # Then the 16 bits value is truncated to 13 bits. Therefore, the qTemp
    # value must be shifted down by 26, 13 and 0 bits respectively for the 1st,
    # 2nd and 3rd imaginary component. Then each component must be shifted up by 3 bits in
    # order to be interpreted as the original 16 bits signed integer value.
    quats = np.zeros((nrows, 4))
    for i in range(3):
        shift = [13 * (2 - i)] * nrows
        temp_value = q_temp >> shift  # bitsra(qTemp,(3-i)*13);
        temp_value = temp_value & int('1fff', 16)  # bitand(tempValue,hex2dec('1fff'));
        temp_value = temp_value << 3  # bitshift(tempValue,3);
        quats[:, i] = np.int16(temp_value)  # typecast(uint16(tempValue),'int16');

    # Cast the imaginary components to double (or float)
#    q = np.array(q).astype(float)
    # Go back from the -32767 / 32767 range to the -1 / +1 range for each
    # component by dividing by 32767
    quats = quats/32767.

    # Compute the real component as the sum of the square of the imaginary
    # components subtracted to 1. Avoid numerical issue by checking out the
    # magnitude to be 1
#    quats[:, 0] = .8
    norm = np.linalg.norm(quats[:, :3], axis=1)
    bad_norm = np.where(norm > 1)[0]
    quats[:, 3] = np.sqrt(1 - np.sum(quats[:, :3] ** 2, axis=1))
    if bad_norm.shape[0] > 0:
        quats[bad_norm, 3] = 0
        quats[bad_norm, :] = quats[bad_norm, :]/norm[bad_norm].reshape(-1, 1)
    # sort to get wxyz
    sorted_order = np.argsort([1, 2, 3, 0])
    quats = quats[:, sorted_order]
    return quats


def read_file(filename):
    line_size = 40
    data = np.fromfile(filename, dtype=np.uint8).reshape(-1, line_size)
    nrows = data.shape[0]

    timestamp = _decode_timestamp(data[:, 0:5], nrows).reshape(-1, 1)
    timestamp_error = None
    # corrupt = data[:, 6].reshape(-1, 1)

    output = np.concatenate((
        timestamp,
        # corrupt,
        _get_static_flag(data[:, 7], nrows),
        _decode_accel(data[:, 8:13], nrows, data[:, 7]),  # / 1000 * 9.80665,
        _decode_quat(data[:, 13:18], nrows),
        _get_static_flag(data[:, 18], nrows),
        _decode_accel(data[:, 19:24], nrows, data[:, 18]),  # / 1000 * 9.80665,
        _decode_quat(data[:, 24:29], nrows),
        _get_static_flag(data[:, 29], nrows),
        _decode_accel(data[:, 30:35], nrows, data[:, 29]),  # / 1000 * 9.80665,
        _decode_quat(data[:, 35:40], nrows),
    ), axis=1)

    output_pd = pd.DataFrame(output, columns=incoming_from_accessory)
    output_pd['epoch_time'] = output_pd['epoch_time'].astype(float)
    # output_pd['corrupt'] = output_pd['corrupt']. astype(int)
    # output_pd['magn_0'] = output_pd['magn_0']. astype(int)
    output_pd['static_0'] = output_pd['static_0'].astype(int)
    # output_pd['magn_1'] = output_pd['magn_1']. astype(int)
    output_pd['static_1'] = output_pd['static_1']. astype(int)
    # output_pd['magn_2'] = output_pd['magn_2']. astype(int)
    output_pd['static_2'] = output_pd['static_2'].astype(int)
    ms_elapsed = np.ediff1d(timestamp, to_begin=10)
    neg_timestamp = np.where(ms_elapsed < 0)[0]
    big_jumps = np.where(abs(ms_elapsed) > 5 * 60 * 1000)[0]
    if len(neg_timestamp) > 0:
        for i in neg_timestamp:
            if i != len(data) - 1:
                timestamp_error = "SMALL_NEGATIVE_JUMP"
                output_pd.loc[i, 'epoch_time'] = int((output_pd.loc[i - 1, 'epoch_time'] + output_pd.loc[i + 1, 'epoch_time']) / 2)
    if len(big_jumps) > 0:
        output_pd = output_pd.loc[:big_jumps[0] - 1, :]
        timestamp_error = "LARGE_JUMP_DATA_TRUNCATED"
    # output_pd = output_pd.iloc[pos_timestamp]
    # output_pd.reset_index(drop=True, inplace=True)
    
    return output_pd, timestamp_error

