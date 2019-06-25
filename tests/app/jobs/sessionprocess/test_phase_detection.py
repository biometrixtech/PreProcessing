from aws_xray_sdk.core import xray_recorder
xray_recorder.configure(sampling=False)
xray_recorder.begin_segment(name="test")
import numpy as np
import pandas as pd
import numpy.polynomial.polynomial as poly
import os
from app.utils.detect_peaks import detect_peaks

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


def test_lateral_hip_acceleration():
    path = '../../../../testdata/calibration/'
    test_file2 = 'capture28_calibration.csv'
    test_data2 = pd.read_csv(path + test_file2)#, sep='\t', lineterminator='\r')
    hip_accel_data = test_data2["acc_hip_y"][800:1600]
    left_accel_data = test_data2["acc_lf_z"][800:1600]
    right_accel_data = test_data2["acc_rf_z"][800:1600]
    # conversion_factor = 9.807 / 1000
    # hip_accel_data *= conversion_factor
    # left_accel_data *= conversion_factor
    # right_accel_data *= conversion_factor

    left_turning_points = []
    right_turning_points = []
    left_maximum = 0
    right_maximum = 0
    left_max_found = False
    right_max_found = True
    left_crossing_zero = []
    right_crossing_zero = []

    left_troughs = detect_peaks(left_accel_data,mpd=80,threshold=3,edge='both',kpsh=False,valley=True)
    right_troughs = detect_peaks(right_accel_data, mpd=80, threshold=3, edge='both', kpsh=False, valley=True)

    troughs = []
    for lf in left_troughs:
        troughs.append(("L", lf))

    for rf in right_troughs:
        troughs.append(("R", rf))

    troughs = sorted(troughs, key=lambda x: x[1])

    crossing_zero = []

    # for l in range(4, len(left_accel_data) -4):
    #     if (left_accel_data.values[l] > 0 and left_accel_data.values[l + 1] > 0  and left_accel_data.values[l + 2] > 0
    #             and left_accel_data.values[l + 3] > 0 and left_accel_data.values[l - 1] <= 0 and left_accel_data.values[l - 2] < 0 and left_accel_data.values[l - 3] < 0):
    #         #left_crossing_zero.append(l)
    #         crossing_zero.append(("L", l))
    # for r in range(4, len(right_accel_data) -4):
    #     if (right_accel_data.values[r] > 0 and right_accel_data.values[r + 1] > 0  and right_accel_data.values[r + 2] > 0
    #             and right_accel_data.values[r + 3] > 0 and right_accel_data.values[r - 1] <= 0 and right_accel_data.values[r - 2] < 0 and right_accel_data.values[r - 3] < 0):
    #         #right_crossing_zero.append(r)
    #         crossing_zero.append(("R", r))

    # split code
    crossing_zero = sorted(crossing_zero, key=lambda x: x[1])
    crossing_zero_final = []
    zero_cross = crossing_zero

    last_added = ""
    for p in range(0, len(troughs)):
        if troughs[p][0] == "L":
            if p == len(troughs) - 1:
                left_accel_short_data = left_accel_data.values[troughs[p][1]:]

            else:
                left_accel_short_data = left_accel_data.values[troughs[p][1]:troughs[p+1][1]]

            for l in range(4, len(left_accel_short_data) - 4):
                if (left_accel_short_data[l] > 0 and left_accel_short_data[l + 1] > 0 and left_accel_short_data[
                    l + 2] > 0
                        and left_accel_short_data[l + 3] > 0 and left_accel_short_data[l - 1] <= 0 and
                        left_accel_short_data[l - 2] < 0 and left_accel_short_data[l - 3] < 0):
                    # left_crossing_zero.append(l)
                    crossing_zero.append(("L", l+troughs[p][1]))
        else:
            if p == len(troughs) - 1:

                right_accel_short_data = right_accel_data.values[troughs[p][1]:]
            else:

                right_accel_short_data = right_accel_data.values[troughs[p][1]:troughs[p + 1][1]]

            for r in range(4, len(right_accel_short_data) - 4):
                if (right_accel_short_data[r] > 0 and right_accel_short_data[r + 1] > 0 and right_accel_short_data[
                    r + 2] > 0
                        and right_accel_short_data[r + 3] > 0 and right_accel_short_data[r - 1] <= 0 and
                        right_accel_short_data[r - 2] < 0 and right_accel_short_data[r - 3] < 0):
                    # right_crossing_zero.append(r)
                    crossing_zero.append(("R", r+troughs[p][1]))

        #zero_cross = list(z for z in zero_cross if z[1] > troughs[p][1])
        #if troughs[p][0] == zero_cross[0][0]: ##both are left or right
        #    crossing_zero_final.append((troughs[p][0], zero_cross[0][1]))
     #       last_added = troughs[p][0]

    hip_accel = phd._lateral_hip_acceleration_detect(hip_accel_data)
    i=0


