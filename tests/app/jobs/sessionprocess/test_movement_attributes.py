from aws_xray_sdk.core import xray_recorder
xray_recorder.configure(sampling=False)
xray_recorder.begin_segment(name="test")
import numpy as np
import pandas as pd
import os

# Use theano backend for keras
os.environ['KERAS_BACKEND'] = 'theano'

from app.jobs.sessionprocess import movement_attributes as ma


def test_sort_phases():
    '''
    Tests include:
        -outputs are correct format
        -outputs are expected given known inputs
            - single leg balance, take offs, and impacts are appropriately
            detected, with some exceptions if double leg
            - when single leg activities overlap or occur within a radius
            of 3 samples of each other (within same category), double leg
            activity is registered
            - feet eliminated is recognized
            - not standing data is recognized
    '''
    hz = 4
    lf_ph = np.array([0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 2, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1,
                      2, 3, 1, 1, 2, 0, 0, 0, 0, 1, 0, 0, 0, 3, 0, 0, 1, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 3]).reshape(-1,
                                                                                                                   1)
    rf_ph = np.array([1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 2,
                      2, 1, 3, 1, 1, 0, 0, 0, 0, 2, 0, 0, 0, 1, 0, 0, 3, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 1]).reshape(-1,
                                                                                                                   1)
    not_standing = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                             0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                             0, 0, 0, 0, 0]).reshape(-1, 1)
    hacc = np.ones(not_standing.shape)
    hacc[6] = 3
    LDB, RDB, DDB, LSB, RSB, DSB, LI, RI, DI, LT, RT, DT, FE = ma.sort_phases(lf_ph, rf_ph, not_standing, hz, hacc)

    fe_exp = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0,
                       0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0]).reshape(-1, 1)
    ldb_exp = np.array([1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0]).reshape(-1, 1)
    rdb_exp = np.array([0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0]).reshape(-1, 1)
    ddb_exp = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1,
                        0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1,
                        1, 1, 1, 0]).reshape(-1, 1)
    lsb_exp = np.array([0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0]).reshape(-1, 1)
    rsb_exp = np.array([0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0]).reshape(-1, 1)
    dsb_exp = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1,
                        0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1,
                        1, 1, 1, 1]).reshape(-1, 1)
    li_exp = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0]).reshape(-1, 1)
    ri_exp = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
                       1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0]).reshape(-1, 1)
    di_exp = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
                       1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0]).reshape(-1, 1)
    lt_exp = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0,
                       0, 1]).reshape(-1, 1)
    rt_exp = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0,
                       0, 0]).reshape(-1, 1)
    dt_exp = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
                          , 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0,
                       0, 0, 0]).reshape(-1, 1)

    # outputs are correct format
    assert LDB.shape == lf_ph.shape
    assert RDB.shape == lf_ph.shape
    assert DDB.shape == lf_ph.shape
    assert LSB.shape == lf_ph.shape
    assert RSB.shape == lf_ph.shape
    assert DSB.shape == lf_ph.shape
    assert LI.shape == lf_ph.shape
    assert RI.shape == lf_ph.shape
    assert DI.shape == lf_ph.shape
    assert LT.shape == lf_ph.shape
    assert RT.shape == lf_ph.shape
    assert DT.shape == lf_ph.shape
    assert FE.shape == lf_ph.shape

    # output has expected results given known inputs
    assert np.allclose(LDB, ldb_exp)
    assert np.allclose(RDB, rdb_exp)
    assert np.allclose(DDB, ddb_exp)
    assert np.allclose(LSB, lsb_exp)
    assert np.allclose(RSB, rsb_exp)
    assert np.allclose(DSB, dsb_exp)
    assert np.allclose(LI, li_exp)
    assert np.allclose(RI, ri_exp)
    assert np.allclose(DI, di_exp)
    assert np.allclose(LT, lt_exp)
    assert np.allclose(RT, rt_exp)
    assert np.allclose(DT, dt_exp)
    assert np.allclose(FE, fe_exp)


def test_num_runs():
    '''
    Tests include:
        -output appropriately indexes runs of consecutive repetitions of
        the chosen value
    '''
    test = np.array([1, 1, 1, 2, 3, 2, 2, 2, 1, 0, 5, 3, 3, 5, 5, 0])
    runs_0 = ma._num_runs(test, 0)
    runs_1 = ma._num_runs(test, 1)
    runs_2 = ma._num_runs(test, 2)
    runs_3 = ma._num_runs(test, 3)
    runs_5 = ma._num_runs(test, 5)

    # output matches expectation of known array
    assert np.allclose(runs_0, np.array([[9, 10], [15, 16]]))
    assert np.allclose(runs_1, np.array([[0, 3], [8, 9]]))
    assert np.allclose(runs_2, np.array([[3, 4], [5, 8]]))
    assert np.allclose(runs_3, np.array([[4, 5], [11, 13]]))
    assert np.allclose(runs_5, np.array([[10, 11], [13, 15]]))


def test_total_accel():
    '''
    Tests include:
        -output matches expectation of known input vectors
    '''
    test1 = np.array([[0, 0, 1], [0, 1, 0], [1, 0, 0]])
    test1mag = ma.total_accel(test1)
    test1exp = np.array([[1], [1], [1]])
    test0 = np.array([[0, 0, 0], [0, 0, 0], [0, 0, 0]])
    test0mag = ma.total_accel(test0)
    test0exp = np.array([[0], [0], [0]])
    test1_v2 = np.array([[1 / np.sqrt(2), 0, 1 / np.sqrt(2)],
                         [1 / np.sqrt(2), 1 / np.sqrt(2), 0],
                         [0, 1 / np.sqrt(2), 1 / np.sqrt(2)]])
    test1mag_v2 = ma.total_accel(test1_v2)
    test1_v3 = np.array([[1 / np.sqrt(3), 1 / np.sqrt(3), 1 / np.sqrt(3)],
                         [1 / np.sqrt(3), 1 / np.sqrt(3), 1 / np.sqrt(3)],
                         [1 / np.sqrt(3), 1 / np.sqrt(3), 1 / np.sqrt(3)]])
    test1mag_v3 = ma.total_accel(test1_v3)

    # output matches expectation of known input vectors
    assert np.allclose(test1mag, test1exp)
    assert np.allclose(test0mag, test0exp)
    assert np.allclose(test1mag_v2, test1exp)
    assert np.allclose(test1mag_v3, test1exp)


def test_enumerate_stance():
    '''
    Tests include:
        - output is properly formatted
        - results are expected given known input
    '''
    hz = 4
    lf_ph = np.array([0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 2, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1,
                      2, 3, 1, 1, 2, 0, 0, 0, 0, 1, 0, 0, 0, 3, 0, 0, 1, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 3]).reshape(-1,
                                                                                                                   1)
    rf_ph = np.array([1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 2,
                      2, 1, 3, 1, 1, 0, 0, 0, 0, 2, 0, 0, 0, 1, 0, 0, 3, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 1]).reshape(-1,
                                                                                                                   1)
    not_standing = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                             0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                             0, 0, 0, 0, 0]).reshape(-1, 1)
    hacc = np.ones(not_standing.shape)
    hacc[6] = 3
    LDB, RDB, DDB, LSB, RSB, DSB, LI, RI, DI, LT, RT, DT, FE = ma.sort_phases(lf_ph, rf_ph, not_standing, hz, hacc)
    stance = ma.enumerate_stance(LDB, RDB, DDB, LSB, RSB, DSB, LI, RI, DI, LT, RT, DT, FE)
    stance_exp = np.array([2, 2, 2, 2, 4, 4, 2, 4, 4, 4, 3, 3, 2, 1, 5, 5, 5, 5, 5, 5, 1, 1, 5, 5,
                           5, 3, 3, 2, 2, 1, 2, 5, 0, 0, 0, 2, 5, 5, 5, 2, 3, 3, 2, 5, 5, 5, 5, 3,
                           5, 5, 5, 5, 5, 2]).reshape(-1, 1)
    # output is properly formatted
    assert stance.shape == lf_ph.shape

    # output is expected given known input
    assert np.allclose(stance, stance_exp)
