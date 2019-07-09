from ..job import Job


class DriftcorrectionJob(Job):

    def __init__(self, datastore):
        super().__init__(datastore)

    def _run(self):

        self.data = self.datastore.get_data(('transformandplacement', '*'))

        op_cond_fl = self.data[f'magn_lf']
        axl_ref_lf = self.data.loc[:, [f'acc_lf_x', f'acc_lf_y', f'acc_lf_z']]
        q_ref_lf = self.data.loc[:, [f'quat_lf_w', f'quat_lf_x', f'quat_lf_y', f'quat_lf_z']]

        # Do transformation with `self.data`
        acc_corrected_lf = NotImplemented

        self.data.loc[:, [f'acc_lf_x_corrected', f'acc_lf_y_corrected', f'acc_lf_z_corrected']] = acc_corrected_lf

        # Etc

        # Save the data at the end
        self.datastore.put_data('driftcorrection', self.data)

