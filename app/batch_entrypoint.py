#!/usr/bin/env python
# Entrypoint when called as a batch job
from __future__ import print_function
import os
import logging
import sys

from config import load_parameters
from datastore import Datastore


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
_logger = logging.getLogger(__name__)


def main(script):
    if script == 'noop':
        _logger.info('Noop job')
        # A noop job used as a 'gate', using job dependencies to recombine parallel tasks
        return

    if 'SESSION_ID' not in os.environ:
        raise Exception('No session id given')
    else:
        session_id = os.environ['SESSION_ID']

    datastore = Datastore(session_id)

    if script == 'downloadandchunk':
        from jobs.downloadandchunk import DownloadandchunkJob
        DownloadandchunkJob(datastore).run()

    elif script == 'transformandplacement':
        from jobs.transformandplacement import TransformandplacementJob
        TransformandplacementJob(datastore).run()

    elif script == 'sessionprocess':
        load_parameters(['MS_MODEL',
                         'LF_MS_MODEL',
                         'RF_MS_MODEL',
                         'MS_SCALER',
                         'SL_MS_SCALER'],
                         'models')
        # Use theano backend for keras
        os.environ['KERAS_BACKEND'] = 'theano'

        from jobs.sessionprocess import SessionprocessJob
        SessionprocessJob(datastore).run()

    # elif script == 'sessionprocess1':
    #     load_parameters(['MS_MODEL',
    #                      'LF_MS_MODEL',
    #                      'RF_MS_MODEL',
    #                      'MS_SCALER',
    #                      'SL_MS_SCALER'],
    #                      'models')
    #     # Use theano backend for keras
    #     os.environ['KERAS_BACKEND'] = 'theano'
    #     if input_data.get('Sensors') == 3:
    #         print('Running sessionprocess on multi-sensor data')
    #         from sessionProcess2 import sessionProcess
    #     elif input_data.get('Sensors') == 1:
    #         print('Running sessionprocess on single-sensor data')
    #         from sessionProcess1 import sessionProcess
    #     else:
    #         raise Exception('Must have either 1 or 3 sensors')
    #
    #     file_name = input_data.get('Filenames', [])[int(os.environ.get('AWS_BATCH_JOB_ARRAY_INDEX', 0))]
    #     sessionProcess.script_handler(
    #         working_directory,
    #         file_name,
    #         input_data
    #     )
    #     print(meta_data)
    #     send_profiling(meta_data)
    #
    # elif script == 'scoring':
    #     if input_data.get('Sensors') == 3:
    #         print('Running scoring on multi-sensor data')
    #         from scoring import scoringProcess
    #     elif input_data.get('Sensors') == 1:
    #         print('Running scoring on single-sensor data')
    #         from scoring1 import scoringProcess
    #     else:
    #         raise Exception('Must have either 1 or 3 sensors')
    #
    #     boundaries = scoringProcess.script_handler(
    #         working_directory,
    #         input_data.get('Filenames', None),
    #         input_data
    #     )
    #     print(boundaries)
    #
    #     # Chunk files for input to writemongo
    #     from utils import chunk
    #     mkdir(os.path.join(working_directory, 'scoring_chunked'))
    #     file_names = chunk.chunk_by_line(
    #         os.path.join(working_directory, 'scoring'),
    #         os.path.join(working_directory, 'scoring_chunked'),
    #         boundaries
    #     )
    #
    #     send_success(meta_data, {"Filenames": file_names, "FileCount": len(file_names)})
    #
    # elif script == 'aggregatesession':
    #     load_parameters([
    #         'MONGO_HOST',
    #         'MONGO_USER',
    #         'MONGO_PASSWORD',
    #         'MONGO_DATABASE',
    #         'MONGO_REPLICASET',
    #         'MONGO_COLLECTION_SESSION',
    #     ], 'mongo')
    #     if input_data.get('Sensors') == 3:
    #         print('Computing session aggregations on multi-sensor data')
    #         from sessionAgg import agg_session
    #     elif input_data.get('Sensors') == 1:
    #         print('Computing session aggregations on single sensor data')
    #         from sessionAgg1 import agg_session
    #     else:
    #         raise Exception('Must have either 1 or 3 sensors')
    #
    #     agg_session.script_handler(
    #         working_directory,
    #         input_data
    #     )
    #     send_profiling(meta_data)
    #
    # elif script == 'aggregateblocks':
    #     load_parameters([
    #         'MONGO_HOST',
    #         'MONGO_USER',
    #         'MONGO_PASSWORD',
    #         'MONGO_DATABASE',
    #         'MONGO_REPLICASET',
    #         'MONGO_COLLECTION_ACTIVEBLOCKS',
    #     ], 'mongo')
    #     if input_data.get('Sensors') == 3:
    #         print('Computing block multi-sensor data')
    #         from activeBlockAgg import agg_blocks
    #     elif input_data.get('Sensors') == 1:
    #         print('Computing block single-sensor data')
    #         from activeBlockAgg1 import agg_blocks
    #     else:
    #         raise Exception('Must have either 1 or 3 sensors')
    #
    #     agg_blocks.script_handler(
    #         working_directory,
    #         input_data
    #     )
    #     send_profiling(meta_data)
    #
    # elif script == 'advancedstats':
    #     load_parameters([
    #         'MONGO_HOST',
    #         'MONGO_USER',
    #         'MONGO_PASSWORD',
    #         'MONGO_DATABASE',
    #         'MONGO_REPLICASET',
    #         'MONGO_COLLECTION_ACTIVEBLOCKS',
    #     ], 'mongo')
    #     if input_data.get('Sensors') == 3:
    #         print('Computing advanced stats for multi-sensor data')
    #         from advancedStats import advanced_stats
    #         mkdir(os.path.join(working_directory, 'advanced_stats'))
    #         advanced_stats.script_handler(
    #             os.path.join(working_directory, 'advanced_stats'),
    #             input_data
    #         )
    #         send_profiling(meta_data)
    #     elif input_data.get('Sensors') == 1:
    #         print('Skipping advanced stats calculations for single-sensor data')
    #     else:
    #         raise Exception('Must have either 1 or 3 sensors')
    #
    #
    # elif script == 'aggregatetwomin':
    #     load_parameters([
    #         'MONGO_HOST',
    #         'MONGO_USER',
    #         'MONGO_PASSWORD',
    #         'MONGO_DATABASE',
    #         'MONGO_REPLICASET',
    #         'MONGO_COLLECTION_TWOMIN',
    #     ], 'mongo')
    #     if input_data.get('Sensors') == 3:
    #         print('Computing two minute aggregations on multi-sensor data')
    #         from twoMinuteAgg import agg_twomin
    #     elif input_data.get('Sensors') == 1:
    #         print('Computing two minute aggregations on single-sensor data')
    #         from twoMinuteAgg1 import agg_twomin
    #     else:
    #         raise Exception('Must have either 1 or 3 sensors')
    #
    #     agg_twomin.script_handler(
    #         working_directory,
    #         'chunk_{index:02d}'.format(index=int(os.environ.get('AWS_BATCH_JOB_ARRAY_INDEX', 0))),
    #         input_data
    #     )
    #     send_profiling(meta_data)
    #
    # elif script == 'aggregatedateuser':
    #     print('Computing date-user aggregations')
    #     load_parameters([
    #         'MONGO_HOST',
    #         'MONGO_USER',
    #         'MONGO_PASSWORD',
    #         'MONGO_DATABASE',
    #         'MONGO_REPLICASET',
    #         'MONGO_COLLECTION_SESSION',
    #         'MONGO_COLLECTION_DATE',
    #     ], 'mongo')
    #     from dateAggUser import agg_date_user
    #
    #     agg_date_user.script_handler(
    #         input_data
    #     )
    #     send_profiling(meta_data)
    #
    # elif script == 'aggregateprogcomp':
    #     if input_data.get('Sensors') == 3:
    #         print('Computing program composition aggregations')
    #         load_parameters([
    #             'MONGO_HOST',
    #             'MONGO_USER',
    #             'MONGO_PASSWORD',
    #             'MONGO_DATABASE',
    #             'MONGO_REPLICASET',
    #             'MONGO_COLLECTION_PROGCOMP',
    #         ], 'mongo')
    #         from progComp import prog_comp
    #
    #         prog_comp.script_handler(
    #             working_directory,
    #             input_data
    #         )
    #     else:
    #         print('Program composition is not needed for single-sensor data')
    #
    #     send_profiling(meta_data)
    #
    # elif script == 'aggregateprogcompdate':
    #     if input_data.get('Sensors') == 3:
    #         print('Computing program composition date aggregations')
    #         load_parameters([
    #             'MONGO_HOST',
    #             'MONGO_USER',
    #             'MONGO_PASSWORD',
    #             'MONGO_DATABASE',
    #             'MONGO_REPLICASET',
    #             'MONGO_COLLECTION_PROGCOMP',
    #             'MONGO_COLLECTION_PROGCOMPDATE',
    #         ], 'mongo')
    #         from progCompDate import prog_comp_date
    #
    #         prog_comp_date.script_handler(
    #             input_data
    #         )
    #     else:
    #         print('Program composition is not needed for single-sensor data')
    #
    #     send_profiling(meta_data)
    #
    # elif script == 'aggregateteam':
    #     print('Computing team aggregations')
    #     load_parameters([
    #         'MONGO_HOST',
    #         'MONGO_USER',
    #         'MONGO_PASSWORD',
    #         'MONGO_DATABASE',
    #         'MONGO_REPLICASET',
    #         'MONGO_COLLECTION_DATE',
    #         'MONGO_COLLECTION_DATETEAM',
    #         'MONGO_COLLECTION_PROGCOMPDATE',
    #         'MONGO_COLLECTION_TWOMIN',
    #         'MONGO_COLLECTION_TWOMINTEAM',
    #     ], 'mongo')
    #     from teamAgg import agg_team
    #
    #     agg_team.script_handler(
    #         input_data
    #     )
    #     send_profiling(meta_data)
    #
    # elif script == 'aggregatetraininggroup':
    #     print('Computing training group aggregations')
    #     load_parameters([
    #         'MONGO_HOST',
    #         'MONGO_USER',
    #         'MONGO_PASSWORD',
    #         'MONGO_DATABASE',
    #         'MONGO_REPLICASET',
    #         'MONGO_COLLECTION_DATE',
    #         'MONGO_COLLECTION_DATETG',
    #         'MONGO_COLLECTION_PROGCOMP',
    #         'MONGO_COLLECTION_PROGCOMPDATE',
    #         'MONGO_COLLECTION_TWOMIN',
    #         'MONGO_COLLECTION_TWOMINTG',
    #     ], 'mongo')
    #     from TGAgg import agg_tg
    #
    #     agg_tg.script_handler(
    #         input_data
    #     )
    #     send_profiling(meta_data)
    #
    # elif script == 'cleanup':
    #     print('Cleaning up intermediate files')
    #     from cleanup import cleanup
    #     cleanup.script_handler(
    #         working_directory
    #     )
    #     send_profiling(meta_data)

    else:
        raise Exception("Unknown batchjob '{}'".format(script))


if __name__ == '__main__':
    main(sys.argv[1])
