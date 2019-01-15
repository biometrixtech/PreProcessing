from boto3.dynamodb.conditions import Key
from io import StringIO
from shutil import copyfile
import boto3
import errno
import glob
import logging
import os
import pandas
import sys
import tempfile


_ddb_table = boto3.resource('dynamodb').Table('preprocessing-{}-ingest-sessions'.format(os.environ["ENVIRONMENT"]))

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
_logger = logging.getLogger()
_logger.setLevel(logging.INFO)


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
        # TODO
        raise NotImplementedError

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

    def get_data(self, from_stage, part_number=None):
        if from_stage not in self.stages:
            raise ValueError('Unknown stage {}'.format(from_stage))
        plurality, encoding = self.stages[from_stage]

        if plurality == 'chunked' and part_number is None:
            data = self._read_multiple_csv(from_stage)
        else:
            data = self._read_single_csv(from_stage, part_number)

        if encoding == 'binary':
            # TODO
            raise NotImplementedError()

        return data

    def put_data(self, source_job, data, columns=None, part_number=None):
        if source_job not in self.stages:
            raise ValueError('Unknown stage {}'.format(source_job))
        plurality, encoding = self.stages[source_job]

        # First save the file to a temporary location
        if encoding == 'binary':
            # In this case, the `data` is actually the temporary filename
            tmp_filename = data

        else:
            # Data is a pandas DataFrame object
            tmp_filename = '/tmp/output'
            tmp_file = open('/tmp/output', 'wb')
            data.to_csv(tmp_file, index=False, na_rep='', columns=columns)

        # Now move the file into the correct location
        if plurality == 'chunked':
            if part_number is None:
                raise ValueError('Output of {} is chunked, must supply a part number'.format(source_job))

            _mkdir(os.path.join(self.working_directory, source_job))
            if part_number == '*':
                # This is the whole file, we need to chunk it
                # TODO
                raise NotImplementedError()
            else:
                os.rename(tmp_filename, os.path.join(self.working_directory, source_job, part_number))

        else:
            _mkdir(self.working_directory)
            os.rename(tmp_filename, os.path.join(self.working_directory, source_job))

    def _read_single_csv(self, stage, part_number=None):
        """
        Read a single CSV file with pandas.  Copy the file to the local filesystem first,
        as that improves read performance.
        :param stage:
        :return:
        """
        if part_number is not None:
            source_filename = os.path.join(self.working_directory, stage, part_number)
        else:
            source_filename = os.path.join(self.working_directory, stage)

        tmp_filename = '/tmp/readfile'
        copyfile(source_filename, tmp_filename)
        _logger.info("Copied {} to local FS".format(source_filename))

        data = pandas.read_csv(tmp_filename)

        os.remove(tmp_filename)
        _logger.info("Removed temporary file")

        return data

    def _read_multiple_csv(self, stage):
        """
        Read multiple CSV files together.  We do this by loading each CSV file into memory,
        concatenating them, and then feeding the array through a StringIO to pandas.read_csv()
        :param stage:
        :return:
        """
        # Find all files in the directory
        file_names = []
        for file in glob.glob(os.path.join(self.working_directory, stage, '[0-9]*')):
            print("Found file {}".format(file))
            file_name = os.path.basename(file)
            file_names.append(file_name)

        csv_data = []
        count = 0
        for filename in file_names:
            with open(filename, 'r') as f:
                lines = f.readlines()
                if count == 0:
                    # Only the first time do we include the CSV column headers
                    csv_data.extend([lines[0]])
                csv_data.extend(lines[1:])
            count += 1

        _logger.info("{} rows".format(len(csv_data) - 1))
        csv_data = u"\n".join(csv_data)
        return StringIO(csv_data)

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
