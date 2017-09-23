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
    'MONGO_HOST_SESSION',
    'MONGO_USER_SESSION',
    'MONGO_PASSWORD_SESSION',
    'MONGO_DATABASE_SESSION',
    'MONGO_REPLICASET_SESSION',
    'MONGO_COLLECTION_DATE',
    'MONGO_COLLECTION_DATETEAM',
    'MONGO_COLLECTION_DATETG',
    'MONGO_COLLECTION_TEAMAGGSTATUS',
    'MONGO_COLLECTION_TGAGGSTATUS',
    'MONGO_HOST_TWOMIN',
    'MONGO_USER_TWOMIN',
    'MONGO_PASSWORD_TWOMIN',
    'MONGO_DATABASE_TWOMIN',
    'MONGO_REPLICASET_TWOMIN',
    'MONGO_COLLECTION_TWOMIN',
    'MONGO_COLLECTION_TWOMINTEAM',
    'MONGO_COLLECTION_TWOMINTG',
])


def script_handler(input_data):
    logger.info("Running team and training groups aggregation")

    try:
        config = Config(
            AWS=False,
            ENVIRONMENT=os.environ['ENVIRONMENT'],
            MONGO_HOST_SESSION=os.environ['MONGO_HOST_SESSION'],
            MONGO_USER_SESSION=os.environ['MONGO_USER_SESSION'],
            MONGO_PASSWORD_SESSION=os.environ['MONGO_PASSWORD_SESSION'],
            MONGO_DATABASE_SESSION=os.environ['MONGO_DATABASE_SESSION'],
            MONGO_REPLICASET_SESSION=os.environ['MONGO_REPLICASET_SESSION'] if os.environ['MONGO_REPLICASET_SESSION'] != '---' else None,
            MONGO_COLLECTION_DATE=os.environ['MONGO_COLLECTION_DATE'],
            MONGO_COLLECTION_DATETEAM=os.environ['MONGO_COLLECTION_DATETEAM'],
            MONGO_COLLECTION_DATETG=os.environ['MONGO_COLLECTION_DATETG'],
            MONGO_COLLECTION_TEAMAGGSTATUS=os.environ['MONGO_COLLECTION_TEAMAGGSTATUS'],
            MONGO_COLLECTION_TGAGGSTATUS=os.environ['MONGO_COLLECTION_TGAGGSTATUS'],
            MONGO_HOST_TWOMIN=os.environ['MONGO_HOST_TWOMIN'],
            MONGO_USER_TWOMIN=os.environ['MONGO_USER_TWOMIN'],
            MONGO_PASSWORD_TWOMIN=os.environ['MONGO_PASSWORD_TWOMIN'],
            MONGO_DATABASE_TWOMIN=os.environ['MONGO_DATABASE_TWOMIN'],
            MONGO_REPLICASET_TWOMIN=os.environ['MONGO_REPLICASET_TWOMIN'] if os.environ['MONGO_REPLICASET_TWOMIN'] != '---' else None,
            MONGO_COLLECTION_TWOMIN=os.environ['MONGO_COLLECTION_TWOMIN'],
            MONGO_COLLECTION_TWOMINTEAM=os.environ['MONGO_COLLECTION_TWOMINTEAM'],
            MONGO_COLLECTION_TWOMINTG=os.environ['MONGO_COLLECTION_TWOMINTG'],
        )

        # Connect to mongo
        mongo_client_session = MongoClient(config.MONGO_HOST_SESSION,
                                           replicaset=config.MONGO_REPLICASET_SESSION)

        mongo_database_session = mongo_client_session[config.MONGO_DATABASE_SESSION]

        # Authenticate
        mongo_database_session.authenticate(config.MONGO_USER_SESSION, config.MONGO_PASSWORD_SESSION,
                                            mechanism='SCRAM-SHA-1')

        mongo_collection_tgaggstatus = mongo_database_session[config.MONGO_COLLECTION_TGAGGSTATUS]
        mongo_collection_teamaggstatus = mongo_database_session[config.MONGO_COLLECTION_TEAMAGGSTATUS]
        # mongo_collection_date = mongo_database[config.MONGO_COLLECTION_DATE]
        # get the dates/tg requiring aggregation
        tg_agg = _get_tg_agg_status(mongo_collection_tgaggstatus)
        if tg_agg.shape[0] > 0:
            logger.info("Requires TG aggregation")

        # get the dates/team requiring aggregation
        team_agg = _get_tg_agg_status(mongo_collection_teamaggstatus)
        if team_agg.shape[0] > 0:
            logger.info("Requires Team aggregation")

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise


def _get_tg_agg_status(collection):
    docs = list(collection.find({'needsAggregation': True},
                                {'trainingGroupId': 1,
                                 'eventDate': 1,
                                 '_id': 0}))
    tgs = pandas.DataFrame(docs)
    return tgs


def _get_team_agg_status(collection):
    docs = list(collection.find({'needsAggregation': True},
                                {'teamId': 1,
                                 'eventDate': 1,
                                 '_id': 0}))
    teams = pandas.DataFrame(docs)
    return teams

# def _get_hist_data(collection, period, user_id, event_date):
#     """
#     var: variable name to calculate for
#     period: e.g. 1-day, 2-day,...10-day
#     """
# #    total_days = period*4
# #    start_date = event_date - total_days
#     start_date = '2017-03-16'
#     docs = list(collection.find({'userId': {'$eq': user_id},
#                                  'eventDate': {'$gte': start_date, '$lte': event_date}},
#                                  {'userId': 1, 'eventDate': 1, 'totalGRF': 1,
#                                   '_id': 0}))

#     hist_data = pandas.DataFrame(docs)
#     return hist_data


if __name__ == '__main__':
    import time
    start = time.time()
    os.environ['ENVIRONMENT'] = 'Dev'
    os.environ['MONGO_HOST_SESSION'] = 'ec2-34-210-169-8.us-west-2.compute.amazonaws.com:27017'
    os.environ['MONGO_USER_SESSION'] = 'statsUser'
    os.environ['MONGO_PASSWORD_SESSION'] = 'BioMx211'
    os.environ['MONGO_DATABASE_SESSION'] = 'movementStats'
    os.environ['MONGO_REPLICASET_SESSION'] = '---'
    os.environ['MONGO_COLLECTION_DATE'] = 'dateStats_test2'
    os.environ['MONGO_COLLECTION_DATETEAM'] = 'dateStatsTeam_test2'
    os.environ['MONGO_COLLECTION_DATETG'] = 'dateStatsTG_test2'
    os.environ['MONGO_COLLECTION_TEAMAGGSTATUS'] = 'teamAggStatus_tmp3'
    os.environ['MONGO_COLLECTION_TGAGGSTATUS'] = 'trainingGroupAggStatus_tmp3'
    os.environ['MONGO_HOST_TWOMIN'] = 'ec2-34-210-169-8.us-west-2.compute.amazonaws.com:27017'
    os.environ['MONGO_USER_TWOMIN'] = 'statsUser'
    os.environ['MONGO_PASSWORD_TWOMIN'] = 'BioMx211'
    os.environ['MONGO_DATABASE_TWOMIN'] = 'movementStats'
    os.environ['MONGO_REPLICASET_TWOMIN'] = '---'
    os.environ['MONGO_COLLECTION_TWOMIN'] = 'twoMinuteStats_test2'
    os.environ['MONGO_COLLECTION_TWOMINTEAM'] = 'twoMinuteStatsTeam_test2'
    os.environ['MONGO_COLLECTION_TWOMINTG'] = 'twoMinuteStatsTG_test2'

    script_handler(input_data=None)
    print(time.time() - start)
