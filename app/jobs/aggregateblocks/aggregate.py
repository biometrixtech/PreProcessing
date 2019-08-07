from collections import OrderedDict
import copy
import numpy as np
import pandas as pd

from utils.detect_peaks import detect_peaks
from utils import get_ranges


def aggregate(data, record, mass, agg_level):
    """Aggregates different variables for block/unitBlocks
    """
    data.reset_index(drop=True, inplace=True)
    lf_only_grf = np.sum(data['lf_only_grf'])
    rf_only_grf = np.sum(data['rf_only_grf'])

    lf_rf_grf = lf_only_grf + rf_only_grf

    # grf aggregation
    if lf_only_grf == 0. or np.isnan(lf_only_grf) or rf_only_grf == 0. or np.isnan(rf_only_grf):
        # if there's not enough data for left or right only grf, pass Null for relevant variables do not update perc_optimal
        perc_distr = None
        perc_left_grf = None
        perc_right_grf = None
    else:
        # compute perc_distr and update perc_optimal with perc_distr
        perc_left_grf = lf_only_grf / lf_rf_grf * 100
        perc_right_grf = rf_only_grf / lf_rf_grf * 100
        perc_distr = np.abs(perc_left_grf - perc_right_grf)

        # update perc_optimal to take into account grf distribution
        # perc_optimal_block = (2. * perc_optimal_block + (1. - perc_distr / 100.) ** 2) / 3.
    # GRF aggregation
    record['duration'] = (data['epoch_time'].values[-1] - data['epoch_time'].values[0]) / 1000.
    record['totalGRF'] = np.sum(data['total_grf'])
    record['totalGRFAvg'] = record['totalGRF'] / np.sum(data['total_ind']) * 1000000. / mass / 9.807
    # record['optimalGRF'] = perc_optimal_block * record['totalGRF']
    # record['irregularGRF'] = (1. - perc_optimal_block) * record['totalGRF']
    record['LFgRF'] = np.sum(data['lf_grf'])
    record['RFgRF'] = np.sum(data['rf_grf'])
    record['leftGRF'] = np.sum(data['lf_only_grf'])
    record['rightGRF'] = np.sum(data['rf_only_grf'])
    record['singleLegGRF'] = lf_rf_grf
    record['percLeftGRF'] = perc_left_grf
    record['percRightGRF'] = perc_right_grf
    record['percLRGRFDiff'] = perc_distr

    # accel aggregation
    record['totalAccel'] = np.nansum(data['total_accel'])
    record['totalAccelAvg'] = _peak_accel(data['total_accel'].values)

    length_lf, range_lf = _contact_duration(data.phase_lf.values,
                                            data.active.values,
                                            data.epoch_time.values,
                                            ground_phases=[2, 3])
    length_rf, range_rf = _contact_duration(data.phase_rf.values,
                                            data.active.values,
                                            data.epoch_time.values,
                                            ground_phases=[2, 3])

    record = _get_stats(length_lf, length_rf, 'contactDuration', record)

    if agg_level == 'unit_blocks':
        steps_lf = _step_data(data, range_lf, mass, 'LF')
        record['stepsLF'] = steps_lf

        steps_rf = _step_data(data, range_rf, mass, 'RF')
        record['stepsRF'] = steps_rf
    else:
        record['stepsLF'] = None
        record['stepsRF'] = None

    # normalize grf by user's mass and remove scaling
    grf = data.total_grf.values * 1000000. / mass / 9.807
    # peak grf
    peak_grf, peak_grf_lf, peak_grf_rf = _peak_grf(grf,
                                                   data.phase_lf.values,
                                                   data.phase_rf.values)
    record['totalGRF'] = np.sum(peak_grf)
    record['totalGRFAvg'] = np.mean(peak_grf)

    record = _get_peak_grf_stats(peak_grf_lf, peak_grf_rf, record)

    (
        peak_grf_contact_lf,
        peak_grf_impact_lf,
        peak_grf_perc_impact_lf
    ) = _contact_duration_peak_grf(grf,
                                   range_lf,
                                   data.epoch_time.values)

    (
        peak_grf_contact_rf,
        peak_grf_impact_rf,
        peak_grf_perc_impact_rf
    ) = _contact_duration_peak_grf(grf,
                                   range_rf,
                                   data.epoch_time.values)

    record = _get_stats(peak_grf_contact_lf, peak_grf_contact_rf, 'peakGrfContactDuration', record)
    record = _get_stats(peak_grf_impact_lf, peak_grf_impact_rf, 'peakGrfImpactDuration', record)
    record = _get_stats(peak_grf_perc_impact_lf, peak_grf_perc_impact_rf, 'peakGrfPercImpactDuration', record)

    return record


def _step_data(data, ranges, mass, sensor):
    """get linear combination of peak_grf and ground contact time
    """

    steps = []
    # counter = 0
    for range_gc in ranges:
        step_record = OrderedDict()
        step_data = data.loc[range_gc[0]:range_gc[1] - 1, :]
        # if np.all(np.unique(step_data['phase_' + sensor.lower()]) == np.array([0.])):
        #     continue

        contact_duration = float(data.epoch_time[range_gc[1] - 1] - data.epoch_time[range_gc[0]])

        step_start = str(pd.to_datetime(data.epoch_time[range_gc[0]], unit='ms'))

        step_end = str(pd.to_datetime(data.epoch_time[range_gc[1]], unit='ms'))
        step_record['startTime'] = step_start
        step_record['endTime'] = step_end
        step_record['duration'] = contact_duration / 1000.
        step_record['totalGRF'] = np.sum(step_data['total_grf'])
        step_record['totalGRFAvg'] = step_record['totalGRF'] / np.sum(
            step_data['total_ind']) * 1000000. / mass / 9.807

        # accel aggregation
        step_record['totalAccel'] = np.nansum(step_data['total_accel'])
        step_record['totalAccelAvg'] = _peak_accel(step_data['total_accel'].values, mph=5., mpd=1, steps=True)

        mph = 1.2
        grf_sub = data.grf[range_gc[0]:range_gc[1]].values
        norm_grf = grf_sub * 1000000. / mass / 9.807
        peak_indices = detect_peaks(norm_grf, mph=mph, mpd=1)
        if len(peak_indices) != 0:
            peak_grfs = norm_grf[peak_indices]
            peak_index = peak_indices[np.where(np.max(peak_grfs))[0]]
            peak_grf = norm_grf[peak_index]
            ratio = peak_grf / contact_duration * 1000.
            step_record['peakGRF'] = peak_grf[0]
            step_record['peakGrfContactDuration' + sensor] = ratio[0]
            peak_grf = peak_grf - data.grf[max([range_gc[0] - 1, 0])] * 1000000. / mass / 9.807
            if peak_grf > 0.0:
                length_impact = step_data.epoch_time[range_gc[0] + peak_index] - step_data.epoch_time[range_gc[0]]
                perc_impact = length_impact.values / contact_duration
                ratio_impact = peak_grf / length_impact.values * 1000.
                ratio_perc_impact = peak_grf / perc_impact
                step_record['peakGrfImpactDuration' + sensor] = ratio_impact[0]
                step_record['peakGrfPercImpactDuration' + sensor] = ratio_perc_impact[0]
            else:
                step_record['peakGrfImpactDuration' + sensor] = None
                step_record['peakGrfPercImpactDuration' + sensor] = None
        else:
            step_record['peakGRF'] = None
            step_record['peakGrfContactDuration' + sensor] = None
            step_record['peakGrfImpactDuration' + sensor] = None
            step_record['peakGrfPercImpactDuration' + sensor] = None


        apt_range, apt_rate = get_apt_cme(step_data.euler_hip_y.values, step_data.euler_hip_y_diff.values)
        step_record['anteriorPelvicTiltRange'] = apt_range
        step_record['anteriorPelvicTiltRate'] = apt_rate

        adduc_rom = np.nanmean(step_data['adduc_range_of_motion_' + sensor.lower()])
        adduc_motion_covered_abs = np.nanmean(step_data['adduc_motion_covered_abs_' + sensor.lower()])
        adduc_motion_covered_pos = np.nanmean(step_data['adduc_motion_covered_pos_' + sensor.lower()])
        adduc_motion_covered_neg = np.nanmean(step_data['adduc_motion_covered_neg_' + sensor.lower()])
        flex_rom = np.nanmean(step_data['flex_range_of_motion_' + sensor.lower()])
        flex_motion_covered_abs = np.nanmean(step_data['flex_motion_covered_abs_' + sensor.lower()])
        flex_motion_covered_pos = np.nanmean(step_data['flex_motion_covered_pos_' + sensor.lower()])
        flex_motion_covered_neg = np.nanmean(step_data['flex_motion_covered_neg_' + sensor.lower()])

        adduc_rom_hip = np.nanmean(step_data['adduc_range_of_motion_h'])
        adduc_motion_covered_abs_hip = np.nanmean(step_data['adduc_motion_covered_abs_h'])
        adduc_motion_covered_pos_hip = np.nanmean(step_data['adduc_motion_covered_pos_h'])
        adduc_motion_covered_neg_hip = np.nanmean(step_data['adduc_motion_covered_neg_h'])
        flex_rom_hip = np.nanmean(step_data['flex_range_of_motion_h'])
        flex_motion_covered_abs_hip = np.nanmean(step_data['flex_motion_covered_abs_h'])
        flex_motion_covered_pos_hip = np.nanmean(step_data['flex_motion_covered_pos_h'])
        flex_motion_covered_neg_hip = np.nanmean(step_data['flex_motion_covered_neg_h'])

        step_record['adducROM' + sensor] = adduc_rom
        step_record['adducMotionCoveredTotal' + sensor] = adduc_motion_covered_abs
        step_record['adducMotionCoveredPos' + sensor] = adduc_motion_covered_pos
        step_record['adducMotionCoveredNeg' + sensor] = adduc_motion_covered_neg
        step_record['flexROM' + sensor] = flex_rom
        step_record['flexMotionCoveredTotal' + sensor] = flex_motion_covered_abs
        step_record['flexMotionCoveredPos' + sensor] = flex_motion_covered_pos
        step_record['flexMotionCoveredNeg' + sensor] = flex_motion_covered_neg
        step_record['contactDuration' + sensor] = contact_duration

        step_record['adducROMHip'] = adduc_rom_hip
        step_record['adducMotionCoveredTotalHip'] = adduc_motion_covered_abs_hip
        step_record['adducMotionCoveredPosHip'] = adduc_motion_covered_pos_hip
        step_record['adducMotionCoveredNegHip'] = adduc_motion_covered_neg_hip
        step_record['flexROMHip'] = flex_rom_hip
        step_record['flexMotionCoveredTotalHip'] = flex_motion_covered_abs_hip
        step_record['flexMotionCoveredPosHip'] = flex_motion_covered_pos_hip
        step_record['flexMotionCoveredNegHip'] = flex_motion_covered_neg_hip
        step_record['stance'] = list(step_data['stance'].values)
        stance = np.unique(step_record['stance'])
        if len(stance) > 1:
            if np.all(stance == np.array([2., 3.])):
                if sensor == 'LF':
                    rf_air = np.where(step_data.phase_rf.values == 1)[0]
                    if len(rf_air) <= 2:
                        step_record['stance'] = [3.] * len(step_data)
                    else:
                        step_record['stance'] = [0.] * len(step_data)
                if sensor == 'RF':
                    lf_air = np.where(step_data.phase_lf.values == 1)[0]
                    if len(lf_air) <= 2:
                        step_record['stance'] = [3.] * len(step_data)
                    else:
                        step_record['stance'] = [0.] * len(step_data)
            elif np.all(stance == np.array([2., 6.])):
                continue
            elif np.all(stance == np.array([3., 6.])):
                continue
            elif np.all(stance == np.array([2., 4.])):
                step_record['stance'] = [2.] * len(step_data)
            elif np.all(stance == np.array([3., 5.])):
                step_record['stance'] = [3.] * len(step_data)
        steps.append(step_record)

    return steps


def get_apt_cme(euler_hip_y, euler_hip_y_diff):
    half = int(len(euler_hip_y) / 2)
    max_index = np.where(euler_hip_y[half:] == max(euler_hip_y[half:]))[0][0] + half
    euler_y_step_diff = euler_hip_y_diff[:max_index]
    if len(euler_y_step_diff) == 0:
        return None, None
    minima = np.where(euler_y_step_diff == min(euler_y_step_diff))[0][0]
    min_index = np.where(euler_hip_y[minima:max_index] == min(euler_hip_y[minima:max_index]))[0][0] + minima
    range_euler_y = (euler_hip_y[max_index] - euler_hip_y[min_index]) * 180 / np.pi
    if range_euler_y < 0:
        print('max lower than min')
        return None, None
    duration = max_index - min_index
    if duration <= 0:
        print('max index before min')
        return None, None
    range_rate = range_euler_y / duration * 100
    return range_euler_y, range_rate


def _contact_duration_peak_grf(grf, ranges, epoch_time):
    """get linear combination of peak_grf and ground contact time
    """
    mph = 1.2

    gct_block = []
    peak_grf_block = []
    peak_grf_contact = []
    peak_grf_impact = []
    peak_grf_perc_impact = []

    for range_gc in ranges:
        length_step = epoch_time[range_gc[1]] - epoch_time[range_gc[0]]
        grf_sub = grf[range_gc[0]:range_gc[1]]
        peak_indices = detect_peaks(grf_sub, mph=mph, mpd=1)
        if len(peak_indices) != 0:
            peak_grfs = grf_sub[peak_indices]
            peak_index = peak_indices[np.where(np.max(peak_grfs))[0]]
            peak_grf = grf_sub[peak_index]
            ratio = peak_grf / length_step * 1000.
            peak_grf = peak_grf - grf[range_gc[0] - 1]
            if peak_grf > 0.1:
                length_impact = epoch_time[range_gc[0] + peak_index] - epoch_time[range_gc[0]]
                perc_impact = length_impact / length_step
                ratio_impact = peak_grf / length_impact * 1000.
                ratio_perc_impact = peak_grf / perc_impact
                peak_grf_block.append(peak_grf)
                gct_block.append(length_step)
                peak_grf_contact.append(ratio[0])
                peak_grf_impact.append(ratio_impact[0])
                peak_grf_perc_impact.append(ratio_perc_impact[0])

    return peak_grf_contact, peak_grf_impact, peak_grf_perc_impact


def _contact_duration(phase, active, epoch_time, ground_phases):
    """compute contact duration in ms given phase data
    """
    min_gc = 10
    max_gc = 150

    # enumerate phase such that all ground contacts are 0
    _phase = copy.copy(phase)
    _phase[np.array([i in ground_phases for i in _phase])] = 0
    _phase[np.array([i == 0 for i in active])] = 1

    # get index ranges for ground contacts
    ranges, lengths = get_ranges(_phase, 0, True)

    length_index = np.where((lengths >= min_gc) & (lengths <= max_gc))
    ranges = ranges[length_index]

    # subset to only get the points where ground contacts are within a reasonable window
    lengths = lengths[(lengths >= min_gc) & (lengths <= max_gc)]
    # print(f"mean: {np.mean(lengths)}, median: {np.median(lengths)}")
    # print(len(lengths))

    return lengths, ranges


def _peak_grf(grf, phase_lf, phase_rf):
    """
    Identifies instances of peak grf within block and aggregates them
    """
    mph = 1.2
    grf_lf = copy.copy(grf)
    grf_rf = copy.copy(grf)

    lf_ind = np.array([k in [0, 2, 3] for k in phase_lf])
    rf_ind = np.array([k in [0, 2, 3] for k in phase_rf])
    lf_ground = lf_ind * ~rf_ind  # only lf in ground
    rf_ground = ~lf_ind * rf_ind  # only rf in ground

    grf_lf[~lf_ground] = 0
    grf_rf[~rf_ground] = 0

    peaks_lf = detect_peaks(grf_lf, mph=mph, mpd=1)
    peaks_rf = detect_peaks(grf_rf, mph=mph, mpd=1)
    peaks_lf = grf_lf[peaks_lf]
    peaks_rf = grf_rf[peaks_rf]
    peaks_indices = detect_peaks(grf, mph=mph, mpd=6)
    peaks = grf[peaks_indices]

    return peaks, peaks_lf, peaks_rf


def _peak_accel(total_accel, mph=15.0, mpd=5.0, steps=False):
    """
    Get averate of peak_accel for given data
    """
    accel = total_accel * 10000.
    peaks = detect_peaks(accel, mph=mph, mpd=mpd)
    peak_accel = accel[peaks]
    if not steps:
        if len(peak_accel) >= 2:
            return np.percentile(peak_accel, 95)
        else:
            return 0
    else:
        if np.max(accel) > mph:
            return np.max(accel)
        else:
            return 0


def _get_peak_grf_stats(peak_grf_lf, peak_grf_rf, record):
    if len(peak_grf_lf) == 0 or len(peak_grf_rf) == 0:
        record['peakGrfLF'] = None
        record['peakGrfLFStd'] = None
        record['peakGrfLF5'] = None
        record['peakGrfLF50'] = None
        record['peakGrfLF75'] = None
        record['peakGrfLF95'] = None
        record['peakGrfLF99'] = None
        record['peakGrfLFMax'] = None

        record['peakGrfRF'] = None
        record['peakGrfRFStd'] = None
        record['peakGrfRF5'] = None
        record['peakGrfRF50'] = None
        record['peakGrfRF75'] = None
        record['peakGrfRF95'] = None
        record['peakGrfRF99'] = None
        record['peakGrfRFMax'] = None

    else:
        if len(peak_grf_lf) >= 5:
            record['peakGrfLF'] = np.mean(peak_grf_lf)
            record['peakGrfLFStd'] = np.std(peak_grf_lf)
            record['peakGrfLF5'] = np.percentile(peak_grf_lf, 5)
            record['peakGrfLF50'] = np.percentile(peak_grf_lf, 50)
            record['peakGrfLF75'] = np.percentile(peak_grf_lf, 75)
            record['peakGrfLF95'] = np.percentile(peak_grf_lf, 95)
            record['peakGrfLF99'] = np.percentile(peak_grf_lf, 99)
            record['peakGrfLFMax'] = np.max(peak_grf_lf)
        else:
            record['peakGrfLF'] = np.mean(peak_grf_lf)
            record['peakGrfLFStd'] = None
            record['peakGrfLF5'] = np.min(peak_grf_lf)
            record['peakGrfLF50'] = np.percentile(peak_grf_lf, 50)
            record['peakGrfLF75'] = np.max(peak_grf_lf)
            record['peakGrfLF95'] = np.max(peak_grf_lf)
            record['peakGrfLF99'] = np.max(peak_grf_lf)
            record['peakGrfLFMax'] = np.max(peak_grf_lf)

        if len(peak_grf_rf) >= 5:
            record['peakGrfRF'] = np.mean(peak_grf_rf)
            record['peakGrfRFStd'] = np.std(peak_grf_rf)
            record['peakGrfRF5'] = np.percentile(peak_grf_rf, 5)
            record['peakGrfRF50'] = np.percentile(peak_grf_rf, 50)
            record['peakGrfRF75'] = np.percentile(peak_grf_rf, 75)
            record['peakGrfRF95'] = np.percentile(peak_grf_rf, 95)
            record['peakGrfRF99'] = np.percentile(peak_grf_rf, 99)
            record['peakGrfRFMax'] = np.max(peak_grf_rf)
        else:
            record['peakGrfRF'] = np.mean(peak_grf_rf)
            record['peakGrfRFStd'] = None
            record['peakGrfRF5'] = np.min(peak_grf_rf)
            record['peakGrfRF50'] = np.percentile(peak_grf_rf, 50)
            record['peakGrfRF75'] = np.max(peak_grf_rf)
            record['peakGrfRF95'] = np.max(peak_grf_rf)
            record['peakGrfRF99'] = np.max(peak_grf_rf)
            record['peakGrfRFMax'] = np.max(peak_grf_rf)
    return record


def _get_contact_duration_stats(length_lf, length_rf, record):
    if len(length_lf) == 0 or len(length_rf) == 0:
        record['contactDurationLF'] = None
        record['contactDurationLFStd'] = None
        record['contactDurationLF5'] = None
        record['contactDurationLF50'] = None
        record['contactDurationLF95'] = None

        record['contactDurationRF'] = None
        record['contactDurationRFStd'] = None
        record['contactDurationRF5'] = None
        record['contactDurationRF50'] = None
        record['contactDurationRF95'] = None
    else:
        if len(length_lf) >= 5:
            record['contactDurationLF'] = np.mean(length_lf)
            record['contactDurationLFStd'] = np.std(length_lf)
            record['contactDurationLF5'] = np.percentile(length_lf, 5)
            record['contactDurationLF50'] = np.percentile(length_lf, 50)
            record['contactDurationLF95'] = np.percentile(length_lf, 95)
        else:
            record['contactDurationLF'] = np.mean(length_lf)
            record['contactDurationLFStd'] = None
            record['contactDurationLF5'] = np.min(length_lf)
            record['contactDurationLF50'] = np.percentile(length_lf, 50)
            record['contactDurationLF95'] = np.max(length_lf)

        if len(length_rf) >= 5:
            record['contactDurationRF'] = np.mean(length_rf)
            record['contactDurationRFStd'] = np.std(length_rf)
            record['contactDurationRF5'] = np.percentile(length_rf, 5)
            record['contactDurationRF50'] = np.percentile(length_rf, 50)
            record['contactDurationRF95'] = np.percentile(length_rf, 95)
        else:
            record['contactDurationRF'] = np.mean(length_rf)
            record['contactDurationRFStd'] = None
            record['contactDurationRF5'] = np.min(length_rf)
            record['contactDurationRF50'] = np.percentile(length_rf, 50)
            record['contactDurationRF95'] = np.min(length_rf)

    return record


def _get_stats(left, right, var, record):
    if len(left) == 0 or len(right) == 0:
        record[var + 'LF'] = None
        record[var + 'LFStd'] = None
        record[var + 'LF5'] = None
        record[var + 'LF50'] = None
        record[var + 'LF95'] = None

        record[var + 'RF'] = None
        record[var + 'RFStd'] = None
        record[var + 'RF5'] = None
        record[var + 'RF50'] = None
        record[var + 'RF95'] = None
    else:
        if len(left) >= 5:
            record[var + 'LF'] = np.mean(left)
            record[var + 'LFStd'] = np.std(left)
            record[var + 'LF5'] = np.percentile(left, 5)
            record[var + 'LF50'] = np.percentile(left, 50)
            record[var + 'LF95'] = np.percentile(left, 95)
        else:
            record[var + 'LF'] = np.mean(left)
            record[var + 'LFStd'] = None
            record[var + 'LF5'] = np.min(left)
            record[var + 'LF50'] = np.percentile(left, 50)
            record[var + 'LF95'] = np.max(left)

        if len(right) >= 5:
            record[var + 'RF'] = np.mean(right)
            record[var + 'RFStd'] = np.std(right)
            record[var + 'RF5'] = np.percentile(right, 5)
            record[var + 'RF50'] = np.percentile(right, 50)
            record[var + 'RF95'] = np.percentile(right, 95)
        else:
            record[var + 'RF'] = np.mean(right)
            record[var + 'RFStd'] = None
            record[var + 'RF5'] = np.min(right)
            record[var + 'RF50'] = np.percentile(right, 50)
            record[var + 'RF95'] = np.min(right)

    return record


def _get_peak_grf_contact_stats(peak_grf_contact_lf, peak_grf_contact_rf, record):
    if len(peak_grf_contact_lf) == 0 or len(peak_grf_contact_rf) == 0:
        record['peakGrfContactDurationLF'] = None
        record['peakGrfContactDurationLFStd'] = None
        record['peakGrfContactDurationLF5'] = None
        record['peakGrfContactDurationLF50'] = None
        record['peakGrfContactDurationLF95'] = None

        record['peakGrfContactDurationRF'] = None
        record['peakGrfContactDurationRFStd'] = None
        record['peakGrfContactDurationRF5'] = None
        record['peakGrfContactDurationRF50'] = None
        record['peakGrfContactDurationRF95'] = None
    else:
        if len(peak_grf_contact_lf) >= 5:
            record['peakGrfContactDurationLF'] = np.mean(peak_grf_contact_lf)
            record['peakGrfContactDurationLFStd'] = np.std(peak_grf_contact_lf)
            record['peakGrfContactDurationLF5'] = np.percentile(peak_grf_contact_lf, 5)
            record['peakGrfContactDurationLF50'] = np.percentile(peak_grf_contact_lf, 50)
            record['peakGrfContactDurationLF95'] = np.percentile(peak_grf_contact_lf, 95)
        else:
            record['peakGrfContactDurationLF'] = np.mean(peak_grf_contact_lf)
            record['peakGrfContactDurationLFStd'] = None
            record['peakGrfContactDurationLF5'] = np.min(peak_grf_contact_lf)
            record['peakGrfContactDurationLF50'] = np.percentile(peak_grf_contact_lf, 50)
            record['peakGrfContactDurationLF95'] = np.max(peak_grf_contact_lf)

        if len(peak_grf_contact_rf) >= 5:
            record['peakGrfContactDurationRF'] = np.mean(peak_grf_contact_rf)
            record['peakGrfContactDurationRFStd'] = np.std(peak_grf_contact_rf)
            record['peakGrfContactDurationRF5'] = np.percentile(peak_grf_contact_rf, 5)
            record['peakGrfContactDurationRF50'] = np.percentile(peak_grf_contact_rf, 50)
            record['peakGrfContactDurationRF95'] = np.percentile(peak_grf_contact_rf, 95)
        else:
            record['peakGrfContactDurationRF'] = np.mean(peak_grf_contact_rf)
            record['peakGrfContactDurationRFStd'] = None
            record['peakGrfContactDurationRF5'] = np.min(peak_grf_contact_rf)
            record['peakGrfContactDurationRF50'] = np.percentile(peak_grf_contact_rf, 50)
            record['peakGrfContactDurationRF95'] = np.min(peak_grf_contact_rf)

    return record
