from __future__ import print_function

from collections import namedtuple, OrderedDict
import os
from datetime import datetime, timedelta

import numpy
import pandas
from pymongo import MongoClient

from alert import Alert

Config = namedtuple('Config', [
    'AWS',
    'ENVIRONMENT',
    'MONGO_HOST',
    'MONGO_USER',
    'MONGO_PASSWORD',
    'MONGO_DATABASE',
    'MONGO_COLLECTION_SESSION',
    'MONGO_COLLECTION_DATE',
    'MONGO_REPLICASET',
])

def connect_mongo(config):
    """Connect to relevant mongo database and collections
    """
    # Connect to mongo
    mongo_client = MongoClient(config.MONGO_HOST, replicaset=config.MONGO_REPLICASET)

    mongo_database = mongo_client[config.MONGO_DATABASE]

    # Authenticate
    mongo_database.authenticate(config.MONGO_USER, config.MONGO_PASSWORD,
                                mechanism='SCRAM-SHA-1')

    mongo_collection_session = mongo_database[config.MONGO_COLLECTION_SESSION]
    mongo_collection_date = mongo_database[config.MONGO_COLLECTION_DATE]

    return mongo_collection_session, mongo_collection_date


def script_handler(input_data):
    print("Definitely running")

    try:
        config = Config(
            AWS=False,
            ENVIRONMENT=os.environ['ENVIRONMENT'],
            MONGO_HOST=os.environ['MONGO_HOST_SESSION'],
            MONGO_USER=os.environ['MONGO_USER_SESSION'],
            MONGO_PASSWORD=os.environ['MONGO_PASSWORD_SESSION'],
            MONGO_DATABASE=os.environ['MONGO_DATABASE_SESSION'],
            MONGO_COLLECTION_SESSION=os.environ['MONGO_COLLECTION_SESSION'],
            MONGO_COLLECTION_DATE=os.environ['MONGO_COLLECTION_DATE'],
            MONGO_REPLICASET=os.environ['MONGO_REPLICASET_SESSION'] if os.environ['MONGO_REPLICASET_SESSION'] != '---' else None,
        )

        mongo_collection_session, mongo_collection_date = connect_mongo(config)

        team_id = input_data.get('TeamId', None)
        training_group_id = input_data.get('TrainingGroupIds', None)
        user_id = input_data.get('UserId', None)
        user_mass = input_data.get('UserMassKg', None)

        event_date = input_data.get('EventDate')

        # get aggregated data for all sessions sessions for current_day
        current_day = _get_session_data(mongo_collection_session, user_id, event_date)

        # grab maximum required historical data
        hist_records = _get_hist_data(mongo_collection_date, user_id, event_date, period=7)

        current = pandas.DataFrame({'eventDate': event_date,
                                    'totalGRF': current_day['totalGRF'],
                                    'totalAccel': current_day['totalAccel']},
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

        # create ordered dictionary object
        # current variables
        record_out = OrderedDict({'teamId': team_id})
        record_out['userId'] = user_id
        record_out['eventDate'] = str(event_date)
        record_out['sessionType'] = '1'

        # grf
        record_out['totalGRF'] = current_day['totalGRF']
        record_out['optimalGRF'] = current_day['optimalGRF']
        record_out['irregularGRF'] = current_day['irregularGRF']

        # scores
        record_out['control'] = current_day['control']
        record_out['consistency'] = current_day['consistency']
        record_out['symmetry'] = current_day['symmetry']

        # blank placeholders for programcomp
        record_out['grfProgramComposition'] = None
        record_out['totalAccelProgramComposition'] = None
        record_out['planeProgramComposition'] = None
        record_out['stanceProgramComposition'] = None
        record_out['trainingGroups'] = training_group_id

        # new variables
        record_out['userMass'] = user_mass

        # grf distribution
        record_out['LFgRF'] = current_day['LFgRF']
        record_out['RFgRF'] = current_day['RFgRF']
        record_out['singleLegGRF'] = current_day['singleLegGRF']
        record_out['percLeftGRF'] = current_day['percLeftGRF']
        record_out['percRightGRF'] = current_day['percRightGRF']
        record_out['percLRGRFDiff'] = current_day['percLRGRFDiff']

        # acceleration
        record_out['totalAccel'] = current_day['totalAccel']
        record_out['irregularAccel'] = current_day['irregularAccel']

        # scores
        record_out['hipSymmetry'] = current_day['hipSymmetry']
        record_out['ankleSymmetry'] = current_day['ankleSymmetry']
        record_out['hipConsistency'] = current_day['hipConsistency']
        record_out['ankleConsistency'] = current_day['ankleConsistency']
        record_out['consistencyLF'] = current_day['consistencyLF']
        record_out['consistencyRF'] = current_day['consistencyRF']
        record_out['hipControl'] = current_day['hipControl']
        record_out['ankleControl'] = current_day['ankleControl']
        record_out['controlLF'] = current_day['controlLF']
        record_out['controlRF'] = current_day['controlRF']

        # fatigue data
        record_out['percOptimal'] = current_day['percOptimal']
        record_out['percIrregular'] = current_day['percIrregular']
        record_out['startMovementQuality'] = current_day['startMovementQuality']
        record_out['fatigue'] = current_day['fatigue']

        # ACWR
        i = 7
        acwr = _compute_awcr(hist, i, event_date)
        record_out['ACWRGRF' + str(i)] = acwr.totalGRF
        record_out['ACWRTotalAccel' + str(i)] = acwr.totalAccel

        _publish_alerts(record_out, acwr)

        query = {'userId': user_id, 'eventDate': event_date}
        mongo_collection_date.replace_one(query, record_out, upsert=True)
        print("Finished writing date!")

    except Exception as e:
        print(e)
        print('Process did not complete successfully! See error below!')
        raise


def _publish_alerts(record_out, acwr):
    # Training Volume

    if 1.2 < acwr.totalGRF <= 1.5 or acwr.totalGRF < 0.79 and acwr.totalGRF is not None:
        _publish_alert(record_out, category=1, subcategory=1, granularity='total', value=1)
    elif 1.5 < acwr.totalGRF and acwr.totalGRF is not None:
        _publish_alert(record_out, category=1, subcategory=1, granularity='total', value=2)

    if 1.2 < acwr.totalAccel <= 1.5 or acwr.totalAccel < 0.79 and acwr.totalAccel is not None:
        _publish_alert(record_out, category=1, subcategory=2, granularity='total', value=1)
    elif 1.5 < acwr.totalAccel and acwr.totalAccel is not None:
        _publish_alert(record_out, category=1, subcategory=2, granularity='total', value=2)

    # Movement Quality

    # GRF Dist
    if 5 < record_out['percLRGRFDiff'] <= 10:
        _publish_alert(record_out, category=3, subcategory=1, granularity='total', value=1)
    elif record_out['percLRGRFDiff'] > 10:
        _publish_alert(record_out, category=3, subcategory=1, granularity='total', value=2)

    # symmetry
    symmetry_scores = [record_out['symmetry'],
                       record_out['hipSymmetry'],
                       record_out['ankleSymmetry']]
    min_symm = numpy.min(symmetry_scores)
    max_symm = numpy.max(symmetry_scores)
    if min_symm is not None and max_symm is not None:
        symm_comp_diff = numpy.abs(min_symm - max_symm)
        if min_symm < 50 or symm_comp_diff > 30:
            _publish_alert(record_out, category=3, subcategory=2, granularity='total', value=2)
        elif 50 <= min_symm < 65 or 20 <= symm_comp_diff < 30:
            _publish_alert(record_out, category=3, subcategory=2, granularity='total', value=1)

    # Control
    control_scores = [record_out['control'],
                      record_out['hipControl'],
                      record_out['ankleControl'],
                      record_out['controlLF'],
                      record_out['controlRF']]
    min_cont = numpy.min(control_scores)
    max_cont = numpy.max(control_scores)
    print(min_cont, max_cont)
    if min_cont is not None and max_cont is not None:
        control_comp_diff = numpy.abs(min_cont - max_cont)
        if min_cont < 50 or control_comp_diff > 30:
            _publish_alert(record_out, category=3, subcategory=3, granularity='total', value=2)
        elif 50 <= min_cont < 65 or 20 <= control_comp_diff < 30:
            _publish_alert(record_out, category=3, subcategory=3, granularity='total', value=1)

    # Consistency
    # consistency_scores = [record_out['consistency'],
    #                       record_out['hipConsistency'],
    #                       record_out['ankleConsistency'],
    #                       record_out['consistencyLF'],
    #                       record_out['consistencyRF']]
    # min_cons = numpy.min(consistency_scores)
    # max_cons = numpy.max(consistency_scores)
    # if min_cons is not None and max_cons is not None:
    #     consistency_comp_diff = numpy.abs(min_cons - max_cons)
    #     if min_cons < 50 or consistency_comp_diff > 30:
    #         _publish_alert(record_out, category=3, subcategory=4, granularity='total', value=2)
    #     elif 50 <= min_cons < 65 or 20 <= consistency_comp_diff < 30:
    #         _publish_alert(record_out, category=3, subcategory=4, granularity='total', value=1)


def _publish_alert(record_out, category, subcategory, granularity, value):
    alert = Alert(
        user_id=record_out['userId'],
        team_id=record_out['teamId'],
        training_group_ids=record_out['trainingGroups'],
        event_date=record_out['eventDate'],
        session_type=record_out['sessionType'],
        category=category,
        subcategory=subcategory,
        granularity=granularity,
        value=value
    )
    alert.publish()


def _get_session_data(collection, user_id, event_date):
    """ Get aggregated data for the sessions by the user for given date
    Aggregation is done using mongo api
    Returns:
        dictionary with aggregated values for the day
    """
    pipeline = [{'$match': {'userId': {'$eq': user_id},
                            'eventDate': {'$eq': event_date},
                            'sessionType': {'$eq': '1'}
                           }
                },
                {'$group': {'_id': {'userId': "$userId"},
                            'teamId': {'$first': '$teamId'},
                            'userId': {'$first': '$userId'},
                            'eventDate': {'$first': '$eventDate'},
                            'sessionType': {'$first': '$sessionType'},
                            'totalGRF': {'$sum': '$totalGRF'},
                            'optimalGRF': {'$sum': '$optimalGRF'},
                            'irregularGRF': {'$sum': '$irregularGRF'},
                            'control': weighted_sum('control', 'totalAccel'),
                            'consistency': weighted_sum('consistency', 'totalAccel'),
                            'symmetry': weighted_sum('symmetry', 'totalAccel'),
                            'trainingGroups': {'$first': '$trainingGroups'},
                            'LFgRF': {'$sum': '$LFgRF'},
                            'RFgRF': {'$sum': '$RFgRF'},
                            'singleLegGRF': {'$sum': '$singleLegGRF'},
                            'percLeftGRF': weighted_sum('percLeftGRF', 'singleLegGRF'),
                            'percRightGRF': weighted_sum('percRightGRF', 'singleLegGRF'),
                            'startMovementQuality': {'$avg': '$startMovementQuality'},
                            'fatigue': {'$avg': '$sessionFatigue'},
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
                {'$project':{'_id': 0,
                             'userId':1,
                             'totalGRF': {'$cond': [{'$eq': ['$totalGRF', 0]}, None, '$totalGRF']},
                             'optimalGRF': {'$cond': [{'$eq': ['$optimalGRF', 0]}, None, '$optimalGRF']},
                             'irregularGRF': {'$cond': [{'$eq': ['$irregularGRF', 0]}, None, '$irregularGRF']},
                             'control': divide('control', 'totalAccel'),
                             'consistency': divide('consistency', 'totalAccel'),
                             'symmetry': divide('symmetry', 'totalAccel'),
                             'trainingGroups': 1,
                             'percLeftGRF': divide('percLeftGRF', 'singleLegGRF', 1),
                             'percRightGRF': divide('percRightGRF', 'singleLegGRF', 1),
                             'percLRGRFDiff': get_perc_diff(),
                             'totalAccel': {'$cond': [{'$eq': ['$totalAccel', 0]}, None, '$totalAccel']},
                             'irregularAccel': {'$cond': [{'$eq': ['$irregularAccel', 0]}, None, '$irregularAccel']},
                             'LFgRF': {'$cond': [{'$eq': ['$LFgRF', 0]}, None, '$LFgRF']},
                             'RFgRF': {'$cond': [{'$eq': ['$RFgRF', 0]}, None, '$RFgRF']},
                             'singleLegGRF': {'$cond': [{'$eq': ['$singleLegGRF', 0]}, None, '$singleLegGRF']},
                             'percOptimal': get_perc_optimal(),
                             'percIrregular': get_perc_irregular(),
                             'startMovementQuality': 1,
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
    docs = list(collection.aggregate(pipeline))

    return docs[0]


def _get_hist_data(collection, user_id, event_date, period):
    """
    Get max historical data for acwr computation
    currently only returning totalGRF and totalAccel
    Days with no data have value 0
    """
    total_days = period * 4
    event_date_dt = datetime.strptime(event_date, '%Y-%m-%d').date()
    start_date = str(event_date_dt - timedelta(days=total_days))
    # get history excluding current day
    docs = list(collection.find({'userId': {'$eq': user_id},
                                 'sessionType': {'$eq': '1'},
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
        acwr = acwr.where((pandas.notnull(acwr)), None)
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
