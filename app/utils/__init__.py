from decimal import Decimal as _Decimal
import datetime as _datetime
import numpy as np
from scipy.signal import butter, filtfilt


def format_datetime(date_input):
    """
    Formats a date in ISO8601 short format.
    :param date_input:
    :return: str
    """
    if date_input is None:
        return None
    if not isinstance(date_input, _datetime.datetime):
        date_input = parse_datetime(str(date_input))
    return date_input.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_datetime(date_input):
    """
    Parse a date in ISO8601 format to a datetime
    :param str date_input:
    :return: datetime
    """
    format_strings = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
    ]
    for format_string in format_strings:
        try:
            return _datetime.datetime.strptime(date_input, format_string)
        except ValueError:
            continue
    else:
        # Try numpy, which can handle nanosecond resolution:
        try:
            return _datetime.datetime.utcfromtimestamp((np.datetime64(date_input) - np.datetime64('1970-01-01T00:00:00Z')) / np.timedelta64(1, 's'))
        except ValueError:
            raise ValueError(f'Unrecognised datetime format "{date_input}"')


def get_epoch_time(time_string):
    """
    convert a date in ISO8601 format to a epoch_time
    :param str time_string:
    :return: int
    """
    if time_string is not None:
        return int(parse_datetime(time_string).replace(tzinfo=_datetime.timezone.utc).timestamp() * 1000)
    else:
        return None


def format_datetime_from_epoch_time(epoch_time):
    try:
        return format_datetime(_datetime.datetime.utcfromtimestamp(epoch_time))
    except ValueError:
        raise ValueError("Make sure epoch_time is in seconds resolution")



def json_serialise(obj):
    """
    JSON serializer for objects not serializable by default json code
    """
    from datetime import datetime
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    if isinstance(obj, _Decimal):
        return float(obj)
    if isinstance(obj, set):
        return list(obj)
    if isinstance(obj, bytes):
        return obj.decode('utf-8')
    raise TypeError("Type {} is not serializable".format(type(obj).__name__))


def filter_data(x, filt='band', lowcut=0.1, highcut=40, fs=97.5, order=4):
    """forward-backward bandpass butterworth filter
    defaults:
        lowcut freq: 0.1
        hicut freq: 20
        sampling rage: 100hz
        order: 4"""
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    if filt == 'low':
        b, a = butter(order, high, btype='low', analog=False)
    elif filt == 'band':
        b, a = butter(order, [low, high], btype='band', analog=False)
    return filtfilt(b, a, x, axis=0)


def get_ranges(col_data, value, return_length=False):
    """
    For a given categorical data, determine start and end index for the given value
    start: index where it first occurs
    end: index after the last occurrence

    Args:
        col_data
        value: int, value to get ranges for
        return_length: boolean, return the length each range
    Returns:
        ranges: 2d array, start and end index for each occurrence of value
        length: array, length of each range
    """

    # determine where column data is the relevant value
    is_value = np.array(np.array(col_data == value).astype(int)).reshape(-1, 1)

    # if data starts with given value, range starts with index 0
    if is_value[0] == 1:
        t_b = 1
    else:
        t_b = 0

    # mark where column data changes to and from the given value
    absdiff = np.abs(np.ediff1d(is_value, to_begin=t_b))

    # handle the closing edge
    # if the data ends with the given value, if it was the only point, ignore the range,
    # else assign the last index as end of range
    if is_value[-1] == 1:
        if absdiff[-1] == 0:
            absdiff[-1] = 1
        else:
            absdiff[-1] = 0
    # get the ranges where values begin and end
    ranges = np.where(absdiff == 1)[0].reshape((-1, 2))

    if return_length:
        length = ranges[:, 1] - ranges[:, 0]
        return ranges, length
    else:
        return ranges
