from io import StringIO
from shutil import copyfile
import errno
import glob
import os
import pandas


class Filestore:

    def __init__(self, sensor_data_filename, logger):
        self._sensor_data_filename = sensor_data_filename
        self._logger = logger

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

    def put_data(self, as_stage, data, columns, part_number=None):
        if as_stage not in self.stages:
            raise ValueError('Unknown stage {}'.format(as_stage))
        plurality, encoding = self.stages[as_stage]

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
                raise ValueError('Output of {} is chunked, must supply a part number'.format(as_stage))

            self._mkdir(os.path.join(self.working_directory, as_stage))
            if part_number == '*':
                # This is the whole file, we need to chunk it
                # TODO
                raise NotImplementedError()
            else:
                os.rename(tmp_filename, os.path.join(self.working_directory, as_stage, part_number))

        else:
            self._mkdir(self.working_directory)
            os.rename(tmp_filename, os.path.join(self.working_directory, as_stage))

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
        self._logger.info("Copied {} to local FS".format(source_filename))
        data = pandas.read_csv(tmp_filename)
        os.remove(tmp_filename)
        self._logger.info("Removed temporary file")
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

        self._logger.info("{} rows".format(len(csv_data) - 1))
        csv_data = u"\n".join(csv_data)
        return StringIO(csv_data)

    @staticmethod
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

    @property
    def sensor_data_filename(self):
        return self._sensor_data_filename

    @property
    def working_directory(self):
        return os.path.join('/net/efs/preprocessing', self.sensor_data_filename)
