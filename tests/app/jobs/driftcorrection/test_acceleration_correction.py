import numpy as np
import scipy.io
from jobs.driftcorrection.acceleration_correction import axl_correction


def test_match_221e():
    for i in [2, 3, 4]:
        path = f'../../../files/data{i}/'

        dataHC = scipy.io.loadmat(f"{path}data_Heading_corrected.mat").get("data_Heading_corrected")
        q_corr_l = scipy.io.loadmat(f"{path}q_corr_Left.mat").get("q_corr_Left")
        q_corr_h = scipy.io.loadmat(f"{path}q_corr_Hip.mat").get("q_corr_Hip")
        q_corr_r = scipy.io.loadmat(f"{path}q_corr_Right.mat").get("q_corr_Right")

        axl_corr_l_actual = scipy.io.loadmat(f"{path}axl_corr_Left.mat").get("axl_corr_Left")
        axl_corr_h_actual = scipy.io.loadmat(f"{path}axl_corr_Hip.mat").get("axl_corr_Hip")
        axl_corr_r_actual = scipy.io.loadmat(f"{path}axl_corr_Right.mat").get("axl_corr_Right")

        axl_corr_l = axl_correction(q_corr_l, dataHC[:, 2: 5], True)
        axl_corr_h = axl_correction(q_corr_h, dataHC[:,10:13], False)
        axl_corr_r = axl_correction(q_corr_r, dataHC[:,18:21], True)

        decimal_percision = 4

        for a in range(0, 3):
            assert np.equal(np.round(axl_corr_l_actual[:, a], decimal_percision), np.round(axl_corr_l[:, a], decimal_percision)).all()
            assert np.equal(np.round(axl_corr_h_actual[:, a], decimal_percision), np.round(axl_corr_h[:, a], decimal_percision)).all()
            assert np.equal(np.round(axl_corr_r_actual[:, a], decimal_percision), np.round(axl_corr_r[:, a], decimal_percision)).all()
