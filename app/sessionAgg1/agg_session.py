from __future__ import print_function

import os
from shutil import copyfile
from collections import OrderedDict, namedtuple
from pymongo import MongoClient
import numpy
import pandas

#from session import SessionRecord
from alert import Alert

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
    print('Running session aggregation  on "{}"'.format(working_directory.split('/')[-1]))

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
#
#        # first collection
        mongo_client = MongoClient(config.MONGO_HOST, replicaset=config.MONGO_REPLICASET)
#
        mongo_database = mongo_client[config.MONGO_DATABASE]
#
#        # Authenticate
        mongo_database.authenticate(config.MONGO_USER, config.MONGO_PASSWORD,
                                    mechanism='SCRAM-SHA-1')
#
        mongo_collection = mongo_database[config.MONGO_COLLECTION]
#
        tmp_filename = '/tmp/readfile'
        copyfile(os.path.join(working_directory, 'scoring'), tmp_filename)
        print("Copied data file to local FS")
        data = pandas.read_csv(tmp_filename)
        os.remove(tmp_filename)
        print("Removed temporary file")


        team_id = input_data.get('TeamId', None)
        training_group_id = input_data.get('TrainingGroupIds', None)
        user_id = input_data.get('UserId', None)
        session_event_id = input_data.get('SessionId', None)
        user_mass = input_data.get('UserMassKg', None)
        event_date = input_data.get('EventDate')

        active_ind = numpy.array([k == 1 for k in data['active']])
        data['total_accel'] = data['total_accel'].fillna(value=numpy.nan) * active_ind
        data['control'][~active_ind] = numpy.nan
        data['aZ'][~active_ind] = numpy.nan
        data['aZ'] = numpy.abs(data['aZ'])

        data['irregular_accel'] = data['total_accel'] * data['destr_multiplier']
        control = numpy.sum(data['control'] * data['aZ']) / numpy.sum(data['aZ'])
        total_accel = numpy.nansum(data['total_accel'])
        irregular_accel = numpy.nansum(data['irregular_accel'])
        perc_optimal_session = (total_accel - irregular_accel) / total_accel
        # fatigue analysis
        start_movement_quality, session_fatigue = _fatigue_analysis(data, var='control')

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
        record_out['totalGRF'] = None
        record_out['optimalGRF'] = None
        record_out['irregularGRF'] = None
        record_out['LFgRF'] = None
        record_out['RFgRF'] = None

        # scores
        record_out['control'] = control
        record_out['consistency'] = None
        record_out['symmetry'] = None

        # blank placeholders for programcomp
        record_out['grfProgramComposition'] = None
        record_out['totalAccelProgramComposition'] = None
        record_out['planeProgramComposition'] = None
        record_out['stanceProgramComposition'] = None

        # new variables
        # grf distribution
        record_out['leftGRF'] = None
        record_out['rightGRF'] = None
        record_out['singleLegGRF'] = None
        record_out['percLeftGRF'] = None
        record_out['percRightGRF'] = None
        record_out['percLRGRFDiff'] = None

        # acceleration
        record_out['totalAccel'] = total_accel
        record_out['irregularAccel'] = irregular_accel

        # scores
        record_out['hipSymmetry'] = None
        record_out['ankleSymmetry'] = None
        record_out['hipConsistency'] = None
        record_out['ankleConsistency'] = None
        record_out['consistencyLF'] = None
        record_out['consistencyRF'] = None
        record_out['hipControl'] = None
        record_out['ankleControl'] = None
        record_out['controlLF'] = None
        record_out['controlRF'] = None

        # fatigue data
        record_out['percOptimal'] = perc_optimal_session * 100
        record_out['percIrregular'] = (1 - perc_optimal_session) * 100
        # record_out['startMovementQuality'] = start_movement_quality
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

        print("Wrote session record")
        return record_out



    except Exception as e:
        print(e)
        print('Process did not complete successfully! See error below!')
        raise

def _fatigue_analysis(data, var):
    """trend analysis on the variable desired
    data: complete data set with all the variables
    var: variable name for which fatigue analysis is desired
    the variable is aggregated(mean) on two minute level and then linear fit is obtained on the
    aggregated data
    """
    data.set_index(pandas.to_datetime(data.epoch_time, unit='ms'), drop=False, inplace=True)
    groups = data.resample('2T')
    series = groups[var].mean()
    series = numpy.array(series)
    series = series[~numpy.isnan(series)]
    print(series)
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
