import os
import json
import numpy as np
from ..job import Job
from .heading_correction import heading_correction
from .hip_drift_correction import hip_drift_correction
from .foot_drift_correction import foot_drift_correction
from .acceleration_correction import axl_correction
from .placement import get_placement_lateral_hip
from .epoch_time_transform import convert_epochtime_datetime_mselapsed


class DriftcorrectionJob(Job):

    def __init__(self, datastore):
        super().__init__(datastore)

    def _run(self, run_placement=True):

        self.data = self.datastore.get_data('transformandplacement')
        # reset_index = self.datastore.get_metadatum('reset_index', None)
        start_MPh = self.datastore.get_metadatum('start_march_1', None)
        stop_MPh = self.datastore.get_metadatum('end_march_1', None)
        qH0 = np.array(json.loads(self.datastore.get_metadatum('heading_quat_0', None))).reshape(-1, 4)
        qHH = np.array(json.loads(self.datastore.get_metadatum('heading_quat_hip', None))).reshape(-1, 4)
        qH2 = np.array(json.loads(self.datastore.get_metadatum('heading_quat_2', None))).reshape(-1, 4)
        # convert to ndarray
        # data (25 columns) has been through Body Frame Transformation
        data = self.get_ndarray()

        # Heading correction for all sensors
        dataHC = heading_correction(data, qH0, qHH, qH2)

        op_cond_0 = data[:, 1]
        op_cond_h = data[:, 9]
        op_cond_2 = data[:, 17]

        # Drift correction: left foot, hip, right foot
        q_corr_0 = foot_drift_correction(op_cond_0, axl_refCH=dataHC[:, 2: 5], q_refCH=dataHC[:, 5: 9])
        q_corr_h = hip_drift_correction(op_cond_h, q_refCH=dataHC[:, 13:17])
        q_corr_2 = foot_drift_correction(op_cond_2, axl_refCH=dataHC[:, 18:21], q_refCH=dataHC[:, 21:25])

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

        ret = {}

        if run_placement:
            placement_detected, weak_placement = get_placement_lateral_hip(self.data, start_MPh, stop_MPh)

            placement = zip(placement_detected, ['lf', 'hip', 'rf'])
            column_prefixes = ['static_{}', 'acc_{}_x', 'acc_{}_y', 'acc_{}_z', 'quat_{}_x', 'quat_{}_y',
                               'quat_{}_z', 'quat_{}_w']
            renames = {}
            for old, new in placement:
                for prefix in column_prefixes: 
                    renames[prefix.format(str(old))] = prefix.format(str(new))

            self.data = self.data.rename(index=str, columns=renames)

            ret = {
                'placement': placement,
                'weak_placement': weak_placement
            }

        # ms_elapsed and datetime
        data['time_stamp'], data['ms_elapsed'] = convert_epochtime_datetime_mselapsed(data.epoch_time)

        # Save the data at the end
        self.datastore.put_data('driftcorrection', self.data, chunk_size=int(os.environ['CHUNK_SIZE']))
        self.datastore.put_metadata(ret)

        # return ret
