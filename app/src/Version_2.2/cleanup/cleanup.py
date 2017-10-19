from __future__ import print_function

from collections import namedtuple
import glob
import logging
import os
import shutil
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def script_handler(working_directory):

    logger.info('Running cleanup on "{}"'.format(working_directory))

    try:

        # Clean up downloadandchunk output directory
        shutil.rmtree(os.path.join(working_directory, 'downloadandchunk'))

        # Clean up sessionprocess2 output directory
        shutil.rmtree(os.path.join(working_directory, 'scoring_chunked'))

        logger.info('Finished cleanup on {}'.format(working_directory))
        return {}

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise
