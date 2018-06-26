from __future__ import print_function

from collections import namedtuple
from pymongo import MongoClient
from shutil import copyfile
import logging
import os
import pandas
import numpy
import sys
from collections import OrderedDict

from active_blocks import define_blocks

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

    try:
        config = Config(
            AWS=False,
            ENVIRONMENT=os.environ['ENVIRONMENT'],
            MONGO_HOST=os.environ['MONGO_HOST_ACTIVEBLOCKS'],
            MONGO_USER=os.environ['MONGO_USER_ACTIVEBLOCKS'],
            MONGO_PASSWORD=os.environ['MONGO_PASSWORD_ACTIVEBLOCKS'],
            MONGO_DATABASE=os.environ['MONGO_DATABASE_ACTIVEBLOCKS'],
            MONGO_COLLECTION=os.environ['MONGO_COLLECTION_ACTIVEBLOCKS'],
            MONGO_REPLICASET=os.environ['MONGO_REPLICASET_ACTIVEBLOCKS'] if os.environ['MONGO_REPLICASET_ACTIVEBLOCKS'] != '---' else None,
        )

        # first collection
        mongo_client = MongoClient(config.MONGO_HOST, replicaset=config.MONGO_REPLICASET, ssl=True)

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

        team_id = input_data.get('TeamId', None)
        training_group_id = input_data.get('TrainingGroupIds', None)
        user_id = input_data.get('UserId', None)
        session_event_id = input_data.get('SessionId', None)
        user_mass = input_data.get('UserMassKg', None)
        event_date = input_data.get('EventDate')

        active_ind = numpy.array([k == 1 for k in data['active']])
        data['total_accel'] = data['total_accel'].fillna(value=numpy.nan) * active_ind
#        data['control'] = data['control'].fillna(value=numpy.nan) * active_ind
        data['control'][~active_ind] = numpy.nan
        data['aZ'][~active_ind] = numpy.nan
        data['aZ'] = numpy.abs(data['aZ'])
        # accel
        data['irregular_accel'] = data['total_accel'] * data['destr_multiplier']


        # segment data into blocks
        active_blocks = define_blocks(data['active'].values)
        print("Beginning iteration over {} blocks".format(len(active_blocks)))
        for block in active_blocks:
            print(block)
            block_start_index = active_blocks[block][0][0]
            block_end_index = active_blocks[block][-1][1]
            if block_end_index >= len(data):
                block_end_index = len(data) - 1
            block_start = str(pandas.to_datetime(data['epoch_time'][block_start_index], unit='ms'))
            block_end = str(pandas.to_datetime(data['epoch_time'][block_end_index], unit='ms'))
            block_data = data.loc[block_start_index:block_end_index, :]
            record_out = OrderedDict()
            record_out['userId'] = user_id
            record_out['eventDate'] = event_date
            record_out['userMass'] = user_mass
            record_out['teamId'] = team_id
            record_out['trainingGroups'] = training_group_id
            record_out['sessionId'] = session_event_id
            record_out['sessionType'] = '1'

            record_out['timeStart'] = block_start
            record_out['timeEnd'] = block_end

            record_out = _aggregate(block_data, record_out)

            unit_blocks = []
            for unit_block in active_blocks[block]:
                unit_block_start_index = unit_block[0]
                unit_block_end_index = unit_block[1]
                if unit_block_end_index >= len(data):
                    unit_block_end_index = len(data) - 1
                unit_block_data = data.loc[unit_block_start_index:unit_block_end_index]
                unit_block_record = OrderedDict()
                unit_block_start = str(pandas.to_datetime(data['epoch_time'][unit_block_start_index], unit='ms'))
                unit_block_end = str(pandas.to_datetime(data['epoch_time'][unit_block_end_index], unit='ms'))
                unit_block_record['timeStart'] = unit_block_start
                unit_block_record['timeEnd'] = unit_block_end

                unit_block_record = _aggregate(unit_block_data, unit_block_record)

                unit_blocks.append(unit_block_record)
            record_out['unitBlocks'] = unit_blocks

            query = {'sessionId': session_event_id, 'timeStart': block_start}
            mongo_collection.replace_one(query, record_out, upsert=True)

            logger.info("Wrote a bock record")
        return active_blocks

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise

def _aggregate(data, record):
    """Aggregates different variables for block/unitBlocks
    """
    # GRF aggregation
    record['totalGRF'] = None
    record['optimalGRF'] = None
    record['irregularGRF'] = None
    record['LFgRF'] = None
    record['RFgRF'] = None
    record['leftGRF'] = None
    record['rightGRF'] = None
    record['singleLegGRF'] = None
    record['percLeftGRF'] = None
    record['percRightGRF'] = None
    record['percLRGRFDiff'] = None

    # accel aggregation
    record['totalAccel'] = numpy.nansum(data['total_accel'])
    record['irregularAccel'] = numpy.nansum(data['irregular_accel'])

    # control aggregation
    record['control'] = numpy.sum(data['control']*data['aZ']) / numpy.sum(data['aZ'])
    record['hipControl'] = None
    record['ankleControl'] = None
    record['controlLF'] = None
    record['controlRF'] = None

    # symmetry aggregation
    record['symmetry'] = None
    record['hipSymmetry'] = None
    record['ankleSymmetry'] = None

    # consistency aggregation
    record['consistency'] = None
    record['hipConsistency'] = None
    record['ankleConsistency'] = None
    record['consistencyLF'] = None
    record['consistencyRF'] = None

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

    # fatigue
    perc_optimal_block = (record['totalAccel'] - record['irregularAccel']) / record['totalAccel']
    record['percOptimal'] = perc_optimal_block * 100
    record['percIrregular'] = (1 - perc_optimal_block) * 100

    return record
