from __future__ import print_function

from collections import namedtuple
from pymongo import MongoClient
import logging
import os
import pandas
import numpy
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
    'MONGO_COLLECTION_SESSION',
    'MONGO_COLLECTION_DATE',
    'MONGO_REPLICASET',
])


def script_handler(input_data):
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
            MONGO_COLLECTION_SESSION=os.environ['MONGOSESSION_COLLECTION'],
            MONGO_COLLECTION_DATE=os.environ['MONGODATE_COLLECTION'],
            MONGO_REPLICASET=os.environ['MONGOSESSION_REPLICASET'] if os.environ['MONGOSESSION_REPLICASET'] != '---' else None,
        )

        # Connect to mongo
        mongo_client = MongoClient(config.MONGO_HOST, replicaset=config.MONGO_REPLICASET)

        mongo_database = mongo_client[config.MONGO_DATABASE]

        # Authenticate
        mongo_database.authenticate(config.MONGO_USER, config.MONGO_PASSWORD,
                                    mechanism='SCRAM-SHA-1')

        mongo_collection_session = mongo_database[config.MONGO_COLLECTION_SESSION]
        mongo_collection_date = mongo_database[config.MONGO_COLLECTION_DATE]

        team_id = input_data.get('TeamId', None)
        training_group_id = input_data.get('TrainingGroupId', None)
        user_id = input_data.get('UserId', None)
        session_event_id = input_data.get('SessionEventId', None)
        session_type = input_data.get('SessionType', None)
        if session_type is not None:
            session_type = str(session_type)
        user_mass = input_data.get('UserMass', 155) * 4.4482

        # get all sessions
        sessions = _get_session_data(mongo_collection_session, user_id,
                                     event_date, session_type)
        # aggregate grf
        total_grf = numpy.sum(sessions.totalGRF)
        const_grf = numpy.sum(sessions.optimalGRF)
        dest_grf = numpy.sum(sessions.irregularGRF)

        # aggregate scores
        control = numpy.sum(sessions.control * sessions.totalGRF) / total_grf
        consistency = numpy.sum(sessions.consistency * sessions.totalGRF) / total_grf
        symmetry = numpy.sum(sessions.symmetry * sessions.totalGRF) / total_grf

        hist_data = _get_hist_data(mongo_collection_date, 1, user_id, event_date)

        # create ordered dictionary object
        # current variables
        record_out = OrderedDict({'teamId': team_id})
        record_out['teamId'] = team_id
        record_out['userId'] = user_id
        record_out['eventDate'] = str(event_date)
        record_out['sessionType'] = session_type

        # grf
        record_out['totalGRF'] = total_grf
        record_out['optimalGRF'] = const_grf
        record_out['irregularGRF'] = dest_grf
#        record_out['LFgRF'] = lf_grf
#        record_out['RFgRF'] = rf_grf

        # scores
        record_out['control'] = control
        record_out['consistency'] = consistency
        record_out['symmetry'] = symmetry

        # blank placeholders for programcomp
        record_out['grfProgramComposition'] = None
        record_out['totalAccelProgramComposition'] = None
        record_out['planeProgramComposition'] = None
        record_out['stanceProgramComposition'] = None
        record_out['trainingGroups'] = training_group_id

        # new variables
        record_out['userMass'] = user_mass
#        # grf distribution
        # record_out['percLeftGRF'] = perc_left_grf
        # record_out['percRightGRF'] = perc_right_grf
        # record_out['percDistr'] = perc_distr
#
#        # acceleration
#        record_out['totalAccel'] = total_accel
#        record_out['irregularAccel'] = irregular_accel
#
#        # scores
#        record_out['hipSymmetry'] = hip_symmetry
#        record_out['ankleSymmetry'] = ankle_symmetry
#        record_out['hipConsistency'] = hip_consistency
#        record_out['ankleConsistency'] = ankle_consistency
#        record_out['consistencyLF'] = consistency_lf
#        record_out['consistencyRF'] = consistency_rf
#        record_out['hipControl'] = hip_control
#        record_out['ankleControl'] = ankle_control
#        record_out['controlLF'] = control_lf
#        record_out['controlRF'] = control_rf
#
#        # fatigue data
#        record_out['percOptimal'] = perc_optimal_session
#        record_out['sessionFatigue'] = session_fatigue
        query = {'userId': user_id, 'eventDate': event_date}
        record_id = mongo_collection_date.update(query, record_out, upsert=True)
        logger.info("Wrote a record: {}".format(record_id))
        
        
    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise


def _get_session_data(collection, user_id, event_date, session_type):
    pipeline = [{'$match': {'userId': {'$eq': user_id},
                            'eventDate': {'$eq': event_date},
                            'sessionType': {'$eq': session_type}}}
               ]

    docs = list(collection.aggregate(pipeline))

    sessions = pandas.DataFrame(docs)
    return sessions


def _get_hist_data(collection, period, user_id, event_date):
    """
    var: variable name to calculate for
    period: e.g. 1-day, 2-day,...10-day
    """
#    total_days = period*4
#    start_date = event_date - total_days
    start_date = '2017-03-16'
    docs = list(collection.find({'userId': {'$eq': user_id},
                                 'eventDate': {'$gte': start_date, '$lte': event_date}},
                                 {'userId': 1, 'eventDate': 1, 'totalGRF': 1,
                                  '_id': 0}))

    hist_data = pandas.DataFrame(docs)
    return hist_data


if __name__ == '__main__':
    import time
    start = time.time()
    os.environ['ENVIRONMENT'] = 'Dev'
    os.environ['MONGOSESSION_HOST'] = 'ec2-34-210-169-8.us-west-2.compute.amazonaws.com:27017'
    os.environ['MONGOSESSION_USER'] = 'statsUser'
    os.environ['MONGOSESSION_PASSWORD'] = 'BioMx211'
    os.environ['MONGOSESSION_DATABASE'] = 'movementStats'
    os.environ['MONGOSESSION_COLLECTION'] = 'sessionStats_test2'
    os.environ['MONGODATE_COLLECTION'] = 'dateStats_test2'
    os.environ['MONGOSESSION_REPLICASET'] = '---'
    perc_optimal = script_handler(input_data=None)
    print(time.time() - start)

