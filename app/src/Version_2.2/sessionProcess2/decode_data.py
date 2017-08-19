#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 25 13:45:44 2017

@author: dipeshgautam

"""

import numpy as np
import pandas as pd
from columnNames import incoming_from_accessory


# timestamp calculation from first 5 bytes
def _decode_timestamp(timestamp_data, nrows):
    timestamp = 0
    for i in range(5):
        temp = timestamp_data[:, i]
        shift = [8 * (4 - i)] * nrows # shift ith value by 4-i bytes
        shifted = temp << shift

        timestamp = timestamp + shifted
    timestamp = timestamp + 1497866400000 # add fathom-origin (2017-06-19)
    return timestamp

# magn magnitude and corrupt enum calc
def _decode_magn(magn_data, nrow):
    magn_temp = magn_data
    shift = [3] * nrow
    magn_magnitude = magn_temp >> shift # shift to right by 3
    magn_magnitude = magn_magnitude * 32 # multiply by 32 to calculate magnitude in mGauss

    corrupt_enum = magn_temp & 7
    return np.concatenate((magn_magnitude.reshape(-1, 1),
                           corrupt_enum.reshape(-1, 1)), axis=1)

#AXL temporary value for the axl.5 bytes are used to
#represent the 3 axes components of the accelerometer
def _decode_accel(axl_data, nrows):
    axl_temp = 0
    for i in range(5):
        temp = axl_data[:, i]
        shift = [8 * (4 - i)] * nrows
        shifted = temp << shift
        axl_temp = axl_temp + shifted

    #Each AXL axis value is truncated from 16 bits to 13 bits. Therefore, the AXL temp
    #value must be shifted down by 26, 13 and 0 bits respectively for the 1st,
    #2nd and 3rd axes. Then each axes value must be shifted up by 3 bits in
    #order to be interpreted as the original 16 bits signed integer value.
    axl = np.zeros((nrows, 3))
    for i in range(3):
        shift = [13 * (2 - i)] * nrows
        temp_value = axl_temp >> shift #bitsra(axl_temp,(3-i)*13);
        temp_value = temp_value & int('1fff', 16) #bitand(tempValue,hex2dec('1fff'));
        temp_value = temp_value << 3 #bitshift(tempValue,3);
        axl[:, i] = np.int16(temp_value)
    return axl

def _decode_quat(quat_data, nrows):
    #%quaternion temporary value for the quaternion. 5 bytes are used to
    #%represent the 3 imaginary components of the quaternion
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
        temp_value = q_temp >> shift #bitsra(qTemp,(3-i)*13);
        temp_value = temp_value & int('1fff', 16) # bitand(tempValue,hex2dec('1fff'));
        temp_value = temp_value << 3 # bitshift(tempValue,3);
        quats[:, i] = np.int16(temp_value) # typecast(uint16(tempValue),'int16');

    #%Cast the imaginary components to double (or float)
#    q = np.array(q).astype(float)
    #%Go back from the -32767 / 32767 range to the -1 / +1 range for each
    #%component by dividing by 32767
    quats = quats/32767.

    #%Compute the real component as the sum of the square of the imaginary
    #%components subtracted to 1. Avoid numerical issue by checking out the
    #%magnitude to be 1
#    quats[:, 0] = .8
    norm = np.linalg.norm(quats[:, :3], axis=1)
    bad_norm = np.where(norm > 1)[0]
    quats[:, 3] = np.sqrt(1 - np.sum(quats[:, :3] ** 2, axis=1))
    if bad_norm.shape[0] > 0:
#        for i in bad_norm:
        quats[bad_norm, 3] = 0
        quats[bad_norm, :] = quats[bad_norm, :]/norm[bad_norm].reshape(-1, 1)
    return quats

def read_file(filename):
    line_size = 40
    data = np.fromfile(filename, dtype=np.uint8).reshape(-1, line_size)
    nrows = data.shape[0]

    timestamp = _decode_timestamp(data[:, 0:5], nrows).reshape(-1, 1)
    corrupt = data[:, 6].reshape(-1, 1)

    magn_l = _decode_magn(data[:, 7], nrows)
    accel_l = _decode_accel(data[:, 8:13], nrows) / 1000
    quat_l = _decode_quat(data[:, 13:18], nrows)

    magn_h = _decode_magn(data[:, 18], nrows)
    accel_h = _decode_accel(data[:, 19:24], nrows) / 1000
    quat_h = _decode_quat(data[:, 24:29], nrows)

    magn_r = _decode_magn(data[:, 29], nrows)
    accel_r = _decode_accel(data[:, 30:35], nrows) / 1000
    quat_r = _decode_quat(data[:, 35:40], nrows)

    output = np.concatenate((timestamp, corrupt,
                             magn_l,
                             accel_l,
                             quat_l,
                             magn_h,
                             accel_h,
                             quat_h,
                             magn_r,
                             accel_r,
                             quat_r), axis=1)

    # incoming_from_accessory = ['epoch_time', 'corrupt',
    #                            'magn_lf', 'corrupt_lf',
    #                            'LaX', 'LaY', 'LaZ', 'LqX', 'LqY', 'LqZ', 'LqW',
    #                            'magn_h', 'corrupt_h',
    #                            'HaX', 'HaY', 'HaZ', 'HqX', 'HqY', 'HqZ', 'HqW',
    #                            'magn_rf', 'corrupt_lf',
    #                            'RaX', 'RaY', 'RaZ', 'RqX', 'RqY', 'RqZ', 'RqW']
    output_pd = pd.DataFrame(output, columns=incoming_from_accessory)
    output_pd = pd.DataFrame(output, columns=incoming_from_accessory)
    output_pd['epoch_time'] = output_pd['epoch_time']. astype(long)
    output_pd['corrupt'] = output_pd['corrupt']. astype(int)
    output_pd['magn_lf'] = output_pd['magn_lf']. astype(int)
    output_pd['corrupt_lf'] = output_pd['corrupt_lf']. astype(int)
    output_pd['magn_h'] = output_pd['magn_h']. astype(int)
    output_pd['corrupt_h'] = output_pd['corrupt_h']. astype(int)
    output_pd['magn_rf'] = output_pd['magn_rf']. astype(int)
    output_pd['corrupt_rf'] = output_pd['corrupt_rf']. astype(int)
    ms_elapsed = np.ediff1d(timestamp, to_begin=10)
    pos_timestamp = ms_elapsed>=0
    output_pd = output_pd.iloc[pos_timestamp]
    
    return output_pd


if __name__ == '__main__':
#    import timeit
    data = read_file('test5')
#    print(timeit.timeit('read_file("test5")', setup='from __main__ import read_file', number=1))
