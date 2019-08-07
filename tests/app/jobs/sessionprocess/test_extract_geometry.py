from aws_xray_sdk.core import xray_recorder
xray_recorder.configure(sampling=False)
xray_recorder.begin_segment(name="test")
import numpy as np
import pandas as pd
import os

# Use theano backend for keras
os.environ['KERAS_BACKEND'] = 'theano'

from app.utils import quaternion_conversions as qc
from app.jobs.sessionprocess import extract_geometry as eg

path = '../../../files/'


def test_extract_geometry():
    '''
    Tests include:
        -outputs are properly formatted for use later in processing
        -output matches expectation when assumptions of placement are valid
            -good quality data
            -data whose values cross quadrants does not include Euler angle error

    '''
    test_file1 = 'a1bf8bad_short_orientation.csv'
    test_data1 = pd.read_csv(path + test_file1)
    test1_l_quats = np.hstack((np.hstack((np.hstack((
        test_data1.LqW.values.reshape(-1, 1),
        test_data1.LqX.values.reshape(-1, 1))),
                                          test_data1.LqY.values.reshape(-1, 1))),
                               test_data1.LqZ.values.reshape(-1, 1)))
    test1_h_quats = np.hstack((np.hstack((np.hstack((
        test_data1.HqW.values.reshape(-1, 1),
        test_data1.HqX.values.reshape(-1, 1))),
                                          test_data1.HqY.values.reshape(-1, 1))),
                               test_data1.HqZ.values.reshape(-1, 1)))
    test1_r_quats = np.hstack((np.hstack((np.hstack((
        test_data1.RqW.values.reshape(-1, 1),
        test_data1.RqX.values.reshape(-1, 1))),
                                          test_data1.RqY.values.reshape(-1, 1))),
                               test_data1.RqZ.values.reshape(-1, 1)))
    a_L1, f_L1, a_H1, f_H1, a_R1, f_R1 = eg.extract_geometry(test1_l_quats,
                                                             test1_h_quats,
                                                             test1_r_quats)
    test1_LeX = test_data1.LeX
    test1_HeX = test_data1.HeX
    test1_ReX = test_data1.ReX
    test1_LeY = test_data1.LeY
    test1_HeY = test_data1.HeY
    test1_ReY = test_data1.ReY
    test_file2 = 'e0deb549_short_raw.csv'
    test_data2 = pd.read_csv(path + test_file2)
    test2_l_quats = np.hstack((np.hstack((np.hstack((
        test_data2.LqW.values.reshape(-1, 1),
        test_data2.LqX.values.reshape(-1, 1))),
                                          test_data2.LqY.values.reshape(-1, 1))),
                               test_data2.LqZ.values.reshape(-1, 1)))
    test2_h_quats = np.hstack((np.hstack((np.hstack((
        test_data2.HqW.values.reshape(-1, 1),
        test_data2.HqX.values.reshape(-1, 1))),
                                          test_data2.HqY.values.reshape(-1, 1))),
                               test_data2.HqZ.values.reshape(-1, 1)))
    test2_r_quats = np.hstack((np.hstack((np.hstack((
        test_data2.RqW.values.reshape(-1, 1),
        test_data2.RqX.values.reshape(-1, 1))),
                                          test_data2.RqY.values.reshape(-1, 1))),
                               test_data2.RqZ.values.reshape(-1, 1)))
    a_L2, f_L2, a_H2, f_H2, a_R2, f_R2 = eg.extract_geometry(test2_l_quats,
                                                             test2_h_quats,
                                                             test2_r_quats)
    test2_l_euls = qc.quat_to_euler(test2_l_quats)
    test2_h_euls = qc.quat_to_euler(test2_h_quats)
    test2_r_euls = qc.quat_to_euler(test2_r_quats)
    test_file3 = '8cc60460_short_raw.csv'
    test_data3 = pd.read_csv(path + test_file3)
    test3_l_quats = np.hstack((np.hstack((np.hstack((
        test_data3.LqW.values.reshape(-1, 1),
        test_data3.LqX.values.reshape(-1, 1))),
                                          test_data3.LqY.values.reshape(-1, 1))),
                               test_data3.LqZ.values.reshape(-1, 1)))
    test3_h_quats = np.hstack((np.hstack((np.hstack((
        test_data3.HqW.values.reshape(-1, 1),
        test_data3.HqX.values.reshape(-1, 1))),
                                          test_data3.HqY.values.reshape(-1, 1))),
                               test_data3.HqZ.values.reshape(-1, 1)))
    test3_r_quats = np.hstack((np.hstack((np.hstack((
        test_data3.RqW.values.reshape(-1, 1),
        test_data3.RqX.values.reshape(-1, 1))),
                                          test_data3.RqY.values.reshape(-1, 1))),
                               test_data3.RqZ.values.reshape(-1, 1)))
    a_L3, f_L3, a_H3, f_H3, a_R3, f_R3 = eg.extract_geometry(test3_l_quats,
                                                             test3_h_quats,
                                                             test3_r_quats)
    test3_LeX = test_data3.LeX
    test3_HeX = test_data3.HeX
    test3_ReX = test_data3.ReX
    test3_LeY = test_data3.LeY
    test3_HeY = test_data3.HeY
    test3_ReY = test_data3.ReY
    a_L4, f_L4, a_H4, f_H4, a_R4, f_R4 = eg.extract_geometry(test3_r_quats,
                                                             test3_h_quats,
                                                             test3_l_quats)

    # outputs are properly formatted for use later in processing
    assert a_L1.shape == (len(test_data1),)
    assert f_L1.shape, (len(test_data1),)
    assert a_H1.shape, (len(test_data1),)
    assert f_H1.shape, (len(test_data1),)
    assert a_R1.shape, (len(test_data1),)
    assert f_R1.shape, (len(test_data1),)

    # output matches expectation when assumptions of placement are valid
    # good quality data
    assert np.allclose(a_L1, test1_LeX, rtol=1e-04, atol=1e-04)
    assert np.allclose(a_H1, test1_HeX, rtol=1e-04, atol=1e-04)
    assert np.allclose(a_R1, test1_ReX, rtol=1e-04, atol=1e-04)
    assert np.allclose(f_L1, test1_LeY, rtol=1e-04, atol=1e-04)
    assert np.allclose(f_H1, test1_HeY, rtol=1e-04, atol=1e-04)
    assert np.allclose(f_R1, test1_ReY, rtol=1e-04, atol=1e-04)

    # results from data whose values cross quadrants (in expected ways,
    # ie, pitch divots) do not include Euler angle error
    assert not np.allclose(a_L2, test2_l_euls[:, 0], rtol=1e-04, atol=1e-04)
    assert not np.allclose(a_H2, test2_h_euls[:, 0], rtol=1e-04, atol=1e-04)
    assert not np.allclose(a_R2, test2_r_euls[:, 0], rtol=1e-04, atol=1e-04)
    assert not np.allclose(f_L2, test2_l_euls[:, 1], rtol=1e-04, atol=1e-04)
    assert not np.allclose(f_H2, test2_h_euls[:, 1], rtol=1e-04, atol=1e-04)
    assert not np.allclose(f_R2, test2_r_euls[:, 1], rtol=1e-04, atol=1e-04)

    # improper placement assumptions result in some erroneous values
    # untransformed data
    # divots in left foot
    assert not (np.allclose(a_L3, test3_LeX, rtol=1e-04, atol=1e-04)
                     and np.allclose(f_L3, test3_LeY, rtol=1e-04, atol=1e-04))
    assert not (np.allclose(a_H3, test3_HeX, rtol=1e-04, atol=1e-04)
                     and np.allclose(f_H3, test3_HeY, rtol=1e-04, atol=1e-04))
    assert not (np.allclose(a_R3, test3_ReX, rtol=1e-04, atol=1e-04)
                     and np.allclose(f_R3, test3_ReY, rtol=1e-04, atol=1e-04))
    # divots in right foot
    assert not (np.allclose(a_L4, test3_ReX, rtol=1e-04, atol=1e-04)
                     and np.allclose(f_L4, test3_ReY, rtol=1e-04, atol=1e-04))
    assert not (np.allclose(a_H4, test3_HeX, rtol=1e-04, atol=1e-04)
                     and np.allclose(f_H4, test3_HeY, rtol=1e-04, atol=1e-04))
    assert not (np.allclose(a_R4, test3_LeX, rtol=1e-04, atol=1e-04)
                     and np.allclose(f_R4, test3_LeY, rtol=1e-04, atol=1e-04))