from aws_xray_sdk.core import xray_recorder
xray_recorder.configure(sampling=False)
xray_recorder.begin_segment(name="test")
import numpy as np
import numpy.polynomial.polynomial as poly
import os

# Use theano backend for keras
os.environ['KERAS_BACKEND'] = 'theano'

from app.utils import filter_data as fd
from app.utils import get_ranges as gr


def _polyfit(x, y, degree):
    results = {}
    coeffs = poly.polyfit(x.T, y.T, degree)
    results['polynomial'] = coeffs.tolist()
    return results


def test_get_ranges():
    '''
    Tests include:
        -output appropriately indexes runs of consecutive repetitions of
        the chosen value
    '''
    test = np.array([1, 1, 1, 2, 3, 2, 2, 2, 1, 0, 5, 3, 3, 5, 5, 0])
    runs_0 = gr(test, 0)
    runs_1 = gr(test, 1)
    runs_2 = gr(test, 2)
    runs_3 = gr(test, 3)
    runs_5 = gr(test, 5)

    # output matches expectation of known array
    assert np.allclose(runs_0, np.array([[9, 10]]))
    assert np.allclose(runs_1, np.array([[0, 3], [8, 9]]))
    assert np.allclose(runs_2, np.array([[3, 4], [5, 8]]))
    assert np.allclose(runs_3, np.array([[4, 5], [11, 13]]))
    assert np.allclose(runs_5, np.array([[10, 11], [13, 15]]))


def test_zero_runs():
    '''
    Tests include:
        -output is appropriately formatted
        -output matches expectation given known input
    '''
    data1 = np.array([0, 0, np.nan, 1, 1, 1, 2, 1, 1, 0]).reshape(-1, 1)
    data2 = np.array([1, 0, 0, 1, 1, 1, 2, 1, 1, 1]).reshape(-1, 1)
    ranges1, length1 = gr(data1, 1, True)
    ranges2, length2 = gr(data2, 1, True)
    targ_ranges1 = np.array([[3, 6], [7, 9]])
    targ_len1 = np.array([3, 2])
    targ_ranges2 = np.array([[0, 1], [3, 6], [7, 9]])
    targ_len2 = np.array([1, 3, 2])

    # output is appropriately formatted
    assert ranges1.shape == targ_ranges1.shape
    assert len(ranges1) == len(length1)

    # output matches expectation given known input
    assert np.allclose(ranges1, targ_ranges1, equal_nan=True)
    assert np.allclose(length1, targ_len1, equal_nan=True)
    assert np.allclose(ranges2, targ_ranges2, equal_nan=True)
    assert np.allclose(length2, targ_len2, equal_nan=True)


def test_filter_data():
    '''
    Tests include:
        -output is appropriately formatted
        -output matches expectation given known input
    '''

    Fs = 100
    x = np.arange(500)
    s0_01 = np.sin(2 * np.pi * 0.01 * x / Fs)
    s0_1 = np.sin(2 * np.pi * 0.1 * x / Fs)
    s0_5 = np.sin(2 * np.pi * 0.5 * x / Fs)
    s1 = np.sin(2 * np.pi * 1 * x / Fs)
    s5 = np.sin(2 * np.pi * 5 * x / Fs)
    s20 = np.sin(2 * np.pi * 20 * x / Fs)
    s30 = np.sin(2 * np.pi * 30 * x / Fs)
    fs0_01 = fd(s0_01).reshape(1, len(x))
    fs0_1 = fd(s0_1).reshape(1, len(x))
    fs0_5 = fd(s0_5).reshape(1, len(x))
    fs1 = fd(s1).reshape(1, len(x))
    fs5 = fd(s5).reshape(1, len(x))
    fs20 = fd(s20).reshape(1, len(x))
    fs30 = fd(s30).reshape(1, len(x))
    lfs0_1 = fd(s0_1, filt='low').reshape(1, len(x))

    res0_01 = _polyfit(x, fs0_01, 1)
    slopes0_01 = np.abs(np.array(res0_01['polynomial'][1]))
    res0_1 = _polyfit(x, fs0_1, 1)
    slopes0_1 = np.abs(np.array(res0_1['polynomial'][1]))
    res0_5 = _polyfit(x, fs0_5, 1)
    slopes0_5 = np.abs(np.array(res0_5['polynomial'][1]))
    res1 = _polyfit(x, fs1, 1)
    slopes1 = np.abs(np.array(res1['polynomial'][1]))
    res5 = _polyfit(x, fs5, 1)
    slopes5 = np.abs(np.array(res5['polynomial'][1]))
    res20 = _polyfit(x, fs20, 1)
    slopes20 = np.abs(np.array(res20['polynomial'][1]))
    res30 = _polyfit(x, fs30, 1)
    slopes30 = np.abs(np.array(res30['polynomial'][1]))

    # output is appropriately formatted
    assert x.shape == fd(s0_01).shape

    # output matches expectation given known input
    # signals with frequencies to be rejected are smoothed by filter
    assert slopes0_01 < 0.00055
    assert slopes0_1 < 0.00055
    assert slopes0_5 >= 0.00055
    assert slopes1 >= 0.00055
    assert slopes5 >= 0.00055
    assert slopes20 < 0.00055
    assert slopes30 < 0.00055
    assert not np.allclose(lfs0_1.reshape(-1, 1), fs0_1)
    assert np.max(s0_1 - lfs0_1) < 0.0005
