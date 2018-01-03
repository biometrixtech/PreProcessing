from __future__ import print_function

from collections import namedtuple
from pymongo import MongoClient
import logging
import os
import sys
from collections import OrderedDict

from vars_in_mongo import prog_comp_vars

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
    'MONGO_COLLECTION_PROGCOMP',
    'MONGO_COLLECTION_PROGCOMPDATE',
    'MONGO_REPLICASET',
])


def script_handler(input_data):
    logger.info('Running program composition date aggregation')

    try:
        config = Config(
            AWS=False,
            ENVIRONMENT=os.environ['ENVIRONMENT'],
            MONGO_HOST=os.environ['MONGO_HOST_SESSION'],
            MONGO_USER=os.environ['MONGO_USER_SESSION'],
            MONGO_PASSWORD=os.environ['MONGO_PASSWORD_SESSION'],
            MONGO_DATABASE=os.environ['MONGO_DATABASE_SESSION'],
            MONGO_COLLECTION_PROGCOMP=os.environ['MONGO_COLLECTION_PROGCOMP'],
            MONGO_COLLECTION_PROGCOMPDATE=os.environ['MONGO_COLLECTION_PROGCOMPDATE'],
            MONGO_REPLICASET=os.environ['MONGO_REPLICASET_SESSION'] if os.environ['MONGO_REPLICASET_SESSION'] != '---' else None,
        )

        # Connect to session mongo
        mongo_client = MongoClient(config.MONGO_HOST, replicaset=config.MONGO_REPLICASET)
        mongo_database = mongo_client[config.MONGO_DATABASE]
        # Authenticate
        mongo_database.authenticate(config.MONGO_USER, config.MONGO_PASSWORD, mechanism='SCRAM-SHA-1')
        
# TODO: replace this testing part to read from correct collection
        # read from prod for testing
        # mongo_client = MongoClient('172.31.64.60,172.31.38.53,172.31.6.25', replicaset='sessionRS')
        # mongo_database = mongo_client['movementStats']
        # # Authenticate
        # mongo_database.authenticate('statsUser', 'BioMx211', mechanism='SCRAM-SHA-1')
        # mongo_collection_progcomp_test = mongo_database['progCompDateStats']

        # connect to all relevant collections
        mongo_collection_progcomp = mongo_database[config.MONGO_COLLECTION_PROGCOMP]
        mongo_collection_progcompdate = mongo_database[config.MONGO_COLLECTION_PROGCOMPDATE]
        
#        team_id = input_data.get('TeamId', None)
        user_id = input_data.get('UserId', None)
        session_type = input_data.get('SessionType', None)
        if session_type is not None:
            session_type = str(session_type)
        event_date = input_data.get('EventDate')

        data_out = {}
        data_out['teamId'] = input_data.get('TeamId', None)
        data_out['trainingGroups'] = input_data.get('TrainingGroupId', None)
        data_out['userId'] = input_data.get('UserId', None)
        data_out['sessionType'] = input_data.get('SessionType', None)
        if data_out['sessionType'] is not None:
            data_out['sessionType'] = str(data_out['sessionType'])
        data_out['eventDate'] = input_data.get('EventDate', None)

         # Add program composition lists to date data
        prog_comps = ['grf', 'totalAccel', 'plane', 'stance']
        for var in prog_comps:
             out_var = var+'ProgramComposition'
             data_out[out_var] = _aggregate_progcomp(mongo_collection_progcomp, var,
                                                     user_id=user_id, event_date=event_date,
                                                     session_type=session_type)
        # For team date data, sort the variables in order
        record_out = OrderedDict()
        for prog_var in prog_comp_vars:
            try:
                record_out[prog_var] = data_out[prog_var]
            except KeyError:
                record_out[prog_var] = None

        # Upsert the date aggregated collection to mongo (currently replace)
        query = {'userId': user_id, 'eventDate': event_date}
        mongo_collection_progcompdate.replace_one(query, record_out, upsert=True)

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise


def _aggregate_progcomp(collection, var, user_id, event_date, session_type):
    """Aggregate progComp for the user
    """
    prog_var = '$'+var+'ProgramComposition'
    pipeline = [{'$match': {'userId': {'$eq': user_id},
                            'eventDate': {'$eq': event_date},
                            'sessionType': {'$eq': session_type}
                           }
                },
                {'$unwind': prog_var},
                {'$group': {'_id': {'binNumber': prog_var+".binNumber"},
                            'sessionCount': {'$sum': 1},
                            'binNumber': {'$first': prog_var+".binNumber"},
                            'min': {'$first': prog_var+'.min'},
                            'max': {'$first': prog_var+'.max'},
                            'totalGRF': {'$avg': prog_var+'.totalGRF'},
                            'optimalGRF': {'$avg': prog_var+'.optimalGRF'},
                            'irregularGRF': {'$avg': prog_var+'.irregularGRF'},
                            'totalAcceleration': {'$avg': prog_var+'.totalAcceleration'},
                            'msElapsed': {'$avg': prog_var+'.msElapsed'}
                            }
                }
               ]
    docs = list(collection.aggregate(pipeline))
    bins = []
    for doc in docs:
        single_bin = OrderedDict({'min': doc['min']})
        single_bin['max'] = doc['max']
        single_bin['binNumber'] = doc['binNumber']
        single_bin['totalGRF'] = doc['totalGRF']
        single_bin['optimalGRF'] = doc['optimalGRF']
        single_bin['irregularGRF'] = doc['irregularGRF']
        single_bin['totalAcceleration'] = doc['totalAcceleration']
        single_bin['msElapsed'] = doc['msElapsed']
        if doc['totalGRF'] == 0 or doc['totalGRF'] is None:
            single_bin['percOptimal'] = None
            single_bin['percIrregular'] = None
        else:
            single_bin['percOptimal'] = doc['optimalGRF'] / doc['totalGRF'] * 100
            single_bin['percIrregular'] = doc['irregularGRF'] / doc['totalGRF'] * 100
        bins.append(single_bin)

    return sorted(bins, key=lambda k: k['binNumber'])

if __name__ == '__main__':
    import time
    start = time.time()
    input_data = OrderedDict()
    input_data['TeamId'] = 'test_team'
    input_data['TrainingGroupId'] = ['test_tg1', 'test_tg2']
    input_data['UserId'] = 'test_user'
    input_data['SessionEventId'] = 'test_session'
    input_data['SessionType'] = '1'
    input_data['UserMass'] = 133
    input_data['EventDate'] = '2017-03-20'

    os.environ['ENVIRONMENT'] = 'Dev'
    os.environ['MONGO_HOST_SESSION'] = 'ec2-34-210-169-8.us-west-2.compute.amazonaws.com:27017'
    os.environ['MONGO_USER_SESSION'] = 'statsUser'
    os.environ['MONGO_PASSWORD_SESSION'] = 'BioMx211'
    os.environ['MONGO_DATABASE_SESSION'] = 'movementStats'
    os.environ['MONGO_COLLECTION_PROGCOMP'] = 'progCompStats_test2'
    os.environ['MONGO_COLLECTION_PROGCOMPDATE'] = 'progCompDateStats_test2'
    os.environ['MONGO_REPLICASET_SESSION'] = '---'
    file_name = 'C:\\Users\\Administrator\\Desktop\\python_aggregation\\605a9a17-24bf-4fdc-b539-02adbb28a628'
    prog_comp = script_handler(input_data)
    print(time.time() - start)
