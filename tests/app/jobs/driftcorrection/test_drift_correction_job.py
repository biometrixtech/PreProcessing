from aws_xray_sdk.core import xray_recorder
xray_recorder.configure(sampling=False)
xray_recorder.begin_segment(name="test")

from jobs.driftcorrection import DriftcorrectionJob
from tests.app.writemongo.datastore import MockDatastore
import numpy as np
import scipy.io
import os
import json
os.environ['CHUNK_SIZE'] = "100000"

def test_full_job_process():
    for i in [2, 3, 4]:
        path = f'../../../files/data{i}/'
        data_out = scipy.io.loadmat(f"{path}data_out.mat").get("data_out")
        dataC = scipy.io.loadmat(f"{path}dataC.mat").get("dataC")
        if i == 2:
            start_MPh = 934
            stop_MPh = 1460
        elif i == 3:
            start_MPh = 1145
            stop_MPh = 1872
        elif i == 4:
            start_MPh = scipy.io.loadmat(f"{path}start_MPh.mat").get("start_MPh")[0][0]
            stop_MPh = scipy.io.loadmat(f"{path}stop_MPh.mat").get("stop_MPh")[0][0]
        else:
            start_MPh = 800
            stop_MPh = 1400
        qH0 = scipy.io.loadmat(f"{path}q_H_L.mat").get('q_H_L')
        qHH = scipy.io.loadmat(f"{path}q_H_H.mat").get('q_H_H')
        qH2 = scipy.io.loadmat(f"{path}q_H_R.mat").get('q_H_R')

        qH0 = json.dumps(qH0.reshape(-1,).tolist())
        qHH = json.dumps(qHH.reshape(-1,).tolist())
        qH2 = json.dumps(qH2.reshape(-1,).tolist())

        session_id = ""
        event_date = ""
        user_id = ""
        datastore = MockDatastore(session_id, event_date, user_id)
        datastore._metadata["start_march_1"] = str(start_MPh)
        datastore._metadata["end_march_1"] = str(stop_MPh)

        datastore._metadata["heading_quat_0"] = qH0
        datastore._metadata["heading_quat_2"] = qH2
        datastore._metadata["heading_quat_hip"] = qHH
        job = DriftcorrectionJob(datastore)

        # load test data into datastore
        data = np.asanyarray(dataC)
        job.datastore.side_loaded_data = job.get_core_data_frame_from_ndarray(data)
        job._run(run_placement=False)

        # decimal_precision = 3
        # for a in range(0, 25):
        #     diff = np.abs(np.round(job._underlying_ndarray[:, a], decimal_precision) - np.round(data_out[:, a], decimal_precision)).reshape(-1, 1)
        #     error = np.where(diff > 0.0001)
        #     assert np.equal(np.round(job._underlying_ndarray[:, a], decimal_precision), np.round(data_out[:, a], decimal_precision)).all()
