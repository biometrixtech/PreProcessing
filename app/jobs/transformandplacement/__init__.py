from aws_xray_sdk.core import xray_recorder
import boto3
import copy
import logging
import numpy as np
# import os
# import pickle

from ..job import Job
from .apply_data_transformations import apply_data_transformations
from .exceptions import PlacementDetectionException, FileVersionNotSupportedException, HeadingDetectionException, MarchDetectionException, StillDetectionException
from .placement_detection import detect_placement, shift_accel, predict_placement
from .column_vector import Condition
from .sensor_use_detection import detect_single_sensor, detect_data_truncation
from .transform_calculation import compute_transform
from .heading_calculation import heading_foot_finder
from .get_march_and_still import detect_march_and_still
from .body_frame_transformation import body_frame_tran
from utils import get_epoch_time

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
        _logger.info(ret)

        data = body_frame_tran(data, ret['reference_quats']['0'], ret['reference_quats']['1'], ret['reference_quats']['2'])
        try:
            heading_quat_0, heading_quat_2 = heading_foot_finder(data[:3000, 5:9], data[:3000, 21:25], int(ret['start_march_1']), int(ret['end_march_1']))
        except HeadingDetectionException as err:
            self.datastore.put_metadata({'failure': 'HEADING_DETECTION',
                                         'failure_sensor': err.sensor})
            raise err
        else:
            ret['heading_quat_0'] = heading_quat_0.tolist()[0]
            ret['heading_quat_2'] = heading_quat_2.tolist()[0]
            _logger.info(ret)
            self.datastore.put_metadata(ret)

            # convert to pandas
            data = self.get_core_data_frame_from_ndarray(data)

            # self.datastore.put_data('transformandplacement', data, chunk_size=int(os.environ['CHUNK_SIZE']))
            self.datastore.put_data('transformandplacement', data)

    def execute(self, all_data):
        data = all_data

        try:
            # if placement passes without issue, go to multiple sensor processing

            event_date = get_epoch_time(self.datastore.get_metadatum('event_date'))
            start_sample = np.where(data.epoch_time > event_date)[0][0]
            print(start_sample)
            sensors = 3
            data_sub = copy.copy(data.loc[:3000])

            march_still_indices = detect_march_and_still(data_sub, start_sample)
            print(march_still_indices)
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
                'heading_quat_hip': ref_quats[3],
                'start_march_0': str(march_still_indices[0]),
                'end_march_0': str(march_still_indices[1]),
                'start_march_1': str(march_still_indices[4]),
                'end_march_1': str(march_still_indices[5]),
                'start_march_2': str(march_still_indices[8]),
                'end_march_2': str(march_still_indices[9]),
                'sensors': sensors
            }

        # except PlacementDetectionException as err:
        #     _logger.error(err)
        #     raise PlacementDetectionException("Could not detect placement")
        except MarchDetectionException as err:
            self.datastore.put_metadata({'failure': 'MARCH_DETECTION',
                                         'failure_sensor': err.sensor})
            raise err
        except StillDetectionException as err:
            self.datastore.put_metadata({'failure': 'STILL_DETECTION',
                                         'failure_sensor': err.sensor})
            raise err