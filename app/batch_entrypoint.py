#!/usr/bin/env python3
# Entrypoint when called as a batch job
from __future__ import print_function
import os
import logging
import sys

from aws_xray_sdk.core import xray_recorder, patch_all
patch_all()
xray_recorder.configure(
    sampling=False,
    context_missing='LOG_ERROR',
)

from config import load_parameters
from datastore import Datastore


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
_logger = logging.getLogger(__name__)


@xray_recorder.capture('app.main')
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
        load_parameters([
            'MS_MODEL',
            'LF_MS_MODEL',
            'RF_MS_MODEL',
            'MS_SCALER',
            'SL_MS_SCALER'
         ], 'models')
        # Use theano backend for keras
        os.environ['KERAS_BACKEND'] = 'theano'

        from jobs.sessionprocess import SessionprocessJob
        SessionprocessJob(datastore).run()

    elif script == 'scoring':
        from jobs.scoring import ScoringJob
        ScoringJob(datastore).run()

    elif script == 'aggregateblocks':
        load_parameters([
            'MONGO_HOST',
            'MONGO_USER',
            'MONGO_PASSWORD',
            'MONGO_DATABASE',
            'MONGO_REPLICASET',
            'MONGO_COLLECTION_ACTIVEBLOCKS',
        ], 'mongo')
        from jobs.aggregateblocks import AggregateblocksJob
        AggregateblocksJob(datastore).run()

    elif script == 'advancedstats':
        load_parameters([
            'MONGO_HOST',
            'MONGO_USER',
            'MONGO_PASSWORD',
            'MONGO_DATABASE',
            'MONGO_REPLICASET',
            'MONGO_COLLECTION_ACTIVEBLOCKS',
        ], 'mongo')
        from jobs.advancedstats import AdvancedstatsJob
        AdvancedstatsJob(datastore).run()

    elif script == 'sessionprocess1':
        load_parameters([
            'MS_MODEL',
            'LF_MS_MODEL',
            'RF_MS_MODEL',
            'MS_SCALER',
            'SL_MS_SCALER'
        ], 'models')
        # Use theano backend for keras
        os.environ['KERAS_BACKEND'] = 'theano'

        from jobs.sessionprocess1 import Sessionprocess1Job
        Sessionprocess1Job(datastore).run()

    elif script == 'scoring1':
        from jobs.scoring1 import Scoring1Job
        Scoring1Job(datastore).run()

    elif script == 'aggregateblocks1':
        load_parameters([
            'MONGO_HOST',
            'MONGO_USER',
            'MONGO_PASSWORD',
            'MONGO_DATABASE',
            'MONGO_REPLICASET',
            'MONGO_COLLECTION_ACTIVEBLOCKS',
        ], 'mongo')
        from jobs.aggregateblocks1 import Aggregateblocks1Job
        Aggregateblocks1Job(datastore).run()

    elif script == 'cleanup':
        from jobs.cleanup import CleanupJob
        CleanupJob(datastore).run()

    else:
        raise Exception("Unknown batchjob '{}'".format(script))


if __name__ == '__main__':
    job = sys.argv[1]
    with xray_recorder.in_segment('preprocessing.{}.app'.format(os.environ.get('ENVIRONMENT', None))) as segment:
        segment.put_annotation('environment', os.environ.get('ENVIRONMENT', None))
        segment.put_http_meta('url', 'batch://preprocessing.dev.fathomai.com/{}'.format(job))
        main(job)
