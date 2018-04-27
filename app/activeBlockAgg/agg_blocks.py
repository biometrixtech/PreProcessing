from __future__ import print_function

from collections import namedtuple
from pymongo import MongoClient
from shutil import copyfile
import logging
import os
import pandas
import numpy
import sys
from collections import OrderedDict
import copy

from active_blocks import define_blocks
from detect_peaks import detect_peaks

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

Config = namedtuple('Config', [
    'AWS',
    'ENVIRONMENT',
    'MONGO_HOST',
    'MONGO_USER',
    'MONGO_PASSWORD',
    'MONGO_DATABASE',
    'MONGO_COLLECTION',
    'MONGO_REPLICASET',
])


def script_handler(working_directory, input_data):

    try:
        config = Config(
            AWS=False,
            ENVIRONMENT=os.environ['ENVIRONMENT'],
            MONGO_HOST=os.environ['MONGO_HOST_ACTIVEBLOCKS'],
            MONGO_USER=os.environ['MONGO_USER_ACTIVEBLOCKS'],
            MONGO_PASSWORD=os.environ['MONGO_PASSWORD_ACTIVEBLOCKS'],
            MONGO_DATABASE=os.environ['MONGO_DATABASE_ACTIVEBLOCKS'],
            MONGO_COLLECTION=os.environ['MONGO_COLLECTION_ACTIVEBLOCKS'],
            MONGO_REPLICASET=os.environ['MONGO_REPLICASET_ACTIVEBLOCKS'] if os.environ['MONGO_REPLICASET_ACTIVEBLOCKS'] != '---' else None,
        )

        # first collection
        mongo_client = MongoClient(config.MONGO_HOST, replicaset=config.MONGO_REPLICASET)

        mongo_database = mongo_client[config.MONGO_DATABASE]

        # Authenticate
        mongo_database.authenticate(config.MONGO_USER, config.MONGO_PASSWORD,
                                    mechanism='SCRAM-SHA-1')

        mongo_collection = mongo_database[config.MONGO_COLLECTION]

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
                                                     ])
        os.remove(tmp_filename)
        logger.info("Removed temporary file")

        team_id = input_data.get('TeamId', None)
        training_group_id = input_data.get('TrainingGroupIds', None)
        user_id = input_data.get('UserId', None)
        session_event_id = input_data.get('SessionId', None)
        user_mass = input_data.get('UserMassKg', None)
        event_date = input_data.get('EventDate')

        active_ind = numpy.array([k == 1 for k in data['active']])
        total_ind = numpy.array([k != 3 for k in data['phase_lf']]) * active_ind
        data['total_ind'] = total_ind
        lf_ind = numpy.array([k in [0, 1, 4, 6] for k in data['phase_lf']]) * active_ind
        rf_ind = numpy.array([k in [0, 2, 5, 7] for k in data['phase_rf']]) * active_ind
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

        # segment data into blocks
        active_blocks = define_blocks(data['active'].values)
        print("Beginning iteration over {} blocks".format(len(active_blocks)))
        for block in active_blocks:
            print(block)
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
        return active_blocks

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
#    print(len(numpy.where(numpy.isnan(data.total_accel))[0]))
    record['totalAccelAvg'] = record['totalAccel'] / numpy.sum(data['active']) * 10000
#    record['totalAccelAvg'] = record['totalAccel'] / len(data) * 10000
    record['irregularAccel'] = numpy.nansum(data['irregular_accel'])

    if record['totalGRF'] == 0:        # control aggregation
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

    # contact duration analysis
    length_lf = _contact_duration(data.phase_lf.values,
                                  data.active.values,
                                  data.epoch_time.values,
                                  ground_phases=[1, 4, 6])
    length_rf = _contact_duration(data.phase_rf.values,
                                  data.active.values,
                                  data.epoch_time.values,
                                  ground_phases=[2, 5, 7])
#    length_lf, length_rf = _contact_duration(data)

    record = _get_contact_duration_stats(length_lf, length_rf, record)

    # peak grf
    # normalize grf by user's mass and remove scaling
    grf =  data.total_grf.values * 1000000. / mass / 9.807
    peak_grf_lf, peak_grf_rf = _peak_grf(grf,
                                         data.phase_lf.values,
                                         data.phase_rf.values)

    record = _get_peak_grf_stats(peak_grf_lf, peak_grf_rf, record)

    return record


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

    # subset to only get the points where ground contacts are within a reasonable window
    length = length[(length >= min_gc) & (length <= max_gc)]
    return length


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
    mph = 1.686
#    grf = grf * 1000000. / mass / 9.807
    grf_lf = copy.copy(grf)
    grf_rf = copy.copy(grf)

    lf_ind = numpy.array([k in [0, 1, 4, 6] for k in phase_lf])
    rf_ind = numpy.array([k in [0, 2, 5, 7] for k in phase_rf])
    lf_ground = lf_ind * ~rf_ind  # only lf in ground
    rf_ground = ~lf_ind * rf_ind  # only rf in ground

    grf_lf[~lf_ground] = 0
    grf_rf[~rf_ground] = 0

    peaks_lf = detect_peaks(grf_lf, mph=mph, mpd=1)
    peaks_rf = detect_peaks(grf_rf, mph=mph, mpd=1)
    peaks_lf = grf_lf[peaks_lf]
    peaks_rf = grf_rf[peaks_rf]

    return peaks_lf, peaks_rf

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
