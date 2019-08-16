import os
import json
import numpy as np
import logging
from ..job import Job
from .heading_correction import heading_correction
from .correction_parameters import foot_parameters, hip_parameters
# from .hip_drift_correction import hip_drift_correction
# from .foot_drift_correction import foot_drift_correction
from .sensors_drift_correction import sensors_drift_correction
from .acceleration_correction import axl_correction
from .placement import get_placement_lateral_hip, get_placement_hip_correction
from .epoch_time_transform import convert_epochtime_datetime_mselapsed
from .exceptions import PlacementDetectionException
from .change_of_direction import flag_change_of_direction
from utils.quaternion_conversions import quat_as_euler_angles

_logger = logging.getLogger(__name__)


class DriftcorrectionJob(Job):

    def __init__(self, datastore):
        super().__init__(datastore)

    def _run(self, run_placement=True):

        self.data = self.datastore.get_data('transformandplacement')
        start_MPh = int(self.datastore.get_metadatum('start_march_1', None))
        stop_MPh = int(self.datastore.get_metadatum('end_march_1', None))
        qH0 = np.array(json.loads(self.datastore.get_metadatum('heading_quat_0', None))).reshape(-1, 4)
        qHH = np.array(json.loads(self.datastore.get_metadatum('heading_quat_hip', None))).reshape(-1, 4)
        qH2 = np.array(json.loads(self.datastore.get_metadatum('heading_quat_2', None))).reshape(-1, 4)
        # convert to ndarray
        # data (25 columns) has been through Body Frame Transformation
        data = self.get_ndarray()

        # Heading correction for all sensors
        dataHC = heading_correction(data, qH0, qHH, qH2)

        euler_hip_z_hc = quat_as_euler_angles(dataHC[:, 13: 17])[:, 2]

        op_cond_0 = data[:, 1]
        op_cond_h = data[:, 9]
        op_cond_2 = data[:, 17]

        axl_drift_hip = np.copy(dataHC[:, 11])
        q_corr_0, candidate_troughs_0, troughs_0 = sensors_drift_correction(op_cond_0, dataHC[:, 2: 5], dataHC[:, 5: 9], foot_parameters, Foot=True)
        q_corr_h, candidate_correction_points_h, correction_points_h = sensors_drift_correction(op_cond_h, axl_drift_hip, dataHC[:, 13:17], hip_parameters, Foot=False)
        q_corr_2, candidate_troughs_2, troughs_2 = sensors_drift_correction(op_cond_2, dataHC[:, 18:21], dataHC[:, 21:25], foot_parameters, Foot=True)

        dataHC[:, 5: 9] = q_corr_0
        dataHC[:, 13: 17] = q_corr_h
        dataHC[:, 21: 25] = q_corr_2

        # Acceleration correction
        axl_corr_0 = axl_correction(q_corr_0, dataHC[:, 2: 5], True)
        axl_corr_h = axl_correction(q_corr_h, dataHC[:, 10:13], False)
        axl_corr_2 = axl_correction(q_corr_2, dataHC[:, 18:21], True)

        dataHC[:, 2: 5] = axl_corr_0
        dataHC[:, 10: 13] = axl_corr_h
        dataHC[:, 18: 21] = axl_corr_2

        self.data = self.get_core_data_frame_from_ndarray(dataHC)
        convert_accl_to_ms2(self.data)
        self.data['candidate_troughs_0'] = candidate_troughs_0
        self.data['troughs_0'] = troughs_0
        self.data['correction_points_1'] = correction_points_h
        self.data['candidate_troughs_2'] = candidate_troughs_2
        self.data['troughs_2'] = troughs_2

        if run_placement:
            lateral_placement_detected, lateral_weak_placement = get_placement_lateral_hip(self.data, start_MPh, stop_MPh)
            hip_placement_detected, hip_weak_placement = get_placement_hip_correction(self.data)

            if hip_placement_detected != [0, 0, 0]:
                placement_detected = hip_placement_detected
            elif lateral_placement_detected != [0, 0, 0]:
                placement_detected = lateral_placement_detected
            else:
                placement_detected = [0, 0, 0]

            ret = {
                'placement': placement_detected,
                'lateral_placement': lateral_placement_detected,
                'hip_placement': hip_placement_detected,
                'weak_placement_lateral': lateral_weak_placement,
                'weak_placement_hip': hip_weak_placement,
            }
            self.datastore.put_metadata(ret)
            if placement_detected == [0, 0, 0]:
                placement_detected = [0, 1, 2]
                _logger.info('Placement detection failed')
                # raise PlacementDetectionException('Could not detect placement')
            # If placement id detected correctly, rename the columns in dataframe
            placement = zip(placement_detected, ['lf', 'hip', 'rf'])
            column_prefixes = ['static_{}', 'acc_{}_x', 'acc_{}_y', 'acc_{}_z', 'quat_{}_x', 'quat_{}_y',
                               'quat_{}_z', 'quat_{}_w', 'candidate_troughs_{}', 'troughs_{}', 'correction_points_{}']
            renames = {}
            for old, new in placement:
                for prefix in column_prefixes:
                    renames[prefix.format(str(old))] = prefix.format(str(new))
            self.data = self.data.rename(index=str, columns=renames)

        data['change_of_direction'] = flag_change_of_direction(self.data.acc_hip_z.values, euler_hip_z_hc)

        # get ms_elapsed and time_stamp
        self.data['time_stamp'], self.data['ms_elapsed'] = convert_epochtime_datetime_mselapsed(self.data.epoch_time)
        # self.data.to_csv('data_out_troughs.csv', index=False)

        # Save the data at the end
        self.datastore.put_data('driftcorrection', self.data, chunk_size=int(os.environ['CHUNK_SIZE']))


def convert_accl_to_ms2(data):
    conversion_factor = 9.80665 / 1000
    data.acc_0_x *= conversion_factor
    data.acc_0_y *= conversion_factor
    data.acc_0_z *= conversion_factor

    data.acc_1_x *= conversion_factor
    data.acc_1_y *= conversion_factor
    data.acc_1_z *= conversion_factor

    data.acc_2_x *= conversion_factor
    data.acc_2_y *= conversion_factor
    data.acc_2_z *= conversion_factor
