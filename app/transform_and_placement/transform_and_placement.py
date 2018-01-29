from __future__ import print_function

import logging
import os
import sys

from decode_data import read_file
from placement_detection import detect_placement, shift_accel
from transform_calculation import compute_transform

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def script_handler(working_directory, file_name):

    try:
        filepath = os.path.join(working_directory, 'downloadandchunk', file_name)
        count = 100 * 20
        data = read_file(filepath, count)
        shift_accel(data)

        # try:
        placement = detect_placement(data)
        # except:
            # FIXME
            # placement = [0, 1, 2]

        body_frame_transforms = compute_transform(data, placement)
        print(body_frame_transforms)
        
        return {
            'Placement': placement,
            'BodyFrameTransforms': {
                'Left': body_frame_transforms[0],
                'Hip': body_frame_transforms[1],
                'Right': body_frame_transforms[2],
            },
            'HipNeutralYaw': body_frame_transforms[3]
        }

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise