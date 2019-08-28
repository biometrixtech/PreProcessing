class SensorException(Exception):
    def __init__(self, message, sensor=None):
        self._message = message
        self._sensor = sensor

    @property
    def message(self):
        return self._message

    @property
    def sensor(self):
        return self._sensor


class LeftRightDetectionException(SensorException):
    """
    An exception thrown when the sensor placement could not be detected
    """
    pass


class HipCorrectionException(SensorException):
    """
    An exception thrown when the sensor placement could not be detected
    """
    pass
