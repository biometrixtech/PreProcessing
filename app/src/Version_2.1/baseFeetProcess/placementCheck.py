# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 09:21:40 2016

@author: court
"""


import numpy as np

from errors import ErrorId


def placement_check(left_acc, hip_acc, right_acc):
    
    """Perform quick check of sensor placement based on raw acceleration values,
    relevant for beta test designs.
    
    Args:
        raw acceleration values for three sensors, each comprised of x, y,
        and z components (9 components total).
    
    Returns:
        Booleans representing placement and movement errors:
            bad_left_placement
            bad_hip_placement
            bad_right_placement
            moving

    """

#    # find mean acceleration values across time
#    _left_mean = np.nanmean(left_acc, 0)
#    _hip_mean = np.nanmean(hip_acc, 0)
#    _right_mean = np.nanmean(right_acc, 0)

    # find the maximum acceleration range experienced by each sensor
    _left_diff = np.nanmax(np.nanmax(left_acc, 0) - np.nanmin(left_acc, 0))
    _hip_diff = np.nanmax(np.nanmax(hip_acc, 0) - np.nanmin(hip_acc, 0))
    _right_diff = np.nanmax(np.nanmax(right_acc, 0) - np.nanmin(right_acc, 0))

#    # left x should be pos and y should be neg
#    if _left_mean[0] > 200 and _left_mean[1] < -200 and np.absolute(_left_mean[2]) < 400:
#        bad_left_placement = False
#    else:
#        bad_left_placement = True
#
#    # hip y should be very neg and other axes minimally affected by grav
#    if np.absolute(_hip_mean[0]) < 400 and _hip_mean[1] < -800 and np.absolute(_hip_mean[2]) < 500:
#        bad_hip_placement = False
#    else:
#        bad_hip_placement = True
#
#    # right x should be eg and y should be neg
#    if _right_mean[0] < -200 and _right_mean[1] < -200 and np.absolute(_right_mean[2]) < 400:
#        bad_right_placement = False
#    else:
#        bad_right_placement = True

    # Temporary removal of placement checks (March 13, 2017)
    # TODO(Courtney): Automate placement checks
    bad_left_placement = False
    bad_hip_placement = False
    bad_right_placement = False

    # magnitude of maximum acceleration should always be less than 2 Gs
    if _left_diff > 300 or _hip_diff > 300 or _right_diff > 300:
        moving = True
    else:
        moving = False

    if bad_hip_placement and bad_left_placement and bad_right_placement:
        ind = ErrorId.all_sensors.value
    elif bad_hip_placement and bad_left_placement:
        ind = ErrorId.hip_left.value
    elif bad_hip_placement and bad_right_placement:
        ind = ErrorId.hip_right.value
    elif bad_hip_placement:
        ind = ErrorId.hip.value
    elif bad_left_placement and bad_right_placement:
        ind = ErrorId.left_right.value
    elif bad_left_placement:
        ind = ErrorId.left.value
    elif bad_right_placement:
        ind = ErrorId.right.value
    elif moving:
        ind = ErrorId.movement.value
    else:
        ind = ErrorId.no_error.value
        
    return ind
