import numpy as np
import scipy.io
from jobs.driftcorrection.sensors_drift_correction import sensors_drift_correction
from jobs.driftcorrection.correction_parameters import foot_parameters, hip_parameters


def test_match_221e():
    for i in [0, 2, 3, 4, 6]:
        # path = f'../../../files/v_1.8/data{i}/'
        path = f'../../../files/v_1.10/data{i}/'
        if 'v_1.8' in path and i == 6:
            continue
        if 'v_1.10' in path and i != 0:
            continue

        data = scipy.io.loadmat(f"{path}data.mat").get("data")
        dataHC = scipy.io.loadmat(f"{path}data_Heading_corrected.mat").get("data_Heading_corrected")
        q_corr_l_actual = scipy.io.loadmat(f"{path}q_corr_Left.mat").get("q_corr_Left")
        q_corr_h_actual = scipy.io.loadmat(f"{path}q_corr_Hip.mat").get("q_corr_Hip")
        q_corr_r_actual = scipy.io.loadmat(f"{path}q_corr_Right.mat").get("q_corr_Right")

        data = np.asanyarray(data)

        op_cond_l = data[:, 1]
        op_cond_h = data[:, 9]
        op_cond_r = data[:,17]

        # Drift correction: left foot, hip, right foot
        axl_drift_hip = np.copy(dataHC[:, 11])
        q_corr_l, candidate_troughs_0, troughs_0 = sensors_drift_correction(op_cond_l, dataHC[:, 2: 5], dataHC[:, 5: 9], foot_parameters, Foot=True)
        q_corr_r, candidate_troughs_2, troughs_2 = sensors_drift_correction(op_cond_r, dataHC[:, 18:21], dataHC[:, 21:25], foot_parameters, Foot=True)
        hip_parameters.append(troughs_0)
        q_corr_h, candidate_correction_points_h, correction_points_h = sensors_drift_correction(op_cond_h, axl_drift_hip, dataHC[:, 13:17], hip_parameters, Foot=False)

        precision = 10**-4

        for a in range(0, 4):
            assert (np.abs(q_corr_l_actual[:-1, a] - q_corr_l[:-1, a]) < precision).all()
            # assert (np.abs(q_corr_h_actual[:, a] - q_corr_h[:, a]) < precision).all()
            assert (np.abs(q_corr_r_actual[:-1, a] - q_corr_r[:-1, a]) < precision).all()