from aws_xray_sdk.core import xray_recorder
xray_recorder.configure(sampling=False)
xray_recorder.begin_segment(name="test")
import numpy as np
import pandas as pd
import os

# Use theano backend for keras
os.environ['KERAS_BACKEND'] = 'theano'

from app.jobs.sessionprocess import run_relative_cme as rcme


path = '../../../files/'

'''
Tests included:
    --test_run_relative_CMEs
        -properly executes full data file. subfunction operations are
            tested individually below
        -relative CME columns added
    --test__drift_agnostic_CMES
        -output is appropriately formatted
        -output matches expectation given known input
           -values align
           -values filled where relevant
           -values = nan where irrelevant
    --test__driftless_CMS
        -output is appropriately formatted
        -output matches expectation given known input
           -values align
           -values filled where relevant
           -values = nan where irrelevant
    --test__norm_range_of_motion
        -ouput is appropriately formatted
        -output matches expectation given known input
    --test__norm_motion_covered
        -ouput is appropriately formatted
        -output matches expectation given known input
    --test__rough_contact_duration
        -ouput is appropriately formatted
        -output matches expectation knowing known input
            - contact and non contact stretches, all possible stances
            represented
    --test__detect_long_dynamic
        -output is appropriately formatted
        -output matches expectation given known input
    
    --test__remove_filtered_ends
        -output is formatted appropriately
        -output matches expectation when given known inputs
            -trims rows when dynamic activity ends near end
            -splits rows when dynamic activity ends in middle
            -retains rows when no dynamic activity change
            -deletes rows when too short to trim or split


'''


def test_run_relative_CMEs():
    '''
    Tests include:
        -properly executes full data file. subfunction operations are
            tested individually below.
        -relative CME columns added
    '''
    test_file = 'stance_phase_a1bf8bad_transformed_short.csv'
    test_data = pd.read_csv(path + test_file)
    columns = test_data.columns
    data = do.RawFrame(copy.deepcopy(test_data), columns)
    data = rcme.run_relative_cmes(data)

    # relative cme columns added
    assert test_data.__dict__ != data.__dict__


def test_drift_agnostic_CMES():
    '''
    Tests include:
        -output is appropriately formatted
        -output matches expectation given known input
           -values align
           -values filled where relevant
           -values = nan where irrelevant
    '''
    cme = np.empty(10).reshape(-1, 1) * np.nan
    ranges = np.array([[0, 2], [6, 9]])
    stance = np.ones((10, 1)) + 3
    calc_cme = rcme._drift_agnostic_cmes(cme, ranges, stance)
    exp_cme = np.array([2, 2, np.nan, np.nan, np.nan, np.nan, 3, 3, 3,
                        np.nan]).reshape(-1, 1) / 1000.0
    # output is appropriately formatted
    assert calc_cme.shape == exp_cme.shape

    # output matches expectation given known input
    # values align and filled only where relevant
    assert np.allclose(calc_cme, exp_cme, equal_nan=True)


def test_driftless_CMS():
    '''
    Tests include:
        -output is appropriately formatted
        -output matches expectation given known input
    '''
    data = np.array([0, 1, 2, 4, 6, 3, -2, -6, -2, 5])
    cov = np.empty(10).reshape(-1, 1) * np.nan
    cov_pos = np.empty(10).reshape(-1, 1) * np.nan
    cov_neg = np.empty(10).reshape(-1, 1) * np.nan
    ran = np.empty(10).reshape(-1, 1) * np.nan
    ranges = np.array([[0, 2], [4, 9]])
    time = np.ones((10, 1)) + 9
    calc_mot_abs, calc_mot_pos, calc_mot_neg, calc_range = rcme._driftless_cmes(data, ranges, time, cov, cov_pos,
                                                                                cov_neg, ran)
    targ_mot_abs = np.array([50, 50, np.nan, np.nan, 320, 320, 320, 320,
                             320, np.nan]).reshape(-1, 1)
    targ_mot_pos = np.array([50, 50, np.nan, np.nan, 80, 80, 80, 80,
                             80, np.nan]).reshape(-1, 1)
    targ_mot_neg = np.array([0, 0, np.nan, np.nan, -240, -240, -240, -240,
                             -240, np.nan]).reshape(-1, 1)
    targ_range = np.array([50, 50, np.nan, np.nan, 240, 240, 240, 240, 240,
                           np.nan]).reshape(-1, 1)

    # output is appropriately formatted
    assert calc_mot_abs.shape == targ_mot_abs.shape
    assert calc_mot_pos.shape == targ_mot_pos.shape
    assert calc_mot_neg.shape == targ_mot_neg.shape
    assert calc_range.shape == targ_range.shape

    # output matches expectation given known input
    assert np.allclose(calc_mot_abs, targ_mot_abs, equal_nan=True)
    assert np.allclose(calc_mot_pos, targ_mot_pos, equal_nan=True)
    assert np.allclose(calc_mot_neg, targ_mot_neg, equal_nan=True)
    assert np.allclose(calc_range, targ_range, equal_nan=True)


def test_norm_range_of_motion():
    '''
    Tests include:
        -ouput is appropriately formatted
        -output matches expectation given known input
    '''
    data1 = np.array([1, 1, 1, 1, 1]).reshape(-1, 1)
    data2 = np.array([1, 2, 3, 2, 5]).reshape(-1, 1)
    data3 = np.array([0, 0, 0, 0, 0]).reshape(-1, 1)
    data4 = np.array([np.nan, np.nan, np.nan, np.nan, np.nan]).reshape(-1, 1)
    time = np.array([10., 10., 10., 10., 10.]).reshape(-1, 1)
    res1 = rcme._norm_range_of_motion(data1, time)
    res2 = rcme._norm_range_of_motion(data2, time)
    res3 = rcme._norm_range_of_motion(data3, time)
    res4 = rcme._norm_range_of_motion(data4, time)
    targ1 = data3
    targ2 = np.array([80, 80, 80, 80, 80]).reshape(-1, 1)
    targ3 = data3
    targ4 = data4

    # output is appropriately formatted
    assert data1.shape == res1.shape

    # output matches expectation given known input
    assert np.allclose(res1, targ1)
    assert np.allclose(res2, targ2)
    assert np.allclose(res3, targ3)
    assert np.allclose(res4, targ4, equal_nan=True)


def test_norm_motion_covered():
    '''
    Tests include:
        -ouput is appropriately formatted
        -output matches expectation given known input
    '''
    data1 = np.array([1, 1, 1, 1, 1]).reshape(-1, 1)
    data2 = np.array([1, 2, 3, 2, 5]).reshape(-1, 1)
    data3 = np.array([0, 0, 0, 0, 0]).reshape(-1, 1)
    time = np.array([10., 10., 10., 10., 10.]).reshape(-1, 1)
    res1 = rcme._norm_motion_covered(data1, time, 'abs')
    res2 = rcme._norm_motion_covered(data2, time, 'abs')
    res3 = rcme._norm_motion_covered(data3, time, 'abs')
    targ1 = data3
    targ2 = np.array([120, 120, 120, 120, 120]).reshape(-1, 1)
    targ3 = data3

    # output is appropriately formatted
    assert data1.shape == res1.shape

    # output matches expectation given known input
    assert np.allclose(res1, targ1)
    assert np.allclose(res2, targ2)
    assert np.allclose(res3, targ3)


def test_rough_contact_duration():
    '''
    Tests include:
        -ouput is appropriately formatted
        -output matches expectation knowing known input
            - contact and non contact stretches, all possible stances
            represented
    '''
    stance = np.array([0, 0, 1, 0, 0, 3, 3, 3, 2, 2, 4, 4, 0, 3, 5, 5, 5,
                       5, 5, 2, 1, 0, 2, 2, 3, 2, 2, 2, 3, 1, 1, 3]).reshape(-1, 1)
    targ = np.array([np.nan, np.nan, np.nan, np.nan, np.nan, 7, 7, 7, 7,
                     7, 7, 7, np.nan, 7, 7, 7, 7, 7, 7, 7, np.nan, np.nan,
                     7, 7, 7, 7, 7, 7, 7, np.nan, np.nan,
                     1]).reshape(-1, 1) / 1000.0
    test = rcme._rough_contact_duration(stance)

    # output is formatted appropriately
    assert stance.shape == test.shape
    # output matches expectation given known input
    assert np.allclose(test, targ, equal_nan=True)


def test_detect_long_dynamic():
    '''
    Tests include:
        -output appropriately formatted
        -output matches expectations given known inputs
    '''
    flag1 = np.zeros((100000, 1))
    flag1[5:8] = 8
    flag1[15:18] = 8
    flag1[25:28] = 8
    flag1[35:38] = 8
    flag1[45:48] = 8
    calc_range1 = rcme._detect_long_dynamic(flag1)
    flag2 = flag1
    flag2[1000:2000] = 8
    flag2[2500:5000] = 8
    flag2[10000:30000] = 8
    calc_range2 = rcme._detect_long_dynamic(flag2)
    exp_range2 = np.array([[1000, 2000], [2500, 5000], [10000, 30000]])

    # output appropriately formatted
    assert exp_range2.shape[1] == 2

    # output matches expectations given known inputs
    assert calc_range1.size == 0
    assert np.allclose(calc_range2, exp_range2)


def test_remove_filtered_ends():
    '''
    Tests include:
        -output is formatted appropriately
        -output matches expectation when given known inputs
            -trims rows when dynamic activity ends near end
            -splits rows when dynamic activity ends in middle
            -retains rows when no dynamic activity change
            -deletes rows when too short to trim or split
    '''
    data_range = np.array([[0, 5], [15, 25], [30, 40], [50, 60], [67, 75],
                           [80, 82], [85, 100]])
    dyn_range = np.array([[3, 16], [25, 30], [35, 56], [79, 81], [90, 99]])
    trimmed_ends = rcme._remove_filtered_ends(data_range, dyn_range)
    exp_trim = np.array([[0, 5], [18, 25], [33, 40], [50, 54], [58, 60],
                         [67, 75], [85, 97]])

    # output is formatted appropriately
    assert trimmed_ends.shape[1] == 2

    # output matches expectations given known inputs
    #    -trims rows when dynamic activity ends near end
    #    -splits rows when dynamic activity ends in middle
    #    -retains rows when no dynamic activity change
    #    -deletes rows when too short to trim or split
    assert np.allclose(trimmed_ends, exp_trim)
