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

from alert import Alert

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
        training_group_id = input_data.get('TrainingGroupId', None)
        user_id = input_data.get('UserId', None)
#        training_session_log_id = input_data.get('TrainingSessionLogId', None)
        session_event_id = input_data.get('SessionEventId', None)
        session_type = input_data.get('SessionType', None)
        if session_type is not None:
            session_type = str(session_type)
        user_mass = input_data.get('UserMass', 155) * 4.4482
        event_date = input_data.get('EventDate')

        # Prep for session aggregation
        # grf
        total_ind = numpy.array([k != 3 for k in data['phaseLF']])
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
        irregular_accel = numpy.nansum(data['irregularAccel'])

        # fatigue analysis
        session_fatigue = _fatigue_analysis(data, var='perc_optimal')
        print(session_fatigue)
        if numpy.isnan(session_fatigue):
            print('session fatigue nan')
            session_fatigue = 0

        # create ordered dictionary object
        # current variables
        record_out = OrderedDict({'sessionId': session_event_id})
        record_out['sessionType'] = session_type
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
    series = groups[var].mean() * 100
    series = numpy.array(series)
    series = series[~numpy.isnan(series)]
    coefficients = numpy.polyfit(range(len(series)), series, 1)
    fatigue = coefficients[0] * len(series)
    return fatigue


if __name__ == '__main__':
    import time
    start = time.time()
    input_data = OrderedDict()
    input_data['TeamId'] = 'test_team'
    input_data['TrainingGroupId'] = ['test_tg1', 'test_tg2']
    input_data['UserId'] = 'test_user'
    input_data['SessionEventId'] = 'test_session'
    input_data['SessionType'] = '1'
    input_data['UserMass'] = 77
    input_data['eventDate'] = '2017-03-20'

    os.environ['ENVIRONMENT'] = 'Dev'
    os.environ['MONGO_HOST_SESSION'] = 'ec2-34-210-169-8.us-west-2.compute.amazonaws.com:27017'
    os.environ['MONGO_USER_SESSION'] = 'statsUser'
    os.environ['MONGO_PASSWORD_SESSION'] = 'BioMx211'
    os.environ['MONGO_DATABASE_SESSION'] = 'movementStats'
    os.environ['MONGO_COLLECTION_SESSION'] = 'sessionStats_test2'
    os.environ['MONGO_REPLICASET_SESSION'] = '---'
    in_file_name = 'C:\\Users\\Administrator\\Desktop\\python_aggregation\\605a9a17-24bf-4fdc-b539-02adbb28a628'
    perc_optimal = script_handler(in_file_name, input_data)
    print(time.time() - start)

