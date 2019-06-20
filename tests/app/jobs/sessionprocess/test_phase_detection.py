from aws_xray_sdk.core import xray_recorder
xray_recorder.configure(sampling=False)
xray_recorder.begin_segment(name="test")
import numpy as np
import numpy.polynomial.polynomial as poly
import os

# Use theano backend for keras
os.environ['KERAS_BACKEND'] = 'theano'

from app.jobs.sessionprocess import phase_detection as phd


def test_combine_phase():
    pass


def test_body_phase():
    pass


def test_phase_detect():
    '''
    Tests included:
        -output appropriately formatted
        -output matches expectation given known input
            -smoothes false motion
            -does not smooth true motion
    '''



    #acc = np.ones((200, 1))
    acc = np.ones(200)
    acc[50] = 5
    acc[100:] = 5
    hz = 200
    bal = phd._phase_detect(acc)
    #targ = np.zeros((200, 1))
    targ = np.zeros(200)
    targ[100:] = 1
    targ[50:] = 1

    # output formatted appropriately
    assert 200 == len(bal)
    # output matches expectation given known input
    #assert True is np.allclose(bal, targ.reshape(1, -1))
    assert True is np.allclose(bal, targ)


def test_impact_detect():
    pass

