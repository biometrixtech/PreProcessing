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
    'MONGO_HOST',
    'MONGO_USER',
    'MONGO_PASSWORD',
    'MONGO_DATABASE',
    'MONGO_COLLECTION',
    'MONGO_REPLICASET',
])


def script_handler(working_directory, file_name, input_data):
    logger.info('Running twoMinAgg on "{}"'.format(file_name))
    logger.info("Definitely running")

    try:
        config = Config(
            AWS=False,
            ENVIRONMENT=os.environ['ENVIRONMENT'],
            MONGO_HOST=os.environ['MONGO_HOST_TWOMIN'],
            MONGO_USER=os.environ['MONGO_USER_TWOMIN'],
            MONGO_PASSWORD=os.environ['MONGO_PASSWORD_TWOMIN'],
            MONGO_DATABASE=os.environ['MONGO_DATABASE_TWOMIN'],
            MONGO_COLLECTION=os.environ['MONGO_COLLECTION_TWOMIN'],
            MONGO_REPLICASET=os.environ['MONGO_REPLICASET_TWOMIN'] if os.environ['MONGO_REPLICASET_TWOMIN'] != '---' else None,
        )

        # first collection
        mongo_client = MongoClient(config.MONGO_HOST, replicaset=config.MONGO_REPLICASET)

        mongo_database = mongo_client[config.MONGO_DATABASE]

        # Authenticate
        mongo_database.authenticate(config.MONGO_USER, config.MONGO_PASSWORD,
                                    mechanism='SCRAM-SHA-1')

        mongo_collection = mongo_database[config.MONGO_COLLECTION]

        tmp_filename = '/tmp/readfile'
        copyfile(os.path.join(working_directory, 'scoring_chunked', file_name), tmp_filename)
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
        session_event_id = input_data.get('SessionId', None)
        user_mass = input_data.get('UserMassKg', None)
        date_time = datetime.datetime.strptime(str(pandas.DatetimeIndex(data['timeStamp']).round('1s')[0]),
                                               "%Y-%m-%d %H:%M:%S")
        # event_date = date_time.date()
        event_date = input_data.get('EventDate')

        # replace nans with None
        # data = data.where((pandas.notnull(data)), None)
        # print("Filtered out null values")

        # resample data into 2m groups and extract start and end time for each
        # each object in mongo is a group of 30s of data
        data.set_index(pandas.to_datetime(data.epochTime, unit='ms'), drop=False, inplace=True)
        groups = data.resample('2T')
        data_start = groups.timeStamp.min()
        data_end = groups.timeStamp.max()
        print("Resampled into 2m chunks")

        # Prep for 2min aggregation
        # grf
        total_ind = numpy.array([numpy.isfinite(k) for k in data['constructive']])
        lf_ind = numpy.array([k in [0, 1, 4, 6] for k in data['phaseLF']])
        rf_ind = numpy.array([k in [0, 2, 5, 7] for k in data['phaseRF']])
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
            # event_date = date_time.date()
            start_time = pandas.Timedelta(str(date_time.time()))

            # Aggregated values
            total_grf = numpy.sum(data_2m['total_grf'])
            # const_grf = numpy.nansum(data_2m['const_grf'])
            # dest_grf = numpy.nansum(data_2m['dest_grf'])
            if const_grf == 0:
                const_grf = 1e-6
            if dest_grf == 0:
                dest_grf = 1e-6
            perc_optimal_twomin = const_grf / (const_grf + dest_grf)
            if total_grf == 0 or numpy.isnan(total_grf):
                total_grf = 1e-6
            lf_grf = numpy.sum(data_2m['lf_grf'])
            if lf_grf == 0  or numpy.isnan(lf_grf):
                lf_grf = 1e-6
            lf_only_grf = numpy.sum(data_2m['lf_only_grf'])
            # if lf_only_grf == 0  or numpy.isnan(lf_only_grf):
                # print('zero left')
                # lf_only_grf = 1e-6
            rf_grf = numpy.sum(data_2m['rf_grf'])
            if rf_grf == 0 or numpy.isnan(rf_grf):
                rf_grf = 1e-6
            rf_only_grf = numpy.sum(data_2m['rf_only_grf'])
            # if rf_only_grf == 0 or numpy.isnan(rf_only_grf):
                # print('zero right')
                # rf_only_grf = 1e-6
            lf_rf_grf = lf_only_grf + rf_only_grf

            # grf aggregation
            if lf_only_grf == 0.  or numpy.isnan(lf_only_grf) or rf_only_grf == 0. or numpy.isnan(rf_only_grf):
                perc_distr = 0.
                perc_left_grf = None
                perc_right_grf = None
            else:
                perc_left_grf = lf_only_grf / lf_rf_grf * 100
                perc_right_grf = rf_only_grf / lf_rf_grf * 100
                perc_distr = numpy.abs(perc_left_grf - perc_right_grf) 

            # update perc_optimal to take into account grf distribution
            perc_optimal_twomin = (2. * perc_optimal_twomin + (1. - perc_distr / 100.)**2 ) / 3.
            # update optimal and irregular grf with new definition of perc_optimal
            const_grf = perc_optimal_twomin * total_grf
            dest_grf = (1. - perc_optimal_twomin) * total_grf

            total_accumulated_grf += total_grf
            optimal_accumulated_grf += const_grf
            irregular_accumulated_grf += dest_grf

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
            total_accel = numpy.nansum(data_2m['totalAccel'])
            irregular_accel = numpy.nansum(data_2m['irregularAccel'])
            two_min_index = int(start_time/numpy.timedelta64(1, '2m'))

            # create ordered dictionary object
            # current variables
            record_out = OrderedDict({'twoMinuteIndex': two_min_index})
            record_out['sessionId'] = session_event_id
            record_out['sessionType'] = '1'
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
            record_out['leftGRF'] = lf_only_grf
            record_out['rightGRF'] = rf_only_grf
            record_out['singleLegGRF'] = lf_rf_grf
            record_out['percLeftGRF'] = perc_left_grf
            record_out['percRightGRF'] = perc_right_grf
            record_out['percLRGRFDiff'] = perc_distr

            # acceleration
            record_out['totalAccel'] = total_accel
            record_out['irregularAccel'] = irregular_accel

            # component scores
            record_out['ankleConsistency'] = ankle_consistency
            record_out['ankleControl'] = ankle_control

            # fatigue
            record_out['percOptimal'] = perc_optimal_twomin * 100
            record_out['percIrregular'] = (1 - perc_optimal_twomin) * 100

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
            query = {'sessionId': session_event_id, 'twoMinuteIndex': two_min_index}
            mongo_collection.replace_one(query, record_out, upsert=True)

            logger.info("Wrote a record")
        return record_ids

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise
