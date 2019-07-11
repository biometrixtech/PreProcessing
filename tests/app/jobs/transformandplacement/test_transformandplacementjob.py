from aws_xray_sdk.core import xray_recorder
xray_recorder.configure(sampling=False)
xray_recorder.begin_segment(name="test")

from jobs.transformandplacement import TransformandplacementJob
from tests.app.writemongo.datastore import MockDatastore
import numpy as np
import scipy.io


def convert_accel(data):
    conversion_factor = 9.807 / 1000
    data.acc_0_x *= conversion_factor
    data.acc_0_y *= conversion_factor
    data.acc_0_z *= conversion_factor
    data.static_0 *= 8

    data.acc_1_x *= conversion_factor
    data.acc_1_y *= conversion_factor
    data.acc_1_z *= conversion_factor
    data.static_1 *= 8

    data.acc_2_x *= conversion_factor
    data.acc_2_y *= conversion_factor
    data.acc_2_z *= conversion_factor
    data.static_2 *= 8


def test_full_job_process():
    path = '../../../files/'
    data = scipy.io.loadmat(f"{path}data2.mat").get("data")  # raw data
    data_out = scipy.io.loadmat(f"{path}data2C.mat").get("dataC")  # transformed data

    session_id = "unit_test"
    event_date = "2019-07-11"
    user_id = "unit_test"
    datastore = MockDatastore(session_id, event_date, user_id)
    datastore._metadata["version"] = "2.3"
    job = TransformandplacementJob(datastore)

    # load test data into datastore
    data = np.asanyarray(data)
    data_pd = job.get_core_data_frame_from_ndarray(data)
    convert_accel(data_pd)
    job.datastore.side_loaded_data = data_pd
    job._run()
