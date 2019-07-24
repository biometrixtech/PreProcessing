from aws_xray_sdk.core import xray_recorder
xray_recorder.configure(sampling=False)
xray_recorder.begin_segment(name="test")

from jobs.transformandplacement import TransformandplacementJob
from jobs.downloadandchunk.decode_data import read_file
from tests.app.writemongo.datastore import MockDatastore
import numpy as np
import scipy.io


def convert_accel(data):
    conversion_factor = 9.807 / 1000
    data.acc_0_x *= conversion_factor
    data.acc_0_y *= conversion_factor
    data.acc_0_z *= conversion_factor

    data.acc_1_x *= conversion_factor
    data.acc_1_y *= conversion_factor
    data.acc_1_z *= conversion_factor

    data.acc_2_x *= conversion_factor
    data.acc_2_y *= conversion_factor
    data.acc_2_z *= conversion_factor


def test_full_job_process():
    path = '../../../files/'
    # data = scipy.io.loadmat(f"{path}data2.mat").get("data")  # raw data
    # data_out = scipy.io.loadmat(f"{path}data2C.mat").get("dataC")  # transformed data
    data_bin_pd = read_file(f"{path}dataBin")
    data_bin = np.asanyarray(data_bin_pd.values)
    data = scipy.io.loadmat(f"{path}data.mat").get("data")  # raw data
    data_out = scipy.io.loadmat(f"{path}dataC.mat").get("dataC")  # transformed data

    session_id = "unit_test"
    event_date = "2019-07-11"
    user_id = "unit_test"
    datastore = MockDatastore(session_id, event_date, user_id)
    datastore._metadata["version"] = "2.3"
    job = TransformandplacementJob(datastore)

    # load test data into datastore
    data = np.asanyarray(data)
    data_pd = job.get_core_data_frame_from_ndarray(data)
    for a in range(1, 25):
        assert (np.abs(data_bin[:, a] - data[:, a]) < 0.001).all()

    job.datastore.side_loaded_data = data_pd
    job._run()

    decimal_precision = 3

    for a in range(0, 25):
        max_diff = np.max(np.abs(job._underlying_ndarray[:, a] - data_out[:, a]))
        assert (np.abs(job._underlying_ndarray[:, a] - data_out[:, a]) < 0.02).all()