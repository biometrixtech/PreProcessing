import boto3
import copy
import logging
import os

from ..job import Job
from .apply_data_transformations import apply_data_transformations
from .exceptions import PlacementDetectionException
from .placement_detection import detect_placement, shift_accel
from .sensor_use_detection import detect_single_sensor, detect_data_truncation
from .transform_calculation import compute_transform
from .epoch_time_transform import convert_epochtime_datetime_mselapsed

_logger = logging.getLogger(__name__)
_s3_client = boto3.client('s3')


class TransformandplacementJob(Job):

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

        placement = zip(ret['placement'], ['l', 'h', 'r'])
        column_prefixes = ['magn_', 'corrupt_', 'aX', 'aY', 'aZ', 'qX', 'qY', 'qZ', 'qW']
        for old, new in placement:
            for prefix in column_prefixes:
                data.rename(index=str, columns={prefix + str(old): prefix + str(new)})

        # Apply normalisation transforms
        data = apply_data_transformations(data, ret['body_frame_transforms'], ret['hip_neutral_yaw'])

        # ms_elapsed and datetime
        data.time_stamp, data.ms_elapsed = convert_epochtime_datetime_mselapsed(data.epoch_time)

        self.datastore.put_data('transformandplacement', data, chunk_size=100000)

    def execute(self, all_data):
        data = all_data.loc[:2000000]

        try:
            # if placement passes without issue, go to multiple sensor processing
            sensors = 3
            data_sub = copy.copy(data.loc[:2000])
            shift_accel(data_sub)
            placement = detect_placement(data_sub)

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
            # placement = detect_single_sensor(data)
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
