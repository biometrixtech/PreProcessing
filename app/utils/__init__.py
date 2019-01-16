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
