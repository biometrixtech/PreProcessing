from __future__ import print_function

import numpy as np


def compute_transform(data):
    data.reset_index(inplace=True)
    start, end = detect_still(data)
    data = data.loc[start:end, :]
    data.reset_index(inplace=True)
    return [[1,0,0,0], [0,1,0,0], [0,0,1,0]]


def detect_still(data):
    """Detect part of data with activity for placement detection
    """
    thresh = 2.  # threshold to detect balance phase
    bal_win = 300 # sampling window to determine balance phase
    acc_mag_0 = np.sqrt(data.aX0**2 + data.aY0**2 + data.aZ0**2)
    acc_mag_1 = np.sqrt(data.aX1**2 + data.aY1**2 + data.aZ1**2)
    acc_mag_2 = np.sqrt(data.aX2**2 + data.aY2**2 + data.aZ2**2)
    total_acc_mag = acc_mag_0 + acc_mag_1 + acc_mag_2
    import matplotlib.pyplot as plt
    plt.plot(total_acc_mag)
    plt.axhline(y=3)

    dummy_balphase = []  # dummy variable to store indexes of balance phase

    abs_acc = total_acc_mag  # creating an array of absolute acceleration values
    len_acc = len(total_acc_mag)  # length of acceleration value
    

    for i in range(len_acc-bal_win):
        # check if all the points within bal_win of current point are within
        # movement threshold
        if len(np.where(abs_acc[i:i+bal_win] <= thresh)[0]) == bal_win:
            dummy_balphase += range(i, i+bal_win)

    # determine the unique indexes in the dummy list
    start_bal = []    
    start_bal = np.unique(dummy_balphase)
    start_bal = np.sort(start_bal)

    still = np.zeros(len(data))
    still[start_bal] = 1
    plt.plot(still)
    change = np.ediff1d(still, to_begin=1)
    start = np.where(change==1)[0]
    end = np.where(change==-1)[0]

    # if data ends with movement, assign final point as end of movement
    if len(start) != len(end):
        end = np.append(end, len(data))

    start = start
    for i in range(len(end)):
        end[i] = min([end[i], start[i] + 300])

    return start[0], end[0]