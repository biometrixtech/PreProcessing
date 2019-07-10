from aws_xray_sdk.core import xray_recorder
import boto3
import copy
import logging
import os
# import pickle

from ..job import Job
from .apply_data_transformations import apply_data_transformations
from .exceptions import PlacementDetectionException, FileVersionNotSupportedException
from .placement_detection import detect_placement, shift_accel, predict_placement
from .column_vector import Condition
from .sensor_use_detection import detect_single_sensor, detect_data_truncation
from .transform_calculation import compute_transform, heading_foot_finder
from .get_march_and_still import detect_march_and_still
from .epoch_time_transform import convert_epochtime_datetime_mselapsed
from .body_frame_transformation import body_frame_tran

_logger = logging.getLogger(__name__)
_s3_client = boto3.client('s3')


class TransformandplacementJob(Job):

    @xray_recorder.capture('app.jobs.transformandplacement._run')
    def _run(self):
        data = self.datastore.get_data('downloadandchunk')

        if self.datastore.get_metadatum('version') == '1.0':
            raise FileVersionNotSupportedException("File version is not supported!")
        else:
            ret = self.execute(data)
        # self.datastore.put_metadata(ret)

        # if ret['truncation_index'] is not None:
        #     data = data.loc[:ret['truncation_index']]

        # placement = zip(ret['placement'], ['lf', 'hip', 'rf'])
        # column_prefixes = ['magn_{}', 'corrupt_{}', 'acc_{}_x', 'acc_{}_y', 'acc_{}_z', 'quat_{}_x', 'quat_{}_y', 'quat_{}_z', 'quat_{}_w']
        # renames = {}
        # for old, new in placement:
        #     for prefix in column_prefixes:
        #         renames[prefix.format(str(old))] = prefix.format(str(new))

        # data = data.rename(index=str, columns=renames)

        # Apply normalisation transforms
        # data = apply_data_transformations(data, ret['body_frame_transforms'], ret['hip_neutral_yaw'], ret['sensor_position'])

        data = body_frame_tran(data, ret['reference_quats']['0'], ret['reference_quats']['1'], ret['reference_quats']['2'])
        heading_quat_0, heading_quat_2 = heading_foot_finder(data[:3000, 5:9], data[:3000, 21:25], ret['start_march_1'], ret['end_march_1'])
        ret['heading_quat_0'] = heading_quat_0
        ret['heading_quat_2'] = heading_quat_2
        _logger.info(ret)
        self.datastore.put_metadata(ret)

        # convert to pandas
        data = self.get_core_data_frame_from_ndarray(data)

        # ms_elapsed and datetime
        data['time_stamp'], data['ms_elapsed'] = convert_epochtime_datetime_mselapsed(data.epoch_time)

        self.datastore.put_data('transformandplacement', data, chunk_size=int(os.environ['CHUNK_SIZE']))

    def execute(self, all_data):
        data = all_data

        try:
            # if placement passes without issue, go to multiple sensor processing
            sensors = 3
            data_sub = copy.copy(data.loc[:2000])

            march_still_indices = detect_march_and_still(data_sub)
            ref_quats = compute_transform(data_sub,
                                          march_still_indices[2],
                                          march_still_indices[3],
                                          march_still_indices[6],
                                          march_still_indices[7],
                                          march_still_indices[10],
                                          march_still_indices[11]
                                          )

            return {
                'reference_quats': {
                    '0': ref_quats[0],
                    '1': ref_quats[1],
                    '2': ref_quats[2],
                },
                'hip_heading_quat': ref_quats[3],
                'start_march_0': str(march_still_indices[0]),
                'end_march_0': str(march_still_indices[1]),
                'start_march_1': str(march_still_indices[4]),
                'end_march_1': str(march_still_indices[5]),
                'start_march_2': str(march_still_indices[8]),
                'end_march_2': str(march_still_indices[9]),
                'sensors': sensors
            }

        except PlacementDetectionException as err:
            _logger.error(err)
            raise PlacementDetectionException("Could not detect placement")
            # if it fails, assign a placement, get transform values and go
            # to single sensor processing
            # sensors = 1
            # # detect the single sensor being used
            # placement = [0, 1, 2]
            # truncation_index, single_sensor = detect_data_truncation(data, placement, sensors)

            # # get transformation values
            # data_sub = copy.copy(data.loc[0:2000, :])
            # shift_accel(data_sub)
            # body_frame_transforms = compute_transform(data_sub)

            # return {
            #     'placement': placement,
            #     'body_frame_transforms': {
            #         'left': body_frame_transforms[0],
            #         'hip': body_frame_transforms[1],
            #         'right': body_frame_transforms[2],
            #     },
            #     'hip_neutral_yaw': body_frame_transforms[3],
            #     'sensors': sensors,
            #     'truncation_index': truncation_index,
            #     'sensor_position': {'left': 'single_sensor', 'right': 'single_sensor'}
            # }


# @xray_recorder.capture('app.jobs.transformandplacement._load_model')
# def _load_model(model):
#     path = os.path.join('/net/efs/globalmodels', model)
#     _logger.info("Loading model from {}".format(path))
#     with open(path, 'rb') as f:
#         return pickle.load(f, encoding='latin1')
