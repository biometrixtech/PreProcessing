from decimal import Decimal as _Decimal
import datetime as _datetime
import numpy as np


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
