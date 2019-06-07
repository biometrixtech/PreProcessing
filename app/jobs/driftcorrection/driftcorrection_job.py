from aws_xray_sdk.core import xray_recorder
import logging

from ..job import Job

_logger = logging.getLogger()

SENSOR_SAMPLING_FREQUENCY = 100
FFT_NUM_SAMPLES = 2 ** 10


class DriftcorrectionJob(Job):

    def __init__(self, datastore, sensor):
        self.sensor = sensor
        super().__init__(datastore)

    @xray_recorder.capture('app.jobs.driftcorrection._run')
    def _run(self):

        data = self.datastore.get_data(('transformandplacement', '*'))

        for window in _get_dynamic_windows(data[f'magn_{self.sensor}']):
            window_length = window.stop - window.start
            if window_length < FFT_NUM_SAMPLES:
                _logger.info(f'Dynamic window is too short ({window_length} frames)')
                continue

            peak_indices, trough_indices = self._find_peaks_and_troughs(data, window)

    def _find_peaks_and_troughs(self, data, window):
        peak_indices = []
        trough_indices = []

        # Chunk the dynamic window further into equally-sized blocks, and FFT them
        for i in range(window.start, window.stop, FFT_NUM_SAMPLES):
            chunk = slice(i, i + FFT_NUM_SAMPLES)
            # Ignore the last sub-chunk, which almost certainly won't be the right size to FFT
            if chunk.stop > window.stop:
                continue

            window_data = data[:][chunk]

            normalised_acceleration = _get_normalised_acceleration(window_data)  # TODO

            acceleration_harmonics = _do_fft(normalised_acceleration)  # TODO

            # Find the peaks in the FFT with sufficient magnitude
            is_acceleration_harmonic_peak = (
                (acceleration_harmonics['value'].diff() > 0)
                & (acceleration_harmonics['value'].diff(-1) > 0)
                & acceleration_harmonics['value'] > 100
            )

            if not is_acceleration_harmonic_peak.any():
                _logger.warn(f'No harmonic peaks!')
                continue

            first_harmonic_frequency = is_acceleration_harmonic_peak['frequency'][is_acceleration_harmonic_peak].index[0]
            first_harmonic_value = round(acceleration_harmonics['value'][first_harmonic_frequency] * 2 ** 1.5)
            _logger.info(f'First harmonic peak is at {first_harmonic_frequency}Hz (={first_harmonic_value})')

            peak_indices_sw, trough_indices_sw = _todd_andrews(normalised_acceleration, first_harmonic_frequency, first_harmonic_value)  # TODO
            peak_indices.extend(peak_indices_sw)
            trough_indices.extend(trough_indices_sw)

        return peak_indices, trough_indices


def _todd_andrews(acceleration_data, harmonic_frequency, harmonic_amplitude):
    threshold = harmonic_amplitude / 3
    distance = round(SENSOR_SAMPLING_FREQUENCY / harmonic_frequency * 0.9)

    # Find the first asending or descending phase of the signal
    running_max = (acceleration_data[0], 0)
    running_min = (acceleration_data[0], 0)
    state = 0  # Neither ascending nor descending
    for i in acceleration_data.index:
        value = acceleration_data[i]
        running_max = max(running_max, (value, i))
        running_min = min(running_min, (value, i))
        if value + threshold <= running_max[1]:
            state = -1
            break
        elif value - threshold >= running_min[1]:
            state = +1
            break


def _get_dynamic_windows(data_magn):
    # Find the frames corresponding to the end of dynamic condition windows
    is_start_of_dynamic_window = data_magn.diff() > 0
    is_end_of_dynamic_window = data_magn.diff() < 0

    # Chunk the dataset into 'dynamic condition windows'
    start_index = 0
    count = 0
    for i in range(len(data_magn)):
        if is_end_of_dynamic_window[i]:
            _logger.info(f'Dynamic window #{count} [{start_index}:{i}]')
            count += 1
            yield slice(start_index, i)
        elif is_start_of_dynamic_window[i]:
            start_index = i
