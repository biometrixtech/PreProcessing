from __future__ import print_function
from shutil import copyfile
import logging
import os
import pandas
import numpy
import sys
from collections import OrderedDict

from config import get_mongo_collection
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def script_handler(working_directory, input_data):
    logger.info('Running session aggregation  on "{}"'.format(working_directory.split('/')[-1]))

    try:
        mongo_collection = get_mongo_collection('SESSION')

        tmp_filename = '/tmp/readfile'
        copyfile(os.path.join(working_directory, 'scoring'), tmp_filename)
        logger.info("Copied data file to local FS")
        data = pandas.read_csv(tmp_filename, usecols=[
                                                        'obs_index',
                                                        'time_stamp',
                                                        'epoch_time',
                                                        'ms_elapsed',
                                                        'session_duration',
                                                        'active',
                                                        'loading_lf',
                                                        'loading_rf',
                                                        'phase_lf',
                                                        'phase_rf',
                                                        'impact_phase_lf',
                                                        'impact_phase_rf',
                                                        'grf',
                                                        'grf_lf',
                                                        'grf_rf',
                                                        'const_grf',
                                                        'dest_grf',
                                                        'destr_multiplier',
                                                        'destr_multiplier',
                                                        'symmetry',
                                                        'symmetry_l',
                                                        'symmetry_r',
                                                        'hip_symmetry',
                                                        'hip_symmetry_l',
                                                        'hip_symmetry_r',
                                                        'ankle_symmetry',
                                                        'ankle_symmetry_l',
                                                        'ankle_symmetry_r',
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
                                                        'contra_hip_drop_lf',
                                                        'contra_hip_drop_lf',
                                                        'ankle_rot_lf',
                                                        'ankle_rot_rf',
                                                        'foot_position_lf',
                                                        'foot_position_rf',
                                                        'land_pattern_lf',
                                                        'land_pattern_rf',
                                                        'land_time',
                                                        'rate_force_absorption_lf',
                                                        'rate_force_absorption_rf',
                                                        'rate_force_production_lf',
                                                        'rate_force_production_rf',
                                                        'total_accel',
                                                        'stance',
                                                        'plane',
                                                        'rot',
                                                        'lat',
                                                        'vert',
                                                        'horz'])
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

        # Write the record to mongo
        query = {'sessionId': session_event_id, 'eventDate': str(event_date)}
        mongo_collection.replace_one(query, record_out, upsert=True)

        logger.info("Wrote session record")
#        return record_id

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise


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
