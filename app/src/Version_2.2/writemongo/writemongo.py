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
            MONGO_HOST=os.environ['MONGO_HOST'],
            MONGO_USER=os.environ['MONGO_USER'],
            MONGO_PASSWORD=os.environ['MONGO_PASSWORD'],
            MONGO_DATABASE=os.environ['MONGO_DATABASE'],
            MONGO_COLLECTION=os.environ['MONGO_COLLECTION'],
            MONGO_REPLICASET=os.environ['MONGO_REPLICASET']
        )

        mongo_client = MongoClient(config.MONGO_HOST, replicaset=config.MONGO_REPLICASET)
        mongo_database = mongo_client[config.MONGO_DATABASE]

        # Authenticate
        mongo_database.authenticate(config.MONGO_USER, config.MONGO_PASSWORD, mechanism='SCRAM-SHA-1')

        mongo_collection = mongo_database[config.MONGO_COLLECTION]

        tmp_filename = os.path.join('/tmp', file_name)
        copyfile(os.path.join(config.FP_INPUT, file_name), tmp_filename)
        logger.info("Copied data file to local FS")
        data = pandas.read_csv(tmp_filename)
        os.remove(tmp_filename)
        logger.info("Removed temporary file")

        # replace nans with null
        data = data.where((pandas.notnull(data)), None)

        # resample data into 30s groups and extract start and end time for each
        # each object in mongo is a group of 30s of data
        data.set_index(pandas.to_datetime(data.epoch_time, unit='ms'), drop=False, inplace=True)
        groups = data.resample('30S')
        data_start = groups.time_stamp.min()
        data_end = groups.time_stamp.max()

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
        training_group_id = [input_data.get('TrainingGroupId', None)]
        user_id = input_data.get('UserId', None)
        training_session_log_id = input_data.get('TrainingSessionLogId', None)
        session_event_id = input_data.get('SessionEventId', None)
        session_type = input_data.get('SessionType', None)
        # create dict with movement Attribute columns and add as column
        mov_attrib_cols = ['stance',
                           'plane',
                           'rot',
                           'lat',
                           'vert',
                           'horz']
        # TODO(Stephen): Couldn't find a fast way to create ordered dict without looping. Change this if you have something better.
        data.loc[:, 'movementAttributes'] = data[mov_attrib_cols].to_dict(orient='records')

        # create dict with grf columns and add as column
        grf_cols = ['total',
                    'LF',
                    'RF',
                    'constructive',
                    'destructive',
                    'destrMultiplier',
                    'sessionGRFElapsed']
        data.loc[:, 'groundReactionForce'] = data[grf_cols].to_dict(orient='records')

        # create dict with MQ features columns and add as column
        mq_feat_cols = ['contraHipDropLF',
                        'contraHipDropRF',
                        'ankleRotLF',
                        'ankleRotRF',
                        'footPositionLF',
                        'footPositionRF',
                        'landPatternLF',
                        'landPatternRF',
                        'landTime']
        data.loc[:, 'movementQualityFeatures'] = data[mq_feat_cols].to_dict(orient='records')

        # create dict with scores columns and add as column
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
        data.loc[:, 'movementQualityScores'] = data[scor_cols].to_dict(orient='records')

        # create dict with performance variables columns and add as column
        perf_var_cols = ['rateForceAbsorptionLF',
                         'rateForceAbsorptionRF',
                         'rateForceProductionLF',
                         'rateForceProductionRF',
                         'totalAccel']
        data.loc[:, 'performanceVariables'] = data[perf_var_cols].to_dict(orient='records')

        # Prep for 30s aggregation
        # grf
        total_ind = numpy.array([k != 3 for k in data.phaseLF])
        lf_ind = numpy.array([k in [0, 1, 4] for k in data.phaseLF])
        rf_ind = numpy.array([k in [0, 2, 5] for k in data.phaseRF])
        data['total_grf'] = data['total'].fillna(value=numpy.nan) * total_ind
        data['lf_grf'] = data['total'].fillna(value=numpy.nan) * lf_ind
        data['rf_grf'] = data['total'].fillna(value=numpy.nan) * rf_ind

        record_ids = []

        keys = ['obsIndex',
                'timeStamp',
                'epochTime',
                'msElapsed',
                'sessionDuration',
                'loadingLF',
                'loadingRF',
                'phaseLF',
                'phaseRF',
                'lfImpactPhase',
                'rfImpactPhase',
                'movementAttributes',
                'groundReactionForce',
                'movementQualityFeatures',
                'movementQualityScores',
                'performanceVariables']

        logger.info("Beginning iteration over {} chunks".format(len(data_start)))

        for i, j in zip(data_start, data_end):
            # subset data into 30s chunks
            data_30 = data.loc[(data.timeStamp >= i) & (data.timeStamp <= j),]

            data_values = data_30[keys].to_dict(orient='records')

            date_time = datetime.datetime.strptime(data_30.timeStamp[0].split('.')[0],
                                                   "%Y-%m-%d %H:%M:%S")
            event_date = str(date_time.date())
            start_time = pandas.Timedelta(str(date_time.time()))

            # 30s aggregation scores
            # grf
            total_grf = numpy.sum(data_30['total_grf'])
            lf_grf = numpy.sum(data_30['lf_grf'])
            rf_grf = numpy.sum(data_30['rf_grf'])

            # control aggregation
            control = numpy.sum(data_30['control']*data_30['total_grf']) / total_grf
            hip_control = numpy.sum(data_30['hipControl']*data_30['total_grf']) / total_grf
            ankle_control = numpy.sum(data_30['ankleControl']*data_30['total_grf']) / total_grf
            control_lf = numpy.sum(data_30['controlLF']*data_30['lf_grf']) / lf_grf
            control_rf = numpy.sum(data_30['controlRF']*data_30['rf_grf']) / rf_grf

            # symmetry aggregation
            symmetry = numpy.sum(data_30['symmetry']) / total_grf
            symmetry_l = numpy.sum(data_30['symmetryL']) / lf_grf
            symmetry_r = numpy.sum(data_30['symmetryR']) / rf_grf
            hip_symmetry = numpy.sum(data_30['hipSymmetry']) / total_grf
            hip_symmetry_l = numpy.sum(data_30['hipSymmetryL']) / lf_grf
            hip_symmetry_r = numpy.sum(data_30['hipSymmetryR']) / rf_grf
            ankle_symmetry = numpy.sum(data_30['ankleSymmetry']) / total_grf
            ankle_symmetry_l = numpy.sum(data_30['ankleSymmetryL']) / lf_grf
            ankle_symmetry_r = numpy.sum(data_30['ankleSymmetryR']) / rf_grf

            # consistency aggregation
            consistency = numpy.sum(data_30['consistency']) / total_grf
            hip_consistency = numpy.sum(data_30['hipConsistency']) / total_grf
            ankle_consistency = numpy.sum(data_30['ankleConsistency']) / total_grf
            consistency_lf = numpy.sum(data_30['consistencyLF']) / lf_grf
            consistency_rf = numpy.sum(data_30['consistencyRF']) / rf_grf

            record_out = OrderedDict({'teamId': team_id})
            record_out['userId'] = user_id
            record_out['sessionEventId'] = session_event_id
            record_out['sessionType'] = session_type
            record_out['trainingSessionLogId'] = training_session_log_id
            record_out['eventDate'] = event_date
            record_out['dataStart'] = i
            record_out['dataEnd'] = j
            record_out['thirtySecondMarker'] = int(start_time / numpy.timedelta64(1, '30s'))
            record_out['twoMinuteMarker'] = int(start_time / numpy.timedelta64(1, '2m'))
            record_out['tenMinuteMarker'] = int(start_time / numpy.timedelta64(1, '10m'))
            record_out['dataValues'] = data_values
            record_out['trainingGroups'] = training_group_id

            # data for collection with aggregated values only
            record_out_agg = OrderedDict({'teamId': team_id})
            record_out_agg['userId'] = user_id
            record_out_agg['sessionEventId'] = session_event_id
            record_out_agg['sessionType'] = session_type
            record_out_agg['trainingSessionLogId'] = training_session_log_id
            record_out_agg['eventDate'] = event_date
            record_out_agg['dataStart'] = i
            record_out_agg['dataEnd'] = j
            record_out_agg['thirtySecondMarker'] = int(start_time/numpy.timedelta64(1, '30s'))
            record_out_agg['twoMinuteMarker'] = int(start_time/numpy.timedelta64(1, '2m'))
            record_out_agg['tenMinuteMarker'] = int(start_time/numpy.timedelta64(1, '10m'))
            record_out_agg['trainingGroups'] = training_group_id

            record_out_agg['totalGRF'] = total_grf
            record_out_agg['LFgRF'] = lf_grf
            record_out_agg['RFgRF'] = rf_grf
            record_out_agg['control'] = control
            record_out_agg['hipControl'] = hip_control
            record_out_agg['ankleControl'] = ankle_control
            record_out_agg['controlLF'] = control_lf
            record_out_agg['controlRF'] = control_rf
            record_out_agg['symmetry'] = symmetry
            record_out_agg['symmetryL'] = symmetry_l
            record_out_agg['symmetryR'] = symmetry_r
            record_out_agg['hipSymmetry'] = hip_symmetry
            record_out_agg['hipSymmetryL'] = hip_symmetry_l
            record_out_agg['hipSymmetryR'] = hip_symmetry_r
            record_out_agg['ankleSymmetry'] = ankle_symmetry
            record_out_agg['ankleSymmetryL'] = ankle_symmetry_l
            record_out_agg['ankleSymmetryR'] = ankle_symmetry_r
            record_out_agg['consistency'] = consistency
            record_out_agg['hipConsistency'] = hip_consistency
            record_out_agg['ankleConsistency'] = ankle_consistency
            record_out_agg['consistencyLF'] = consistency_lf
            record_out_agg['consistencyRF'] = consistency_rf

            for key, value in record_out_agg.items():
                try:
                    if numpy.isnan(value):
                        record_out_agg[key] = None
                except TypeError:
                    pass
            # Write each record one at a time.
            # TODO(Stephen): This is appended to the current collection
            record_ids.append(mongo_collection.insert_one(record_out).inserted_id)

            logger.info("Wrote a record")
            # TODO(Stephen) This needs to be inserted into the second collection
            # record_ids_agg.append(mongo2_collection.insert_one(record_out_agg).inserted_id)

        #            all_docs.append(record_out)
        # TODO(Stephen): this is alternative way to insert all at once. Haven't tested the performance of one at a time vs all at once.
        #        record_id = mongo_collection.insert_many(all_docs).inserted_ids
        logger.info("Finished writing")

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise


if __name__ == '__main__':
    input_file_name = sys.argv[1]
    script_handler(input_file_name)
