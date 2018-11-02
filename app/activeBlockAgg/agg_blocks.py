from __future__ import print_function

from shutil import copyfile
import logging
import os
import pandas
import numpy
import sys
from collections import OrderedDict
import copy


from active_blocks import define_blocks
from config import get_mongo_collection
from detect_peaks import detect_peaks

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def script_handler(working_directory, input_data):

    try:
        mongo_collection = get_mongo_collection('ACTIVEBLOCKS')

        tmp_filename = '/tmp/readfile'
        copyfile(os.path.join(working_directory, 'scoring'), tmp_filename)
        logger.info("Copied data file to local FS")
        data = pandas.read_csv(tmp_filename, usecols=['obs_index',
                                                      'epoch_time',
                                                      'ms_elapsed',
                                                      'active',
                                                      'phase_lf',
                                                      'phase_rf',
                                                      'grf',
                                                      'grf_lf',
                                                      'grf_rf',
                                                      'const_grf',
                                                      'dest_grf',
                                                      'destr_multiplier',
                                                      'symmetry',
                                                      'hip_symmetry',
                                                      'ankle_symmetry',
                                                      'consistency',
                                                      'hip_consistency',
                                                      'ankle_consistency',
                                                      'consistency_lf',
                                                      'consistency_rf',
                                                      'control',
                                                      'hip_control',
                                                      'ankle_control',
                                                      'control_lf',
                                                      'control_rf',
                                                      'total_accel',
                                                      'adduc_motion_covered_abs_lf', 'adduc_motion_covered_pos_lf', 'adduc_motion_covered_neg_lf',
                                                      'adduc_range_of_motion_lf',
                                                      'flex_motion_covered_abs_lf', 'flex_motion_covered_pos_lf', 'flex_motion_covered_neg_lf',
                                                      'flex_range_of_motion_lf',
                                                      'contact_duration_lf',
                                                      'adduc_motion_covered_abs_h', 'adduc_motion_covered_pos_h', 'adduc_motion_covered_neg_h',
                                                      'adduc_range_of_motion_h',
                                                      'flex_motion_covered_abs_h', 'flex_motion_covered_pos_h', 'flex_motion_covered_neg_h',
                                                      'flex_range_of_motion_h',
                                                      'contact_duration_h',
                                                      'adduc_motion_covered_abs_rf', 'adduc_motion_covered_pos_rf', 'adduc_motion_covered_neg_rf',
                                                      'adduc_range_of_motion_rf',
                                                      'flex_motion_covered_abs_rf', 'flex_motion_covered_pos_rf', 'flex_motion_covered_neg_rf',
                                                      'flex_range_of_motion_rf',
                                                      'contact_duration_rf',
                                                      'stance',
                                                      'contra_hip_drop_lf',
                                                      'contra_hip_drop_rf',
                                                      'ankle_rot_lf',
                                                      'ankle_rot_rf',
                                                      'foot_position_lf',
                                                      'foot_position_rf',
                                                      'land_pattern_lf',
                                                      'land_pattern_rf',
                                                      'land_time'
                                                      ],
#                                                    nrows=100000
                                                    )

        os.remove(tmp_filename)
        logger.info("Removed temporary file")


        team_id = input_data.get('TeamId', None)
        training_group_id = input_data.get('TrainingGroupIds', None)
        user_id = input_data.get('UserId', None)
        session_event_id = input_data.get('SessionId', None)
        user_mass = input_data.get('UserMassKg', None)
        event_date = input_data.get('EventDate')

        data.active[data.stance == 0] = 0
        active_ind = numpy.array([k == 1 for k in data['active']])
        total_ind = numpy.array([k != 1 for k in data['stance']]) * active_ind
        total_ind = numpy.array([k != 0 for k in data['stance']]) * active_ind
        data['total_ind'] = total_ind
        lf_ind = numpy.array([k in [0, 2, 3] for k in data['phase_lf']]) * active_ind
        rf_ind = numpy.array([k in [0, 2, 3] for k in data['phase_rf']]) * active_ind
        lf_ground = lf_ind * ~rf_ind # only lf in ground
        rf_ground = ~lf_ind * rf_ind # only rf in ground

        

        data['total_grf'] = data['grf'].fillna(value=numpy.nan) * total_ind
        data['lf_grf'] = data['grf'].fillna(value=numpy.nan) * lf_ind
        data['rf_grf'] = data['grf'].fillna(value=numpy.nan) * rf_ind
        data['lf_only_grf'] = data['grf'].fillna(value=numpy.nan) * lf_ground
        data['rf_only_grf'] = data['grf'].fillna(value=numpy.nan) * rf_ground

        data['const_grf'] = data['const_grf'].fillna(value=numpy.nan) * total_ind
        data['dest_grf'] = data['dest_grf'].fillna(value=numpy.nan) * total_ind
        data['perc_optimal'] = pandas.DataFrame(data['const_grf'] / (data['const_grf'] + data['dest_grf']))

        # accel
        data['total_accel'] = data['total_accel'] * active_ind
        data['irregular_accel'] = data['total_accel'] * data['destr_multiplier']

        # scores
        data['symmetry'] = data['symmetry'] * active_ind
        data['hip_symmetry'] = data['hip_symmetry'] * active_ind
        data['ankle_symmetry'] = data['ankle_symmetry'] * active_ind
        data['consistency'] = data['consistency'] * active_ind
        data['hip_consistency'] = data['hip_consistency'] * active_ind
        data['ankle_consistency'] = data['ankle_consistency'] * active_ind
        data['consistency_lf'] = data['consistency_lf'] * active_ind
        data['consistency_rf'] = data['consistency_rf'] * active_ind
        data.control_lf[~active_ind] = numpy.nan
        data.control_rf[~active_ind] = numpy.nan

        # segment data into blocks
        active_blocks = define_blocks(data['active'].values)
        print("Beginning iteration over {} blocks".format(len(active_blocks)))
        for block in active_blocks:
            block_start_index = active_blocks[block][0][0]
            block_end_index = active_blocks[block][-1][1]
            if block_end_index >= len(data):
                block_end_index = len(data) - 1
            block_start = str(pandas.to_datetime(data['epoch_time'][block_start_index], unit='ms'))
            block_end = str(pandas.to_datetime(data['epoch_time'][block_end_index], unit='ms'))
            block_data = data.loc[block_start_index:block_end_index, :]

            record_out = OrderedDict()
            record_out['userId'] = user_id
            record_out['eventDate'] = event_date
            record_out['userMass'] = user_mass
            record_out['teamId'] = team_id
            record_out['trainingGroups'] = training_group_id
            record_out['sessionId'] = session_event_id
            record_out['sessionType'] = '1'

            record_out['timeStart'] = block_start
            record_out['timeEnd'] = block_end

            record_out = _aggregate(block_data, record_out, user_mass)

            unit_blocks = []
            for unit_block in active_blocks[block]:
                unit_block_start_index = unit_block[0]
                unit_block_end_index = unit_block[1]
                if unit_block_end_index >= len(data):
                    unit_block_end_index = len(data) - 1
                unit_block_data = data.loc[unit_block_start_index:unit_block_end_index]
                unit_block_record = OrderedDict()
                unit_block_start = str(pandas.to_datetime(data['epoch_time'][unit_block_start_index], unit='ms'))
                unit_block_end = str(pandas.to_datetime(data['epoch_time'][unit_block_end_index], unit='ms'))
                unit_block_record['timeStart'] = unit_block_start
                unit_block_record['timeEnd'] = unit_block_end

                unit_block_record = _aggregate(unit_block_data, unit_block_record, user_mass)

                unit_blocks.append(unit_block_record)

            record_out['unitBlocks'] = unit_blocks

            query = {'sessionId': session_event_id, 'timeStart': block_start}
            mongo_collection.replace_one(query, record_out, upsert=True)

            logger.info("Wrote a bock record")

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise

def _aggregate(data, record, mass):
    """Aggregates different variables for block/unitBlocks
    """
    data.reset_index(drop=True, inplace=True)
    const_grf = numpy.nansum(data['const_grf'])
    dest_grf = numpy.nansum(data['dest_grf'])
    if const_grf == 0 and dest_grf == 0:
        perc_optimal_block = 1.
    else:
        perc_optimal_block = const_grf / (const_grf + dest_grf)

    lf_only_grf = numpy.sum(data['lf_only_grf'])
    rf_only_grf = numpy.sum(data['rf_only_grf'])

    lf_rf_grf = lf_only_grf + rf_only_grf

    # grf aggregation
    if lf_only_grf == 0. or numpy.isnan(lf_only_grf) or rf_only_grf == 0. or numpy.isnan(rf_only_grf):
        # if there's not enough data for left or right only grf, pass Null for relevant variables
        # do not update perc_optimal
        perc_distr = None
        perc_left_grf = None
        perc_right_grf = None
    else:
        # compute perc_distr and update perc_optimal with perc_distr
        perc_left_grf = lf_only_grf / lf_rf_grf * 100
        perc_right_grf = rf_only_grf / lf_rf_grf * 100
        perc_distr = numpy.abs(perc_left_grf - perc_right_grf)

        # update perc_optimal to take into account grf distribution
        perc_optimal_block = (2. * perc_optimal_block + (1. - perc_distr / 100.)**2) / 3.
    # GRF aggregation
    record['duration'] = (data['epoch_time'].values[-1] - data['epoch_time'].values[0]) / 1000.
    record['totalGRF'] = numpy.sum(data['total_grf'])
    record['totalGRFAvg'] = record['totalGRF'] / numpy.sum(data['total_ind']) * 1000000. / mass / 9.807
    record['optimalGRF'] = perc_optimal_block * record['totalGRF']
    record['irregularGRF'] = (1. - perc_optimal_block) * record['totalGRF']
    record['LFgRF'] = numpy.sum(data['lf_grf'])
    record['RFgRF'] = numpy.sum(data['rf_grf'])
    record['leftGRF'] = numpy.sum(data['lf_only_grf'])
    record['rightGRF'] = numpy.sum(data['rf_only_grf'])
    record['singleLegGRF'] = lf_rf_grf
    record['percLeftGRF'] = perc_left_grf
    record['percRightGRF'] = perc_right_grf
    record['percLRGRFDiff'] = perc_distr

    # accel aggregation
    record['totalAccel'] = numpy.nansum(data['total_accel'])
    record['peakAccel'] = _peak_accel(data['total_accel'].values)
    record['irregularAccel'] = numpy.nansum(data['irregular_accel'])

    if record['totalGRF'] == 0:
        # control aggregation
        record['control'] = None
        record['hipControl'] = None
        record['ankleControl'] = None
        try:
            record['controlLF'] = numpy.sum(data['control_lf']*data['lf_grf']) / record['LFgRF']
        except ZeroDivisionError:
            record['controlLF'] = None
        try:
            record['controlRF'] = numpy.sum(data['control_rf']*data['rf_grf']) / record['RFgRF']
        except ZeroDivisionError:
            record['controlRF'] = None

        # symmetry aggregation
        record['symmetry'] = None
        record['hipSymmetry'] = None
        record['ankleSymmetry'] = None

        # consistency aggregation
        record['consistency'] = None
        record['hipConsistency'] = None
        record['ankleConsistency'] = None
        try:
            record['consistencyLF'] = numpy.sum(data['consistency_lf']) / record['LFgRF']
        except ZeroDivisionError:
            record['consistencyLF'] = None
        try:
            record['consistencyRF'] = numpy.sum(data['consistency_rf']) / record['RFgRF']
        except ZeroDivisionError:
            record['consistencyRF'] = None
    else:
        # control aggregation
        record['control'] = numpy.sum(data['control']*data['total_grf']) / record['totalGRF']
        record['hipControl'] = numpy.sum(data['hip_control']*data['total_grf']) / record['totalGRF']
        record['ankleControl'] = numpy.sum(data['ankle_control']*data['total_grf']) / record['totalGRF']
        try:
            record['controlLF'] = numpy.sum(data['control_lf']*data['lf_grf']) / record['LFgRF']
        except ZeroDivisionError:
            record['controlLF'] = None
        try:
            record['controlRF'] = numpy.sum(data['control_rf']*data['rf_grf']) / record['RFgRF']
        except ZeroDivisionError:
            record['controlRF'] = None

        # symmetry aggregation
        record['symmetry'] = numpy.sum(data['symmetry']) / record['totalGRF']
        record['hipSymmetry'] = numpy.sum(data['hip_symmetry']) / record['totalGRF']
        record['ankleSymmetry'] = numpy.sum(data['ankle_symmetry']) / record['totalGRF']

        # consistency aggregation
        record['consistency'] = numpy.sum(data['consistency']) / record['totalGRF']
        record['hipConsistency'] = numpy.sum(data['hip_consistency']) / record['totalGRF']
        record['ankleConsistency'] = numpy.sum(data['ankle_consistency']) / record['totalGRF']
        try:
            record['consistencyLF'] = numpy.sum(data['consistency_lf']) / record['LFgRF']
        except ZeroDivisionError:
            record['consistencyLF'] = None
        try:
            record['consistencyRF'] = numpy.sum(data['consistency_rf']) / record['RFgRF']
        except ZeroDivisionError:
            record['consistencyRF'] = None

    # enforce validity of scores
    scor_cols = ['symmetry',
                 'hipSymmetry',
                 'ankleSymmetry',
                 'consistency',
                 'hipConsistency',
                 'ankleConsistency',
                 'consistencyLF',
                 'consistencyRF',
                 'control',
                 'hipControl',
                 'ankleControl',
                 'controlLF',
                 'controlRF']
    for key in scor_cols:
        value = record[key]
        try:
            if numpy.isnan(value):
                record[key] = None
            elif value >= 100:
                record[key] = 100
        except TypeError:
            pass

    # fatigue
    record['percOptimal'] = perc_optimal_block * 100
    record['percIrregular'] = (1 - perc_optimal_block) * 100

    length_lf, range_lf = _contact_duration(data.phase_lf.values,
                                            data.active.values,
                                            data.epoch_time.values,
                                            ground_phases=[2, 3])
    length_rf, range_rf = _contact_duration(data.phase_rf.values,
                                            data.active.values,
                                            data.epoch_time.values,
                                            ground_phases=[2, 3])


    for left_step in range_lf:
        left_phase = numpy.unique(data.phase_lf[left_step[0]:left_step[1]].values)
        if numpy.all(left_phase == numpy.array([2., 3.])):
            left_takeoff = _get_ranges(data.phase_lf[left_step[0]:left_step[1]], 3)
            if len(left_takeoff) > 0: # has takeoff as part of ground contact
                left_takeoff = left_takeoff[0]
                if data.phase_lf[left_step[0] + left_takeoff[0] - 1] == 2: # impact-->takeoff not ground-->takeoff
                    left_takeoff_start = left_step[0] + left_takeoff[0]
                    left_end = left_step[1]
                    right_start = range_rf[:, 0]
                    right_step = range_rf[(left_takeoff_start <= right_start) & (right_start <= left_end)]
                    if len(right_step) > 0: # any right step that starts impact withing left_takeoff
                        # make sure start of right step is impact
                        right_step = right_step[0]
                        if data.phase_rf[right_step[0]] == 2 and 3 in numpy.unique(data.phase_rf[right_step[0]:right_step[1]].values):
                            data.loc[left_step[0]:right_step[1], 'stance'] = [6] * (right_step[1] - left_step[0] + 1)
                    else:
                        data.loc[left_step[0]:left_step[1], 'stance'] = [2] * (left_step[1] - left_step[0] + 1)
    for right_step in range_rf:
        right_phase = numpy.unique(data.phase_rf[right_step[0]:right_step[1]].values)
        if numpy.all(right_phase == numpy.array([2., 3.])):
            right_takeoff = _get_ranges(data.phase_rf[right_step[0]:right_step[1]], 3)
            if len(right_takeoff) > 0: # has takeoff as part of ground contact
                right_takeoff = right_takeoff[0]
                if data.phase_rf[right_step[0] + right_takeoff[0] - 1] == 2: # impact-->takeoff not ground-->takeoff
                    right_takeoff_start = right_step[0] + right_takeoff[0]
                    right_end = right_step[1]
                    left_start = range_lf[:, 0]
                    left_step = range_lf[(right_takeoff_start <= left_start) & (left_start <= right_end)]
                    if len(left_step) > 0: # any left step that starts impact withing right_takeoff
                        # make sure start of left step is impact
                        left_step = left_step[0]
                        if data.phase_lf[left_step[0]] == 2 and 3 in data.phase_lf[left_step[0]:left_step[1]].values:
                            data.loc[right_step[0]:left_step[1], 'stance'] = [6] * (left_step[1] - right_step[0] + 1)
                    else:
                        data.loc[right_step[0]:right_step[1], 'stance'] = [2] * (right_step[1] - right_step[0] + 1)

    record = _get_stats(length_lf, length_rf, 'contactDuration', record)
    # normalize grf by user's mass and remove scaling
    grf = data.total_grf.values * 1000000. / mass / 9.807
    # peak grf
    peak_grf_lf, peak_grf_rf = _peak_grf(grf,
                                         data.phase_lf.values,
                                         data.phase_rf.values)

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


    steps_lf = _step_data(data, range_lf, mass, 'LF')
    record['stepsLF'] = steps_lf

    steps_rf = _step_data(data, range_rf,  mass, 'RF')
    record['stepsRF'] = steps_rf

    record = _get_stats(peak_grf_contact_lf, peak_grf_contact_rf, 'peakGrfContactDuration', record)
    record = _get_stats(peak_grf_impact_lf, peak_grf_impact_rf, 'peakGrfImpactDuration', record)
    record = _get_stats(peak_grf_perc_impact_lf, peak_grf_perc_impact_rf, 'peakGrfPercImpactDuration', record)

    return record



def _step_data(data, ranges, mass, sensor):
    """get linear combination of peak_grf and ground contact time
    """

    steps = []
    for range_gc in ranges:
        step_record = OrderedDict()
        step_data = data.loc[range_gc[0]:range_gc[1]-1, :]
        if numpy.all(numpy.unique(step_data['phase_' + sensor.lower()]) == numpy.array([0.])):
            continue
        const_grf = numpy.nansum(step_data['const_grf'])
        dest_grf = numpy.nansum(step_data['dest_grf'])
        if const_grf == 0 and dest_grf == 0:
            perc_optimal_step = 1.
        else:
            perc_optimal_step = const_grf / (const_grf + dest_grf)

        contact_duration = data.epoch_time[range_gc[1] - 1] - data.epoch_time[range_gc[0]]

        step_start = str(pandas.to_datetime(data.epoch_time[range_gc[0]], unit='ms'))

        step_end = str(pandas.to_datetime(data.epoch_time[range_gc[1]], unit='ms'))
        step_record['startTime'] = step_start
        step_record['endTime'] = step_end
        step_record['duration'] = contact_duration / 1000.
        step_record['totalGRF'] = numpy.sum(step_data['total_grf'])
        step_record['totalGRFAvg'] = step_record['totalGRF'] / numpy.sum(step_data['total_ind']) * 1000000. / mass / 9.807
        step_record['optimalGRF'] = perc_optimal_step * step_record['totalGRF']
        step_record['irregularGRF'] = (1. - perc_optimal_step) * step_record['totalGRF']
    
        # accel aggregation
        step_record['totalAccel'] = numpy.nansum(step_data['total_accel'])
        step_record['peakAccel'] = _peak_accel(step_data['total_accel'].values, mph=5., mpd=1, steps=True)
        step_record['irregularAccel'] = numpy.nansum(step_data['irregular_accel'])
    
        if step_record['totalGRF'] == 0:
            # control aggregation
            step_record['control'] = None
            step_record['hipControl'] = None
            step_record['ankleControl'] = None
            step_record['control' + sensor] = None
    
            # symmetry aggregation
            step_record['symmetry'] = None
            step_record['hipSymmetry'] = None
            step_record['ankleSymmetry'] = None
    
            # consistency aggregation
            step_record['consistency'] = None
            step_record['hipConsistency'] = None
            step_record['ankleConsistency'] = None
            step_record['consistency' + sensor] = None
        else:
            # control aggregation
            step_record['control'] = numpy.sum(step_data['control']*step_data['total_grf']) / step_record['totalGRF']
            step_record['hipControl'] = numpy.sum(step_data['hip_control']*step_data['total_grf']) / step_record['totalGRF']
            step_record['ankleControl'] = numpy.sum(step_data['ankle_control']*step_data['total_grf']) / step_record['totalGRF']
            step_record['control' + sensor] = numpy.sum(step_data['control_' + sensor.lower()]*step_data['total_grf']) / step_record['totalGRF']
    
            # symmetry aggregation
            step_record['symmetry'] = numpy.sum(step_data['symmetry']) / step_record['totalGRF']
            step_record['hipSymmetry'] = numpy.sum(step_data['hip_symmetry']) / step_record['totalGRF']
            step_record['ankleSymmetry'] = numpy.sum(step_data['ankle_symmetry']) / step_record['totalGRF']
    
            # consistency aggregation
            step_record['consistency'] = numpy.sum(step_data['consistency']) / step_record['totalGRF']
            step_record['hipConsistency'] = numpy.sum(step_data['hip_consistency']) / step_record['totalGRF']
            step_record['ankleConsistency'] = numpy.sum(step_data['ankle_consistency']) / step_record['totalGRF']
            step_record['consistency' + sensor] = numpy.sum(step_data['consistency_' + sensor.lower()]) / step_record['totalGRF']
        # fatigue
        step_record['percOptimal'] = perc_optimal_step * 100
        step_record['percIrregular'] = (1 - perc_optimal_step) * 100

        mph = 1.1
        grf_sub = data.grf[range_gc[0]:range_gc[1]].values
        norm_grf = grf_sub * 1000000. / mass / 9.807
        peak_indices = detect_peaks(norm_grf, mph=mph, mpd=1)
        if len(peak_indices) != 0:
            peak_grfs = norm_grf[peak_indices]
            peak_grf = numpy.max(peak_grfs)
            peak_index = peak_indices[numpy.where(numpy.max(peak_grfs))[0]]
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

        adduc_rom = numpy.nanmean(step_data['adduc_range_of_motion_' + sensor.lower()])
        adduc_motion_covered_abs = numpy.nanmean(step_data['adduc_motion_covered_abs_' + sensor.lower()])
        adduc_motion_covered_pos = numpy.nanmean(step_data['adduc_motion_covered_pos_' + sensor.lower()])
        adduc_motion_covered_neg = numpy.nanmean(step_data['adduc_motion_covered_neg_' + sensor.lower()])
        flex_rom = numpy.nanmean(step_data['flex_range_of_motion_' + sensor.lower()])
        flex_motion_covered_abs = numpy.nanmean(step_data['flex_motion_covered_abs_' + sensor.lower()])
        flex_motion_covered_pos = numpy.nanmean(step_data['flex_motion_covered_pos_' + sensor.lower()])
        flex_motion_covered_neg = numpy.nanmean(step_data['flex_motion_covered_neg_' + sensor.lower()])


        adduc_rom_hip = numpy.nanmean(step_data['adduc_range_of_motion_h'])
        adduc_motion_covered_abs_hip = numpy.nanmean(step_data['adduc_motion_covered_abs_h'])
        adduc_motion_covered_pos_hip = numpy.nanmean(step_data['adduc_motion_covered_pos_h'])
        adduc_motion_covered_neg_hip = numpy.nanmean(step_data['adduc_motion_covered_neg_h'])
        flex_rom_hip = numpy.nanmean(step_data['flex_range_of_motion_h'])
        flex_motion_covered_abs_hip = numpy.nanmean(step_data['flex_motion_covered_abs_h'])
        flex_motion_covered_pos_hip = numpy.nanmean(step_data['flex_motion_covered_pos_h'])
        flex_motion_covered_neg_hip = numpy.nanmean(step_data['flex_motion_covered_neg_h'])

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
        step_record['contraHipDrop' + sensor] = list(step_data['contra_hip_drop_' + sensor.lower()].values)
        step_record['ankleRotation' + sensor] = list(step_data['ankle_rot_' + sensor.lower()].values)
        step_record['landPattern' + sensor] = list(step_data['land_pattern_' + sensor.lower()].values)
        step_record['landTime'] = list(step_data['land_time'].values)
        step_record['stance'] = list(step_data['stance'].values)
        stance = numpy.unique(step_record['stance'])
        if len(stance) > 1:
            if numpy.all(stance == numpy.array([2., 3.])):
                if sensor == 'LF':
                    rf_air = numpy.where(step_data.phase_rf.values == 1)[0]
                    if len(rf_air) <= 2:
                        step_record['stance'] = [3.] * len(step_data)
                    else:
                        step_record['stance'] = [0.] * len(step_data)
                if sensor == 'RF':
                    lf_air = numpy.where(step_data.phase_lf.values == 1)[0]
                    if len(lf_air) <= 2:
                        step_record['stance'] = [3.] * len(step_data)
                    else:
                        step_record['stance'] = [0.] * len(step_data)
            elif numpy.all(stance == numpy.array([2., 6.])):
                continue
            elif numpy.all(stance == numpy.array([3., 6.])):
                continue
            elif numpy.all(stance == numpy.array([2., 4.])):
                step_record['stance'] = [2.] * len(step_data)
            elif numpy.all(stance == numpy.array([3., 5.])):
                step_record['stance'] = [3.] * len(step_data)
        steps.append(step_record)
    return steps


def _contact_duration_peak_grf(grf, ranges, epoch_time):
    """get linear combination of peak_grf and ground contact time
    """
    mph = 1.1

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
            peak_grf = numpy.max(peak_grfs)
            peak_index = peak_indices[numpy.where(numpy.max(peak_grfs))[0]]
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
    min_gc = 80.
    max_gc = 1500.

    # enumerate phase such that all ground contacts are 0
    _phase = copy.copy(phase)
    _phase[numpy.array([i in ground_phases for i in _phase])] = 0
    _phase[numpy.array([i == 0 for i in active])] = 1

    # get index ranges for ground contacts
    ranges = _get_ranges(_phase, 0)
    length = epoch_time[ranges[:, 1]] - epoch_time[ranges[:, 0]]

    length_index = numpy.where((length >= min_gc) & (length <= max_gc))
    ranges = ranges[length_index]

    # subset to only get the points where ground contacts are within a reasonable window
    length = length[(length >= min_gc) & (length <= max_gc)]

    return length, ranges


def _get_ranges(col_data, value):
    """
    For a given categorical data, determine start and end index for the given value
    start: index where it first occurs
    end: index after the last occurence

    Args:
        col_data
        value: int, value to get ranges for
    Returns:
        ranges: 2d array, start and end index for each occurance of value
    """

    # determine where column data is the relevant value
    is_value = numpy.array(numpy.array(col_data == value).astype(int)).reshape(-1, 1)

    # if data starts with given value, range starts with index 0
    if is_value[0] == 1:
        t_b = 1
    else:
        t_b = 0

    # mark where column data changes to and from the given value
    absdiff = numpy.abs(numpy.ediff1d(is_value, to_begin=t_b))

    # handle the closing edge
    # if the data ends with the given value, if it was the only point, ignore the range,
    # else assign the last index as end of range
    if is_value[-1] == 1:
        if absdiff[-1] == 0:
            absdiff[-1] = 1
        else:
            absdiff[-1] = 0
    # determine the number of consecutive NaNs
    ranges = numpy.where(absdiff == 1)[0].reshape((-1, 2))

    return ranges


def _peak_grf(grf, phase_lf, phase_rf):
    """Identifies instances of peak grf within block and aggregates them
    """
    mph = 1.1
#    grf = grf * 1000000. / mass / 9.807
    grf_lf = copy.copy(grf)
    grf_rf = copy.copy(grf)

    lf_ind = numpy.array([k in [0, 2, 3] for k in phase_lf])
    rf_ind = numpy.array([k in [0, 2, 3] for k in phase_rf])
    lf_ground = lf_ind * ~rf_ind  # only lf in ground
    rf_ground = ~lf_ind * rf_ind  # only rf in ground

    grf_lf[~lf_ground] = 0
    grf_rf[~rf_ground] = 0

    peaks_lf = detect_peaks(grf_lf, mph=mph, mpd=1)
    peaks_rf = detect_peaks(grf_rf, mph=mph, mpd=1)
    peaks_lf = grf_lf[peaks_lf]
    peaks_rf = grf_rf[peaks_rf]

    return peaks_lf, peaks_rf


def _peak_accel(total_accel, mph=15, mpd=5, steps=False):
    """Get averate of peak_accel for given data
    """
    accel = total_accel * 10000.
    peaks = detect_peaks(accel, mph=mph, mpd=mpd)
    peak_accel = accel[peaks]
    if not steps:
        if len(peak_accel) >= 2:
            return numpy.percentile(peak_accel, 95)
        else:
            return 0
    else:
        if numpy.max(accel) > mph:
            return numpy.max(accel)
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
            record['peakGrfLF'] = numpy.mean(peak_grf_lf)
            record['peakGrfLFStd'] = numpy.std(peak_grf_lf)
            record['peakGrfLF5'] = numpy.percentile(peak_grf_lf, 5)
            record['peakGrfLF50'] = numpy.percentile(peak_grf_lf, 50)
            record['peakGrfLF75'] = numpy.percentile(peak_grf_lf, 75)
            record['peakGrfLF95'] = numpy.percentile(peak_grf_lf, 95)
            record['peakGrfLF99'] = numpy.percentile(peak_grf_lf, 99)
            record['peakGrfLFMax'] = numpy.max(peak_grf_lf)
        else:
            record['peakGrfLF'] = numpy.mean(peak_grf_lf)
            record['peakGrfLFStd'] = None
            record['peakGrfLF5'] = numpy.min(peak_grf_lf)
            record['peakGrfLF50'] = numpy.percentile(peak_grf_lf, 50)
            record['peakGrfLF75'] = numpy.max(peak_grf_lf)
            record['peakGrfLF95'] = numpy.max(peak_grf_lf)
            record['peakGrfLF99'] = numpy.max(peak_grf_lf)
            record['peakGrfLFMax'] = numpy.max(peak_grf_lf)

        if len(peak_grf_rf) >= 5:
            record['peakGrfRF'] = numpy.mean(peak_grf_rf)
            record['peakGrfRFStd'] = numpy.std(peak_grf_rf)
            record['peakGrfRF5'] = numpy.percentile(peak_grf_rf, 5)
            record['peakGrfRF50'] = numpy.percentile(peak_grf_rf, 50)
            record['peakGrfRF75'] = numpy.percentile(peak_grf_rf, 75)
            record['peakGrfRF95'] = numpy.percentile(peak_grf_rf, 95)
            record['peakGrfRF99'] = numpy.percentile(peak_grf_rf, 99)
            record['peakGrfRFMax'] = numpy.max(peak_grf_rf)
        else:
            record['peakGrfRF'] = numpy.mean(peak_grf_rf)
            record['peakGrfRFStd'] = None
            record['peakGrfRF5'] = numpy.min(peak_grf_rf)
            record['peakGrfRF50'] = numpy.percentile(peak_grf_rf, 50)
            record['peakGrfRF75'] = numpy.max(peak_grf_rf)
            record['peakGrfRF95'] = numpy.max(peak_grf_rf)
            record['peakGrfRF99'] = numpy.max(peak_grf_rf)
            record['peakGrfRFMax'] = numpy.max(peak_grf_rf)
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
            record['contactDurationLF'] = numpy.mean(length_lf)
            record['contactDurationLFStd'] = numpy.std(length_lf)
            record['contactDurationLF5'] = numpy.percentile(length_lf, 5)
            record['contactDurationLF50'] = numpy.percentile(length_lf, 50)
            record['contactDurationLF95'] = numpy.percentile(length_lf, 95)
        else:
            record['contactDurationLF'] = numpy.mean(length_lf)
            record['contactDurationLFStd'] = None
            record['contactDurationLF5'] = numpy.min(length_lf)
            record['contactDurationLF50'] = numpy.percentile(length_lf, 50)
            record['contactDurationLF95'] = numpy.max(length_lf)

        if len(length_rf) >= 5:
            record['contactDurationRF'] = numpy.mean(length_rf)
            record['contactDurationRFStd'] = numpy.std(length_rf)
            record['contactDurationRF5'] = numpy.percentile(length_rf, 5)
            record['contactDurationRF50'] = numpy.percentile(length_rf, 50)
            record['contactDurationRF95'] = numpy.percentile(length_rf, 95)
        else:
            record['contactDurationRF'] = numpy.mean(length_rf)
            record['contactDurationRFStd'] = None
            record['contactDurationRF5'] = numpy.min(length_rf)
            record['contactDurationRF50'] = numpy.percentile(length_rf, 50)
            record['contactDurationRF95'] = numpy.min(length_rf)

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
            record[var + 'LF'] = numpy.mean(left)
            record[var + 'LFStd'] = numpy.std(left)
            record[var + 'LF5'] = numpy.percentile(left, 5)
            record[var + 'LF50'] = numpy.percentile(left, 50)
            record[var + 'LF95'] = numpy.percentile(left, 95)
        else:
            record[var + 'LF'] = numpy.mean(left)
            record[var + 'LFStd'] = None
            record[var + 'LF5'] = numpy.min(left)
            record[var + 'LF50'] = numpy.percentile(left, 50)
            record[var + 'LF95'] = numpy.max(left)

        if len(right) >= 5:
            record[var + 'RF'] = numpy.mean(right)
            record[var + 'RFStd'] = numpy.std(right)
            record[var + 'RF5'] = numpy.percentile(right, 5)
            record[var + 'RF50'] = numpy.percentile(right, 50)
            record[var + 'RF95'] = numpy.percentile(right, 95)
        else:
            record[var + 'RF'] = numpy.mean(right)
            record[var + 'RFStd'] = None
            record[var + 'RF5'] = numpy.min(right)
            record[var + 'RF50'] = numpy.percentile(right, 50)
            record[var + 'RF95'] = numpy.min(right)

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
            record['peakGrfContactDurationLF'] = numpy.mean(peak_grf_contact_lf)
            record['peakGrfContactDurationLFStd'] = numpy.std(peak_grf_contact_lf)
            record['peakGrfContactDurationLF5'] = numpy.percentile(peak_grf_contact_lf, 5)
            record['peakGrfContactDurationLF50'] = numpy.percentile(peak_grf_contact_lf, 50)
            record['peakGrfContactDurationLF95'] = numpy.percentile(peak_grf_contact_lf, 95)
        else:
            record['peakGrfContactDurationLF'] = numpy.mean(peak_grf_contact_lf)
            record['peakGrfContactDurationLFStd'] = None
            record['peakGrfContactDurationLF5'] = numpy.min(peak_grf_contact_lf)
            record['peakGrfContactDurationLF50'] = numpy.percentile(peak_grf_contact_lf, 50)
            record['peakGrfContactDurationLF95'] = numpy.max(peak_grf_contact_lf)

        if len(peak_grf_contact_rf) >= 5:
            record['peakGrfContactDurationRF'] = numpy.mean(peak_grf_contact_rf)
            record['peakGrfContactDurationRFStd'] = numpy.std(peak_grf_contact_rf)
            record['peakGrfContactDurationRF5'] = numpy.percentile(peak_grf_contact_rf, 5)
            record['peakGrfContactDurationRF50'] = numpy.percentile(peak_grf_contact_rf, 50)
            record['peakGrfContactDurationRF95'] = numpy.percentile(peak_grf_contact_rf, 95)
        else:
            record['peakGrfContactDurationRF'] = numpy.mean(peak_grf_contact_rf)
            record['peakGrfContactDurationRFStd'] = None
            record['peakGrfContactDurationRF5'] = numpy.min(peak_grf_contact_rf)
            record['peakGrfContactDurationRF50'] = numpy.percentile(peak_grf_contact_rf, 50)
            record['peakGrfContactDurationRF95'] = numpy.min(peak_grf_contact_rf)

    return record
