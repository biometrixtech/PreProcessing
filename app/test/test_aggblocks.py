"""Testing functions within activeBlockAgg module
"""
import numpy

from ..activeBlockAgg import agg_blocks


### Tests for _get_ranges() function
def test_ranges():
    """Normal data with two ranges
    """
    col_data = numpy.array([0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0])
    res_data = agg_blocks._get_ranges(col_data, 1)
    expected_output = numpy.array([[3, 6], [8, 10]])

    assert isinstance(res_data, numpy.ndarray)
    assert res_data.shape[0] == 2
    assert numpy.all(res_data == expected_output)

def test_ranges_nodata():
    """No value present
    """
    col_data = numpy.array([0, 0, 0, 0, 0])
    res_data = agg_blocks._get_ranges(col_data, 1)
    assert isinstance(res_data, numpy.ndarray)
    assert res_data.shape[0] == 0

def test_ranges_startonly():
    """Data starts with value
    """
    col_data = numpy.array([1, 0, 0, 0, 0])
    res_data = agg_blocks._get_ranges(col_data, 1)
    expected_output = numpy.array([[0, 1]])
    assert isinstance(res_data, numpy.ndarray)
    assert res_data.shape[0] == 1
    assert numpy.all(res_data == expected_output)

def test_ranges_endonly():
    """Data ends with single value.
    """
    col_data = numpy.array([0, 0, 0, 0, 1])
    res_data = agg_blocks._get_ranges(col_data, 1)
    assert isinstance(res_data, numpy.ndarray)
    assert res_data.shape[0] == 0

def test_ranges_multiple_with_lastedge():
    """Data ends with single value.
    """
    col_data = numpy.array([0, 1, 1, 0, 1])
    res_data = agg_blocks._get_ranges(col_data, 1)
    assert isinstance(res_data, numpy.ndarray)
    assert res_data.shape[0] == 1


### Tests for _contact_duration() function
def test_contact_duration():
    """Normal case left foot has one range, right has two
    """
    lf_phase = numpy.array([3, 1, 1, 1, 3])
    rf_phase = numpy.array([3, 2, 3, 2, 3])
    epoch_time = numpy.array([0, 100, 200, 300, 400])
    active = numpy.array([1, 1, 1, 1, 1])
    lf_ground = [1, 4, 6]
    rf_ground = [2, 5, 7]

    dur_lf = agg_blocks._contact_duration(lf_phase, active, epoch_time, lf_ground)
    dur_rf = agg_blocks._contact_duration(rf_phase, active, epoch_time, rf_ground)
    assert dur_lf == numpy.array([300])
    assert numpy.all(dur_rf == numpy.array([100, 100]))

def test_contact_duration_short():
    """Contact durations present but shorter than the threshold
    """
    lf_phase = numpy.array([3, 1, 1, 1, 3])
    rf_phase = numpy.array([3, 2, 3, 2, 3])
    epoch_time = numpy.array([0, 10, 20, 30, 40])
    active = numpy.array([1, 1, 1, 1, 1])
    lf_ground = [1, 4, 6]
    rf_ground = [2, 5, 7]

    dur_lf = agg_blocks._contact_duration(lf_phase, active, epoch_time, lf_ground)
    dur_rf = agg_blocks._contact_duration(rf_phase, active, epoch_time, rf_ground)
    assert dur_lf.shape[0] == 0
    assert dur_rf.shape[0] == 0

def test_contact_duration_long():
    """Contact durations present but longer than the threshold
    """
    lf_phase = numpy.array([3, 1, 1, 1, 3])
    epoch_time = numpy.array([0, 1000, 2000, 3000, 4000])
    active = numpy.array([1, 1, 1, 1, 1])
    lf_ground = [1, 4, 6]

    dur_lf = agg_blocks._contact_duration(lf_phase, active, epoch_time, lf_ground)
    assert dur_lf.shape[0] == 0

def test_contact_duration_nocontact():
    """Foot always in air.
    """
    lf_phase = numpy.array([3, 3, 3, 3, 3])
    epoch_time = numpy.array([0, 100, 200, 300, 400])
    active = numpy.array([1, 1, 1, 1, 1])
    lf_ground = [1, 4, 6]
    dur_lf = agg_blocks._contact_duration(lf_phase, active, epoch_time, lf_ground)
    assert dur_lf.shape[0] == 0


#class TestDurationStats(object):
### Tests for _get_contact_duration_stats() function
def test_duration_stats():
    """One feet is normal (>5 durations) other has <5 contacts
    """
    record = {}
    length_lf = numpy.array([100, 100, 200, 300, 300])
    length_rf = numpy.array([100, 200])
    record = agg_blocks._get_contact_duration_stats(length_lf, length_rf, record)

    assert record['contactDurationLF'] is not None
    assert record['contactDurationLFStd'] is not None
    assert record['contactDurationLF5'] is not None
    assert record['contactDurationLF50'] is not None
    assert record['contactDurationLF95'] is not None

    assert record['contactDurationRF'] is not None
    assert record['contactDurationRFStd'] is None
    assert record['contactDurationRF5'] is not None
    assert record['contactDurationRF50'] is not None
    assert record['contactDurationRF95'] is not None

def test_duration_stats_empty():
    """One of the feet has no contact duration
    """
    record = {}
    length_lf = numpy.array([])
    length_rf = numpy.array([200])
    record = agg_blocks._get_contact_duration_stats(length_lf, length_rf, record)

    assert record['contactDurationLF'] is None
    assert record['contactDurationLFStd'] is None
    assert record['contactDurationLF5'] is None
    assert record['contactDurationLF50'] is None
    assert record['contactDurationLF95'] is None

    assert record['contactDurationRF'] is None
    assert record['contactDurationRFStd'] is None
    assert record['contactDurationRF5'] is None
    assert record['contactDurationRF50'] is None
    assert record['contactDurationRF95'] is None

def test_duration_stats_below_five():
    """both left and right feet have less than 5 duration (>0)
    """
    record = {}
    length_lf = numpy.array([100])
    length_rf = numpy.array([100, 200])
    record = agg_blocks._get_contact_duration_stats(length_lf, length_rf, record)

    assert record['contactDurationLF'] == 100
    assert record['contactDurationLFStd'] is None
    assert record['contactDurationLF5'] == 100
    assert record['contactDurationLF50'] == 100
    assert record['contactDurationLF95'] == 100

    assert record['contactDurationRF'] == 150
    assert record['contactDurationRFStd'] is None
    assert record['contactDurationRF5'] == 100
    assert record['contactDurationRF50'] == 150
    assert record['contactDurationRF95'] == 100


### Tests for _peak_grf() function
### threshold in normalized grf for peak detection is 1.686
def test_peak_grf():
    """grf has two peaks right foot is always in air and left is "impacting"
    left should have two peaks and no peaks for right foot
    """
    total_grf = numpy.array([1.5, 1.6, 1.7, 1.8, 1.9, 1.8, 1.7, 1.9, 1.8])
    phase_lf = numpy.array([4, 4, 4, 4, 4, 4, 4, 4, 4])
    phase_rf = numpy.array([1, 1, 1, 1, 1, 1, 1, 1, 1])
    peak_grf_lf, peak_grf_rf = agg_blocks._peak_grf(total_grf,
                                                    phase_lf,
                                                    phase_rf)
    assert len(peak_grf_lf) == 2
    assert numpy.all(peak_grf_lf == numpy.array([1.9, 1.9]))
    assert len(peak_grf_rf) == 0

def test_peak_grf_nopeaks():
    """peaks in grf are not below threshold
    """
    total_grf = numpy.array([1., 1.3, 1.5, 1.3, 1.1, .95, 1, 1., 1.])
    phase_lf = numpy.array([4, 4, 4, 4, 4, 4, 4, 4, 4])
    phase_rf = numpy.array([1, 1, 1, 1, 1, 1, 1, 1, 1])
    peak_grf_lf, peak_grf_rf = agg_blocks._peak_grf(total_grf,
                                                    phase_lf,
                                                    phase_rf)
    assert len(peak_grf_lf) == 0
    assert len(peak_grf_rf) == 0

def test_peak_grf_flat():
    """Grf is flat above threshold
    """
    total_grf = numpy.array([2., 2., 2., 2., 2., 2., 2., 2., 2.])
    phase_lf = numpy.array([4, 4, 4, 4, 4, 4, 4, 4, 4])
    phase_rf = numpy.array([1, 1, 1, 1, 1, 1, 1, 1, 1])
    peak_grf_lf, peak_grf_rf = agg_blocks._peak_grf(total_grf,
                                                    phase_lf,
                                                    phase_rf)
    assert len(peak_grf_lf) == 0
    assert len(peak_grf_rf) == 0


#class TestPeakGRFStats(object):
def test_peakgrf_stats():
    """ Left should have all stats, right should have everything but std
    """
    record = {}
    peak_grf_lf = numpy.array([1.8, 1.8, 2.3, 2.6, 2.3])
    peak_grf_rf = numpy.array([1.97, 2.5])
    record = agg_blocks._get_peak_grf_stats(peak_grf_lf, peak_grf_rf, record)
    assert record['peakGrfLF'] is not None
    assert record['peakGrfLFStd'] is not None
    assert record['peakGrfLF5'] is not None
    assert record['peakGrfLF50'] is not None
    assert record['peakGrfLF75'] is not None
    assert record['peakGrfLF95'] is not None
    assert record['peakGrfLF99'] is not None
    assert record['peakGrfLFMax'] is not None

    assert record['peakGrfRF'] is not None
    assert record['peakGrfRFStd'] is None
    assert record['peakGrfRF5'] is not None
    assert record['peakGrfRF50'] is not None
    assert record['peakGrfRF75'] is not None
    assert record['peakGrfRF95'] is not None
    assert record['peakGrfRF99'] is not None
    assert record['peakGrfRFMax'] is not None

def test_peakgrf_stats_empty():
    """ all records should be NULL
    """
    record = {}
    peak_grf_lf = numpy.array([])
    peak_grf_rf = numpy.array([2])
    record = agg_blocks._get_peak_grf_stats(peak_grf_lf, peak_grf_rf, record)

    assert record['peakGrfLF'] is None
    assert record['peakGrfLFStd'] is None
    assert record['peakGrfLF5'] is None
    assert record['peakGrfLF50'] is None
    assert record['peakGrfLF75'] is None
    assert record['peakGrfLF95'] is None
    assert record['peakGrfLF99'] is None
    assert record['peakGrfLFMax'] is None

    assert record['peakGrfRF'] is None
    assert record['peakGrfRFStd'] is None
    assert record['peakGrfRF5'] is None
    assert record['peakGrfRF50'] is None
    assert record['peakGrfRF75'] is None
    assert record['peakGrfRF95'] is None
    assert record['peakGrfRF99'] is None
    assert record['peakGrfRFMax'] is None

def test_peakgrf_stats_below_five():
    """both should have everything but std
    """
    record = {}
    peak_grf_lf = numpy.array([1.8])
    peak_grf_rf = numpy.array([1.8, 2.0])
    record = agg_blocks._get_peak_grf_stats(peak_grf_lf, peak_grf_rf, record)

    assert record['peakGrfLF'] is not None
    assert record['peakGrfLFStd'] is None
    assert record['peakGrfLF5'] is not None
    assert record['peakGrfLF50'] is not None
    assert record['peakGrfLF75'] is not None
    assert record['peakGrfLF95'] is not None
    assert record['peakGrfLF99'] is not None
    assert record['peakGrfLFMax'] is not None

    assert record['peakGrfRF'] is not None
    assert record['peakGrfRFStd'] is None
    assert record['peakGrfRF5'] is not None
    assert record['peakGrfRF50'] is not None
    assert record['peakGrfRF75'] is not None
    assert record['peakGrfRF95'] is not None
    assert record['peakGrfRF99'] is not None
    assert record['peakGrfRFMax'] is not None
