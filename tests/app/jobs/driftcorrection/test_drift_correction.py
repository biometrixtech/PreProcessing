import numpy as np
import scipy.io
from jobs.driftcorrection.hip_drift_correction import hip_drift_correction
from jobs.driftcorrection.foot_drift_correction import foot_drift_correction


def test_match_221e():

    path = '../../../files/'

    data = scipy.io.loadmat(f"{path}data2.mat").get("data")
    dataHC = scipy.io.loadmat(f"{path}data2_Heading_corrected.mat").get("data_Heading_corrected")
    q_corr_l_actual = scipy.io.loadmat(f"{path}data2_q_corr_Left.mat").get("q_corr_Left")
    q_corr_h_actual = scipy.io.loadmat(f"{path}data2_q_corr_Hip.mat").get("q_corr_Hip")
    q_corr_r_actual = scipy.io.loadmat(f"{path}data2_q_corr_Right.mat").get("q_corr_Right")

    data = np.asanyarray(data)

    op_cond_l = data[:, 1]
    op_cond_h = data[:, 9]
    op_cond_r = data[:,17]

    # Drift correction: left foot, hip, right foot
    q_corr_l = foot_drift_correction(op_cond_l, dataHC[:, 2: 5], dataHC[:, 5: 9])[0]
    q_corr_h = hip_drift_correction (op_cond_h, dataHC[:,13:17])[0]
    q_corr_r = foot_drift_correction(op_cond_r, dataHC[:,18:21], dataHC[:,21:25])[0]

    decimal_percision = 7

    for a in range(0, 4):
            assert np.equal(np.round(q_corr_l_actual[:, a], decimal_percision), np.round(q_corr_l[:, a], decimal_percision)).all()
            assert np.equal(np.round(q_corr_h_actual[:, a], decimal_percision), np.round(q_corr_h[:, a], decimal_percision)).all()
            assert np.equal(np.round(q_corr_r_actual[:, a], decimal_percision), np.round(q_corr_r[:, a], decimal_percision)).all()