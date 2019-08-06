from aws_xray_sdk.core import xray_recorder
xray_recorder.configure(sampling=False)
xray_recorder.begin_segment(name="test")

from jobs.transformandplacement import TransformandplacementJob
# from jobs.downloadandchunk.decode_data import read_file
from tests.app.writemongo.datastore import MockDatastore
import numpy as np
import scipy.io


def test_full_job_process():
    for i in [2, 3, 4]:
        path = f'../../../files/data{i}/'
        data = scipy.io.loadmat(f"{path}data.mat").get("data")  # raw data
        # data_bin_pd = read_file(f"{path}dataBin")
        # convert_accel(data_bin_pd)
        # data_bin = np.asanyarray(data_bin_pd)
        session_id = "unit_test"
        event_date = "2019-07-11"
        user_id = "unit_test"
        datastore = MockDatastore(session_id, event_date, user_id)
        datastore._metadata["version"] = "2.3"
        job = TransformandplacementJob(datastore)

        # load test data into datastore
        data = np.asanyarray(data)
        data_pd = job.get_core_data_frame_from_ndarray(data)
        # for a in range(1, 25):
        #     assert (np.abs(data_bin[:, a] - data[:, a]) < 0.001).all()

        job.datastore.side_loaded_data = data_pd
        job._run()