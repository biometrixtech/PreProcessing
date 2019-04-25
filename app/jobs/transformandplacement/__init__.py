from aws_xray_sdk.core import xray_recorder
import boto3
import copy
import logging
import os
import pickle

from ..job import Job
from .apply_data_transformations import apply_data_transformations
from .exceptions import PlacementDetectionException
from .placement_detection import detect_placement, shift_accel, predict_placement
from .sensor_use_detection import detect_single_sensor, detect_data_truncation
from .transform_calculation import compute_transform
from .epoch_time_transform import convert_epochtime_datetime_mselapsed

_logger = logging.getLogger(__name__)
_s3_client = boto3.client('s3')


class TransformandplacementJob(Job):

    @xray_recorder.capture('app.jobs.transformandplacement._run')
    def _run(self):
        data = self.datastore.get_data('downloadandchunk')

        if self.datastore.get_metadatum('version') == '1.0':
            ret = {
                'placement': [0, 1, 2],
                'body_frame_transforms': {
                    'left': [1, 0, 0, 0],
                    'hip': [1, 0, 0, 0],
                    'right': [1, 0, 0, 0],
                },
                'hip_neutral_yaw': [1, 0, 0, 0],
                'sensors': 3,
                'truncation_index': None,
            }
        else:
            ret = self.execute(data)

        _logger.info(ret)
        self.datastore.put_metadata(ret)

        if ret['truncation_index'] is not None:
            data = data.loc[:ret['truncation_index']]

        placement = zip(ret['placement'], ['lf', 'hip', 'rf'])
        column_prefixes = ['magn_{}', 'corrupt_{}', 'acc_{}_x', 'acc_{}_y', 'acc_{}_z', 'quat_{}_x', 'quat_{}_y', 'quat_{}_z', 'quat_{}_w']
        renames = {}
        for old, new in placement:
            for prefix in column_prefixes:
                renames[prefix.format(str(old))] = prefix.format(str(new))

        data = data.rename(index=str, columns=renames)

        # Apply normalisation transforms
        data = apply_data_transformations(data, ret['body_frame_transforms'], ret['hip_neutral_yaw'])

        # ms_elapsed and datetime
        data['time_stamp'], data['ms_elapsed'] = convert_epochtime_datetime_mselapsed(data.epoch_time)

        self.datastore.put_data('transformandplacement', data, chunk_size=100000)

    def execute(self, all_data):
        data = all_data.loc[:2000000]

        try:
            # if placement passes without issue, go to multiple sensor processing
            sensors = 3
            data_sub = copy.copy(data.loc[:2000])
            shift_accel(data_sub)
            # placement = detect_placement(data_sub)
            condition_list = _load_model(os.environ['PLACEMENT_MODEL'])
            placement, left_condition, right_condition = predict_placement(data_sub, condition_list)
            _logger.info(placement, left_condition, right_condition)

            # if placement passed, check to see if any sensor fell down or data missing for
            # any of the sensors
            truncation_index, single_sensor = detect_data_truncation(data, placement)

            if single_sensor:
                _logger.info('single Sensor')
                sensors = 1

            body_frame_transforms = compute_transform(data_sub, placement, sensors)

            return {
                'placement': placement,
                'body_frame_transforms': {
                    'left': body_frame_transforms[0],
                    'hip': body_frame_transforms[1],
                    'right': body_frame_transforms[2],
                },
                'hip_neutral_yaw': body_frame_transforms[3],
                'sensors': sensors,
                'truncation_index': truncation_index,
            }

        except PlacementDetectionException as err:
            _logger.error(err)
            # if it fails, assign a placement, get transform values and go
            # to single sensor processing
            sensors = 1
            # detect the single sensor being used
            placement = [0, 1, 2]
            truncation_index, single_sensor = detect_data_truncation(data, placement, sensors)

            # get transformation values
            data_sub = copy.copy(data.loc[0:2000, :])
            shift_accel(data_sub)
            body_frame_transforms = compute_transform(data_sub, placement, sensors)

            return {
                'placement': placement,
                'body_frame_transforms': {
                    'left': body_frame_transforms[0],
                    'hip': body_frame_transforms[1],
                    'right': body_frame_transforms[2],
                },
                'hip_neutral_yaw': body_frame_transforms[3],
                'sensors': sensors,
                'truncation_index': truncation_index,
            }


@xray_recorder.capture('app.jobs.transformandplacement._load_model')
def _load_model(model):
    path = os.path.join('/net/efs/globalmodels', model)
    # path = os.path.join(model)
    _logger.info("Loading model from {}".format(path))
    with open(path, 'rb') as f:
        return pickle.load(f, encoding='latin1')
