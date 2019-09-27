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
    for i in [0, 2, 3, 4, 6]:
        path = f'../../../files/v_1.8/data{i}/'
        # path = f'../../../files/v_1.10/data{i}/'
        if 'v_1.8' in path and i == 6:
            continue
        if 'v_1.10' in path and i != 0:
            continue
        if 'v_1.10' not in path and i == 0:
            continue

        data_out = scipy.io.loadmat(f"{path}data_out.mat").get("data_out")
        dataC = scipy.io.loadmat(f"{path}dataC.mat").get("dataC")
        start_MPh = scipy.io.loadmat(f"{path}start_MPh.mat").get("start_MPh")[0][0]
        stop_MPh = scipy.io.loadmat(f"{path}stop_MPh.mat").get("stop_MPh")[0][0]
        qH0 = scipy.io.loadmat(f"{path}q_H_L.mat").get('q_H_L')
        qHH = scipy.io.loadmat(f"{path}q_H_H.mat").get('q_H_H')
        qH2 = scipy.io.loadmat(f"{path}q_H_R.mat").get('q_H_R')

        qH0 = json.dumps(qH0.reshape(-1,).tolist())
        qHH = json.dumps(qHH.reshape(-1,).tolist())
        qH2 = json.dumps(qH2.reshape(-1,).tolist())

        session_id = ""
        event_date = ""
        user_id = ""
        end_date = ""
        datastore = MockDatastore(session_id, event_date, user_id, end_date)
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

        # for a in range(0, 25):
        #     if 9 <= a < 17:
        #         continue
        #     if a in [2, 3, 4, 18, 19, 20]:
        #         precision = 10**-2
        #     else:
        #         precision = 10 ** -4
        #     assert (np.abs(job._underlying_ndarray[:-1, a] - data_out[:-1, a]) < precision).all()
