import os
import subprocess
import glob
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def chunk_by_line(input_filename, output_dir, chunk_size):
    # Get the column headers (first line of first file)
    header_filename = '{base_fn}-header'.format(base_fn=input_filename)
    os.system(
        'head -n 1 {tmp_filename} > {header_filename}'.format(
            tmp_filename=input_filename,
            header_filename=header_filename
        )
    )

    # Strip the header from the file
    body_filename = input_filename + '-body'
    os.system('tail -n +2 {tmp_filename} > {body_filename}'.format(tmp_filename=input_filename, body_filename=body_filename))

    # Divide file into chunks
    if isinstance(chunk_size, list):
        subprocess.call(['csplit', '-f', input_filename, '-b', '-%02d', body_filename] + [str(l) for l in chunk_size])
    else:
        subprocess.call([
            'split',
            '-l', str(chunk_size),
            '-d',
            body_filename,
            input_filename + '-',
        ])

    # Prepend the column headers to each file and copy to the EFS directory
    file_names = []
    for file in glob.glob(input_filename + '-[0-9]*'):
        file_name = os.path.basename(file)

        with open(output_dir + '/' + file_name, 'w') as efs_output:
            subprocess.call(['cat', header_filename, file], stdout=efs_output)

        # Clean up /tmp directory
        os.remove(file)

        logger.info('Processed "{}" chunk'.format(file))
        file_names.append(file_name)

    os.remove(body_filename)
    os.remove(header_filename)

    logger.info('Finished processing "{}" into {} chunks'.format(input_filename, len(file_names)))
    return file_names


def chunk_by_byte(input_filename, output_dir, boundaries):
    # Divide file into chunks
    filename = os.path.basename(input_filename)
    output_filename = output_dir + '/' + filename
    print('output_filename: {}'.format(output_filename))
    if isinstance(boundaries, list):
        raise Exception("Not supported")
    else:
        subprocess.call([
            'split',
            '-b', str(boundaries),
            '-d',
            input_filename,
            output_filename + '-',
        ])

    # Find them again!
    file_names = []
    for file in glob.glob(output_filename + '-[0-9]*'):
        print("Found file {}".format(file))
        file_name = os.path.basename(file)
        file_names.append(file_name)

    print(file_names)
    return file_names
