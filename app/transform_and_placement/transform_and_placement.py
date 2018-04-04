from __future__ import print_function

import logging
import os
import sys
import copy

import numpy as np

from decode_data import read_file
from placement_detection import detect_placement, shift_accel
from transform_calculation import compute_transform
from single_sensor_detection import detect_used_sensor, check_long_inactivity
from exceptions import PlacementDetectionException

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def script_handler(working_directory, file_name):

    try:
        filepath = os.path.join(working_directory, 'downloadandchunk', file_name)
        count = 100 * 20
        count = 2000000
        data = read_file(filepath, count)
        plot_accel(data)

        try:
            # if placement passes without issue, go to multiple sensor processing
            data_sub = copy.copy(data.loc[:2000])
            shift_accel(data_sub)
            placement = detect_placement(data_sub)

            # TODO add better detection of sensor not being used
#            accel0 = np.sqrt(data.aX0**2 + data.aY0**2 + data.aZ0**2)
#            accel1 = np.sqrt(data.aX1**2 + data.aY1**2 + data.aZ1**2)
#            accel2 = np.sqrt(data.aX2**2 + data.aY2**2 + data.aZ2**2)

#            sensor0, mov0 = check_long_inactivity(accel0, win=48000)
#            sensor1, mov1 = check_long_inactivity(accel1, win=48000)
#            sensor2, mov2 = check_long_inactivity(accel2, win=48000)
#            print(mov0, mov1, mov2)
#            if sum([sensor0, sensor1, sensor2]) == 0:
#                sensors = 3
#            else:
#                sensors = 1
            sensors = 3
            body_frame_transforms = compute_transform(data_sub, placement)

            return {
                'Placement': placement,
                'BodyFrameTransforms': {
                    'Left': body_frame_transforms[0],
                    'Hip': body_frame_transforms[1],
                    'Right': body_frame_transforms[2],
                },
                'HipNeutralYaw': body_frame_transforms[3],
                'Sensors' : sensors
            }

        except PlacementDetectionException as err:
            # if it fails, assign a placement, get transform values and go
            # to single sensor processing
            print(err)
            sensors = 1
            placement = detect_used_sensor(data)
            data_sub = copy.copy(data.loc[0:2000, :])
#        finally:
            shift_accel(data_sub)
            body_frame_transforms = compute_transform(data_sub, placement)

            return {
                'Placement': placement,
                'BodyFrameTransforms': {
                    'Left': body_frame_transforms[0],
                    'Hip': body_frame_transforms[1],
                    'Right': body_frame_transforms[2],
                },
                'HipNeutralYaw': body_frame_transforms[3],
                'Sensors' : sensors
            }

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise
        
def plot_accel(data):
    import matplotlib.pyplot as plt
    plt.plot(data.aZ0)
    plt.plot(data.aZ1)
    plt.plot(data.aZ2)
