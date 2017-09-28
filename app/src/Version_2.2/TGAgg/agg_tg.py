from __future__ import print_function

from collections import namedtuple
from pymongo import MongoClient
import logging
import os
import pandas
import numpy
import sys
from collections import OrderedDict
from vars_in_mongo import athlete_vars, tg_vars, tg_twomin_vars, athlete_twomin_vars

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

Config = namedtuple('Config', [
    'AWS',
    'ENVIRONMENT',
    'FP_INPUT',
    'MONGO_HOST_SESSION',
    'MONGO_USER_SESSION',
    'MONGO_PASSWORD_SESSION',
    'MONGO_DATABASE_SESSION',
    'MONGO_REPLICASET_SESSION',
    'MONGO_COLLECTION_DATE',
    'MONGO_COLLECTION_DATETG',
    'MONGO_COLLECTION_PROGCOMP',
    'MONGO_HOST_TWOMIN',
    'MONGO_USER_TWOMIN',
    'MONGO_PASSWORD_TWOMIN',
    'MONGO_DATABASE_TWOMIN',
    'MONGO_REPLICASET_TWOMIN',
    'MONGO_COLLECTION_TWOMIN',
    'MONGO_COLLECTION_TWOMINTG',
])


def script_handler(input_data):
    logger.info("Running training groups aggregation")

    try:
        config = Config(
            AWS=False,
            ENVIRONMENT=os.environ['ENVIRONMENT'],
            FP_INPUT='/net/efs/writemongo/input',
            MONGO_HOST_SESSION=os.environ['MONGO_HOST_SESSION'],
            MONGO_USER_SESSION=os.environ['MONGO_USER_SESSION'],
            MONGO_PASSWORD_SESSION=os.environ['MONGO_PASSWORD_SESSION'],
            MONGO_DATABASE_SESSION=os.environ['MONGO_DATABASE_SESSION'],
            MONGO_REPLICASET_SESSION=os.environ['MONGO_REPLICASET_SESSION'] if os.environ['MONGO_REPLICASET_SESSION'] != '---' else None,
            MONGO_COLLECTION_DATE=os.environ['MONGO_COLLECTION_DATE'],
            MONGO_COLLECTION_DATETG=os.environ['MONGO_COLLECTION_DATETG'],
            MONGO_COLLECTION_PROGCOMP=os.environ['MONGO_COLLECTION_PROGCOMP'],
            MONGO_HOST_TWOMIN=os.environ['MONGO_HOST_TWOMIN'],
            MONGO_USER_TWOMIN=os.environ['MONGO_USER_TWOMIN'],
            MONGO_PASSWORD_TWOMIN=os.environ['MONGO_PASSWORD_TWOMIN'],
            MONGO_DATABASE_TWOMIN=os.environ['MONGO_DATABASE_TWOMIN'],
            MONGO_REPLICASET_TWOMIN=os.environ['MONGO_REPLICASET_TWOMIN'] if os.environ['MONGO_REPLICASET_TWOMIN'] != '---' else None,
            MONGO_COLLECTION_TWOMIN=os.environ['MONGO_COLLECTION_TWOMIN'],
            MONGO_COLLECTION_TWOMINTG=os.environ['MONGO_COLLECTION_TWOMINTG'],
        )
        # Connect to session mongo
        mongo_client_session = MongoClient(config.MONGO_HOST_SESSION,
                                           replicaset=config.MONGO_REPLICASET_SESSION)
        mongo_database_session = mongo_client_session[config.MONGO_DATABASE_SESSION]
        # Authenticate
        mongo_database_session.authenticate(config.MONGO_USER_SESSION, config.MONGO_PASSWORD_SESSION,
                                            mechanism='SCRAM-SHA-1')

        # Connect to twomin mongo
        mongo_client_twomin = MongoClient(config.MONGO_HOST_TWOMIN,
                                          replicaset=config.MONGO_REPLICASET_TWOMIN)
        mongo_database_twomin = mongo_client_twomin[config.MONGO_DATABASE_TWOMIN]
        # Authenticate
        mongo_database_twomin.authenticate(config.MONGO_USER_TWOMIN, config.MONGO_PASSWORD_TWOMIN,
                                           mechanism='SCRAM-SHA-1')

        # read from prod for testing
#        mongo_client = MongoClient('172.31.64.60,172.31.38.53,172.31.6.25', replicaset='sessionRS')
#        mongo_database = mongo_client['movementStats']
##        # Authenticate
#        mongo_database.authenticate('statsUser', 'BioMx211', mechanism='SCRAM-SHA-1')
###        mongo_collection = mongo_database['dateStats']
#        mongo_collection_progcomp = mongo_database['progCompDateStats']
        # connect to all relevant collections
        mongo_collection_date = mongo_database_session[config.MONGO_COLLECTION_DATE]
        mongo_collection_datetg = mongo_database_session[config.MONGO_COLLECTION_DATETG]
#        mongo_collection_progcomp = mongo_database_session[config.MONGO_COLLECTION_PROGCOMP]

        mongo_collection_twomin = mongo_database_twomin[config.MONGO_COLLECTION_TWOMIN]
        mongo_collection_twomintg = mongo_database_twomin[config.MONGO_COLLECTION_TWOMINTG]

        training_group_ids = input_data.get('TrainingGroupId', None)
        session_type = input_data.get('SessionType', None)
        if session_type is not None:
            session_type = str(session_type)
        event_date = input_data.get('eventDate')

        for tg_id in training_group_ids:
            # get twoMinute aggregated TG data
            tg_two_min = _aggregate_tg_twomin(mongo_collection_twomin, tg_id, event_date, session_type)
            for two_min in tg_two_min:
                # for each two minute record, sort the variables in order
                two_min_record = OrderedDict()
                for two_min_var in tg_twomin_vars:
                    try:
                        two_min_record[two_min_var] = two_min[two_min_var]
                    except KeyError:
                        print('Missing Var in two min: {}'.format(two_min_var))
                        two_min_record[two_min_var] = None
                two_min_record['trainingGroupId'] = tg_id
                query = {'trainingGroupId': tg_id, 'eventDate': event_date,
                         'twoMinuteIndex': two_min['twoMinuteIndex']}
                # upsert the single collection to mongo (currently replace look into update as well)
                mongo_collection_twomintg.replace_one(query, two_min_record, upsert=True)
    
            # get date level aggregated data for TG (minus prog comp)
            tg_date = _aggregate_tg(mongo_collection_date, tg_id, event_date, session_type)
    
            # Add program composition lists to team data
#            prog_comps = ['grf', 'totalAccel', 'plane', 'stance']
#            for var in prog_comps:
#                out_var = var+'ProgramComposition'
#                tg_date[out_var] = _aggregate_tg_progcomp(mongo_collection_progcomp, var,
#                                                              tg_id='f87e1deb-f022-4223-acaa-4926b6094343',
#                                                              event_date=event_date, session_type=session_type)
            # For TG date data, sort the variables in order
            record_out = OrderedDict()
            for tg_var in tg_vars:
                try:
                    record_out[tg_var] = tg_date[tg_var]
                except KeyError:
                    record_out[tg_var] = None
    
            # Upsert the date aggregated collection to mongo (currently replace)
            query = {'trainingGroupId': tg_id, 'eventDate': event_date}
            mongo_collection_datetg.replace_one(query, record_out, upsert=True)


    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise

def _aggregate_tg_twomin(collection, tg_id, event_date, session_type):
    pipeline = [{'$match': {'trainingGroups': {'$eq': tg_id},
                            'eventDate': {'$eq': event_date},
                            'sessionType': {'$eq': session_type}
                           }
                },
                {'$group': {'_id': {'twoMinuteIndex': '$twoMinuteIndex'},
#                            'trainingGroupId': {'$first': '$teamId'},
                            'eventDate': {'$first': '$eventDate'},
                            'sessionType': {'$first': '$sessionType'},
                            'twoMinuteIndex': {'$first': '$twoMinuteIndex'},
                            'totalGRF': {'$sum': '$totalGRF'},
                            'optimalGRF': {'$sum': '$optimalGRF'},
                            'irregularGRF': {'$sum': '$irregularGRF'},
                            'control': {'$sum': {'$multiply': ['$control', '$totalGRF']}},
                            'consistency': {'$sum': {'$multiply': ['$consistency', '$totalGRF']}},
                            'symmetry': {'$sum': {'$multiply': ['$symmetry', '$totalGRF']}},
                            'userCount': {'$sum': 1},
                            'LFgRF': {'$sum': '$LFgRF'},
                            'RFgRF': {'$sum': '$RFgRF'},
                            'singleLegGRF': {'$sum': '$singleLegGRF'},
                            'percLeftGRF': {'$sum': {'$multiply': ['$percLeftGRF', '$singleLegGRF']}},
                            'percRightGRF': {'$sum': {'$multiply': ['$percRightGRF', '$singleLegGRF']}},
                            'totalAccel': {'$sum': '$totalAccel'},
                            'irregularAccel': {'$sum': '$irregularAccel'},
                            'hipSymmetry': {'$sum': {'$multiply': ['$hipSymmetry', '$totalGRF']}},
                            'ankleSymmetry': {'$sum': {'$multiply': ['$ankleSymmetry', '$totalGRF']}},
                            'hipConsistency': {'$sum': {'$multiply': ['$hipConsistency', '$totalGRF']}},
                            'ankleConsistency': {'$sum': {'$multiply': ['$ankleConsistency', '$totalGRF']}},
                            'consistencyLF': {'$sum': {'$multiply': ['$consistencyLF', '$LFgRF']}},
                            'consistencyRF': {'$sum': {'$multiply': ['$consistencyRF', '$RFgRF']}},
                            'hipControl': {'$sum': {'$multiply': ['$hipControl', '$totalGRF']}},
                            'ankleControl': {'$sum': {'$multiply': ['$ankleControl', '$totalGRF']}},
                            'controlLF': {'$sum': {'$multiply': ['$controlLF', '$LFgRF']}},
                            'controlRF': {'$sum': {'$multiply': ['$controlRF', '$RFgRF']}}
                           }
                },
                {'$project':{'_id': 0,
#                             'trainingGroupId':1,
                             'userId': None,
                             'eventDate': 1,
                             'sessionType': 1,
                             'twoMinuteIndex': 1,
                             'totalGRF': {'$divide': ['$totalGRF', '$userCount']},
                             'optimalGRF': {'$divide': ['$optimalGRF', '$userCount']},
                             'irregularGRF': {'$divide': ['$irregularGRF', '$userCount']},
                             'control': {'$divide': ['$control', '$totalGRF']},
                             'consistency': {'$divide': ['$consistency', '$totalGRF']},
                             'symmetry': {'$divide': ['$symmetry', '$totalGRF']},
                             'percLeftGRF': {'$divide': ['$percLeftGRF', '$singleLegGRF']},
                             'percRightGRF': {'$divide': ['$percRightGRF', '$singleLegGRF']},
                             'percDistr': {'$abs': {'$multiply': [{'$subtract': [{'$divide': ['$percLeftGRF', '$singleLegGRF']},
                                                                                 {'$divide': ['$percRightGRF', '$singleLegGRF']}]}, 100]}},
                             'totalAccel': 1,
                             'irregularAccel': 1,
                             'LFgRF': 1,
                             'RFgRF': 1,
                             'singleLegGRF': 1,
                             'percOptimal': {'$divide': ['$optimalGRF', {'$sum': ['$optimalGRF', '$irregularGRF']}]},
                             'hipSymmetry': {'$divide': ['$hipSymmetry', '$totalGRF']},
                             'ankleSymmetry': {'$divide': ['$ankleSymmetry', '$totalGRF']},
                             'hipConsistency': {'$divide': ['$hipConsistency', '$totalGRF']},
                             'ankleConsistency': {'$divide': ['$ankleConsistency', '$totalGRF']},
                             'consistencyLF': {'$divide': ['$consistencyLF', '$LFgRF']},
                             'consistencyRF': {'$divide': ['$consistencyRF', '$RFgRF']},
                             'hipControl': {'$divide': ['$hipControl', '$totalGRF']},
                             'ankleControl': {'$divide': ['$ankleControl', '$totalGRF']},
                             'controlLF': {'$divide': ['$controlLF', '$LFgRF']},
                             'controlRF': {'$divide': ['$controlRF', '$RFgRF']}
                            }
                }
               ]
    # get all the two minute aggregated records for the team and sort by twoMinIndex
    tg_stats = list(collection.aggregate(pipeline))
    tg_stats = sorted(tg_stats, key=lambda k: k['twoMinuteIndex'])
    team_all = []
    for two_min in tg_stats:
        # for each twoMinuteIndex, get the list of all athlete records
        TwoMinIndex = two_min['twoMinuteIndex']
        ath_pipeline = [{'$match': {'trainingGroups': {'$eq': tg_id},
                                    'eventDate': {'$eq': event_date},
                                    'sessionType': {'$eq': session_type},
                                    'twoMinuteIndex': {'$eq': TwoMinIndex}
                                   }
                        },
                       ]
        ath_stats = list(collection.aggregate(ath_pipeline))
        # sort each athlete record to proper order of variables
        ath_stats_sorted = []
        for athlete in ath_stats:
            single_ath = OrderedDict()
            for ath_2min_var in athlete_twomin_vars:
                single_ath[ath_2min_var] = athlete[ath_2min_var]
            # remove some variables from athlete data
            single_ath['sessionId'] = None
            single_ath['timeStart'] = None
#            single_ath['trainingGroups'] = None
            ath_stats_sorted.append(single_ath)
        two_min['athleteStats'] = ath_stats_sorted
        two_min['teamId'] = None
        two_min['trainingGroupId'] = tg_id
        # return team data with athlete added
        team_all.append(two_min)
    return tg_stats


def _aggregate_tg_progcomp(collection, var, tg_id, event_date, session_type):
    """Aggregate progComp for the team
    """
    prog_var = '$'+var+'ProgramComposition'
    pipeline = [{'$match': {'trainingGroups': {'$eq': tg_id},
                            'eventDate': {'$eq': event_date},
                            'sessionType': {'$eq': session_type}
                           }
                },
                {'$unwind': prog_var},
                {'$group': {'_id': {'binNumber': prog_var+".binNumber"},
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
        bins.append(single_bin)

    return sorted(bins, key=lambda k: k['binNumber'])


def _aggregate_tg(collection, tg_id, event_date, session_type):
    """Aggregate team data for the given date
    """
    pipeline = [{'$match': {'trainingGroups': {'$eq': tg_id},
                            'eventDate': {'$eq': event_date},
                            'sessionType': {'$eq': session_type}
                           }
                },
                {'$group': {'_id': {'trainingGroupId': "$trainingGroups"},
                            'trainingGroupId': {'$first': '$trainingGroups'},
                            'eventDate': {'$first': '$eventDate'},
                            'sessionType': {'$first': '$sessionType'},
                            'totalGRF': {'$sum': '$totalGRF'},
                            'optimalGRF': {'$sum': '$optimalGRF'},
                            'irregularGRF': {'$sum': '$irregularGRF'},
                            'control': {'$sum': {'$multiply': ['$control', '$totalGRF']}},
                            'consistency': {'$sum': {'$multiply': ['$consistency', '$totalGRF']}},
                            'symmetry': {'$sum': {'$multiply': ['$symmetry', '$totalGRF']}},
                            'userCount': {'$sum': 1},
                            'LFgRF': {'$sum': '$LFgRF'},
                            'RFgRF': {'$sum': '$RFgRF'},
                            'singleLegGRF': {'$sum': '$singleLegGRF'},
                            'percLeftGRF': {'$sum': {'$multiply': ['$percLeftGRF', '$singleLegGRF']}},
                            'percRightGRF': {'$sum': {'$multiply': ['$percRightGRF', '$singleLegGRF']}},
                            'totalAccel': {'$sum': '$totalAccel'},
                            'irregularAccel': {'$sum': '$irregularAccel'},
                            'hipSymmetry': {'$sum': {'$multiply': ['$hipSymmetry', '$totalGRF']}},
                            'ankleSymmetry': {'$sum': {'$multiply': ['$ankleSymmetry', '$totalGRF']}},
                            'hipConsistency': {'$sum': {'$multiply': ['$hipConsistency', '$totalGRF']}},
                            'ankleConsistency': {'$sum': {'$multiply': ['$ankleConsistency', '$totalGRF']}},
                            'consistencyLF': {'$sum': {'$multiply': ['$consistencyLF', '$LFgRF']}},
                            'consistencyRF': {'$sum': {'$multiply': ['$consistencyRF', '$RFgRF']}},
                            'hipControl': {'$sum': {'$multiply': ['$hipControl', '$totalGRF']}},
                            'ankleControl': {'$sum': {'$multiply': ['$ankleControl', '$totalGRF']}},
                            'controlLF': {'$sum': {'$multiply': ['$controlLF', '$LFgRF']}},
                            'controlRF': {'$sum': {'$multiply': ['$controlRF', '$RFgRF']}}
                           }
                },
                {'$project':{'_id': 0,
                             'trainingGroupId':1,
                             'userId': None,
                             'eventDate': 1,
                             'sessionType': 1,
                             'totalGRF': {'$divide': ['$totalGRF', '$userCount']},
                             'optimalGRF': {'$divide': ['$optimalGRF', '$userCount']},
                             'irregularGRF': {'$divide': ['$irregularGRF', '$userCount']},
                             'control': {'$divide': ['$control', '$totalGRF']},
                             'consistency': {'$divide': ['$consistency', '$totalGRF']},
                             'symmetry': {'$divide': ['$symmetry', '$totalGRF']},
                             'percLeftGRF': {'$divide': ['$percLeftGRF', '$singleLegGRF']},
                             'percRightGRF': {'$divide': ['$percRightGRF', '$singleLegGRF']},
                             'percDistr': {'$abs': {'$multiply': [{'$subtract': [{'$divide': ['$percLeftGRF', '$singleLegGRF']},
                                                                                 {'$divide': ['$percRightGRF', '$singleLegGRF']}]}, 100]}},
                             'totalAccel': 1,
                             'irregularAccel': 1,
                             'LFgRF': 1,
                             'RFgRF': 1,
                             'singleLegGRF': 1,
                             'percOptimal': {'$divide': ['$optimalGRF', {'$sum': ['$optimalGRF', '$irregularGRF']}]},
                             'hipSymmetry': {'$divide': ['$hipSymmetry', '$totalGRF']},
                             'ankleSymmetry': {'$divide': ['$ankleSymmetry', '$totalGRF']},
                             'hipConsistency': {'$divide': ['$hipConsistency', '$totalGRF']},
                             'ankleConsistency': {'$divide': ['$ankleConsistency', '$totalGRF']},
                             'consistencyLF': {'$divide': ['$consistencyLF', '$LFgRF']},
                             'consistencyRF': {'$divide': ['$consistencyRF', '$RFgRF']},
                             'hipControl': {'$divide': ['$hipControl', '$totalGRF']},
                             'ankleControl': {'$divide': ['$ankleControl', '$totalGRF']},
                             'controlLF': {'$divide': ['$controlLF', '$LFgRF']},
                             'controlRF': {'$divide': ['$controlRF', '$RFgRF']}
                            }
                }
               ]
    ath_pipeline = [{'$match': {'trainingGroups': {'$eq': tg_id},
                            'eventDate': {'$eq': event_date},
                            'sessionType': {'$eq': session_type}
                           }
                     }
                    ]
    tg_stats = list(collection.aggregate(pipeline))[0]
    ath_stats = list(collection.aggregate(ath_pipeline))
    athlete_stats = []
    for athlete in ath_stats:
#        return athlete
        single_ath = OrderedDict()
        for ath_var in athlete_vars:
            single_ath[ath_var] = athlete[ath_var]
        single_ath['trainingGroups'] = None
        athlete_stats.append(single_ath)
    tg_stats['AthleteStats'] = athlete_stats
    tg_stats['trainingGroupId'] = tg_id
    return tg_stats


if __name__ == '__main__':
    import time
    start = time.time()
    input_data = OrderedDict()
    input_data = OrderedDict()
    input_data['TeamId'] = 'test_team'
    input_data['TrainingGroupId'] = ['test_tg1', 'test_tg2']
    input_data['UserId'] = 'test_user'
    input_data['SessionEventId'] = 'test_session'
    input_data['SessionType'] = '1'
    input_data['UserMass'] = 77
    input_data['eventDate'] = '2017-03-20'

    os.environ['ENVIRONMENT'] = 'Dev'
    os.environ['MONGO_HOST_SESSION'] = 'ec2-34-210-169-8.us-west-2.compute.amazonaws.com:27017'
    os.environ['MONGO_USER_SESSION'] = 'statsUser'
    os.environ['MONGO_PASSWORD_SESSION'] = 'BioMx211'
    os.environ['MONGO_DATABASE_SESSION'] = 'movementStats'
    os.environ['MONGO_REPLICASET_SESSION'] = '---'
    os.environ['MONGO_COLLECTION_DATE'] = 'dateStats_test2'
    os.environ['MONGO_COLLECTION_DATETEAM'] = 'dateStatsTeam_test2'
    os.environ['MONGO_COLLECTION_DATETG'] = 'dateStatsTG_test2'
    os.environ['MONGO_COLLECTION_PROGCOMP'] = 'progCompDateStats_test2'
    os.environ['MONGO_HOST_TWOMIN'] = 'ec2-34-210-169-8.us-west-2.compute.amazonaws.com:27017'
    os.environ['MONGO_USER_TWOMIN'] = 'statsUser'
    os.environ['MONGO_PASSWORD_TWOMIN'] = 'BioMx211'
    os.environ['MONGO_DATABASE_TWOMIN'] = 'movementStats'
    os.environ['MONGO_REPLICASET_TWOMIN'] = '---'
    os.environ['MONGO_COLLECTION_TWOMIN'] = 'twoMinuteStats_test2'
    os.environ['MONGO_COLLECTION_TWOMINTEAM'] = 'twoMinuteStatsTeam_test2'
    os.environ['MONGO_COLLECTION_TWOMINTG'] = 'twoMinuteStatsTG_test2'

    result = script_handler(input_data)
    print(time.time() - start)
