"""
get ms_elapsed and convert epoch_time to timestamp
"""

import datetime
import numpy as np


def get_times(epoch_time):
    """
    Converting epochtime from the sensor data to datetime and milli
    seconds elapsed.

    Args:
        epoch_time: epochtime from the sensor data.

    Returns:
        two arrays.
        dummy_time_stamp: date time
        dummy_time_elapsed: milliseconds elapsed
    """

    dummy_time_stamp = []

    dummy_time_elapsed = np.ediff1d(epoch_time, to_begin=0)
    for i in enumerate(epoch_time):
        dummy_time_stamp.append(datetime.datetime.utcfromtimestamp(np.array(
            epoch_time[i[0]]/1000.)).strftime('%Y-%m-%d %H:%M:%S.%f'))

    return dummy_time_stamp, dummy_time_elapsed
