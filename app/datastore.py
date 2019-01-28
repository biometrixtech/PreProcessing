from boto3.dynamodb.conditions import Key
from io import StringIO
from shutil import copyfile
import boto3
import datetime
import errno
import glob
import json
import logging
import os
import pandas
import shutil
import tempfile

from utils import format_datetime, json_serialise
from utils.chunk import chunk_by_line
from utils.dynamodb_update import DynamodbUpdate


_logger = logging.getLogger(__name__)

_ddb_table = boto3.resource('dynamodb').Table('preprocessing-{}-ingest-sessions'.format(os.environ["ENVIRONMENT"]))


class Datastore:

    def __init__(self, session_id):
        self._session_id = session_id
        self._metadata = None

        if not os.path.isdir('/net/efs/preprocessing'):
            raise Exception("/net/efs/preprocessing directory does not exist.  Has the EFS filesystem been initialised?")

    def get_metadatum(self, datum, default=NotImplemented):
        if self._metadata is None:
            self._load_metadata_from_ddb()

        if datum not in self._metadata:
            if default == NotImplemented:
                raise KeyError('Key {} not found in metadata'.format(datum))
            else:
                return default

        return self._metadata[datum]

    def put_metadatum(self, datum, value):
        self.put_metadata({datum: value})

    def put_metadata(self, data):
        upsert = DynamodbUpdate()
        for key, value in data.items():
            upsert.set(key, value)

        _logger.debug(json.dumps({
            'UpdateExpression': upsert.update_expression,
            'ExpressionAttributeNames': upsert.parameter_names,
            'ExpressionAttributeValues': upsert.parameter_values,
        }, default=json_serialise))

        if len(upsert.parameter_names) == 0:
            return

        # Update updated_date, if we're updating anything else
        upsert.set('updated_date', format_datetime(datetime.datetime.now()))

        _ddb_table.update_item(
            Key={'id': self.session_id},
            UpdateExpression=upsert.update_expression,
            ExpressionAttributeNames=upsert.parameter_names,
            ExpressionAttributeValues=upsert.parameter_values
        )

    def _load_metadata_from_ddb(self):
        ret = _ddb_table.query(
            Select='ALL_ATTRIBUTES',
            Limit=10000,
            KeyConditionExpression=Key('id').eq(self.session_id),
        )
        if len(ret['Items']) == 0:
            raise ValueError('Could not load metadata for session {} from DynamoDB'.format(self.session_id))
        self._metadata = ret['Items'][0]

    stages = {
        'downloadandchunk': ('chunked', 'binary'),
        'sessionprocess2': ('chunked', 'csv'),
        'scoring': ('combined', 'csv'),
    }

    def get_data(self, source_job, columns=None):
        if isinstance(source_job, tuple):
            source_job, part_number = source_job
        else:
            part_number = None

        if part_number == '*':
            data = self._read_multiple_csv(source_job, columns=columns)
        else:
            data = self._read_single_csv(source_job, part_number, columns=columns)

        return data

    def put_data(self, source_job, data, columns=None, chunk_size=0, is_binary=False):
        if isinstance(source_job, tuple):
            source_job, part_number = source_job
        else:
            part_number = None

        # First save the file to a temporary location
        if isinstance(data, str):
            # In this case, the `data` is actually the temporary filename
            tmp_filename = data
            _logger.debug('Data already saved in temporary file {}'.format(tmp_filename))

        else:
            # Data is a pandas DataFrame object
            tmp_filename = self.get_temporary_filename()
            _logger.debug('Saving dataset (size {}) to {}'.format(data.shape, tmp_filename))
            with open(tmp_filename, 'wb') as tmp_file:
                data.to_csv(tmp_file, index=False, na_rep='', columns=columns)
            _logger.debug('Filesize of {} is {}'.format(tmp_filename, os.path.getsize(tmp_filename)))

        # Now move the file into the correct location
        if chunk_size > 0:
            if part_number is not None:
                raise ValueError('Output of {} is chunked, cannot accept part number'.format(source_job))

            output_dir = os.path.join(self.working_directory, source_job)
            _mkdir(output_dir)

            if is_binary:
                # TODO
                raise NotImplementedError()
            else:
                # TODO
                chunk_by_line(tmp_filename, output_dir, chunk_size)

        else:
            if part_number is not None:
                _mkdir(os.path.join(self.working_directory, source_job))
                output_filename = os.path.join(self.working_directory, source_job, "{:04d}".format(part_number))
            else:
                _mkdir(self.working_directory)
                output_filename = os.path.join(self.working_directory, source_job)
            _logger.debug('Copying {} to {}'.format(tmp_filename, output_filename))
            shutil.copyfile(tmp_filename, output_filename)

    def _read_single_csv(self, source_job, part_number=None, columns=None):
        """
        Read a single CSV file with pandas.  Copy the file to the local filesystem first,
        as that improves read performance.
        :param source_job:
        :return:
        """
        if part_number is not None:
            source_filename = os.path.join(self.working_directory, source_job, "{:04d}".format(part_number))
        else:
            source_filename = os.path.join(self.working_directory, source_job)

        tmp_filename = self.get_temporary_filename()
        copyfile(source_filename, tmp_filename)
        _logger.info("Copied {} to local filesystem {}".format(source_filename, tmp_filename))

        data = pandas.read_csv(tmp_filename, columns=columns)

        os.remove(tmp_filename)
        _logger.info("Removed temporary file")

        return data

    def _read_multiple_csv(self, source_job, columns=None):
        """
        Read multiple CSV files together.  We do this by loading each CSV file into memory,
        concatenating them, and then feeding the array through a StringIO to pandas.read_csv()
        :param source_job:
        :return:
        """
        csv_data = []
        count = 0
        for filename in glob.glob(os.path.join(self.working_directory, source_job, '[0-9]*')):
            _logger.debug('Reading {}'.format(filename))
            with open(filename, 'r') as f:
                lines = f.readlines()
                if count == 0:
                    # Only the first time do we include the CSV column headers
                    csv_data.extend([lines[0]])
                csv_data.extend(lines[1:])
            count += 1

        _logger.info("{} rows".format(len(csv_data) - 1))
        csv_data = u"\n".join(csv_data)
        return pandas.read_csv(StringIO(csv_data), columns=columns)

    @property
    def session_id(self):
        return self._session_id

    @property
    def working_directory(self):
        return os.path.join('/net/efs/preprocessing', self.session_id)

    @staticmethod
    def get_temporary_filename():
        return os.path.join(tempfile.gettempdir(), next(tempfile._get_candidate_names()))


def _mkdir(path):
    """
    Create a directory, but don't fail if it already exists
    :param path:
    """
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
