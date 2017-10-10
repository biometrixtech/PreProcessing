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
            MONGO_HOST=os.environ['MONGO_HOST_SESSION'],
            MONGO_USER=os.environ['MONGO_USER_SESSION'],
            MONGO_PASSWORD=os.environ['MONGO_PASSWORD_SESSION'],
            MONGO_DATABASE=os.environ['MONGO_DATABASE_SESSION'],
            MONGO_COLLECTION_SESSION=os.environ['MONGO_COLLECTION_SESSION'],
            MONGO_COLLECTION_DATE=os.environ['MONGO_COLLECTION_DATE'],
            MONGO_REPLICASET=os.environ['MONGO_REPLICASET_SESSION'] if os.environ['MONGO_REPLICASET_SESSION'] != '---' else None,
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
        session_type = input_data.get('SessionType', None)
        if session_type is not None:
            session_type = str(session_type)
        user_mass = input_data.get('UserMass', 155) * 4.4482

        event_date = input_data.get('EventDate')

        # get aggregated data for all sessions sessions for current_day
        current_day = _get_session_data(mongo_collection_session, user_id,
                                        event_date, session_type)

        # grab maximum required historical data
        hist_records = _get_hist_data(mongo_collection_date, user_id,
                                      event_date, period=10)

        current = pandas.DataFrame({'eventDate': event_date,
                                    'totalAccel': current_day['totalAccel'],
                                    'totalGRF': current_day['totalGRF']},
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
        # hist_data = hist_data.fillna(0)
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
                hist_data.loc[hist_data.eventDate == i, 'totalAccel'] = subset['totalAccel'].values[0]
            # append current day's data to the end
            hist_data = hist_data.append(current)
        else:
            # if no hist data available, mark as nan and append current day
            hist_data.totalGRF = numpy.nan
            hist_data.totalAccel = numpy.nan
            hist_data = hist_data.append(current)

        # create ordered dictionary object
        # current variables
        record_out = OrderedDict({'teamId': team_id})
        record_out['userId'] = user_id
        record_out['eventDate'] = str(event_date)
        record_out['sessionType'] = session_type

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
        record_out['fatigue'] = current_day['fatigue']

        # ACWR
        i = 7
        acwr = _compute_awcr(hist_data, i, event_date)
        record_out['ACWRGRF' + str(i)] = acwr.totalGRF
        record_out['ACWRTotalAccel' + str(i)] = acwr.totalAccel
        query = {'userId': user_id, 'eventDate': event_date}
        mongo_collection_date.replace_one(query, record_out, upsert=True)
        logger.info("Finished writing date!")

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise


def _get_session_data(collection, user_id, event_date, session_type):
    """ Get aggregated data for the sessions (of given session_type) by the user for given date
    Aggregation is done using mongo api
    Returns:
        dictionary with aggregated values for the day
    """
    pipeline = [{'$match': {'userId': {'$eq': user_id},
                            'eventDate': {'$eq': event_date},
                            'sessionType': {'$eq': session_type}
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
                            'control': {'$sum': {'$multiply': ['$control', '$totalGRF']}},
                            'consistency': {'$sum': {'$multiply': ['$consistency', '$totalGRF']}},
                            'symmetry': {'$sum': {'$multiply': ['$symmetry', '$totalGRF']}},
                            'trainingGroups': {'$first': '$trainingGroups'},
                            'LFgRF': {'$sum': '$LFgRF'},
                            'RFgRF': {'$sum': '$RFgRF'},
                            'singleLegGRF': {'$sum': '$singleLegGRF'},
                            'percLeftGRF': {'$sum': {'$multiply': ['$percLeftGRF', '$singleLegGRF']}},
                            'percRightGRF': {'$sum': {'$multiply': ['$percRightGRF', '$singleLegGRF']}},
                            'fatigue': {'$avg': '$sessionFatigue'},
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
                             'userId':1,
                             'totalGRF': 1,
                             'optimalGRF':1,
                             'irregularGRF':1,
                             'control': {'$divide': ['$control', '$totalGRF']},
                             'consistency': {'$divide': ['$consistency', '$totalGRF']},
                             'symmetry': {'$divide': ['$symmetry', '$totalGRF']},
                             'trainingGroups': 1,
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
                                 'eventDate': {'$gte': start_date, '$lt': event_date}},
                                {'userId': 1,
                                 'eventDate': 1,
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
    acute = acute_data.sum()
    acute.totalAccel = acute.totalAccel / acute_data.shape[0] * period
    acute.totalGRF = acute.totalGRF / acute_data.shape[0] * period

    # subset chronic data and compute chronic value
    chronic_data = hist.loc[(hist.eventDate >= str(chronic_period_start)) &\
                             (hist.eventDate <= str(chronic_period_end))]
    chronic = chronic_data.sum()
    chronic.totalAccel = chronic.totalAccel / chronic_data.shape[0] * period
    chronic.totalGRF = chronic.totalGRF / chronic_data.shape[0] * period
    del acute['eventDate']
    del chronic['eventDate']

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
    input_data['UserMass'] = 155
    input_data['EventDate'] = '2017-03-20'

    os.environ['ENVIRONMENT'] = 'Dev'
    os.environ['MONGO_HOST_SESSION'] = 'ec2-34-210-169-8.us-west-2.compute.amazonaws.com:27017'
    os.environ['MONGO_USER_SESSION'] = 'statsUser'
    os.environ['MONGO_PASSWORD_SESSION'] = 'BioMx211'
    os.environ['MONGO_DATABASE_SESSION'] = 'movementStats'
    os.environ['MONGO_COLLECTION_SESSION'] = 'sessionStats_test3'
    os.environ['MONGO_COLLECTION_DATE'] = 'dateStats_test3'
    os.environ['MONGO_REPLICASET_SESSION'] = '---'
    script_handler(input_data)
    print(time.time() - start)
