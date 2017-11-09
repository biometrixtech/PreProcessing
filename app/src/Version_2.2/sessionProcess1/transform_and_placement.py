from __future__ import print_function

from collections import namedtuple
import logging
import os
import sys

from decode_data import read_file
from placement_detection import detect_placement
from transform_calculation import compute_transform

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

#Config = namedtuple('Config', [
#    'AWS',
#    'ENVIRONMENT',
#])


def script_handler(working_directory, file_name):
#    logger.info('Running placement and transform on "{}/{}"'.format(file_name))

    try:
        filepath = os.path.join(working_directory, 'downloadandchunk', file_name)
        count = 100 * 60
        data = read_file(filepath, count)
        placement = detect_placement(data)
        qstill = compute_transform(data)
        
        return {'Placement': placement, 'Normalisation': qstill}

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise


if __name__ == '__main__':
#    input_file_name = sys.argv[1]
    input_file_name = 'test_file'
    data, placement, qstill = script_handler(working_directory=None, file_name=input_file_name)
