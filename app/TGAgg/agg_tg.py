from __future__ import print_function

from collections import namedtuple, OrderedDict
import os
from datetime import datetime, timedelta

import numpy
import pandas
from pymongo import MongoClient

from vars_in_mongo import athlete_vars, tg_vars, tg_twomin_vars, athlete_twomin_vars


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


def connect_mongo(config):
    """Get mongo client connection
    """
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

    # connect to all relevant collections
    mongo_collection_date = mongo_database_session[config.MONGO_COLLECTION_DATE]
    mongo_collection_datetg = mongo_database_session[config.MONGO_COLLECTION_DATETG]
    mongo_collection_progcomp = mongo_database_session[config.MONGO_COLLECTION_PROGCOMP]

    mongo_collection_twomin = mongo_database_twomin[config.MONGO_COLLECTION_TWOMIN]
    mongo_collection_twomintg = mongo_database_twomin[config.MONGO_COLLECTION_TWOMINTG]

    return (mongo_collection_date, mongo_collection_datetg, mongo_collection_progcomp,
            mongo_collection_twomin, mongo_collection_twomintg)


def script_handler(input_data):
    print("Running training groups aggregation")

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
            MONGO_COLLECTION_PROGCOMP=os.environ['MONGO_COLLECTION_PROGCOMPDATE'],
            MONGO_HOST_TWOMIN=os.environ['MONGO_HOST_TWOMIN'],
            MONGO_USER_TWOMIN=os.environ['MONGO_USER_TWOMIN'],
            MONGO_PASSWORD_TWOMIN=os.environ['MONGO_PASSWORD_TWOMIN'],
            MONGO_DATABASE_TWOMIN=os.environ['MONGO_DATABASE_TWOMIN'],
            MONGO_REPLICASET_TWOMIN=os.environ['MONGO_REPLICASET_TWOMIN'] if os.environ['MONGO_REPLICASET_TWOMIN'] != '---' else None,
            MONGO_COLLECTION_TWOMIN=os.environ['MONGO_COLLECTION_TWOMIN'],
            MONGO_COLLECTION_TWOMINTG=os.environ['MONGO_COLLECTION_TWOMINTG'],
        )

        (
            mongo_collection_date,
            mongo_collection_datetg,
            mongo_collection_progcomp,
            mongo_collection_twomin,
            mongo_collection_twomintg
        ) = connect_mongo(config)

        training_group_ids = input_data.get('TrainingGroupIds', None) or {}
        event_date = input_data.get('EventDate')

        for tg_id in training_group_ids:
            # get twoMinute aggregated TG data
            tg_two_min = _aggregate_tg_twomin(mongo_collection_twomin, tg_id, event_date)
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
            tg_date = _aggregate_tg(mongo_collection_date, tg_id, event_date)

            # grab maximum required historical data
            hist_records = _get_hist_data(mongo_collection_datetg, tg_id, event_date, period=7)

            current = pandas.DataFrame({'eventDate': event_date,
                                        'totalGRF': tg_date['totalGRF'],
                                        'totalAccel': tg_date['totalAccel']},
                                       index=[str(datetime.strptime(event_date, '%Y-%m-%d').date())])

            if len(hist_records) != 0:
                # convert historical data into pandas dataframe and add current day
                # convert read data into pandas dataframe and remove duplicates and sort
                # TODO: removing dups should be unnecessary as data should already be unique in mongo
                hist = pandas.DataFrame(hist_records)
                hist.drop_duplicates(subset='eventDate', keep='first', inplace=True)
                hist.sort_values(by='eventDate', inplace=True)
                hist.reset_index(drop=True, inplace=True)

                hist = hist.append(current)
                hist.index = hist.eventDate
            else:
                hist = current

            # Add program composition lists to team data
            prog_comps = ['grf', 'totalAccel', 'plane', 'stance']
            for var in prog_comps:
                out_var = var+'ProgramComposition'
                tg_date[out_var] = _aggregate_tg_progcomp(mongo_collection_progcomp,
                                                          var,
                                                          tg_id=tg_id,
                                                          event_date=event_date)
            # For TG date data, sort the variables in order
            record_out = OrderedDict()
            for tg_var in tg_vars:
                try:
                    record_out[tg_var] = tg_date[tg_var]
                except KeyError:
                    record_out[tg_var] = None
            # ACWR
            i = 7
            acwr = _compute_awcr(hist, i, event_date)
            record_out['ACWRGRF' + str(i)] = acwr.totalGRF
            record_out['ACWRTotalAccel' + str(i)] = acwr.totalAccel

            # Upsert the date aggregated collection to mongo (currently replace)
            query = {'trainingGroupId': tg_id, 'eventDate': event_date}
            mongo_collection_datetg.replace_one(query, record_out, upsert=True)

    except Exception as e:
        print(e)
        print('Process did not complete successfully! See error below!')
        raise


def _aggregate_tg_twomin(collection, tg_id, event_date):
    pipeline = [{'$match': {'trainingGroups': {'$eq': tg_id},
                            'eventDate': {'$eq': event_date},
                            'sessionType': {'$eq': '1'}}},
                {'$group': {'_id': {'twoMinuteIndex': '$twoMinuteIndex'},
                            'eventDate': {'$first': '$eventDate'},
                            'sessionType': {'$first': '$sessionType'},
                            'twoMinuteIndex': {'$first': '$twoMinuteIndex'},
                            'totalGRF': {'$sum': '$totalGRF'},
                            'optimalGRF': {'$sum': '$optimalGRF'},
                            'irregularGRF': {'$sum': '$irregularGRF'},
                            'control': weighted_sum('control', 'totalAccel'),
                            'consistency': weighted_sum('consistency', 'totalAccel'),
                            'symmetry': weighted_sum('symmetry', 'totalAccel'),
                            'userCount': {'$sum': 1},
                            'LFgRF': {'$sum': '$LFgRF'},
                            'RFgRF': {'$sum': '$RFgRF'},
                            'singleLegGRF': {'$sum': '$singleLegGRF'},
                            'percLeftGRF': weighted_sum('percLeftGRF', 'singleLegGRF'),
                            'percRightGRF': weighted_sum('percRightGRF', 'singleLegGRF'),
                            'totalAccel': {'$sum': '$totalAccel'},
                            'irregularAccel': {'$sum': '$irregularAccel'},
                            'hipSymmetry': weighted_sum('hipSymmetry', 'totalAccel'),
                            'ankleSymmetry': weighted_sum('ankleSymmetry', 'totalAccel'),
                            'hipConsistency': weighted_sum('hipConsistency', 'totalAccel'),
                            'ankleConsistency': weighted_sum('ankleConsistency', 'totalAccel'),
                            'consistencyLF': weighted_sum('consistencyLF', 'totalAccel'),
                            'consistencyRF': weighted_sum('consistencyRF', 'totalAccel'),
                            'hipControl': weighted_sum('hipControl', 'totalAccel'),
                            'ankleControl': weighted_sum('ankleControl', 'totalAccel'),
                            'controlLF': weighted_sum('controlLF', 'totalAccel'),
                            'controlRF': weighted_sum('controlRF', 'totalAccel'),
                           }
                },
                {'$project': {'_id': 0,
                              'userId': None,
                              'eventDate': 1,
                              'sessionType': 1,
                              'twoMinuteIndex': 1,
                              'totalGRF': divide('totalGRF', 'userCount'),
                              'optimalGRF': divide('optimalGRF', 'userCount'),
                              'irregularGRF': divide('irregularGRF', 'userCount'),
                              'control': divide('control', 'totalAccel'),
                              'consistency': divide('consistency', 'totalAccel'),
                              'symmetry': divide('symmetry', 'totalAccel'),
                              'percLeftGRF': divide('percLeftGRF', 'singleLegGRF', 1),
                              'percRightGRF': divide('percRightGRF', 'singleLegGRF', 1),
                              'percLRGRFDiff': get_perc_diff(),
                              'totalAccel': divide('totalAccel', 'userCount'),
                              'irregularAccel': divide('irregularAccel', 'userCount'),
                              'LFgRF': divide('LFgRF', 'userCount'),
                              'RFgRF': divide('RFgRF', 'userCount'),
                              'singleLegGRF': divide('singleLegGRF', 'userCount'),
                              'percOptimal': get_perc_optimal(),
                              'percIrregular': get_perc_irregular(),
                              'hipSymmetry': divide('hipSymmetry', 'totalAccel'),
                              'ankleSymmetry': divide('ankleSymmetry', 'totalAccel'),
                              'hipConsistency': divide('hipConsistency', 'totalAccel'),
                              'ankleConsistency': divide('ankleConsistency', 'totalAccel'),
                              'consistencyLF': divide('consistencyLF', 'totalAccel'),
                              'consistencyRF': divide('consistencyRF', 'totalAccel'),
                              'hipControl': divide('hipControl', 'totalAccel'),
                              'ankleControl': divide('ankleControl', 'totalAccel'),
                              'controlLF': divide('controlLF', 'totalAccel'),
                              'controlRF': divide('controlRF', 'totalAccel'),
                             }
                }
               ]

    # get all the two minute aggregated records for the team and sort by twoMinIndex
    tg_stats = list(collection.aggregate(pipeline))
    tg_stats = sorted(tg_stats, key=lambda k: k['twoMinuteIndex'])
    team_all = []
    for two_min in tg_stats:
        # for each twoMinuteIndex, get the list of all athlete records
        two_min_index = two_min['twoMinuteIndex']
        ath_pipeline = [{'$match': {'trainingGroups': {'$eq': tg_id},
                                    'eventDate': {'$eq': event_date},
                                    'sessionType': {'$eq': '1'},
                                    'twoMinuteIndex': {'$eq': two_min_index}}}]
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


def _aggregate_tg_progcomp(collection, var, tg_id, event_date):
    """Aggregate progComp for the team
    """
    prog_var = '$'+var+'ProgramComposition'
    pipeline = [{'$match': {'trainingGroups': {'$eq': tg_id},
                            'eventDate': {'$eq': event_date},
                            'sessionType': {'$eq': '1'}}},
                {'$unwind': prog_var},
                {'$group': {'_id': {'binNumber': prog_var+".binNumber"},
                            'binNumber': {'$first': prog_var+".binNumber"},
                            'min': {'$first': prog_var+'.min'},
                            'max': {'$first': prog_var+'.max'},
                            'totalGRF': {'$avg': prog_var+'.totalGRF'},
                            'optimalGRF': {'$avg': prog_var+'.optimalGRF'},
                            'irregularGRF': {'$avg': prog_var+'.irregularGRF'},
                            'totalAcceleration': {'$avg': prog_var+'.totalAcceleration'},
                            'msElapsed': {'$avg': prog_var+'.msElapsed'}}}]
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


def _aggregate_tg(collection, tg_id, event_date):
    """Aggregate team data for the given date
    """
    pipeline = [{'$match': {'trainingGroups': {'$eq': tg_id},
                            'eventDate': {'$eq': event_date},
                            'sessionType': {'$eq': '1'}}},
                {'$group': {'_id': {'trainingGroupId': "$trainingGroups"},
                            'trainingGroupId': {'$first': '$trainingGroups'},
                            'eventDate': {'$first': '$eventDate'},
                            'sessionType': {'$first': '$sessionType'},
                            'totalGRF': {'$sum': '$totalGRF'},
                            'optimalGRF': {'$sum': '$optimalGRF'},
                            'irregularGRF': {'$sum': '$irregularGRF'},
                            'control': weighted_sum('control', 'totalAccel'),
                            'consistency': weighted_sum('consistency', 'totalAccel'),
                            'symmetry': weighted_sum('symmetry', 'totalAccel'),
                            'userCount': {'$sum': 1},
                            'LFgRF': {'$sum': '$LFgRF'},
                            'RFgRF': {'$sum': '$RFgRF'},
                            'singleLegGRF': {'$sum': '$singleLegGRF'},
                            'percLeftGRF': weighted_sum('percLeftGRF', 'singleLegGRF'),
                            'percRightGRF': weighted_sum('percRightGRF', 'singleLegGRF'),
                            'startPercOptimal': {'$avg': '$startPercOptimal'},
                            'fatigue': {'$avg': '$fatigue'},
                            'totalAccel': {'$sum': '$totalAccel'},
                            'irregularAccel': {'$sum': '$irregularAccel'},
                            'hipSymmetry': weighted_sum('hipSymmetry', 'totalAccel'),
                            'ankleSymmetry': weighted_sum('ankleSymmetry', 'totalAccel'),
                            'hipConsistency': weighted_sum('hipConsistency', 'totalAccel'),
                            'ankleConsistency': weighted_sum('ankleConsistency', 'totalAccel'),
                            'consistencyLF': weighted_sum('consistencyLF', 'totalAccel'),
                            'consistencyRF': weighted_sum('consistencyRF', 'totalAccel'),
                            'hipControl': weighted_sum('hipControl', 'totalAccel'),
                            'ankleControl': weighted_sum('ankleControl', 'totalAccel'),
                            'controlLF': weighted_sum('controlLF', 'totalAccel'),
                            'controlRF': weighted_sum('controlRF', 'totalAccel'),
                           }
                },
                {'$project': {'_id': 0,
                              'trainingGroupId': 1,
                              'userId': None,
                              'eventDate': 1,
                              'sessionType': 1,
                              'totalGRF': divide('totalGRF', 'userCount'),
                              'optimalGRF': divide('optimalGRF', 'userCount'),
                              'irregularGRF': divide('irregularGRF', 'userCount'),
                              'control': divide('control', 'totalAccel'),
                              'consistency': divide('consistency', 'totalAccel'),
                              'symmetry': divide('symmetry', 'totalAccel'),
                              'percLeftGRF': divide('percLeftGRF', 'singleLegGRF', 1),
                              'percRightGRF': divide('percRightGRF', 'singleLegGRF', 1),
                              'percLRGRFDiff': get_perc_diff(),
                              'totalAccel': divide('totalAccel', 'userCount'),
                              'irregularAccel': divide('irregularAccel', 'userCount'),
                              'singleLegGRF': divide('singleLegGRF', 'userCount'),
                              'percOptimal': get_perc_optimal(),
                              'percIrregular': get_perc_irregular(),
                             'startPercOptimal': 1,
                              'fatigue': 1,
                              'hipSymmetry': divide('hipSymmetry', 'totalAccel'),
                              'ankleSymmetry': divide('ankleSymmetry', 'totalAccel'),
                              'hipConsistency': divide('hipConsistency', 'totalAccel'),
                              'ankleConsistency': divide('ankleConsistency', 'totalAccel'),
                              'consistencyLF': divide('consistencyLF', 'totalAccel'),
                              'consistencyRF': divide('consistencyRF', 'totalAccel'),
                              'hipControl': divide('hipControl', 'totalAccel'),
                              'ankleControl': divide('ankleControl', 'totalAccel'),
                              'controlLF': divide('controlLF', 'totalAccel'),
                              'controlRF': divide('controlRF', 'totalAccel'),
                             }
                }
               ]
    ath_pipeline = [{'$match': {
        'trainingGroups': {'$eq': tg_id},
        'eventDate': {'$eq': event_date},
        'sessionType': {'$eq': '1'}
    }}]
    tg_stats = list(collection.aggregate(pipeline))[0]
    ath_stats = list(collection.aggregate(ath_pipeline))
    athlete_stats = []
    for athlete in ath_stats:
        single_ath = OrderedDict()
        for ath_var in athlete_vars:
            single_ath[ath_var] = athlete[ath_var]
        single_ath['trainingGroups'] = None
        athlete_stats.append(single_ath)
    tg_stats['AthleteStats'] = athlete_stats
    tg_stats['trainingGroupId'] = tg_id
    return tg_stats


def _get_hist_data(collection, tg_id, event_date, period):
    """
    Get max historical data for acwr computation
    currently only returning totalGRF and totalAccel
    Days with no data have value 0
    """
    total_days = period * 4
    event_date_dt = datetime.strptime(event_date, '%Y-%m-%d').date()
    start_date = str(event_date_dt - timedelta(days=total_days))
    # get history excluding current day
    docs = list(collection.find({'trainingGroups': {'$eq': tg_id},
                                 'sessionType': {'eq': '1'},
                                 'eventDate': {'$gte': start_date, '$lt': event_date}},
                                {'eventDate': 1,
                                 'totalGRF': 1,
                                 'totalAccel': 1,
                                 '_id': 0}))
    return docs


def _compute_awcr(hist, period, event_date):
    """compute acute chronic workload ration for all the variables
        acwr is defined as acute/chronic where
        acute = sum(workload) for current period
        chronic = avg(period_workload) for 4 previous periods
    """
    # TODO: probably don't need this with actual data(there should be no duplication)
#    hist.drop_duplicates(subset='eventDate', keep='first', inplace=True)
    # get the start and end dates of acute and chronic data
    acute_period_end = datetime.strptime(event_date, '%Y-%m-%d').date()
    acute_period_start = acute_period_end - timedelta(days=period - 1)

    # current period is currently included in chronic
    chronic_period_end = acute_period_end
    chronic_period_start = chronic_period_end - timedelta(days=4*period-1)

    # subset acute data and compute acute value
    acute_data = hist.loc[(hist.eventDate >= str(acute_period_start)) &\
                          (hist.eventDate <= str(acute_period_end))]
    acute = acute_data.sum(skipna=True)
    acute.fillna(value=numpy.nan, inplace=True)
    acute.totalAccel = acute.totalAccel / acute_data.shape[0] * period
    acute.totalGRF = acute.totalGRF / acute_data.shape[0] * period

    # subset chronic data and compute chronic value
    chronic_data = hist.loc[(hist.eventDate >= str(chronic_period_start)) &\
                             (hist.eventDate <= str(chronic_period_end))]
    data_start_date = datetime.strptime(chronic_data.eventDate[0], '%Y-%m-%d').date()
    diff = chronic_period_end - data_start_date
    if diff.days >= 10 and chronic_data.shape[0] >= 4:
        chronic = chronic_data.sum()
        chronic.fillna(value=numpy.nan, inplace=True)
        chronic.totalAccel = chronic.totalAccel / chronic_data.shape[0] * period
        chronic.totalGRF = chronic.totalGRF / chronic_data.shape[0] * period
        del acute['eventDate']
        del chronic['eventDate']

        acwr = acute/chronic
        acwr[numpy.isnan(acwr)] = None
    else:
        acwr = pandas.Series({'totalAccel': None,
                              'totalGRF': None})

    return acwr


def divide(var0, var1, cond_var=0):
    """Dict for conditional division in mongo by checking existence of variable
    """
    if cond_var == 0:
        return {'$cond': [{'$eq': ['$'+var0, 0]}, None, {'$divide': ['$'+var0, '$'+var1]}]}
    elif cond_var == 1:
        return {'$cond': [{'$eq': ['$'+var1, 0]}, None, {'$divide': ['$'+var0, '$'+var1]}]}


def weighted_sum(var, weight):
    """Dict for weighted sum in mongo
    """
    return {'$sum': {'$multiply': ['$'+var, '$'+weight]}}


def get_perc_optimal():
    """Dict for percOptimal mongo agg
    """
    return {'$cond': [{'$eq': ['$totalAccel', 0]},
                      None,
                      {'$multiply':
                          [{'$divide': [{'$subtract': ['$totalAccel', '$irregularAccel']},
                                        '$totalAccel']}, 100]}]}


def get_perc_irregular():
    """Dict for percIrregular mongo agg
    """
    return {'$cond': [{'$eq': ['$totalAccel', 0]},
                      None,
                      {'$multiply': [{'$divide': ['$irregularAccel', '$totalAccel']}, 100]}]}


def get_perc_diff():
    """Dict for percLRGRFDiff mongo agg
    """
    return {'$cond': [{'$eq': ['$singleLegGRF', 0]},
                      None, {'$abs': {'$subtract': [{'$divide': ['$percLeftGRF', '$singleLegGRF']},
                                                    {'$divide': ['$percRightGRF', '$singleLegGRF']}
                                                   ]}}]}
