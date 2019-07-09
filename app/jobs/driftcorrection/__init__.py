from ..job import Job
import numpy as np
from jobs.driftcorrection.heading_correction import heading_correction
from jobs.driftcorrection.heading_correction import heading_hip_finder, heading_foot_finder
from jobs.driftcorrection.hip_drift_correction import hip_drift_correction
from jobs.driftcorrection.foot_drift_correction import foot_drift_correction
from jobs.driftcorrection.acceleration_correction import axl_correction


class DriftcorrectionJob(Job):

    def __init__(self, datastore):
        super().__init__(datastore)

    def _run(self):

        self.data = self.datastore.get_data(('transformandplacement', '*'))
        reset_index = self.datastore.get_metadatum('reset_index', None)
        start_MPh = self.datastore.get_metadatum('start_MPh', None)
        stop_MPh = self.datastore.get_metadatum('stop_MPh', None)
        qHH = self.datastore.get_metadatum('qHH', None)

        # convert to ndarray
        # data (25 columns) has been through Body Frame Transformation
        data = self.get_ndarray()

        # Sampling frequency
        fs = 100
        # Set maximum length within search (MPh) from the beginning of the data (secs*Fs)
        nsearch = 30 * fs

        ## Heading values
        # TODO: move to transformandplacement
        # Heading value for hip sensor
        #qHH = heading_hip_finder(data[:nsearch, 13:17], reset_index)

        # Heading values for foot sensors (with marching phase)
        qH0, qH2 = heading_foot_finder(data[:nsearch, 1:9], data[:nsearch, 17:25], start_MPh, stop_MPh)

        # Heading correction for all sensors
        dataHC = heading_correction(data, qH0, qHH, qH2)

        op_cond_0 = data[:, 1]
        op_cond_h = data[:, 9]
        op_cond_2 = data[:, 17]

        # Drift correction: left foot, hip, right foot
        q_corr_0 = foot_drift_correction(op_cond_0, dataHC[:, 2: 5], dataHC[:, 5: 9])
        q_corr_h = hip_drift_correction(op_cond_h, dataHC[:, 13:17])
        q_corr_2 = foot_drift_correction(op_cond_2, dataHC[:, 18:21], dataHC[:, 21:25])

        dataHC[:, 5: 9] = q_corr_0
        dataHC[:, 13: 17] = q_corr_h
        dataHC[:, 21: 25] = q_corr_2

        # Acceleration correction
        axl_corr_0 = axl_correction(q_corr_0, dataHC[:, 2: 5])
        axl_corr_h = axl_correction(q_corr_h, dataHC[:, 10:13])
        axl_corr_2 = axl_correction(q_corr_2, dataHC[:, 18:21])

        dataHC[:, 2: 5] = axl_corr_0
        dataHC[:, 10: 13] = axl_corr_h
        dataHC[:, 18: 21] = axl_corr_2

        self.data = self.get_core_data_frame_from_ndarray(dataHC)

        # op_cond_fl = self.data[f'magn_lf']
        # axl_ref_lf = self.data.loc[:, [f'acc_lf_x', f'acc_lf_y', f'acc_lf_z']]
        # q_ref_lf = self.data.loc[:, [f'quat_lf_w', f'quat_lf_x', f'quat_lf_y', f'quat_lf_z']]
        #
        # # Do transformation with `self.data`
        # acc_corrected_lf = NotImplemented
        #
        # self.data.loc[:, [f'acc_lf_x_corrected', f'acc_lf_y_corrected', f'acc_lf_z_corrected']] = acc_corrected_lf

        # Etc
        #convert to pandas before placement
        #placement goes here
        #rename columns to match l,h,r (lines 50-57 of t&p job)

        # Save the data at the end
        self.datastore.put_data('driftcorrection', self.data)
