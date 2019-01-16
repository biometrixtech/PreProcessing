from decimal import Decimal as _Decimal
import datetime as _datetime


def format_datetime(date_input):
    """
    Formats a date in ISO8601 short format.
    :param date_input:
    :return: str
    """
    if date_input is None:
        return None
    if not isinstance(date_input, _datetime.datetime):
        for format_string in ["%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ"]:
            try:
                date_input = _datetime.datetime.strptime(date_input, format_string)
                break
            except ValueError:
                continue
        else:
            raise ValueError('Unrecognised datetime format')
    return date_input.strftime("%Y-%m-%dT%H:%M:%SZ")


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
