
import psycopg2
#import requests
import boto3
import logging
import logging.handlers
#import time
import os

from wsgiref.simple_server import make_server

import columnNames as cols


# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Handler 
LOG_FILE = '/opt/python/log/sample-app.log'
handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=1048576, backupCount=5)
handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add Formatter to Handler
handler.setFormatter(formatter)

# add Handler to Logger
logger.addHandler(handler)


quer_create = "CREATE TEMP TABLE temp_mov AS SELECT * FROM movement LIMIT 0"

quer_delete = "delete from movement where session_event_id = (%s)"

# Query to copy data over from temp table to movement table
quer_update = """UPDATE movement
    set mech_stress = temp_mov.mech_stress,
        control = temp_mov.control,
        hip_control = temp_mov.hip_control,
        ankle_control = temp_mov.ankle_control,
        control_lf = temp_mov.control_lf,
        control_rf = temp_mov.control_rf,
        consistency = temp_mov.consistency,
        hip_consistency = temp_mov.hip_consistency,
        ankle_consistency = temp_mov.ankle_consistency,
        consistency_lf = temp_mov.consistency_lf,
        consistency_rf = temp_mov.consistency_rf,
        symmetry = temp_mov.symmetry,
        hip_symmetry = temp_mov.hip_symmetry,
        ankle_symmetry = temp_mov.ankle_symmetry,
        destr_multiplier = temp_mov.destr_multiplier,
        dest_mech_stress = temp_mov.dest_mech_stress,
        const_mech_stress = temp_mov.const_mech_stress,
        session_duration = temp_mov.session_duration,
        session_mech_stress_elapsed = temp_mov.session_mech_stress_elapsed
    from temp_mov
    where movement.session_event_id = temp_mov.session_event_id and
          movement.obs_index = temp_mov.obs_index"""

quer_update_session_events = """update session_events
                                set session_success=True,
                                updated_at = now()
                                where sesnor_data_filename = (%s)"""
# finally drop the temp table
quer_drop = "DROP TABLE temp_mov"


def application(environ, start_response):
    path    = environ['PATH_INFO']
    method  = environ['REQUEST_METHOD']

    # Read environment variables
    db_name = os.environ['db_name']
    db_host = os.environ['db_host']
    db_username = os.environ['db_username']
    db_password = os.environ['db_password']
    sub_folder = os.environ['sub_folder']+'/'

    column_session2_out = cols.column_session2_out
    column_scoring_out = cols.column_scoring_out

    s3 = boto3.resource('s3')
    if method == 'POST':
        conn = psycopg2.connect(dbname=db_name, user=db_username, host=db_host,
                            password=db_password)
        cur = conn.cursor()
        file_name = path.split('/')[2]
        if path.split('/')[1] == 'preScoring':
            cont_read = 'biometrix-scoringcontainer'
            # Read file from s3
            obj = s3.Bucket(cont_read).Object(sub_folder+file_name)
            fileobj = obj.get()
            content = fileobj['Body']
            columns = ','.join(column_session2_out)
            # Copy content of file to movement table
            cur.copy_expert("COPY movement (%s) FROM STDIN WITH CSV HEADER DELIMITER AS ',' NULL as ''" % (columns,), content)
            conn.commit()
            conn.close()
            response = 'Success'
        elif path.split('/')[1] == 'postScoring':
            cont_read = 'biometrix-sessionprocessedcontainer'
            cont_write = 'biometrix-userhistcreate'
            obj = s3.Bucket(cont_read).Object(sub_folder+file_name)
            fileobj = obj.get()
            logger.info('Got Fileobj')
            content = fileobj['Body']
            cur.execute(quer_create)
            logger.info('temp table created')
            column_scoring_out_1 = ','.join(column_scoring_out)
            #logger.info(column_scoring_out_1)
            cur.copy_expert("COPY temp_mov (%s) FROM STDIN WITH CSV HEADER DELIMITER AS ',' NULL as ''" % (column_scoring_out_1,), content)
            logger.info('copied to temp_table')
            cur.execute(quer_update)
            conn.commit()
            logger.info('updated movement table')
            cur.execute(quer_drop)
            conn.commit()
            logger.info('dropped temp table')
            cur.execute(quer_update_session_events, (file_name,))
            conn.commit()
            conn.close()
            logger.info('Updated data for file:'+ file_name)
            #SUB_FOLDER = 'dev/'
            s3.Bucket(cont_write).put_object(Key=sub_folder+'mov_'+file_name, Body='nothing')
            logger.info('Success!')
            response = 'Success'
        else:
            response = 'URL not properly formatted'

    else:
        response = 'Fail'
    status = '200 OK'
    headers = [('Content-type', 'text/html')]
    # string = requests.META['QUERY_STRING']
    start_response(status, headers)
    return response


if __name__ == '__main__':
    httpd = make_server('', 8000, application)
    print("Serving on port 8000...")
    httpd.serve_forever()
