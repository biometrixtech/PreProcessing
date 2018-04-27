from __future__ import print_function

from collections import namedtuple
from pymongo import MongoClient
from shutil import copyfile
import logging
import os
import pandas
import numpy
#import datetime
import sys
from collections import OrderedDict
import copy

from alert import Alert
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
    logger.info('Running session aggregation  on "{}"'.format(working_directory.split('/')[-1]))

    try:
        config = Config(
            AWS=False,
            ENVIRONMENT=os.environ['ENVIRONMENT'],
            MONGO_HOST=os.environ['MONGO_HOST_SESSION'],
            MONGO_USER=os.environ['MONGO_USER_SESSION'],
            MONGO_PASSWORD=os.environ['MONGO_PASSWORD_SESSION'],
            MONGO_DATABASE=os.environ['MONGO_DATABASE_SESSION'],
            MONGO_COLLECTION=os.environ['MONGO_COLLECTION_SESSION'],
            MONGO_REPLICASET=os.environ['MONGO_REPLICASET_SESSION'] if os.environ['MONGO_REPLICASET_SESSION'] != '---' else None,
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
        data = pandas.read_csv(tmp_filename)
        os.remove(tmp_filename)
        logger.info("Removed temporary file")

        # rename columns to match mongo
        data.columns = ['obsIndex', 'timeStamp', 'epochTime', 'msElapsed', 'sessionDuration',
                        'active',
                        'loadingLF', 'loadingRF',
                        'phaseLF', 'phaseRF', 'lfImpactPhase', 'rfImpactPhase',
                        'total', 'LF', 'RF', 'constructive', 'destructive', 'destrMultiplier', 'sessionGRFElapsed',
                        'symmetry', 'symmetryL', 'symmetryR', 'hipSymmetry', 'hipSymmetryL', 'hipSymmetryR',
                        'ankleSymmetry', 'ankleSymmetryL', 'ankleSymmetryR',
                        'consistency', 'hipConsistency', 'ankleConsistency', 'consistencyLF', 'consistencyRF',
                        'control', 'hipControl', 'ankleControl', 'controlLF', 'controlRF',
                        'contraHipDropLF', 'contraHipDropRF', 'ankleRotLF', 'ankleRotRF', 'footPositionLF',
                        'footPositionRF',
                        'landPatternLF', 'landPatternRF', 'landTime',
                        'rateForceAbsorptionLF', 'rateForceAbsorptionRF', 'rateForceProductionLF',
                        'rateForceProductionRF', 'totalAccel',
                        'stance', 'plane', 'rot', 'lat', 'vert', 'horz']

        team_id = input_data.get('TeamId', None)
        training_group_id = input_data.get('TrainingGroupIds', None)
        user_id = input_data.get('UserId', None)
#        training_session_log_id = input_data.get('TrainingSessionLogId', None)
        session_event_id = input_data.get('SessionId', None)
        user_mass = input_data.get('UserMassKg', None)
        event_date = input_data.get('EventDate')

        # Prep for session aggregation
        # grf
        total_ind = numpy.array([numpy.isfinite(k) for k in data['constructive']])
        lf_ind = numpy.array([k in [0, 1, 4, 6] for k in data['phaseLF']])
        rf_ind = numpy.array([k in [0, 2, 5, 7] for k in data['phaseRF']])
        lf_ground = lf_ind * ~rf_ind  # only lf in ground
        rf_ground = ~lf_ind * rf_ind  # only rf in ground

        data['total_grf'] = data['total'].fillna(value=numpy.nan) * total_ind
        data['lf_grf'] = data['total'].fillna(value=numpy.nan) * lf_ind
        data['rf_grf'] = data['total'].fillna(value=numpy.nan) * rf_ind
        data['lf_only_grf'] = data['total'].fillna(value=numpy.nan) * lf_ground
        data['rf_only_grf'] = data['total'].fillna(value=numpy.nan) * rf_ground

        data['const_grf'] = data['constructive'].fillna(value=numpy.nan) * total_ind
        data['dest_grf'] = data['destructive'].fillna(value=numpy.nan) * total_ind
        data['perc_optimal'] = pandas.DataFrame(data['const_grf'] / (data['const_grf'] + data['dest_grf']))

        # accel
        data['irregularAccel'] = data['totalAccel'] * data['destrMultiplier']

#       Aggregated values
        total_grf = numpy.sum(data['total_grf'])
        const_grf = numpy.nansum(data['const_grf'])
        dest_grf = numpy.nansum(data['dest_grf'])
        if const_grf == 0 and dest_grf == 0:
            perc_optimal_session = 1.
        else:
            perc_optimal_session = const_grf / (const_grf + dest_grf)
        if total_grf == 0 or numpy.isnan(total_grf):
            total_grf = 1e-6
        lf_grf = numpy.sum(data['lf_grf'])
        if lf_grf == 0 or numpy.isnan(lf_grf):
            lf_grf = 1e-6
        lf_only_grf = numpy.sum(data['lf_only_grf'])
        if lf_only_grf == 0 or numpy.isnan(lf_only_grf):
            print('zero left')
            lf_only_grf = 1e-6
        rf_grf = numpy.sum(data['rf_grf'])
        if rf_grf == 0 or numpy.isnan(rf_grf):
            rf_grf = 1e-6
        rf_only_grf = numpy.sum(data['rf_only_grf'])
        if rf_only_grf == 0 or numpy.isnan(rf_only_grf):
            print('zero right')
            rf_only_grf = 1e-6
        lf_rf_grf = lf_only_grf + rf_only_grf

        # grf aggregation
        perc_left_grf = lf_only_grf / lf_rf_grf * 100
        perc_right_grf = rf_only_grf / lf_rf_grf * 100
        perc_distr = numpy.abs(perc_left_grf - perc_right_grf)

        # update perc_optimal to take into account grf distribution
        perc_optimal_session = (2. * perc_optimal_session + (1. - perc_distr / 100.)**2 ) / 3.
        # update optimal and irregular grf with new definition of perc_optimal
        const_grf = perc_optimal_session * total_grf
        dest_grf = (1. - perc_optimal_session) * total_grf

        # control aggregation
        control = numpy.sum(data['control']*data['total_grf']) / total_grf
        hip_control = numpy.sum(data['hipControl']*data['total_grf']) / total_grf
        ankle_control = numpy.sum(data['ankleControl']*data['total_grf']) / total_grf
        control_lf = numpy.sum(data['controlLF']*data['lf_grf']) / lf_grf
        control_rf = numpy.sum(data['controlRF']*data['rf_grf']) / rf_grf

        # symmetry aggregation
        symmetry = numpy.sum(data['symmetry']) / total_grf
        hip_symmetry = numpy.sum(data['hipSymmetry']) / total_grf
        ankle_symmetry = numpy.sum(data['ankleSymmetry']) / total_grf

        # consistency aggregation
        consistency = numpy.sum(data['consistency']) / total_grf
        hip_consistency = numpy.sum(data['hipConsistency']) / total_grf
        ankle_consistency = numpy.sum(data['ankleConsistency']) / total_grf
        consistency_lf = numpy.sum(data['consistencyLF']) / lf_grf
        consistency_rf = numpy.sum(data['consistencyRF']) / rf_grf

        # acceleration aggregation
        total_accel = numpy.nansum(data['totalAccel'])
        irregular_accel = total_accel * (1 - perc_optimal_session)
        # irregular_accel = numpy.nansum(data['irregularAccel'])

        # fatigue analysis
        start_movement_quality, session_fatigue = _fatigue_analysis(data, var='perc_optimal')
        # print(session_fatigue)

        # contact duration analysis
        length_lf = _contact_duration(data.phaseLF.values,
                                      data.active.values,
                                      data.epochTime.values,
                                      ground_phases=[1, 4, 6])
        length_rf = _contact_duration(data.phaseRF.values,
                                      data.active.values,
                                      data.epochTime.values,
                                      ground_phases=[2, 5, 7])
        # peak grf
        # normalize grf by user's mass and remove scaling
        grf =  data.total_grf.values * 1000000. / user_mass / 9.807
        peak_grf_lf, peak_grf_rf = _peak_grf(grf,
                                             data.phaseLF.values,
                                             data.phaseRF.values)

        # create ordered dictionary object
        # current variables
        record_out = OrderedDict({'sessionId': session_event_id})
        record_out['sessionType'] = '1'
        record_out['phaseLF'] = None
        record_out['phaseRF'] = None
        record_out['userMass'] = user_mass
        record_out['trainingGroups'] = training_group_id
        record_out['teamId'] = team_id
        record_out['userId'] = user_id
        record_out['eventDate'] = str(event_date)

        # grf
        record_out['totalGRF'] = total_grf
        record_out['optimalGRF'] = const_grf
        record_out['irregularGRF'] = dest_grf
        record_out['LFgRF'] = lf_grf
        record_out['RFgRF'] = rf_grf

        # scores
        record_out['control'] = control
        record_out['consistency'] = consistency
        record_out['symmetry'] = symmetry

        # blank placeholders for programcomp
        record_out['grfProgramComposition'] = None
        record_out['totalAccelProgramComposition'] = None
        record_out['planeProgramComposition'] = None
        record_out['stanceProgramComposition'] = None

        # new variables
        # grf distribution
        record_out['leftGRF'] = lf_only_grf
        record_out['rightGRF'] = rf_only_grf
        record_out['singleLegGRF'] = lf_rf_grf
        record_out['percLeftGRF'] = perc_left_grf
        record_out['percRightGRF'] = perc_right_grf
        record_out['percLRGRFDiff'] = perc_distr

        # acceleration
        record_out['totalAccel'] = total_accel
        record_out['irregularAccel'] = irregular_accel

        # scores
        record_out['hipSymmetry'] = hip_symmetry
        record_out['ankleSymmetry'] = ankle_symmetry
        record_out['hipConsistency'] = hip_consistency
        record_out['ankleConsistency'] = ankle_consistency
        record_out['consistencyLF'] = consistency_lf
        record_out['consistencyRF'] = consistency_rf
        record_out['hipControl'] = hip_control
        record_out['ankleControl'] = ankle_control
        record_out['controlLF'] = control_lf
        record_out['controlRF'] = control_rf

        # fatigue data
        record_out['percOptimal'] = perc_optimal_session * 100
        record_out['percIrregular'] = (1 - perc_optimal_session) * 100
        record_out['startMovementQuality'] = start_movement_quality
        record_out['sessionFatigue'] = session_fatigue

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
            value = record_out[key]
            try:
                if numpy.isnan(value):
                    record_out[key] = None
                elif value >= 100:
                    record_out[key] = 100
            except TypeError:
                pass

        record_out = _get_contact_duration_stats(length_lf, length_rf, record_out)
        record_out = _get_peak_grf_stats(peak_grf_lf, peak_grf_rf, record_out)

        _publish_alerts(record_out)

        # Write the record to mongo
        query = {'sessionId': session_event_id, 'eventDate': str(event_date)}
        mongo_collection.replace_one(query, record_out, upsert=True)

        logger.info("Wrote session record")
#        return record_id

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise


def _publish_alerts(record_out):
    # Session fatigue
    if -20 < record_out['sessionFatigue'] < -10:
        _publish_alert(record_out, category=2, subcategory=2, granularity='total', value=1)
    elif record_out['sessionFatigue'] <= -20:
        _publish_alert(record_out, category=2, subcategory=2, granularity='total', value=2)


def _publish_alert(record_out, category, subcategory, granularity, value):
    alert = Alert(
        user_id=record_out['userId'],
        team_id=record_out['teamId'],
        training_group_ids=record_out['trainingGroups'],
        event_date=record_out['eventDate'],
        session_type=record_out['sessionType'],
        category=category,
        subcategory=subcategory,
        granularity=granularity,
        value=value
    )
    alert.publish()


def _fatigue_analysis(data, var):
    """trend analysis on the variable desired
    data: complete data set with all the variables
    var: variable name for which fatigue analysis is desired
    the variable is aggregated(mean) on two minute level and then linear fit is obtained on the
    aggregated data
    """
    data.set_index(pandas.to_datetime(data.epochTime, unit='ms'), drop=False, inplace=True)
    groups = data.resample('2T')
    if var == 'perc_optimal':
        series = groups[var].mean() * 100
    else:
        total_grf = groups['total_grf'].sum()
        series = groups[var].sum() / total_grf
    series = numpy.array(series)
    series = series[~numpy.isnan(series)]
    coefficients = numpy.polyfit(range(len(series)), series, 1)

    # slope * len for total change
    fatigue = coefficients[0] * len(series)
    if numpy.isnan(fatigue):
        fatigue = None

    # use intercept for start
    start = coefficients[1]
    if numpy.isnan(start):
        start = None
    elif start > 100:
        start = 100
    elif start < 0:
        start = 0
    return start, fatigue


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
