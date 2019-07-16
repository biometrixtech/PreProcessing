from jobs.driftcorrection.heading_correction import heading_correction
from jobs.transformandplacement.heading_calculation import heading_foot_finder
from jobs.transformandplacement.transform_calculation import compute_transform
from jobs.transformandplacement.get_march_and_still import detect_march_and_still
import numpy as np
import scipy.io
from scipy.signal import find_peaks as _find_peaks
import pandas as pd


def find_reset(op_cond):
    """
    Find a confident reset_index in a long enough static phase.

    Parameters
    ----------
    op_cond : array_like
        global op_cond, as or value of left, hip and right.

    Returns
    -------
    reset_index : number
        Confident static reset index.
    """
    op_cond = np.asanyarray(op_cond)
    # Sampling frequency
    fs = 100
    # Set maximum lenght whithin search (MPh) from the beginning of the data (secs*Fs)
    nsearch = 30*fs
    # op_down counter and threshold for resetIndex
    op_down_count = 0
    op_down_th = 0.3*fs

    for i in range(nsearch):
        if op_cond[i] == 0:
            op_down_count += 1
            if op_down_count > op_down_th and i + 1 > 0.5*fs:
                return i
        else:
            op_down_count = 0

    return -1


def find_marching(op_cond, axl):
    """
    Find the  marching phase window, typical BioMX protocol used then for foot
    sensorss heading estimation.

    Parameters
    ----------
    op_cond : array_like
        Dynamic-static phase trigger of a foot sensor.
    axl : array_like
        Raw accelerations vector.

    Returns
    -------
    start_MPh : number
        Start marching phase index.
    stop_MPh : number
        Stop marching phase index.
    """
    op_cond = np.copy(op_cond)
    axl = np.asanyarray(axl, dtype=float)

    ## Sampling frequence setting
    fs = 100
    ## Initialization
    # Set minimum lenght of searched marching phase windows (MPh) (secs*fs)
    nsamples_min = 3*fs
    # Set maximum lenght of searched marching phase windows (MPh) (secs*fs)
    nsamples_max = 10*fs
    # parameter to manage unespected op_cond down
    hyst_cnt_pullDw_TH = 15

    # Axl Norm and gravity subtraction
    axl_norm = np.linalg.norm(axl, axis=1) - 1000

    op_down_count = 0
    for i in range(1, op_cond.size):
        ## Hysteresis
        if op_cond[i-1] == 1 and op_cond[i] == 0:
            op_down_count += 1
            if op_down_count < hyst_cnt_pullDw_TH:
                op_cond[i] = 1
                continue
        op_down_count = 0

    start_op_cond = 0
    marching_found = False
    for i in range(1, op_cond.size):
        ## Found start of dynamic condition window
        if op_cond[i-1] == 0 and op_cond[i] == 1:
            start_op_cond = i
        ## Found end of dynamic condition window - i points to the end of the dynamic operating condition
        if op_cond[i-1] == 1 and op_cond[i] == 0:
            stop_op_cond = i + 1
            ## Marching phase constrain in length and not first dyn phase if op_cond[1]==1
            if i + 1 - start_op_cond >= nsamples_min and start_op_cond != 0:
                start_MPh = start_op_cond
                stop_MPh = stop_op_cond
                peak_pos, _ = _find_peaks(axl_norm[start_MPh:stop_MPh], height=1000)
                if peak_pos.size >= 4:
                    marching_found = True
        if i + 1 - start_op_cond >= nsamples_max and start_op_cond != 0 and op_cond[i] == 0:
            start_MPh = start_op_cond
            stop_MPh = i + 1
            peak_pos, _ = _find_peaks(axl_norm[start_MPh:stop_MPh], height=1000)
            if peak_pos.size >= 4:
                marching_found = True
        if marching_found:
            break

    if not marching_found:
        start_MPh = np.nan
        stop_MPh = np.nan

    return start_MPh, stop_MPh


def test_match_221e():

    path = '../../../files/'

    data = scipy.io.loadmat(f"{path}data.mat").get("data")
    dataC = scipy.io.loadmat(f"{path}dataC.mat").get("dataC")
    dataHC_actual = scipy.io.loadmat(f"{path}data_Heading_corrected.mat").get("data_Heading_corrected")

    #df = pd.DataFrame(data=data[1:, 1:], index=data[1:, 0], columns=data[0, 1:])

    data = np.asanyarray(data)
    # Creating pandas dataframe from numpy array
    df = pd.DataFrame({'epoch_time': data[:, 0], 'static_0': data[:, 1], 'acc_0_x': data[:, 2],
                            'acc_0_y': data[:, 3], 'acc_0_z': data[:, 4], 'quat_0_w': data[:, 5],
                            'quat_0_x': data[:, 6], 'quat_0_y': data[:, 7], 'quat_0_z': data[:, 8],
                            'static_1': data[:, 9], 'acc_1_x': data[:, 10], 'acc_1_y': data[:, 11],'acc_1_z': data[:, 12],
                            'quat_1_w': data[:, 13],'quat_1_x': data[:, 14], 'quat_1_y': data[:, 15], 'quat_1_z': data[:, 16],
                            'static_2': data[:, 17], 'acc_2_x': data[:, 18], 'acc_2_y': data[:, 19],
                            'acc_2_z': data[:, 20], 'quat_2_w': data[:, 21], 'quat_2_x': data[:, 22],
                            'quat_2_y': data[:, 23], 'quat_2_z': data[:, 24]})

    #data.loc[start_still_0:end_still_0, ['quat_0_w', 'quat_0_x', 'quat_0_y', 'quat_0_z']].values.reshape(-1, 4)

    # fs = 100 # Hz
    # # Find reset_index
    # op_cond_l = data[:, 1]
    # op_cond_h = data[:, 9]
    # op_cond_r = data[:,17]
    # op_cond = np.logical_or(op_cond_h, np.logical_or(op_cond_l, op_cond_r))
    # reset_index = find_reset(op_cond)
    #
    # # Set maximum lenght whithin search (MPh) from the beginning of the data (secs*fs)
    # nsearch = 30*fs
    #
    # # Find MarchingPhase only with left sensor data, and with right sensor ones if it's needed
    # dataL = np.asanyarray(dataC[:nsearch, 1:9])
    # op_condL = dataL[:, 0]
    # axlL = dataL[:, 1:4]
    # start_MPh, stop_MPh = find_marching(op_condL, axlL)

    march_still_indices = detect_march_and_still(df.loc[0:2000, :])

    ## Heading values
    # Heading value for hip sensor
    _qHH = np.array(compute_transform(df.loc[0:2000, :],
                            march_still_indices[2],
                            march_still_indices[3],
                            march_still_indices[6],
                            march_still_indices[7],
                            march_still_indices[10],
                            march_still_indices[11]
                          )[3]).reshape(-1,4)
    # Heading values for foot sensors (with marching phase)
    _qHL, _qHR = heading_foot_finder(dataC[:3000, 5:9], dataC[:3000, 21:25], march_still_indices[4], march_still_indices[5])
    # validate heading values are close
    qHL = np.array([0.6105888416883907, 0.0, 0.0, 0.7919477674731012]).reshape(-1,4)
    qHR = np.array([0.98869923264537, 0.0, 0.0, 0.14991273250280193]).reshape(-1,4)
    qHH = np.array([-0.9129943863557917, -0.0, -0.0, -0.40797211973713515]).reshape(-1,4)
    assert np.equal(np.round(_qHL, 6), np.round(qHL, 6)).all()
    assert np.equal(np.round(_qHH, 6), np.round(qHH, 6)).all()
    assert np.equal(np.round(_qHR, 6), np.round(qHR, 6)).all()

    # Heading correction for all sensors
    dataHC_observed = heading_correction(dataC, qHL, qHH, qHR)

    for a in range(0, 25):
        assert np.equal(np.round(dataHC_actual[:, a], 3), np.round(dataHC_observed[:, a], 3)).all()
