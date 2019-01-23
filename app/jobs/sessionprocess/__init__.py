from keras.models import load_model
import boto3
import logging
import numpy as np
import os
import pickle

from ..job import Job
from .run_analytics import run_session

_logger = logging.getLogger(__name__)
_s3_client = boto3.client('s3')


class SessionprocessJob(Job):

    def _run(self):

        _logger.info("STARTED PROCESSING!")

        # GRF
        # load model
        grf_fit = _load_model(os.environ['MS_MODEL'])
        grf_fit_lf = _load_model(os.environ['LF_MS_MODEL'])
        grf_fit_rf = _load_model(os.environ['RF_MS_MODEL'])
        sc = _load_scaler(os.environ['MS_SCALER'])
        sc_single_leg = _load_scaler(os.environ['SL_MS_SCALER'])

        _logger.info("LOADING DATA")
        part_number = None  # TODO chunking
        sdata = self.datastore.get_data('transformandplacement', part_number)
        _logger.info("DATA LOADED!")

        if len(sdata) == 0:
            raise Exception('Sensor data is empty!')

        if self.datastore.get_metadatum('version', '2.3') != '1.0':
            self._flag_data_quality(sdata)

        # Read user mass
        mass = self.datastore.get_metadatum('user_mass')

        size = len(sdata)
        sdata['obs_index'] = np.array(range(size)).reshape(-1, 1) + 1

        # Process the data and pass it as argument to run_session as
        file_version = self.datastore.get_metadatum('version')
        hip_n_transform = self.datastore.get_metadatum('hip_n_transform', None)
 
        output_data_batch = run_session(sdata, file_version, mass, grf_fit, grf_fit_lf, grf_fit_rf, sc, sc_single_leg, hip_n_transform)

        # Output data
        output_data_batch = output_data_batch.replace('None', '')
        output_data_batch = output_data_batch.round(5)
        self.datastore.put_data('sessionprocess', output_data_batch)

        _logger.info('Outcome: Success!')

    def _flag_data_quality(self, data):
        big_jump = 30
        baseline_az = np.nanmean(data.loc[0:100, ['acc_lf_z', 'acc_hip_z', 'acc_rf_z']], axis=0).reshape(1, 3)
        diff = data.loc[:, ['acc_lf_z', 'acc_hip_z', 'acc_rf_z']].values - baseline_az
        high_accel = (diff >= big_jump).astype(int)
        for i in range(3):
            if high_accel[0, i] == 1:
                t_b = 1
            else:
                t_b = 0
            absdiff = np.abs(np.ediff1d(high_accel[:, i], to_begin=t_b)).reshape(-1, 1)
            if high_accel[-1, i] == 1:
                absdiff = np.concatenate([absdiff, np.array([[1]])], 0)
            ranges = np.where(absdiff == 1)[0].reshape((-1, 2))
            length = ranges[:, 1] - ranges[:, 0]
            accel_error_count = len(np.where(length > 10)[0])
            if accel_error_count > 5:
                self._send_notification(accel_error_count)
                break

    def _send_notification(self, accel_error_count):
        message = 'Possible acceleration issue with file: {} with {} instances of possible jumps'.format(
            self.datastore.session_id,
            accel_error_count
        )
        subject = 'Accel Data quality: {}'.format(self.datastore.session_id)
        sns_client = boto3.client('sns')
        sns_topic = 'arn:aws:sns:{}:887689817172:preprocessing-{}-dataquality'.format(
            os.environ['AWS_DEFAULT_REGION'],
            os.environ['ENVIRONMENT']
        )
        _logger.debug(sns_topic)
        sns_client.publish(TopicArn=sns_topic, Message=message, Subject=subject)


def _load_model(model):
    path = os.path.join('/net/efs/globalmodels', model)
    _logger.info("Loading model from {}".format(path))
    return load_model(str(path))


def _load_scaler(model):
    path = os.path.join('/net/efs/globalscalers', model)
    _logger.info("Loading scaler from {}".format(path))
    with open(path) as f:
        return pickle.load(f)
