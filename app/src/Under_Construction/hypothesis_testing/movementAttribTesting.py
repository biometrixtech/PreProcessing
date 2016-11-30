# -*- coding: utf-8 -*-
"""
Created on Wed Nov 23 12:36:37 2016

@author: court
"""

import numpy as np
from hypothesis import given, example, assume
import hypothesis.strategies as st
from hypothesis.extra.numpy import arrays
import random as rand

import movementAttrib_for_testing as ma

"""
Property and unit testing for movementAttrib script. Functions used in block,
training, and practice processes.

Some edits made to movementAttrib windows in movementAttrib_for_testing in
order to allow small data sets to be run.
"""


@given(arrays(np.int16, (rand.randint(1,20),3), elements=st.floats(
              min_value=-2000, max_value=2000)))
def test_total_accel(hip_acc_aif):
    """
    Property and unit testing for total acceleration calculation.

    Arg:
        hip_acc_aif: nx3 array representing acc in 3 axes of hip sensor.

    Tests included:
        -- output is np.ndarray, with elements of floats
        -- length of output is same as that of input acceleration (n)
        -- unit tests
            - 1 m/s2 in each positive direction has magnitude of sqrt(3)
            - unit vectors have calculated magnitude of 1
            - zero acceleration has zero magnitude
    """

    accel_mag = ma.total_accel(hip_acc_aif)
    assert type(accel_mag) == np.ndarray
    assert len(accel_mag) == len(hip_acc_aif)
    assert type(accel_mag[0][0]) == np.float32
    all_ones_test = np.array([[1,1,1],[1,1,1],[1,1,1]])
    assert np.array_equal(ma.total_accel(all_ones_test),
                          np.array([[np.sqrt(3)], [np.sqrt(3)], [np.sqrt(3)]]))
    ones_test = np.array([[0,0,1],[0,0,1],[0,0,1]])
    assert np.array_equal(ma.total_accel(ones_test), np.array([[1],[1],[1]]))
    zeros_test = np.array([[0,0,0],[0,0,0],[0,0,0]])
    assert np.array_equal(ma.total_accel(zeros_test), np.array([[0],[0],[0]]))


@given(st.integers(1,10))
def test_plane_analysis(length):
    """
    Property testing for plane analysis.

    Arg:
        length: length of test data to be created, int

    Data generated for tests:
        hip_acc: lengthx3 array representing acc in 3 axes of hip sensor
        hip_eul: lengthx3 array representing rotation in 3 axes of hip sensor
        ms_elapsed: lengthx3 array representing dummy time elapsed in session

    Calculation outputs:
        lat: instantaneous lateral components of acceleration
        vert: instantaneous vertical components of acceleration
        horz: instantaneous horizontal components of acceleration
        rot: instantaneous rotational components of acceleration
        lat_binary: instantaneous binaries of whether lateral acc is
            significant
        vert_binary: instantaneous binaries of whether vertical acc is
            significant
        horz_binary: instantaneous binaries of whether horizontal acc is
            significant
        rot_binary: instantaneous binaries of whether rotational acc is
            significant
        stationary_binary: instantaneous binaries of whether body is stationary
        accel_mag: instantaneous total magnitudes of body's lateral
            acceleration

    Tests included:
        - output shapes are all lengthx1 arrays
        - lat, vert, horz, rot, and accel_mag elements are all floats
        - lat_binary, vert_binary, horz_binary, rot_binary, stationary_binary
            elements are all 0 or 1
        - if body stationary, then not in any plane of movement

    """

    # create variables
    elapsed = [4,6,8]
    ms_elapsed = np.zeros(length).reshape(length,1)
    for i in range(1,length):
        ms_elapsed[i] = ms_elapsed[i-1] + st.sampled_from(elapsed).example()
    hip_acc = arrays(np.float, (length, 3), elements=st.floats(
        min_value=-40, max_value=40)).example()
    hip_eul = arrays(np.float, (length, 3), elements=st.floats(
        min_value=-np.pi, max_value=np.pi)).example()
    # perform calculations and analyze
    lat, vert, horz, rot, lat_binary, vert_binary, horz_binary, rot_binary, \
    stationary_binary, accel_mag = ma.plane_analysis(hip_acc, hip_eul,
                                                     ms_elapsed)
    assert type(lat) == np.ndarray
    assert type(vert) == np.ndarray
    assert type(horz) == np.ndarray
    assert type(rot) == np.ndarray
    assert type(lat_binary) == np.ndarray
    assert type(vert_binary) == np.ndarray
    assert type(horz_binary) == np.ndarray
    assert type(rot_binary) == np.ndarray
    assert type(stationary_binary) == np.ndarray
    assert type(accel_mag) == np.ndarray
    for i in range(length):
        assert type(lat[i][0]) == np.float64
        assert type(vert[i][0]) == np.float64
        assert type(horz[i][0]) == np.float64
        assert type(rot[i][0]) == np.float64
        assert np.in1d(lat_binary[i], [0, 1])
        assert np.in1d(vert_binary[i], [0, 1])
        assert np.in1d(horz_binary[i], [0, 1])
        assert np.in1d(rot_binary[i], [0, 1])
        assert np.in1d(stationary_binary[i], [0, 1])
        assert type(accel_mag[i][0]) == np.float64
        if stationary_binary[i] == 1:
            assert lat_binary[i] + vert_binary[i] + rot_binary[i] \
                + horz_binary[i] == 0
    assert lat.shape == ms_elapsed.shape
    assert vert.shape == ms_elapsed.shape
    assert horz.shape == ms_elapsed.shape
    assert rot.shape == ms_elapsed.shape
    assert lat_binary.shape == ms_elapsed.shape
    assert vert_binary.shape == ms_elapsed.shape
    assert horz_binary.shape == ms_elapsed.shape
    assert rot_binary.shape == ms_elapsed.shape
    assert stationary_binary.shape == ms_elapsed.shape
    assert accel_mag.shape == ms_elapsed.shape


@given(st.integers(15,30))
def test_standing_or_not(length):
    """
    Property testing for standing_or_not.

    Args:
        length: length of test data to be created, int

    Data generated for tests:
        hip_eul: lengthx3 array representing rotation in 3 axes of hip sensor
        ms_elapsed: lengthx3 array representing dummy time elapsed in session

    Calculation outputs:
        standing: instantaneous binaries representing whether body has been
            standing for significant period of time
        not_standing: instantaneous binaries representing whether body has not
            been standing for significant period of time

    Tests included:
        - output shapes are lengthx1 arrays
        - output element values are all 0 or 1
        - outputs are exclusive (one is always 1, the other always 0)

    Warning: MS_WIN_SIZE too large to set relevant examples. Tests will show
        not_standing = array([1, 1, ..., 1, 1]).reshape(-1,1) almost
        exclusively.
    
    """
    # create ms_elapsed
    elapsed = [4,6,8]
    ms_elapsed = np.zeros(length).reshape(length,1)
    hip_eul = np.zeros((length,3))
    for i in range(1,length):
        ms_elapsed[i] = ms_elapsed[i-1] + st.sampled_from(elapsed).example()
        hip_eul[i] = arrays(np.float, (1,3), elements=st.floats(
            min_value=-np.pi, max_value=np.pi)).example()
    # perform calculations and analyze
    standing, not_standing = ma.standing_or_not(hip_eul, ms_elapsed)
    assert standing.shape == ms_elapsed.shape
    assert not_standing.shape == ms_elapsed.shape
    assert type(standing) == np.ndarray
    assert type(not_standing) == np.ndarray
    for i in range(length):
        assert standing[i] + not_standing[i] == 1
        assert np.in1d(standing[i], [0, 1])
        assert np.in1d(not_standing[i], [0, 1])


@given(st.integers(15,30))
def test_double_or_single_leg(length):
    """
    Property testing for double_or_single_leg.

    Args:
        length: length of test data to be created, int

    Data generated for tests:
        lf_phase: lengthx1 array representing dummy left foot phases
        rf_phase: lengthx1 array representing dummy right foot phases
        standing: lengthx1 binary array representing if body is standing
        epoch_time: lengthx1 array representing dummy epoch times

    Calculation outputs:
        double_leg: instantaneous binaries representing whether body has been
            standing on two legs for significant period of time
        single_leg: instantaneous binaries representing whether body is
            standing on one leg
        feet_eliminated: instantaneous binaries representing whether body has
            no feet in contact with the ground

    Tests included:
        - output shapes are lengthx1 arrays
        - output element values are all 0 or 1
        - outputs are exclusive (one is always 1, the others always 0)

    Warning: MS_WIN_SIZE too large to set relevant examples. Tests will show
        double_leg = array([0, 0, ..., 0, 0]).reshape(-1,1) almost
        exclusively.
    
    """

    # create variables
    left_phases = [0, 1, 3, 4]
    right_phases = [0, 2, 3, 5]
    stand = [0,1]
    elapsed = [4,6,8]
    lf_phase = np.zeros(length).reshape(length,1)
    rf_phase = np.zeros(length).reshape(length,1)
    standing = np.zeros(length).reshape(length,1)
    epoch_time = np.zeros(length).reshape(length,1)
    for i in range(1,length):
        lf_phase[i] = st.sampled_from(left_phases).example()
        if lf_phase[i] == 3:
            rf_phase[i] = 3
        else:
            rf_phase[i] = st.sampled_from(right_phases).example()
        standing[i] = st.sampled_from(stand).example()
        epoch_time[i] = epoch_time[i-1] + st.sampled_from(elapsed).example()
    # perform calculations and analyze
    double_leg, single_leg, feet_eliminated = ma.double_or_single_leg(lf_phase,
                                                            rf_phase, standing,
                                                            epoch_time)
    assert double_leg.shape == epoch_time.shape
    assert single_leg.shape == epoch_time.shape
    assert feet_eliminated.shape == epoch_time.shape
    assert type(double_leg) == np.ndarray
    assert type(single_leg) == np.ndarray
    assert type(feet_eliminated) == np.ndarray
    for i in range(length):
        assert double_leg[i] + single_leg[i] + feet_eliminated[i] == 1
        assert np.in1d(double_leg[i], [0, 1])
        assert np.in1d(single_leg[i], [0, 1])
        assert np.in1d(feet_eliminated[i], [0, 1])


@given(st.integers(15,30))
def test_stationary_or_dynamic(length):
    """
    Property testing for stationary_or_dynamic.

    Args:
        length: length of test data to be created, int

    Data generated for tests:
        lf_phase: lengthx1 array representing dummy left foot phases
        rf_phase: lengthx1 array representing dummy right foot phases
        single_leg: lengthx1 binary array representing if standing on single
            leg
        epoch_time: lengthx1 array representing dummy epoch times

    Calculation outputs:
        stationary: instantaneous binaries representing whether body has been
            standing still for significant period of time
        dynamic: instantaneous binaries representing whether body has not been
            standing still for significant period of time

    Tests included:
        - output shapes are lengthx1 arrays
        - output element values are all 0 or 1
        - outputs are exclusive (one is always 1, the others always 0)

    Warning: MS_WIN_SIZE too large to set relevant examples. Tests will show
        stationary = array([0, 0, ..., 0, 0]).reshape(-1,1) almost exclusively.
    
    """

    left_phases = [0, 1, 3, 4]
    right_phases = [0, 2, 3, 5]
    stat = [0,1]
    elapsed = [4,6,8]
    lf_phase = np.zeros(length).reshape(length,1)
    rf_phase = np.zeros(length).reshape(length,1)
    single_leg = np.zeros(length).reshape(length,1)
    epoch_time = np.zeros(length).reshape(length,1)
    for i in range(1,length):
        lf_phase[i] = st.sampled_from(left_phases).example()
        if lf_phase[i] == 3:
            rf_phase[i] = 3
        else:
            rf_phase[i] = st.sampled_from(right_phases).example()
        single_leg[i] = st.sampled_from(stat).example()
        epoch_time[i] = epoch_time[i-1] + st.sampled_from(elapsed).example()
    stationary, dynamic = ma.stationary_or_dynamic(lf_phase, rf_phase,
                                                   single_leg, epoch_time)
    assert stationary.shape == epoch_time.shape
    assert dynamic.shape == epoch_time.shape
    assert type(stationary) == np.ndarray
    assert type(dynamic) == np.ndarray
    for i in range(length):
        assert np.in1d(stationary[i] + dynamic[i], [0, 1])
        assert np.in1d(stationary[i], [0, 1])
        assert np.in1d(dynamic[i], [0, 1])


if __name__ == '__main__' :

    test_total_accel()
    print 'total_accel success'
    test_plane_analysis()
    print 'plane_analysis success'
    test_standing_or_not()
    print 'standing_or_not success'
    test_double_or_single_leg()
    print 'double_or_single_leg success'
    test_stationary_or_dynamic()
    print 'stationary_or_dynamic success'