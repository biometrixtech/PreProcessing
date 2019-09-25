class SensorException(Exception):
    def __init__(self, message="", sensor=0):
        self._message = message
        self._sensor = sensor

    @property
    def message(self):
        return self._message

    @property
    def sensor(self):
        return self._sensor

class PlacementDetectionException(Exception):
    """
    An exception thrown when the sensor placement could not be detected
    """
    pass


class FileVersionNotSupportedException(Exception):
    """
    An exception thrown for old version of the file
    """
    pass


class HeadingDetectionException(SensorException):
    """
    An exception thrown for old version of the file
    """
    pass


class StillDetectionException(SensorException):
    """
    An exception thrown for old version of the file
    """
    pass


class MarchDetectionException(SensorException):
    """
    An exception thrown for old version of the file
    """
    pass


class NoDataException(Exception):
    """
    An exception thrown when there's no data
    """
    pass
