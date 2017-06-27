from __future__ import print_function

from collections import namedtuple
from pymongo import MongoClient
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
])


def script_handler(file_name):

    logger.info('Running writemongo on "{}"'.format(file_name))

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
        )

        mongo_client = MongoClient(config.MONGO_HOST)
        mongo_database = mongo_client[config.MONGO_DATABASE]

        # Authenticate
        mongo_database.authenticate(config.MONGO_USER, config.MONGO_PASSWORD, mechanism='SCRAM-SHA-1')

        mongo_collection = mongo_database[config.MONGO_COLLECTION]

        data = pandas.read_csv(os.path.join(config.FP_INPUT, file_name))
        # replace nans with nul
        data = data.where((pandas.notnull(data)), None)

        # resample data into 30s groups and extract start and end time for each
        # each object in mongo is a group of 30s of data
        data.set_index(pandas.to_datetime(data.epoch_time, unit='ms'), drop=False, inplace=True)
        groups = data.resample('30S')
        dataStart = groups.time_stamp.min()
        dataEnd = groups.time_stamp.max()

        #TODO(Stephen) dummy values these need to be read from db
        team_id = 'test_team'
        training_group_id = ['tg_1', 'tg_2']
        user_id = 'test_user'
        training_session_log_id = 'ts_log'
        session_event_id = 'first_event'
        session_type = str(1)
        # all_docs = []
        record_ids = []
        for i, j in zip(dataStart, dataEnd):
            # subset data into 30s chunks
            data_30 = data.loc[(data.time_stamp>=i) & (data.time_stamp<=j), ]
            # create dict with movement Attribute columns and add as column
            mov_attrib_cols = ['stance',
                               'plane',
                               'rot',
                               'lat',
                               'vert',
                               'horz']
            #TODO(Stephen): Couldn't find a fast way to create ordered dict without looping. Change this if you have something better.
            data_30.loc[:,'movementAttributes'] = data_30[mov_attrib_cols].to_dict(orient='records')
        
            # create dict with grf columns and add as column
            grf_cols = ['grf',
                        'grf_lf',
                        'grf_rf',
                        'const_grf',
                        'destr_grf',
                        'destr_multiplier',
                        'session_grf_elapsed']
            data_30.loc[:,'groundReactionForce'] = data_30[grf_cols].to_dict(orient='records')
        
            # create dict with MQ features columns and add as column
            mq_feat_cols = ['contra_hip_drop_lf',
                            'contra_hip_drop_rf',
                            'ankle_rot_lf',
                            'ankle_rot_rf',
                            'foot_position_lf',
                            'foot_position_rf',
                            'land_pattern_lf',
                            'land_pattern_rf',
                            'land_time']
            data_30.loc[:,'movementQualityFeatures'] = data_30[mq_feat_cols].to_dict(orient='records')
        
            # create dict with scores columns and add as column
            scor_cols = ['symmetry',
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
                         'control_rf']
            data_30.loc[:,'movementQualityScores'] = data_30[scor_cols].to_dict(orient='records')
        
            # create dict with performance variables columns and add as column
            perf_var_cols = ['rate_force_absorption_lf',
                             'rate_force_absorption_rf',
                             'rate_force_production_lf',
                             'rate_force_production_rf',
                             'total_accel']
            data_30.loc[:,'performanceVariables'] = data_30[perf_var_cols].to_dict(orient='records')
        
            keys = ['obs_index',
                    'time_stamp',
                    'epoch_time',
                    'ms_elapsed', 
                    'session_duration',
                    'loading_lf',
                    'loading_rf',
                    'phase_lf',
                    'phase_rf',
                    'impact_phase_lf',
                    'impact_phase_rf',
                    'movementAttributes',
                    'groundReactionForce',
                    'movementQualityFeatures',
                    'movementQualityScores',
                    'performanceVariables']

            dataValues = data_30[keys].to_dict(orient='records')

            date_time = datetime.datetime.strptime(data_30.time_stamp[0].split('.')[0],
                                                   "%Y-%m-%d %H:%M:%S")
            eventDate = str(date_time.date())
            start_time = pandas.Timedelta(str(date_time.time()))
            
            record_out = OrderedDict({'teamId': team_id})
            record_out['userId'] =  user_id
            record_out['sessionEventId'] = session_event_id
            record_out['sessionType'] = session_type
            record_out['trainingSessionLogId'] = training_session_log_id
            record_out['eventDate'] = eventDate
            record_out['dataStart'] = i
            record_out['dataEnd'] = j
            record_out['thirtySecondMarker'] = int(start_time/numpy.timedelta64(1, '30s'))
            record_out['twoMinuteMarker'] = int(start_time/numpy.timedelta64(1, '2m'))
            record_out['tenMinuteMarker'] = int(start_time/numpy.timedelta64(1, '10m'))
            record_out['dataValues'] = dataValues
            record_out['trainingGroups'] = training_group_id
            # Write each record one at a time.
            record_ids.append(mongo_collection.insert_one(record_out).inserted_id)
#            all_docs.append(record_out)
#TODO(Stephen): this is alternative way to insert all at once. Haven't tested the performance of one at a time vs all at once.
#        record_id = mongo_collection.insert_many(all_docs).inserted_ids


    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise


if __name__ == '__main__':
    input_file_name = sys.argv[1]
    script_handler(input_file_name)
