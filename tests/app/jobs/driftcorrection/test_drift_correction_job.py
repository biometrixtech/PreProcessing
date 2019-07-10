from aws_xray_sdk.core import xray_recorder
xray_recorder.configure(sampling=False)
xray_recorder.begin_segment(name="test")

from jobs.driftcorrection import DriftcorrectionJob
from jobs.driftcorrection.heading_correction import heading_hip_finder
from tests.app.writemongo.datastore import MockDatastore
import numpy as np
import scipy.io
from scipy.signal import find_peaks as _find_peaks


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


def test_full_job_process():

    path = '../../../files/'

    data = scipy.io.loadmat(f"{path}data2.mat").get("data") # need to start with BFT data; but hip_finders users pre-transformed data
    data_out = scipy.io.loadmat(f"{path}data2_out.mat").get("data_out")
    dataC = scipy.io.loadmat(f"{path}data2C.mat").get("dataC")

    fs = 100  # Hz
    # Find reset_index
    op_cond_l = dataC[:, 1]
    op_cond_h = dataC[:, 9]
    op_cond_r = dataC[:, 17]
    op_cond = np.logical_or(op_cond_h, np.logical_or(op_cond_l, op_cond_r))
    reset_index = find_reset(op_cond)

    # Set maximum lenght whithin search (MPh) from the beginning of the data (secs*fs)
    nsearch = 30*fs

    # Find MarchingPhase only with left sensor data, and with right sensor ones if it's needed
    dataL = np.asanyarray(dataC[:nsearch, 1:9])
    op_condL = dataL[:, 0]
    axlL = dataL[:, 1:4]
    start_MPh, stop_MPh = find_marching(op_condL, axlL)

    qHH = heading_hip_finder(data[:nsearch, 13:17], reset_index)

    session_id = ""
    event_date = ""
    user_id = ""
    datastore = MockDatastore(session_id, event_date, user_id)
    datastore._metadata["reset_index"] = reset_index
    datastore._metadata["start_MPh"] = start_MPh
    datastore._metadata["stop_MPh"] = stop_MPh
    datastore._metadata["qHH"] = qHH
    job = DriftcorrectionJob(datastore)

    # load test data into datastore
    data = np.asanyarray(dataC)
    job.datastore.side_loaded_data = job.get_core_data_frame_from_ndarray(data)
    job._run()

    decimal_precision = 4

    for a in range(0, 25):
        assert np.equal(np.round(job._underlying_ndarray[:, a], decimal_precision), np.round(data_out[:, a], decimal_precision)).all()


