import boto3
import copy
import json
import logging
import os
import pandas as pd
import re
import subprocess
import sys

from ..job import Job
from .exceptions import PlacementDetectionException
from .placement_detection import detect_placement, shift_accel
from .sensor_use_detection import detect_single_sensor, detect_data_truncation
from .transform_calculation import compute_transform

_logger = logging.getLogger(__name__)
_s3_client = boto3.client('s3')


class TransformandplacementJob(Job):

    def _run(self):
        if self.datastore.get_metadatum('version') == '1.0':
            ret = {
                'Placement': [0, 1, 2],
                'BodyFrameTransforms': {
                    'Left': [1, 0, 0, 0],
                    'Hip': [1, 0, 0, 0],
                    'Right': [1, 0, 0, 0],
                },
                'HipNeutralYaw': [1, 0, 0, 0],
                'Sensors': 3,
            }
        else:
            ret = self.execute()

        _logger.info(ret)

    def execute(self):
        data = self.datastore.get_data('downloadandchunk')
        data = data.loc[:2000000]

        try:
            # if placement passes without issue, go to multiple sensor processing
            sensors = 3
            data_sub = copy.copy(data.loc[:2000])
            shift_accel(data_sub)
            placement = detect_placement(data_sub)

            # if placement passed, check to see if any sensor fell down or data missing for
            # any of the sensors
            truncated, single_sensor, index = detect_data_truncation(data, placement)

            if truncated:
                if index < 2000:
                    raise PlacementDetectionException('File too short after truncation.')
                else:
                    _logger.info('Data truncated at index: {}'.format(index))
                    tmp_filename = filepath + '_tmp'
                    # truncate combined file at lines where truncation was detected
                    os.system(
                        'head -c {bytes} {filepath} > {truncated_filename}'.format(
                            bytes=index * 40,
                            filepath=filepath,
                            truncated_filename=tmp_filename
                            )
                        )
                    # copy tmp_file to replace the original file
                    os.system('cat {tmp_filename} > {filepath}'.format(
                        tmp_filename=tmp_filename,
                        filepath=filepath))
                    # finally delete temporary file
                    os.remove(tmp_filename)

            elif single_sensor:
                _logger.info('single Sensor')
                sensors = 1

            body_frame_transforms = compute_transform(data_sub, placement, sensors)

            return {
                'Placement': placement,
                'BodyFrameTransforms': {
                    'Left': body_frame_transforms[0],
                    'Hip': body_frame_transforms[1],
                    'Right': body_frame_transforms[2],
                },
                'HipNeutralYaw': body_frame_transforms[3],
                'Sensors': sensors
            }

        except PlacementDetectionException as err:
            _logger.error(err)
            # if it fails, assign a placement, get transform values and go
            # to single sensor processing
            sensors = 1
            # detect the single sensor being used
            # placement = detect_single_sensor(data)
            placement = [0, 1, 2]
            truncated, single_sensor, index = detect_data_truncation(data, placement, sensors)
            if truncated:
                if index <= 2000:
                    raise PlacementDetectionException('File too short after truncation.')
                else:
                    _logger.info('Data truncated at index: {}'.format(index))
                    tmp_filename = filepath + '_tmp'
                    # truncate combined file at lines where truncation was detected
                    os.system(
                        'head -c {bytes} {filepath} > {truncated_filename}'.format(
                            bytes=index * 40,
                            filepath=filepath,
                            truncated_filename=tmp_filename
                            )
                        )
                    # copy tmp_file to replace the original file
                    os.system('cat {tmp_filename} > {filepath}'.format(
                        tmp_filename=tmp_filename,
                        filepath=filepath))
                    # finally delete temporary file
                    os.remove(tmp_filename)

            # get transformation values
            data_sub = copy.copy(data.loc[0:2000, :])
            shift_accel(data_sub)
            body_frame_transforms = compute_transform(data_sub, placement, sensors)

            return {
                'Placement': placement,
                'BodyFrameTransforms': {
                    'Left': body_frame_transforms[0],
                    'Hip': body_frame_transforms[1],
                    'Right': body_frame_transforms[2],
                },
                'HipNeutralYaw': body_frame_transforms[3],
                'Sensors': sensors
            }
