
class DriftcorrectionJob:

    def __init__(self, datastore, sensor):
        self.sensor = sensor
        self.datastore = datastore

        self._peak_indices = []
        self._trough_indices = []

    def _run(self):

        self.data = self.datastore.get_data(('transformandplacement', '*'))

        op_cond = self.data[f'magn_{self.sensor}']
        axl_ref = self.data.loc[:, [f'acc_{self.sensor}_x', f'acc_{self.sensor}_y', f'acc_{self.sensor}_z']]
        q_ref = self.data.loc[:, [f'quat_{self.sensor}_w', f'quat_{self.sensor}_x', f'quat_{self.sensor}_y', f'quat_{self.sensor}_z']]

        # Do transformation with `self.data`
        acc_corrected = NotImplemented

        self.data.loc[:, [f'acc_{self.sensor}_x_corrected', f'acc_{self.sensor}_y_corrected', f'acc_{self.sensor}_z_corrected']] = acc_corrected
        self.datastore.put_data('driftcorrection', self.data)


if __name__ == '__main__':
    import pandas

    class MockDatastore:
        def get_data(self, *_):
            # Use a CSV (remove the sep= parameter) or TSV with columns `magn_lf`, `acc_lf_x`, `quat_lf_w`, etc
            return pandas.read_csv('/opt/data.csv', sep='\t')

        def put_data(self, *_):
            # You could store and test the output data here
            pass

        @property
        def session_id(self):
            return '0' * 40

    DriftcorrectionJob(MockDatastore(), 'lf')._run()
