from __future__ import print_function

from collections import namedtuple
from pymongo import MongoClient
import logging
import os
import pandas
import numpy
import sys
from collections import OrderedDict
from datetime import datetime, timedelta
from vars_in_mongo import athlete_vars, team_vars, team_twomin_vars, athlete_twomin_vars

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
    'MONGO_COLLECTION_DATETEAM',
    'MONGO_COLLECTION_PROGCOMP',
    'MONGO_HOST_TWOMIN',
    'MONGO_USER_TWOMIN',
    'MONGO_PASSWORD_TWOMIN',
    'MONGO_DATABASE_TWOMIN',
    'MONGO_REPLICASET_TWOMIN',
    'MONGO_COLLECTION_TWOMIN',
    'MONGO_COLLECTION_TWOMINTEAM',
])


def script_handler(input_data):
    logger.info("Running team aggregation")

    try:
        config = Config(
            AWS=False,
            ENVIRONMENT=os.environ['ENVIRONMENT'],
            FP_INPUT='/net/efs/aggregate/input',
            MONGO_HOST_SESSION=os.environ['MONGO_HOST_SESSION'],
            MONGO_USER_SESSION=os.environ['MONGO_USER_SESSION'],
            MONGO_PASSWORD_SESSION=os.environ['MONGO_PASSWORD_SESSION'],
            MONGO_DATABASE_SESSION=os.environ['MONGO_DATABASE_SESSION'],
            MONGO_REPLICASET_SESSION=os.environ['MONGO_REPLICASET_SESSION'] if os.environ['MONGO_REPLICASET_SESSION'] != '---' else None,
            MONGO_COLLECTION_DATE=os.environ['MONGO_COLLECTION_DATE'],
            MONGO_COLLECTION_DATETEAM=os.environ['MONGO_COLLECTION_DATETEAM'],
            MONGO_COLLECTION_PROGCOMP=os.environ['MONGO_COLLECTION_PROGCOMPDATE'],
            MONGO_HOST_TWOMIN=os.environ['MONGO_HOST_TWOMIN'],
            MONGO_USER_TWOMIN=os.environ['MONGO_USER_TWOMIN'],
            MONGO_PASSWORD_TWOMIN=os.environ['MONGO_PASSWORD_TWOMIN'],
            MONGO_DATABASE_TWOMIN=os.environ['MONGO_DATABASE_TWOMIN'],
            MONGO_REPLICASET_TWOMIN=os.environ['MONGO_REPLICASET_TWOMIN'] if os.environ['MONGO_REPLICASET_TWOMIN'] != '---' else None,
            MONGO_COLLECTION_TWOMIN=os.environ['MONGO_COLLECTION_TWOMIN'],
            MONGO_COLLECTION_TWOMINTEAM=os.environ['MONGO_COLLECTION_TWOMINTEAM'],
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
# TODO: replace this testing part to read from correct collection
        # read from prod for testing
        # mongo_client = MongoClient('172.31.64.60,172.31.38.53,172.31.6.25', replicaset='sessionRS')
        # mongo_database = mongo_client['movementStats']
        # # Authenticate
        # mongo_database.authenticate('statsUser', 'BioMx211', mechanism='SCRAM-SHA-1')
        # mongo_collection_progcomp_test = mongo_database['progCompDateStats']

        # connect to all relevant collections
        mongo_collection_date = mongo_database_session[config.MONGO_COLLECTION_DATE]
        mongo_collection_dateteam = mongo_database_session[config.MONGO_COLLECTION_DATETEAM]
        mongo_collection_progcomp = mongo_database_session[config.MONGO_COLLECTION_PROGCOMP]

        mongo_collection_twomin = mongo_database_twomin[config.MONGO_COLLECTION_TWOMIN]
        mongo_collection_twominteam = mongo_database_twomin[config.MONGO_COLLECTION_TWOMINTEAM]
        
        team_id = input_data.get('TeamId', None)
        session_type = input_data.get('SessionType', None)
        if session_type is not None:
            session_type = str(session_type)
        event_date = input_data.get('EventDate')

        # get twoMinute aggregated team data
        team_two_min = _aggregate_team_twomin(mongo_collection_twomin, team_id, event_date, session_type)
        for two_min in team_two_min:
            # for each two minute record, sort the variables in order
            two_min_record = OrderedDict()
            for two_min_var in team_twomin_vars:
                try:
                    two_min_record[two_min_var] = two_min[two_min_var]
                except KeyError:
                    two_min_record[two_min_var] = None
            query = {'teamId': team_id, 'eventDate': event_date,
                     'twoMinuteIndex': two_min['twoMinuteIndex']}
            # upsert the single collection to mongo (currently replace look into update as well)
            mongo_collection_twominteam.replace_one(query, two_min_record, upsert=True)

        # get date level aggregated data for team (minus prog comp)
        team_date = _aggregate_team(mongo_collection_date, team_id, event_date, session_type)

        # grab maximum required historical data
        hist_records = _get_hist_data(mongo_collection_dateteam, team_id,
                                      event_date, period=10)

        current = pandas.DataFrame({'eventDate': event_date,
                                    'totalAccel': team_date['totalAccel'],
                                    'totalGRF': team_date['totalGRF']},
                                   index=[str(datetime.strptime(event_date, '%Y-%m-%d').date())])

        # create a pandas dataframe with entry for every day in the history
        event_date_dt = datetime.strptime(event_date, '%Y-%m-%d').date()
        total_days = 40
        # initialize empty dataframe with 40 rows (maximum history)
        index = pandas.date_range(event_date_dt-timedelta(total_days),
                                  periods=total_days, freq='D').date.astype(str)

        columns = ['eventDate', 'totalGRF', 'totalAccel']
        hist_data = pandas.DataFrame(index=index, columns=columns)
        hist_data.eventDate = index
        hist_data = hist_data.fillna(0)
        if len(hist_records) != 0:
            # If data is present, for any of the previous 40 days, insert that to data frame
            # convert read data into pandas dataframe and remove duplicates and sort
            # TODO: removing duplicates should be unnecessary as data should already be unique in mongo
            hist = pandas.DataFrame(hist_records)
            hist.drop_duplicates(subset='eventDate', keep='first', inplace=True)
            hist.sort_values(by='eventDate', inplace=True)
            hist.reset_index(drop=True, inplace=True)

            # for days with available data in mongo, insert the actual data
            count = 0
            for i in hist.eventDate:
                i = str(datetime.strptime(i, '%Y-%m-%d').date())
                if count == 0:
                    # assign nan to every data before the first date data is available for
                    hist_data.loc[hist_data.eventDate < i, 'totalGRF'] = numpy.nan
                    hist_data.loc[hist_data.eventDate < i, 'totalAccel'] = numpy.nan

                count += 1
                subset = hist.loc[hist.eventDate == i, :]
                hist_data.loc[hist_data.eventDate == i, 'eventDate'] = subset['eventDate'].values[0]
                hist_data.loc[hist_data.eventDate == i, 'totalGRF'] = subset['totalGRF'].values[0]
                hist_data.loc[hist_data.eventDate == i, 'totalAccel'] = subset['control'].values[0]
            # append current day's data to the end
            hist_data = hist_data.append(current)
        else:
            # if no hist data available, mark as nan and append current day
            hist_data.totalGRF = numpy.nan
            hist_data.totalAccel = numpy.nan
            hist_data = hist_data.append(current)


        # Add program composition lists to team data
        prog_comps = ['grf', 'totalAccel', 'plane', 'stance']
        for var in prog_comps:
            out_var = var+'ProgramComposition'
            team_date[out_var] = _aggregate_team_progcomp(mongo_collection_progcomp, var,
                                                          team_id=team_id, event_date=event_date,
                                                          session_type=session_type)
        # For team date data, sort the variables in order
        record_out = OrderedDict()
        for team_var in team_vars:
            try:
                record_out[team_var] = team_date[team_var]
            except KeyError:
                record_out[team_var] = None
        # ACWR
        for i in numpy.arange(1, 11, 1):
            acwr = _compute_awcr(hist_data, 'grf', i, event_date)
            record_out['ACWRGRF' + str(i)] = acwr.totalGRF
            record_out['ACWRTotalAccel' + str(i)] = acwr.totalAccel
        # Upsert the date aggregated collection to mongo (currently replace)
        query = {'teamId': team_id, 'eventDate': event_date}
        mongo_collection_dateteam.replace_one(query, record_out, upsert=True)

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise


def _aggregate_team_twomin(collection, team_id, event_date, session_type):
    pipeline = [{'$match': {'teamId': {'$eq': team_id},
                            'eventDate': {'$eq': event_date},
                            'sessionType': {'$eq': session_type}
                           }
                },
                {'$group': {'_id': {'teamId': "$teamId",
                                    'twoMinuteIndex': '$twoMinuteIndex'},
                            'teamId': {'$first': '$teamId'},
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
                             'teamId':1,
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
                             'percLRGRFDiff': {'$abs': {'$subtract': [{'$divide': ['$percLeftGRF', '$singleLegGRF']},
                                                                                 {'$divide': ['$percRightGRF', '$singleLegGRF']}
                                                                     ]
                                                       }
                                              },
                             'totalAccel': 1,
                             'irregularAccel': 1,
                             'LFgRF': 1,
                             'RFgRF': 1,
                             'singleLegGRF': 1,
                             'percOptimal': {'$multiply': [{'$divide': ['$optimalGRF', {'$sum': ['$optimalGRF', '$irregularGRF']}]}, 100
                                                          ]
                                            },
                             'percIrregular': {'$multiply': [{'$divide': ['$irregularGRF', {'$sum': ['$optimalGRF', '$irregularGRF']}]}, 100
                                                          ]
                                            },
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
    team_stats = list(collection.aggregate(pipeline))
    team_stats = sorted(team_stats, key=lambda k: k['twoMinuteIndex'])
    team_all = []
    for two_min in team_stats:
        # for each twoMinuteIndex, get the list of all athlete records
        TwoMinIndex = two_min['twoMinuteIndex']
        ath_pipeline = [{'$match': {'teamId': {'$eq': team_id},
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
        # return team data with athlete added
        team_all.append(two_min)
    return team_stats


def _aggregate_team_progcomp(collection, var, team_id, event_date, session_type):
    """Aggregate progComp for the team
    """
    prog_var = '$'+var+'ProgramComposition'
    pipeline = [{'$match': {'teamId': {'$eq': team_id},
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
        if doc['totalGRF'] == 0 or doc['totalGRF'] is None:
            single_bin['percOptimal'] = None
            single_bin['percIrregular'] = None
        else:
            single_bin['percOptimal'] = doc['optimalGRF'] / doc['totalGRF'] * 100
            single_bin['percIrregular'] = doc['irregularGRF'] / doc['totalGRF'] * 100
        bins.append(single_bin)

    return sorted(bins, key=lambda k: k['binNumber'])


def _aggregate_team(collection, team_id, event_date, session_type):
    """Aggregate team data for the given date
    """
    pipeline = [{'$match': {'teamId': {'$eq': team_id},
                            'eventDate': {'$eq': event_date},
                            'sessionType': {'$eq': session_type}
                           }
                },
                {'$group': {'_id': {'teamId': "$teamId"},
                            'teamId': {'$first': '$teamId'},
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
                            'fatigue': {'$avg': '$fatigue'},
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
                             'teamId':1,
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
                             'percLRGRFDiff': {'$abs': {'$subtract': [{'$divide': ['$percLeftGRF', '$singleLegGRF']},
                                                                                 {'$divide': ['$percRightGRF', '$singleLegGRF']}
                                                                     ]
                                                       }
                                              },
                             'totalAccel': 1,
                             'irregularAccel': 1,
                             'LFgRF': 1,
                             'RFgRF': 1,
                             'singleLegGRF': 1,
                             'percOptimal': {'$multiply': [{'$divide': ['$optimalGRF', {'$sum': ['$optimalGRF', '$irregularGRF']}]}, 100
                                                          ]
                                            },
                             'percIrregular': {'$multiply': [{'$divide': ['$irregularGRF', {'$sum': ['$optimalGRF', '$irregularGRF']}]}, 100
                                                          ]
                                            },
                             'fatigue': 1,
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
    ath_pipeline = [{'$match': {'teamId': {'$eq': team_id},
                            'eventDate': {'$eq': event_date},
                            'sessionType': {'$eq': session_type}
                           }
                     }
                    ]
    team_stats = list(collection.aggregate(pipeline))[0]
    ath_stats = list(collection.aggregate(ath_pipeline))
    athlete_stats = []
    for athlete in ath_stats:
        single_ath = OrderedDict()
        for ath_var in athlete_vars:
            single_ath[ath_var] = athlete[ath_var]
        athlete_stats.append(single_ath)
    team_stats['AthleteStats'] = athlete_stats
    return team_stats


def _get_hist_data(collection, team_id, event_date, period):
    """
    Get max historical data for acwr computation
    currently only returning totalGRF and totalAccel
    Days with no data have value 0
    """
    total_days = period * 4
    event_date_dt = datetime.strptime(event_date, '%Y-%m-%d').date()
    start_date = str(event_date_dt - timedelta(days=total_days))
    # get history excluding current day
    docs = list(collection.find({'teamId': {'$eq': team_id},
                                 'eventDate': {'$gte': start_date, '$lt': event_date}},
                                {'eventDate': 1,
                                 'totalGRF': 1,
                                 'totalAccel': 1,
                                 '_id': 0}))
    return docs


def _compute_awcr(hist, var, period, event_date):
    """compute acute chronic workload ration for all the variables
        acwr is defined as acute/chronic where
        acute = sum(workload) for current period
        chronic = avg(period_workload) for 4 previous periods
    """
    # TODO: probably don't need this with actual data(there should be no duplication)
    hist.drop_duplicates(subset='eventDate', keep='first', inplace=True)
    # get the start and end dates of acute and chronic data
    acute_period_end = datetime.strptime(event_date, '%Y-%m-%d').date()
    acute_period_start = acute_period_end - timedelta(days=period - 1)

    # current period is currently included in chronic
    chronic_period_end = acute_period_end
    chronic_period_start = chronic_period_end - timedelta(days=4*period-1)

    # subset acute data and compute acute value
    acute_data = hist.loc[(hist.eventDate >= str(acute_period_start)) &\
                          (hist.eventDate <= str(acute_period_end))]
    acute = acute_data.sum()

    # subset chronic data and compute chronic value
    chronic_data = hist.loc[(hist.eventDate >= str(chronic_period_start)) &\
                             (hist.eventDate <= str(chronic_period_end))]

    # rolling sum on period (0 for missing days)
    rolling_sum = chronic_data.rolling(period, min_periods=1).sum()
    chronic = rolling_sum.mean()

    acwr = acute/chronic

    return acwr



if __name__ == '__main__':
    import time
    start = time.time()
    input_data = OrderedDict()
    input_data['TeamId'] = 'test_team'
    input_data['TrainingGroupId'] = ['test_tg1', 'test_tg2']
    input_data['UserId'] = 'test_user'
    input_data['SessionEventId'] = 'test_session'
    input_data['SessionType'] = '1'
    input_data['UserMass'] = 77
    input_data['EventDate'] = '2017-03-20'

    os.environ['ENVIRONMENT'] = 'Dev'
    os.environ['MONGO_HOST_SESSION'] = 'ec2-34-210-169-8.us-west-2.compute.amazonaws.com:27017'
    os.environ['MONGO_USER_SESSION'] = 'statsUser'
    os.environ['MONGO_PASSWORD_SESSION'] = 'BioMx211'
    os.environ['MONGO_DATABASE_SESSION'] = 'movementStats'
    os.environ['MONGO_REPLICASET_SESSION'] = '---'
    os.environ['MONGO_COLLECTION_DATE'] = 'dateStats_test3'
    os.environ['MONGO_COLLECTION_DATETEAM'] = 'dateStatsTeam_test3'
    os.environ['MONGO_COLLECTION_PROGCOMP'] = 'progCompDateStats_test3'
    os.environ['MONGO_HOST_TWOMIN'] = 'ec2-34-210-169-8.us-west-2.compute.amazonaws.com:27017'
    os.environ['MONGO_USER_TWOMIN'] = 'statsUser'
    os.environ['MONGO_PASSWORD_TWOMIN'] = 'BioMx211'
    os.environ['MONGO_DATABASE_TWOMIN'] = 'movementStats'
    os.environ['MONGO_REPLICASET_TWOMIN'] = '---'
    os.environ['MONGO_COLLECTION_TWOMIN'] = 'twoMinuteStats_test3'
    os.environ['MONGO_COLLECTION_TWOMINTEAM'] = 'twoMinuteStatsTeam_test3'

    result = script_handler(input_data)
    print(time.time() - start)
