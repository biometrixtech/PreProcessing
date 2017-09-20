from __future__ import print_function

from collections import namedtuple
from pymongo import MongoClient
from shutil import copyfile
import logging
import os
import pandas
import numpy
import datetime
import sys
from collections import OrderedDict

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

Config = namedtuple('Config', [
    'AWS',
    'ENVIRONMENT',
    'FP_INPUT',
    'MONGO_HOST',
    'MONGO_USER',
    'MONGO_PASSWORD',
    'MONGO_DATABASE',
    'MONGO_COLLECTION',
    'MONGO_REPLICASET',
])


def script_handler(file_name, input_data):
    logger.info('Running writemongo on "{}"'.format(file_name))
    logger.info("Definitely running")

    try:
        config = Config(
            AWS=False,
            ENVIRONMENT=os.environ['ENVIRONMENT'],
            FP_INPUT='/net/efs/writemongo/input',
            MONGO_HOST=os.environ['MONGOSESSION_HOST'],
            MONGO_USER=os.environ['MONGOSESSION_USER'],
            MONGO_PASSWORD=os.environ['MONGOSESSION_PASSWORD'],
            MONGO_DATABASE=os.environ['MONGOSESSION_DATABASE'],
            MONGO_COLLECTION=os.environ['MONGOSESSION_COLLECTION'],
            MONGO_REPLICASET=os.environ['MONGOSESSION_REPLICASET'] if os.environ['MONGOSESSION_REPLICASET'] != '---' else None,
        )

        # first collection
        mongo_client = MongoClient(config.MONGO_HOST, replicaset=config.MONGO_REPLICASET)

        mongo_database = mongo_client[config.MONGO_DATABASE]

        # Authenticate
        mongo_database.authenticate(config.MONGO_USER, config.MONGO_PASSWORD,
                                    mechanism='SCRAM-SHA-1')

        mongo_collection = mongo_database[config.MONGO_COLLECTION]

        tmp_filename = os.path.join('/tmp', file_name)
        copyfile(os.path.join(config.FP_INPUT, file_name), tmp_filename)
        logger.info("Copied data file to local FS")
        data = pandas.read_csv(tmp_filename)
        os.remove(tmp_filename)
        logger.info("Removed temporary file")

        # for testing only
#        data = pandas.read_csv(file_name)

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
        date_time = datetime.datetime.strptime(str(pandas.DatetimeIndex(data['timeStamp']).round('1s')[0]),
                                               "%Y-%m-%d %H:%M:%S")
        event_date = date_time.date()
        # testing only
#        team_id = 'test_tg'
#        training_group_id = 'test_tg'
#        user_id = 'test_user'
##        training_session_log_id = 'test_tslog'
#        session_event_id = 'test_session'
#        session_type = '1'
#        user_mass = 77

        # Prep for session aggregation
        # grf
        # indicator for when grf should be present
        total_ind = numpy.array([k != 3 for k in data['phaseLF']])
        lf_ind = numpy.array([k in [0, 1, 4] for k in data['phaseLF']])
        rf_ind = numpy.array([k in [0, 2, 5] for k in data['phaseRF']])
        lf_ground = lf_ind * ~rf_ind # only lf in ground
        rf_ground = ~lf_ind * rf_ind # only rf in ground

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
        if total_grf == 0:
            total_grf = 1e-6
        lf_grf = numpy.sum(data['lf_grf'])
        if lf_grf == 0:
            lf_grf = 1e-6
        lf_only_grf = numpy.sum(data['lf_only_grf'])
        if lf_only_grf == 0:
            print('zero left')
            lf_only_grf = 1e-6
        rf_grf = numpy.sum(data['rf_grf'])
        if rf_grf == 0:
            rf_grf = 1e-6
        rf_only_grf = numpy.sum(data['rf_only_grf'])
        if rf_only_grf == 0:
            print('zero right')
            rf_only_grf = 1e-6
        lf_rf_grf = lf_only_grf + rf_only_grf

        # grf aggregation
        perc_left_grf = lf_only_grf / lf_rf_grf
        perc_right_grf = rf_only_grf / lf_rf_grf
        perc_distr = numpy.abs(perc_left_grf - perc_right_grf) * 100
        # control aggregation
        control = numpy.sum(data['control']*data['total_grf']) / total_grf
        hip_control = numpy.sum(data['hipControl']*data['total_grf']) / total_grf
        ankle_control = numpy.sum(data['ankleControl']*data['total_grf']) / total_grf
        control_lf = numpy.sum(data['controlLF']*data['lf_grf']) / lf_grf
        control_rf = numpy.sum(data['controlRF']*data['rf_grf']) / rf_grf

        # symmetry aggregation
        symmetry = numpy.sum(data['symmetry']) / total_grf
        symmetry_l = numpy.sum(data['symmetryL']) / lf_grf
        symmetry_r = numpy.sum(data['symmetryR']) / rf_grf
        hip_symmetry = numpy.sum(data['hipSymmetry']) / total_grf
        hip_symmetry_l = numpy.sum(data['hipSymmetryL']) / lf_grf
        hip_symmetry_r = numpy.sum(data['hipSymmetryR']) / rf_grf
        ankle_symmetry = numpy.sum(data['ankleSymmetry']) / total_grf
        ankle_symmetry_l = numpy.sum(data['ankleSymmetryL']) / lf_grf
        ankle_symmetry_r = numpy.sum(data['ankleSymmetryR']) / rf_grf

        # consistency aggregation
        consistency = numpy.sum(data['consistency']) / total_grf
        hip_consistency = numpy.sum(data['hipConsistency']) / total_grf
        ankle_consistency = numpy.sum(data['ankleConsistency']) / total_grf
        consistency_lf = numpy.sum(data['consistencyLF']) / lf_grf
        consistency_rf = numpy.sum(data['consistencyRF']) / rf_grf

        total_accel = numpy.sum(data['totalAccel'])
        irregular_accel = numpy.sum(data['irregularAccel'])

        session_fatigue = _fatigue_analysis(data, var='perc_optimal')

        record_out = OrderedDict({'sessonId': session_event_id})
        record_out['sessionType'] = session_type
        record_out['phaseLF'] = None
        record_out['phaseRF'] = None
        record_out['userMass'] = user_mass
        record_out['trainingGroups'] = training_group_id
        record_out['teamId'] = team_id
        record_out['userId'] = user_id
        record_out['eventDate'] = str(event_date)

        record_out['totalGRF'] = total_grf
        record_out['optimalGRF'] = const_grf
        record_out['irregularGRF'] = dest_grf
        record_out['LFgRF'] = lf_grf
        record_out['RFgRF'] = rf_grf
        record_out['control'] = control
        record_out['consistency'] = consistency
        record_out['symmetry'] = symmetry
        record_out['grfProgramComposition'] = None
        record_out['totalAccelProgramComposition'] = None
        record_out['planeProgramComposition'] = None
        record_out['stanceProgramComposition'] = None

        record_out['percLeftGRF'] = perc_left_grf
        record_out['percRightGRF'] = perc_right_grf
        record_out['percDistr'] = perc_distr

        record_out['totalAccel'] = total_accel
        record_out['irregularAccel'] = irregular_accel

        record_out['symmetryL'] = symmetry_l
        record_out['symmetryR'] = symmetry_r
        record_out['hipSymmetry'] = hip_symmetry
        record_out['hipSymmetryL'] = hip_symmetry_l
        record_out['hipSymmetryR'] = hip_symmetry_r
        record_out['ankleSymmetry'] = ankle_symmetry
        record_out['ankleSymmetryL'] = ankle_symmetry_l
        record_out['ankleSymmetryR'] = ankle_symmetry_r
        record_out['hipConsistency'] = hip_consistency
        record_out['ankleConsistency'] = ankle_consistency
        record_out['consistencyLF'] = consistency_lf
        record_out['consistencyRF'] = consistency_rf
        record_out['hipControl'] = hip_control
        record_out['ankleControl'] = ankle_control
        record_out['controlLF'] = control_lf
        record_out['controlRF'] = control_rf
        record_out['sessionFatigue'] = session_fatigue

        scor_cols = ['symmetry',
                     'symmetryL',
                     'symmetryR',
                     'hipSymmetry',
                     'hipSymmetryL',
                     'hipSymmetryR',
                     'ankleSymmetry',
                     'ankleSymmetryL',
                     'ankleSymmetryR',
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
        # Write each record one at a time.
        record_id = mongo_collection.insert_one(record_out).inserted_id

        logger.info("Wrote a record")
        return record_id

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise


def _fatigue_analysis(data, var):
    data.set_index(pandas.to_datetime(data.epochTime, unit='ms'), drop=False, inplace=True)
    groups = data.resample('2T')
    series = groups[var].mean()
#    from statsmodels.tsa.seasonal import seasonal_decompose
    series = numpy.array(series)
#    series = series.values
#    series = series[~numpy.isnan(series)]
#    result = seasonal_decompose(series, model='additive', freq=1)
#    series = result.trend
    series = series[~numpy.isnan(series)]
    coefficients = numpy.polyfit(range(len(series)), series, 1)
#    print(coefficients[0])
#    mse = residuals[0]/(len(series))
#    nrmse = numpy.sqrt(mse)/(series.max() - series.min())
    return coefficients[0]*100
#    print('Slope ' + str(coefficients[0]*100))
#    print('NRMSE: ' + str(nrmse))
#    print(result.trend)
#    print(result.seasonal)
#    print(result.resid)
#    print(result.observed)
#    print(series)
#    result.plot()
#    plt.show()

def _compute_acwr(var, period, user_id, event_date):
    """
    var: variable name to calculate for
    period: e.g. 1-day, 2-day,...10-day
    """
    mongo_collection = _connect_mongo(None)
    total_days = period*4
    start_date = event_date - total_days
    start_date = '2017-03-16'
    pipeline = [{'$match': {'userId': {'$eq': user_id},
                            'eventDate': {'$gte': start_date, '$lte': event_date}}},
                {'$group': {'_id': '$eventDate',
                            var: {'$first': str('$'+var)}}}
               ]

    docs = list(mongo_collection.aggregate(pipeline))

    hist_data = pandas.DataFrame(docs)
    return hist_data

def _connect_mongo(connection_string):
    """
    connection_string for the mongo collection
    """
#    connection_string = 'mongodb://statsUser:BioMx211@172.31.64.242,172.31.36.192,172.31.4.164:27017/?replicaSet=twoMinuteRS&authMechanism=SCRAM-SHA-1'
#    client=MongoClient(connection_string)
#    database = client['movementStats']
#    mongo_collection = database['twoMinuteStats']

    # twoMinuteStats
#    mongo_client = MongoClient('172.31.64.242,172.31.36.192,172.31.4.164', replicaset='twoMinuteRS')
#    mongo_database = mongo_client['movementStats']
    # Authenticate
#    mongo_database.authenticate('statsUser', 'BioMx211', mechanism='SCRAM-SHA-1')
#    mongo_collection = mongo_database['twoMinuteStats']

    # session
    mongo_client = MongoClient('172.31.64.60,172.31.38.53,172.31.6.25', replicaset='sessionRS')
    mongo_database = mongo_client['movementStats']
    # Authenticate
    mongo_database.authenticate('statsUser', 'BioMx211', mechanism='SCRAM-SHA-1')
    mongo_collection = mongo_database['sessionStats']

    return mongo_collection

    
if __name__ == '__main__':
    import matplotlib.pyplot as plt
    import time
    start = time.time()
    os.environ['ENVIRONMENT'] = 'Dev'
    os.environ['MONGOSESSION_HOST'] = 'ec2-34-210-169-8.us-west-2.compute.amazonaws.com:27017'
    os.environ['MONGOSESSION_USER'] = 'statsUser'
    os.environ['MONGOSESSION_PASSWORD'] = 'BioMx211'
    os.environ['MONGOSESSION_DATABASE'] = 'movementStats'
    os.environ['MONGOSESSION_COLLECTION'] = 'sessionStats_test2'
    os.environ['MONGOSESSION_REPLICASET'] = '---'
    file_name = 'C:\\Users\\Administrator\\Desktop\\python_aggregation\\605a9a17-24bf-4fdc-b539-02adbb28a628'
    perc_optimal = script_handler(file_name, input_data=None)
    print(time.time() - start)

