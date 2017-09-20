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
            MONGO_HOST=os.environ['MONGOTWOMIN_HOST'],
            MONGO_USER=os.environ['MONGOTWOMIN_USER'],
            MONGO_PASSWORD=os.environ['MONGOTWOMIN_PASSWORD'],
            MONGO_DATABASE=os.environ['MONGOTWOMIN_DATABASE'],
            MONGO_COLLECTION=os.environ['MONGOTWOMIN_COLLECTION'],
            MONGO_REPLICASET=os.environ['MONGOTWOMIN_REPLICASET'] if os.environ['MONGOTWOMIN_REPLICASET'] != '---' else None,
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
        session_event_id = input_data.get('SessionEventId', None)
        session_type = input_data.get('SessionType', None)
        if session_type is not None:
            session_type = str(session_type)
        user_mass = input_data.get('UserMass', 155) * 4.4482
        date_time = datetime.datetime.strptime(str(pandas.DatetimeIndex(data['timeStamp']).round('1s')[0]),
                                               "%Y-%m-%d %H:%M:%S")
        event_date = date_time.date()

        # replace nans with None
        data = data.where((pandas.notnull(data)), None)
        print("Filtered out null values")

        # resample data into 2m groups and extract start and end time for each
        # each object in mongo is a group of 30s of data
        data.set_index(pandas.to_datetime(data.epochTime, unit='ms'), drop=False, inplace=True)
        groups = data.resample('2T')
        data_start = groups.timeStamp.min()
        data_end = groups.timeStamp.max()
        print("Resampled into 2m chunks")

        # Prep for 2min aggregation
        # grf
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


        print("Beginning iteration over {} chunks".format(len(data_start)))
        record_ids = []
        total_accumulated_grf = 0
        optimal_accumulated_grf = 0
        irregular_accumulated_grf = 0
        for i, j in zip(data_start, data_end):

            data_2m = data.loc[(data.timeStamp >= i) & (data.timeStamp <= j), ]
            try:
                date_time = datetime.datetime.strptime(str(pandas.DatetimeIndex(data_2m.timeStamp).round('1s')[0]),
                                                       "%Y-%m-%d %H:%M:%S")
            except IndexError:
                print("i: {}".format(i))
                print("j: {}".format(j))
                print(len(data_2m))
            event_date = date_time.date()
            start_time = pandas.Timedelta(str(date_time.time()))

            # Aggregated values
            total_grf = numpy.sum(data_2m['total_grf'])
            total_accumulated_grf += total_grf
            const_grf = numpy.nansum(data_2m['const_grf'])
            optimal_accumulated_grf += const_grf
            dest_grf = numpy.nansum(data_2m['dest_grf'])
            irregular_accumulated_grf += dest_grf
            perc_optimal_session = const_grf / (const_grf + dest_grf)
            if total_grf == 0:
                total_grf = 1e-6
            lf_grf = numpy.sum(data_2m['lf_grf'])
            if lf_grf == 0:
                lf_grf = 1e-6
            lf_only_grf = numpy.sum(data_2m['lf_only_grf'])
            if lf_only_grf == 0:
                print('zero left')
                lf_only_grf = 1e-6
            rf_grf = numpy.sum(data_2m['rf_grf'])
            if rf_grf == 0:
                rf_grf = 1e-6
            rf_only_grf = numpy.sum(data_2m['rf_only_grf'])
            if rf_only_grf == 0:
                print('zero right')
                rf_only_grf = 1e-6
            lf_rf_grf = lf_only_grf + rf_only_grf

            # grf aggregation
            perc_left_grf = lf_only_grf / lf_rf_grf
            perc_right_grf = rf_only_grf / lf_rf_grf
            perc_distr = numpy.abs(perc_left_grf - perc_right_grf) * 100
            # control aggregation
            control = numpy.sum(data_2m['control']*data_2m['total_grf']) / total_grf
            hip_control = numpy.sum(data_2m['hipControl']*data_2m['total_grf']) / total_grf
            ankle_control = numpy.sum(data_2m['ankleControl']*data_2m['total_grf']) / total_grf
            control_lf = numpy.sum(data_2m['controlLF']*data_2m['lf_grf']) / lf_grf
            control_rf = numpy.sum(data_2m['controlRF']*data_2m['rf_grf']) / rf_grf

            # symmetry aggregation
            symmetry = numpy.sum(data_2m['symmetry']) / total_grf
            hip_symmetry = numpy.sum(data_2m['hipSymmetry']) / total_grf
            ankle_symmetry = numpy.sum(data_2m['ankleSymmetry']) / total_grf

            # consistency aggregation
            consistency = numpy.sum(data_2m['consistency']) / total_grf
            hip_consistency = numpy.sum(data_2m['hipConsistency']) / total_grf
            ankle_consistency = numpy.sum(data_2m['ankleConsistency']) / total_grf
            consistency_lf = numpy.sum(data_2m['consistencyLF']) / lf_grf
            consistency_rf = numpy.sum(data_2m['consistencyRF']) / rf_grf

            # acceleration aggregation
            total_accel = numpy.sum(data_2m['totalAccel'])
            irregular_accel = numpy.sum(data_2m['irregularAccel'])
            two_min_index = int(start_time/numpy.timedelta64(1, '2m'))

            # create ordered dictionary object
            # current variables
            record_out = OrderedDict({'twoMinuteIndex': two_min_index})
            record_out['sessonId'] = session_event_id
            record_out['sessionType'] = session_type
            record_out['timeStart'] = i
            record_out['phaseLF'] = None
            record_out['phaseRF'] = None

            # component scores
            record_out['hipControl'] = hip_control
            record_out['controlLF'] = control_lf
            record_out['controlRF'] = control_rf
            record_out['hipSymmetry'] = hip_symmetry
            record_out['ankleSymmetry'] = ankle_symmetry
            record_out['hipConsistency'] = hip_consistency
            record_out['consistencyLF'] = consistency_lf
            record_out['consistencyRF'] = consistency_rf
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

            # accumulated grf
            record_out['totalAccumulatedGRF'] = total_accumulated_grf
            record_out['optimalAccumulatedGRF'] = optimal_accumulated_grf
            record_out['irregularAccumulatedGRF'] = irregular_accumulated_grf

            # new variables
            # grf
            record_out['userMass'] = user_mass
            record_out['percLeftGRF'] = perc_left_grf
            record_out['percRightGRF'] = perc_right_grf
            record_out['percDistr'] = perc_distr

            # acceleration
            record_out['totalAccel'] = total_accel
            record_out['irregularAccel'] = irregular_accel

            # component scores
            record_out['ankleConsistency'] = ankle_consistency
            record_out['ankleControl'] = ankle_control

            # fatigue
            record_out['percOptimal'] = perc_optimal_session

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
            record_ids.append(mongo_collection.insert_one(record_out).inserted_id)
#            break

            logger.info("Wrote a record")
        return record_ids

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise

if __name__ == '__main__':
    import time
    start = time.time()
    os.environ['ENVIRONMENT'] = 'Dev'
    os.environ['MONGOTWOMIN_HOST'] = 'ec2-34-210-169-8.us-west-2.compute.amazonaws.com:27017'
    os.environ['MONGOTWOMIN_USER'] = 'statsUser'
    os.environ['MONGOTWOMIN_PASSWORD'] = 'BioMx211'
    os.environ['MONGOTWOMIN_DATABASE'] = 'movementStats'
    os.environ['MONGOTWOMIN_COLLECTION'] = 'twoMinuteStats_test2'
    os.environ['MONGOTWOMIN_REPLICASET'] = '---'
    in_file_name = 'C:\\Users\\Administrator\\Desktop\\python_aggregation\\605a9a17-24bf-4fdc-b539-02adbb28a628'
    perc_optimal = script_handler(in_file_name, input_data=None)
    print(time.time() - start)

