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
    header_filename = os.path.join('/tmp', input_filename + '_header')
    os.system(
        'head -n 1 {tmp_filename} > {header_filename}'.format(
            tmp_filename=input_filename,
            header_filename=header_filename
        )
    )

    # Strip the header from the file
    body_filename = os.path.join('/tmp', input_filename + '_body')
    os.system(
        'tail -n +2 {input_filename} > {body_filename}'.format(
            input_filename=input_filename,
            body_filename=body_filename
        )
    )

    # Divide file into chunks
    tmp_chunk_dir = os.path.join('/tmp', input_filename)
    if isinstance(chunk_size, list):
        if len(chunk_size) == 0:
            # Special case the scenario where we have no boundaries, and hence only expect one output file
            subprocess.call(['cp', body_filename, tmp_chunk_dir + '_00'])
        else:
            subprocess.call(['csplit', '-f', tmp_chunk_dir, '-b', '_%02d', body_filename] + [str(l) for l in chunk_size])
    else:
        subprocess.call([
            'split',
            '-l', str(chunk_size),
            '-d',
            body_filename,
            tmp_chunk_dir + '_',
        ])

    # Prepend the column headers to each file and copy to the output directory
    file_names = []
    for file in glob.glob(tmp_chunk_dir + '_[0-9]*'):
        file_name = os.path.basename(file)
        output_filepath = os.path.join(output_dir, file_name)
        os.system(
            'cat {header_filename} {file} > {output_filepath}'.format(
                header_filename=header_filename,
                file=file,
                output_filepath=output_filepath
            )
        )

        # Clean up /tmp directory
        os.remove(file)

        logger.info('Processed "{}" chunk'.format(file))
        file_names.append(output_filepath)

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
            output_filename + '_',
        ])

    # Find them again!
    file_names = []
    for file in glob.glob(output_filename + '_[0-9]*'):
        print("Found file {}".format(file))
        file_name = os.path.basename(file)
        file_names.append(file_name)
    print(file_names)
    return file_names