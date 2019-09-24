from aws_xray_sdk.core import xray_recorder
import boto3
import copy
import logging
import numpy as np
# import os
# import pickle

from ..job import Job
from .apply_data_transformations import apply_data_transformations
from .exceptions import FileVersionNotSupportedException, HeadingDetectionException, MarchDetectionException, StillDetectionException, NoDataException
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
            start_march = int(ret['start_march_1'])
            end_march = int(ret['end_march_1'])
            heading_quat_0, heading_quat_2 = heading_foot_finder(data[start_march:end_march, 5:9], data[start_march:end_march, 21:25])
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
            if data.epoch_time[0] - event_date > 20 * 1000:  # need data within 20s of event_date
                raise NoDataException("Start of data is more than 20s from event_date")
            try:
                start_sample = np.where(data.epoch_time > event_date)[0][0]
            except:
                start_sample = 0
            print(start_sample)
            sensors = 3
            data_sub = copy.copy(data.loc[:start_sample + 3500])

            # if start_sample > 100:  # new start procedure
            #     search_samples = {'march_detection_start': start_sample + 500,
            #                       'march_detection_end': start_sample + 3000,
            #                       'samples_before_march': 250}
            # else: # start_sample should be 0 for existing data, use current thresholds
            #     search_samples = {'march_detection_start': 775,
            #                       'march_detection_end': 2000,
            #                       'samples_before_march': 75}
            # print(search_samples)
            # march_still_indices = detect_march_and_still(data_sub, search_samples)
            march_still_indices = detect_march_and_still(data_sub)
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

        except MarchDetectionException as err:
            self.datastore.put_metadata({'failure': 'MARCH_DETECTION',
                                         'failure_sensor': err.sensor})
            raise err
        except StillDetectionException as err:
            self.datastore.put_metadata({'failure': 'STILL_DETECTION',
                                         'failure_sensor': err.sensor})
            raise err
        except NoDataException as err:
            self.datastore.put_metadata({'failure': 'NO_DATA'})
