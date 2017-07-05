import os
import subprocess
import glob
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def chunk_file(tmp_filename, output_dir, chunk_size):
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
        '-l', str(chunk_size),
        '-d', body_filename,
        tmp_filename + '-',
    ])

    # Prepend the column headers to each file and copy to the EFS directory
    file_names = []
    for file in glob.glob(tmp_filename + '-[0-9]*'):
        file_name = os.path.basename(file)

        with open(output_dir + '/' + file_name, 'w') as efs_output:
            subprocess.call(['cat', header_filename, file], stdout=efs_output)

        # Clean up /tmp directory
        os.remove(file)

        logger.info('Processed "{}" chunk'.format(file))
        file_names.append(file_name)

    os.remove(body_filename)
    os.remove(header_filename)

    logger.info('Finished processing "{}" into {} chunks'.format(tmp_filename, len(file_names)))
    return file_names
