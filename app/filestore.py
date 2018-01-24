from io import StringIO
from shutil import copyfile
import os

import glob
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

    def get_data(self, from_stage):
        if from_stage not in self.stages:
            raise ValueError('Unknown stage {}'.format(from_stage))
        plurality, encoding = self.stages[from_stage]

        if plurality == 'chunked':
            data = self._read_multiple_csv(from_stage)
        else:
            data = self._read_single_csv(from_stage)

        if encoding == 'binary':
            raise NotImplementedError

        return data

    def _read_single_csv(self, stage):
        """
        Read a single CSV file with pandas.  Copy the file to the local filesystem first,
        as that improves read performance.
        :param stage:
        :return:
        """
        tmp_filename = '/tmp/readfile'
        copyfile(os.path.join(self.working_directory, stage), tmp_filename)
        self._logger.info("Copied data file to local FS")
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

    @property
    def sensor_data_filename(self):
        return self._sensor_data_filename

    @property
    def working_directory(self):
        return os.path.join('/net/efs/preprocessing', self.sensor_data_filename)
