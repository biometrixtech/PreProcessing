# -*- coding: utf-8 -*-
from __future__ import print_function


import os
import sys
import errno
from collections import namedtuple

from .decode_data import read_file
from .get_single_sensor import get_single_sensor_data
from .transform_data import apply_data_transformations
from .runAnalytics import run_session
import columnNames as cols


Config = namedtuple('Config', [
    'AWS',
    'ENVIRONMENT',
])


def mkdir(path):
    """
    Create a directory, but don't fail if it already exists
    :param path:
    """
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def script_handler(working_directory, file_name, data):
    """Comple all the single sensor processing
    """

    print('Received sessionProcess request for {}'.format(file_name))

    try:
        config = Config(
            AWS=False,
            ENVIRONMENT=os.environ['ENVIRONMENT'],
        )
        mkdir(os.path.join(working_directory, 'sessionprocess1'))

        print("STARTED PROCESSING!")

        print("LOADING DATA")
        # read sensor data
        sdata = read_file(os.path.join(working_directory, 'downloadandchunk', file_name))
        if len(sdata) == 0:
            print("Sensor data is empty!", info=False)
            return "Fail!"
        print("DATA LOADED!")

        sdata = get_single_sensor_data(sdata.loc[:, :], data['Placement'][1])
        sdata = apply_data_transformations(sdata, data['BodyFrameTransforms'], data['HipNeutralYaw'])
        
        output_data = run_session(sdata)

        # Prepare data for dumping
        output_data = output_data.replace('None', '')
        output_data = output_data.round(5)

        # Output data
        fileobj = open(os.path.join(os.path.join(working_directory, 'sessionprocess1', file_name)), 'wb')
        output_data.to_csv(fileobj, index=False, na_rep='', columns=cols.column_session1_out)

        # return output_data

    except Exception as e:
        print(e)
        print('Process did not complete successfully! See error below!')
        raise
