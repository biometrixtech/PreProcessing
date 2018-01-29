

class NoHistoricalDataException(Exception):
    """
    An exception thrown when there is not enough historical data
    """
    pass


class NotEnoughCMEValuesException(Exception):
    """
    An exception thrown when there is not enough CME values in historical data
    """
    pass
