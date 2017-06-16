from __future__ import print_function

from collections import namedtuple
import boto3
import glob
import logging
import os
import subprocess
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

Config = namedtuple('Config', [
    'AWS',
    'ENVIRONMENT',
    'FP_INPUT',
    'FP_OUTPUT',
    'KMS_REGION',
    'S3_REGION',
    'S3_BUCKET',
    'S3_KEY',
    'CHUNK_SIZE',
])


def script_handler(s3_bucket, s3_path, chunk_size=100):

    logger.info('Running downloadAndChunk on "{}/{}"'.format(s3_bucket, s3_path))

    try:
        config = Config(
            AWS=False,
            ENVIRONMENT=os.environ['ENVIRONMENT'],
            FP_INPUT=None,
            FP_OUTPUT='/net/efs/downloadandchunk/output',
            KMS_REGION='us-west-2',
            S3_REGION='us-west-2',
            S3_BUCKET=s3_bucket,
            S3_KEY=s3_path,
            CHUNK_SIZE=chunk_size
        )

        s3_client = boto3.client('s3', region_name=config.S3_REGION)

        # Download file
        tmp_filename = '/tmp/' + config.S3_KEY
        s3_client.download_file(
            config.S3_BUCKET,
            config.ENVIRONMENT + '/' + config.S3_KEY,
            tmp_filename,
        )
        logger.info('Downloaded "{}/{}" from S3'.format(s3_bucket, s3_path))

        # Get the column headers (first line of first file)
        header_filename = '{base_fn}-header'.format(base_fn=tmp_filename)
        os.system(
            'head -n 1 {tmp_filename} > {header_filename}'.format(
                tmp_filename=tmp_filename,
                header_filename=header_filename
            )
        )

        # Strip the header from the file
        os.system('tail -n +2 {tmp_filename} > {tmp_filename}-body'.format(tmp_filename=tmp_filename))

        # Divide file into chunks
        body_filename = tmp_filename + '-body'
        subprocess.call([
            'split',
            '-l', str(config.CHUNK_SIZE),
            '-d', body_filename,
            tmp_filename + '-',
        ])

        # Prepend the column headers to each file and copy to the EFS directory
        chunks = 0
        all_output_files = []
        for file in glob.glob(tmp_filename + '-[0-9]*'):
            file_name = os.path.basename(file)

            with open(config.FP_OUTPUT + '/' + file_name, 'w') as efs_output:
                subprocess.call(['cat', header_filename, file], stdout=efs_output)

            # Clean up /tmp directory
            os.remove(file)

            logger.info('Processed "{}" chunk'.format(file))
            chunks += 1
            all_output_files.append(file_name)

        os.remove(tmp_filename)
        os.remove(body_filename)
        os.remove(header_filename)

        logger.info('Finished processing "{}/{}" into {} chunks'.format(s3_bucket, s3_path, chunks))
        return all_output_files

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise


if __name__ == '__main__':
    input_file_name = sys.argv[1]
    script_handler('biometrix-sessioncontainer2', input_file_name)
