from __future__ import print_function


import os
import datetime
from shutil import copyfile
from collections import namedtuple, OrderedDict

import numpy
import pandas
from pymongo import MongoClient


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

def connect_mongo(config):
    """Get mongo client connection
    """
    # first collection
    mongo_client = MongoClient(config.MONGO_HOST, replicaset=config.MONGO_REPLICASET)

    mongo_database = mongo_client[config.MONGO_DATABASE]

    # Authenticate
    mongo_database.authenticate(config.MONGO_USER, config.MONGO_PASSWORD,
                                mechanism='SCRAM-SHA-1')

    return mongo_database[config.MONGO_COLLECTION]


#def get_ids(input_data):
#    team_id = input_data.get('TeamId', None)
#    training_group_id = input_data.get('TrainingGroupIds', None)
#    user_id = input_data.get('UserId', None)
#    session_event_id = input_data.get('SessionId', None)
#    user_mass = input_data.get('UserMassKg', None)
#    event_date = input_data.get('EventDate')
#
#    return team_id, training_group_id, user_id, session_event_id, user_mass, event_date


def script_handler(working_directory, file_name, input_data):
    print('Running twoMinAgg on "{}"'.format(file_name))
    print("Definitely running")

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
        mongo_collection = connect_mongo(config)


        tmp_filename = '/tmp/readfile'
#        copyfile(os.path.join(working_directory, 'scoring_chunked', file_name), tmp_filename)
        copyfile(os.path.join(working_directory, 'scoring'), tmp_filename)
        print("Copied data file to local FS")
        data = pandas.read_csv(tmp_filename)
        os.remove(tmp_filename)
        print("Removed temporary file")
#        return data

        # resample data into 2m groups and extract start and end time for each
        # each object in mongo is a group of 2min of data
        data.set_index(pandas.to_datetime(data['epoch_time'], unit='ms'), drop=False, inplace=True)
        groups = data.resample('2T')
        data_start = groups.time_stamp.min()
        data_end = groups.time_stamp.max()
        print("Resampled into 2m chunks")

        # Prep for 2min aggregation
        active_ind = numpy.array([k == 1 for k in data['active']])
        data['total_accel'] = data['total_accel'].fillna(value=numpy.nan) * active_ind
#        data['control'][~active_ind] = numpy.nan
        data['aZ'][~active_ind] = numpy.nan
        data['aZ'] = numpy.abs(data['aZ'])

        # accel
        data['irregular_accel'] = data['total_accel'] * data['destr_multiplier']
        print("Beginning iteration over {} chunks".format(len(data_start)))
        for i, j in zip(data_start, data_end):

            import time
            st_time = time.time()

            data_2m = data.loc[(data['time_stamp'] >= i) & (data['time_stamp'] <= j), ]
            try:
                date_time = datetime.datetime.strptime(str(pandas.to_datetime(data_2m['epoch_time'][0], unit='ms').round('1s')),
                                                       "%Y-%m-%d %H:%M:%S")

#                date_time = datetime.datetime.strptime(str(pandas.DatetimeIndex(data_2m['time_stamp']).round('1s')[0]),
#                                                       "%Y-%m-%d %H:%M:%S")
            except IndexError:
                print("i: {}".format(i))
                print("j: {}".format(j))
                print(len(data_2m))
            start_time = pandas.Timedelta(str(date_time.time()))
            two_min_index = int(start_time/numpy.timedelta64(1, '2m'))

            # create ordered dictionary object
            # current variables
            record_out = OrderedDict({'twoMinuteIndex': two_min_index})
            record_out['sessionId'] = input_data.get('SessionId', None)
            record_out['sessionType'] = '1'
            record_out['timeStart'] = i
            record_out['phaseLF'] = None
            record_out['phaseRF'] = None
            record_out['trainingGroups'] = input_data.get('TrainingGroupIds', None)
            record_out['teamId'] = input_data.get('TeamId', None)
            record_out['userId'] = input_data.get('UserId', None)
            record_out['eventDate'] = str(input_data.get('EventDate'))
            record_out['userMass'] = input_data.get('UserMassKg', None)

            record_out = _aggregate(data_2m, record_out)

            # Write the record to mongo
            query = {'sessionId': record_out['sessionId'], 'twoMinuteIndex': two_min_index}
            mongo_collection.replace_one(query, record_out, upsert=True)

            print("Wrote a record")
            print(time.time() - st_time)

    except Exception as e:
        print(e)
        print('Process did not complete successfully! See error below!')
        raise

def _aggregate(data, record):
    """Aggregates different variables for block/unitBlocks
    """
#     component scores
    record['hipControl'] = None
    record['controlLF'] = None
    record['controlRF'] = None
    record['hipSymmetry'] = None
    record['ankleSymmetry'] = None
    record['hipConsistency'] = None
    record['consistencyLF'] = None
    record['consistencyRF'] = None

    # GRF aggregation
    record['totalGRF'] = None
    record['optimalGRF'] = None
    record['irregularGRF'] = None
    record['LFgRF'] = None
    record['RFgRF'] = None

    # scores aggregation
    z_accel = numpy.sum(data['aZ'])
    if z_accel > 0:
        record['control'] = numpy.sum(data['control']*data['aZ']) / numpy.sum(data['aZ'])
    else:
        record['control'] = None
    record['symmetry'] = None
    record['consistency'] = None

    # accumulated grf
    record['totalAccumulatedGRF'] = None
    record['optimalAccumulatedGRF'] = None
    record['irregularAccumulatedGRF'] = None

    record['leftGRF'] = None
    record['rightGRF'] = None
    record['singleLegGRF'] = None
    record['percLeftGRF'] = None
    record['percRightGRF'] = None
    record['percLRGRFDiff'] = None

    # accel aggregation
    record['totalAccel'] = numpy.nansum(data['total_accel'])
    record['irregularAccel'] = numpy.nansum(data['irregular_accel'])

    # component scores
    record['ankleConsistency'] = None
    record['ankleControl'] = None

    # fatigue
    if record['totalAccel'] == 0:
        record['totalAccel'] = None
        record['irregularAccel'] = None
        record['percOptimal'] = None
        record['percIrregular'] = None
    else:
        perc_optimal_2min = (record['totalAccel'] - record['irregularAccel']) / record['totalAccel']
        record['percOptimal'] = perc_optimal_2min * 100
        record['percIrregular'] = (1 - perc_optimal_2min) * 100

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

    return record
