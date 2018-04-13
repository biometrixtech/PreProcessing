# -*- coding: utf-8 -*-
from __future__ import print_function

from collections import namedtuple
from io import StringIO
import os

import runScoring

Config = namedtuple('Config', [
    'AWS',
    'ENVIRONMENT',
])


def script_handler(working_directory, filenames, data):

    print('Received scoring request for {}'.format(", ".join(filenames)))

    try:
        config = Config(
            AWS=False,
            ENVIRONMENT=os.environ['ENVIRONMENT'],
        )

        data_stream = cat_csv_files(
            [os.path.join(working_directory, 'sessionprocess1', f) for f in sorted(filenames)])

        boundaries = runScoring.run_scoring(data_stream, data,
                                            os.path.join(working_directory, 'scoring')
                                           )
        return boundaries

    except Exception as e:
        print(e)
        print('Process did not complete successfully! See error below!')
        raise


def cat_csv_files(filenames):
    csv_data = []
    count = 0
    for filename in filenames:
        with open(filename, 'r') as f:
            lines = f.readlines()
            if count == 0:
                csv_data.extend([lines[0]])
            csv_data.extend(lines[1:])
        count += 1

    print("{} rows".format(len(csv_data) - 1))
    csv_data = u"\n".join(csv_data)
    return StringIO(csv_data)
