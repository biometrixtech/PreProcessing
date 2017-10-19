from __future__ import print_function

from collections import namedtuple
from io import StringIO
import json
import logging
import os
import runScoring
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.info('Loading sessionProcess')

Config = namedtuple('Config', [
    'AWS',
    'ENVIRONMENT',
    'FP_INPUT',
    'FP_OUTPUT',
    'FP_SCORINGHIST',
    'S3_BUCKET_HISTORY',
])


def script_handler(filenames, data):

    logger.info('Received scoring request for {}'.format(", ".join(filenames)))

    try:
        config = Config(
            AWS=False,
            ENVIRONMENT=os.environ['ENVIRONMENT'],
            FP_INPUT='/net/efs/scoring/input',
            FP_OUTPUT='/net/efs/scoring/output',
            FP_SCORINGHIST='/net/efs/scoringhist',
            S3_BUCKET_HISTORY='biometrix-scoringhist'
        )

        # Get the base filename
        file_name = filenames[0].split('_')[0]

        current_stream = cat_csv_files([os.path.join(config.FP_INPUT, f) for f in sorted(filenames)])

        historical_filenames = data.get('HistoricalFiles', [])
        if not isinstance(historical_filenames, list) or len(historical_filenames) == 0:
            # No historical files
            historical_filenames = []

        historical_stream = cat_csv_files(
            [os.path.join(config.FP_INPUT, f) for f in filenames] +
            [os.path.join(config.FP_OUTPUT, f) for f in historical_filenames]
        )

        boundaries = runScoring.run_scoring(current_stream, historical_stream, file_name, data, config=config)
        return file_name, boundaries

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise


def cat_csv_files(filenames):
        csv_data = []
        count = 0
        for filename in filenames:
            with open(filename, 'r') as f:
                lines = f.readlines()
                if count == 0:
                    csv_data.extend([lines[0]])
                csv_data.extend(lines[1:])
            count += 1

        print("{} rows".format(len(csv_data) - 1))
        csv_data = u"\n".join(csv_data)
        return StringIO(csv_data)

if __name__ == '__main__':
    argv_file_name = json.loads(sys.argv[1])
    script_handler(argv_file_name, {"UserMass": 60, "SessionEventId": "7c6b5f4f-afd8-4793-8f76-dc57b985d4b6"})
