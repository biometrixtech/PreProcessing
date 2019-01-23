import os
import subprocess
import glob
import logging

_logger = logging.getLogger(__name__)


def shell(cmd):
    if isinstance(cmd, str):
        _logger.debug(cmd)
        os.system(cmd)
    elif isinstance(cmd, list):
        _logger.debug(' '.join(cmd))
        subprocess.call(cmd)


def chunk_by_line(input_filename, output_dir, chunk_size):
    # Get the column headers (first line of first file)
    header_filename = '/tmp/chunk_header'
    shell(
        'head -n 1 {tmp_filename} > {header_filename}'.format(
            tmp_filename=input_filename,
            header_filename=header_filename
        )
    )
    _logger.debug('Filesize of {} is {}'.format(header_filename, os.path.getsize(header_filename)))

    # Strip the header from the file
    body_filename = '/tmp/chunk_body'
    shell(
        'tail -n +2 {input_filename} > {body_filename}'.format(
            input_filename=input_filename,
            body_filename=body_filename
        )
    )
    _logger.debug('Filesize of {} is {}'.format(body_filename, os.path.getsize(body_filename)))

    # Divide file into chunks
    tmp_chunk_dir = '/tmp/chunk'
    os.mkdir(tmp_chunk_dir)
    if isinstance(chunk_size, list):
        if len(chunk_size) == 0:
            # Special case the scenario where we have no boundaries, and hence only expect one output file
            shell(['cp', body_filename, tmp_chunk_dir + '/00'])
        else:
            shell(['csplit', '-f', tmp_chunk_dir + '/', '-b', '_%04d', body_filename] + [str(l) for l in chunk_size])
    else:
        shell([
            'split',
            '-l', str(chunk_size),
            '-a', '4',
            '-d',
            body_filename,
            tmp_chunk_dir + '/',
        ])

    # Prepend the column headers to each file and copy to the output directory
    file_names = []
    _logger.debug(tmp_chunk_dir)
    for file in glob.glob(tmp_chunk_dir + '/[0-9]*'):
        file_name = os.path.basename(file)
        output_filepath = os.path.join(output_dir, file_name)
        shell(
            'cat {header_filename} {file} > {output_filepath}'.format(
                header_filename=header_filename,
                file=file,
                output_filepath=output_filepath
            )
        )

        # Clean up /tmp directory
        os.remove(file)

        _logger.info('Processed "{}" chunk'.format(file))
        file_names.append(output_filepath)

    os.remove(body_filename)
    os.remove(header_filename)
    os.rmdir(tmp_chunk_dir)

    _logger.info('Finished processing "{}" into {} chunks'.format(input_filename, len(file_names)))
    return file_names


def chunk_by_byte(input_filename, output_dir, boundaries):
    # Divide file into chunks
    filename = os.path.basename(input_filename)
    output_filename = output_dir + '/' + filename
    _logger.debug('output_filename: {}'.format(output_filename))
    if isinstance(boundaries, list):
        raise Exception("Not supported")
    else:
        shell([
            'split',
            '-b', str(boundaries),
            '-d',
            input_filename,
            output_filename + '_',
        ])

    # Find them again!
    file_names = []
    for file in glob.glob(output_filename + '_[0-9]*'):
        _logger.info("Found file {}".format(file))
        file_name = os.path.basename(file)
        file_names.append(file_name)
    _logger.debug(file_names)
    return sorted(file_names)
