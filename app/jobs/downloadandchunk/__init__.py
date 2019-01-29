from aws_xray_sdk.core import xray_recorder
import boto3
import hashlib
import json
import logging
import os
import pandas as pd
import re
import subprocess
import sys

from ..job import Job
from .decode_data import read_file

_logger = logging.getLogger(__name__)
_s3_client = boto3.client('s3')


class DownloadandchunkJob(Job):

    @xray_recorder.capture('app.jobs.downloadandchunk._run')
    def _run(self):
        s3_files = self.datastore.get_metadatum('s3_files', None) or self.datastore.get_metadatum('s3Files')
        s3_files.remove('_empty')  # Placeholder list entry
        _logger.info(s3_files)

        if len(s3_files) == 0:
            raise Exception('There are no uploaded chunks for session {}'.format(self.datastore.session_id))

        # Compare the hashes of each chunk to eliminate duplicate files
        files_by_hash = {}

        # Download file
        s3_bucket = 'biometrix-preprocessing-{}-{}'.format(os.environ['ENVIRONMENT'], os.environ['AWS_DEFAULT_REGION'])
        for s3_key in s3_files:

            tmp_filename = self.datastore.get_temporary_filename()
            _s3_client.download_file(s3_bucket, s3_key, tmp_filename)

            with open(tmp_filename, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).digest().encode('hex')
            files_by_hash.setdefault(file_hash, []).append((s3_key, tmp_filename))

            _logger.debug('Downloaded "s3://{}/{}", which has hash {}, to {}'.format(s3_bucket, s3_key, file_hash, tmp_filename))

        # Keep only the first file exhibiting each hash, and sort by upload timestamp
        s3_files = sorted([sorted(files)[0] for files in files_by_hash.values()])

        _logger.debug(json.dumps(s3_files))

        # Concatenate the chunks together
        concat_filename = self.datastore.get_temporary_filename()
        _logger.info('Concatenating {} chunks to {}'.format(len(s3_files), concat_filename))

        for (s3_filename, local_filename) in s3_files:
            subprocess.check_call('cat {} >> {}'.format(local_filename, concat_filename), shell=True)

        # Decode the raw data
        if self.datastore.get_metadatum('version', '2.3') == '1.0':
            data = pd.read_csv(concat_filename)
        else:
            data = read_file(concat_filename)
            if len(data) == 0:
                raise Exception("Sensor data is empty!")
            _logger.info("Decoded data")

        # Save to datastore
        self.datastore.put_data(self.name, data)

        # Upload combined, undecoded file back to s3
        combined_s3_key = self.datastore.session_id + '_combined'
        _logger.debug('Uploading combined file to "s3://biometrix-decode/{}",'.format(s3_bucket, combined_s3_key))
        _s3_client.upload_file(concat_filename, 'biometrix-decode', combined_s3_key)
