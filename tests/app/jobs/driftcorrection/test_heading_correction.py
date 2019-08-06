from jobs.driftcorrection.heading_correction import heading_correction
import numpy as np
import scipy.io


def test_match_221e():
    for i in [2, 3, 4]:
        path = f'../../../files/data{i}/'
        dataC = scipy.io.loadmat(f"{path}dataC.mat").get("dataC")
        dataHC_actual = scipy.io.loadmat(f"{path}data_Heading_corrected.mat").get("data_Heading_corrected")
        qH0 = scipy.io.loadmat(f"{path}q_H_L.mat").get('q_H_L').reshape(-1, 4)
        qHH = scipy.io.loadmat(f"{path}q_H_H.mat").get('q_H_H').reshape(-1, 4)
        qH2 = scipy.io.loadmat(f"{path}q_H_R.mat").get('q_H_R').reshape(-1, 4)

        # Heading correction for all sensors
        dataHC_observed = heading_correction(dataC, qH0, qHH, qH2)

        decimal_percision = 4
        for a in range(0, 25):
            assert np.equal(np.round(dataHC_actual[:, a], decimal_percision), np.round(dataHC_observed[:, a], decimal_percision)).all()
