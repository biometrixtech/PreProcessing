# -*- coding: utf-8 -*-
"""
Created on Thu Jan 11 16:09:14 2018

@author: court
"""
import boto3
import numpy as np
import numpy.polynomial.polynomial as poly
import os


class DataQuality:

    def __init__(self, session_id):
        self._session_id = session_id

    def run(self, data, transformed):
        if transformed:
            self._check_geom_error(data)
            self._check_timestamp(data)
        else:
            self._flag_data_quality(data)

    def _check_geom_error(self, data):
        LaX = data.LaX
        LaY = data.LaY
        LaZ = data.LaZ
        HaX = data.HaX
        HaY = data.HaY
        HaZ = data.HaZ
        RaX = data.RaX
        RaY = data.RaY
        RaZ = data.RaZ

        window = 50
        degree = 1
        error_count = 0
        acceptable_acc = 5
        error_accel_names = []

        for accel in [LaX, LaY, LaZ, HaX, HaY, HaZ, RaX, RaY, RaZ]:

            results = self._polyfit(np.array(range(window)), self._rolling_window(accel, window), degree)

            offsets = np.abs(np.array(results['polynomial'][0]))
            slopes = np.abs(np.array(results['polynomial'][1]))
            r2_vals = results['determination']

            test_vals = np.zeros(offsets.shape)
            test_vals[(slopes < 0.0002) & (r2_vals > 0.95)] = 1
            test_vals[(test_vals == 1) & (offsets < acceptable_acc)] = 0

            sum_test = sum(test_vals)

            if sum_test != 0:
                error_count += 1
                error_accel_names.append(accel.name)

        if error_count != 0:
            self._send_notification('Potential geometric interpretation error: {} {}'.format(np.unique(error_accel_names), error_count))

    def _check_timestamp(self, data):
        timestamp = data.epoch_time.values.reshape(-1, 1)
        ms_diffs = np.ediff1d(timestamp)
        if np.logical_or(ms_diffs < 6, ms_diffs > 16):
            unexpected_indices = np.where(np.logical_or(ms_diffs < 6, ms_diffs > 16))
            self._send_notification('Timestamp jumps identified at {}'.format(unexpected_indices))

    def _rolling_window(self, a, window):
        shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
        strides = a.strides + (a.strides[-1],)
        return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)

    def _polyfit(self, x, y, degree):
        results = {}
        coeffs = poly.polyfit(x.T, y.T, degree)
        results['polynomial'] = coeffs.tolist()
        yhat = poly.polyval(x, coeffs)
        ybar = (np.sum(y, axis=1) / len(y))
        ssreg = np.sum((yhat.T - ybar).T ** 2, axis=1)
        sstot = np.sum((y.T - ybar).T ** 2, axis=1)
        results['determination'] = 1 - (ssreg / sstot)

        return results

    def _flag_data_quality(self, data):
        big_jump = 30
        baseline_az = np.nanmean(data.loc[0:100, ['LaZ', 'HaZ', 'RaZ']], axis=0).reshape(1, 3)
        diff = data.loc[:, ['LaZ', 'HaZ', 'RaZ']].values - baseline_az
        high_accel = (diff >= big_jump).astype(int)
        for i in range(3):
            if high_accel[0, i] == 1:
                t_b = 1
            else:
                t_b = 0
            absdiff = np.abs(np.ediff1d(high_accel[:, i], to_begin=t_b)).reshape(-1, 1)
            if high_accel[-1, i] == 1:
                absdiff = np.concatenate([absdiff, [1]], 0)
            ranges = np.where(absdiff == 1)[0].reshape((-1, 2))
            length = ranges[:, 1] - ranges[:, 0]
            accel_error_count = len(np.where(length > 10)[0])
            if accel_error_count > 5:
                self._send_notification('Encountered {} acceleration jump errors'.format(accel_error_count))

    def _send_notification(self, message):
        boto3.client('sns').publish(
            TopicArn='arn:aws:sns:{AWS_DEFAULT_REGION}:887689817172:preprocessing-{ENVIRONMENT}-dataquality'.format(**os.environ),
            Message=message,
            Subject='Data quality: {}'.format(self._session_id),
            MessageAttributes={'session_id': {'DataType': 'String', 'StringValue': self._session_id}}
        )
