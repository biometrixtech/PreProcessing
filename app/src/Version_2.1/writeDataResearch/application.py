
import psycopg2
import cStringIO
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


create_temp_table = """CREATE TEMP TABLE research_data AS 
                       SELECT team_id, user_id, session_event_id, time_stamp, 
                      mech_stress, total_accel,
                      LaX, LaY, LaZ, LeX, LeY, LeZ, LqW, LqX, LqY, LqZ,
                      HaX, HaY, HaZ, HeX, HeY, HeZ, HqW, HqX, HqY, HqZ,
                      RaX, RaY, RaZ, ReX, ReY, ReZ, RqW, RqX, RqY, RqZ
                     FROM movement where session_event_id = %s"""
get_user_id = 'select id from users where team_id = (%s)'

get_session_event_id = """select id from session_events where user_id = (%s) 
                        and created_at::date > current_date - interval '12 day'
                        and session_success = True"""


def application(environ, start_response):
    path    = environ['PATH_INFO']
    method  = environ['REQUEST_METHOD']

    # Read environment variables
    db_name = os.environ['db_name']
    db_host = os.environ['db_host']
    db_username = os.environ['db_username']
    db_password = os.environ['db_password']
    sub_folder = os.environ['sub_folder']+'/'

    column_research = ','.join(cols.column_research)

    S3 = boto3.resource('s3')
    if method == 'POST':
        conn = psycopg2.connect(dbname=db_name, user=db_username, host=db_host,
                            password=db_password)
        cur = conn.cursor()
        team_id = path.split('/')[1]
        cur.execute(get_user_id, (team_id,))
        user_ids = cur.fetchall()
        for user_id in user_ids:
            response = user_id[0]
            cur.execute(get_session_event_id, user_id)
            session_event_ids = cur.fetchall()
            for session_event_id in session_event_ids:
                if len(session_event_id) != 0:
                    cur.execute(create_temp_table, session_event_id)
                    f = cStringIO.StringIO()
                    cur.copy_expert("COPY research_data (%s) to STDOUT WITH CSV HEADER DELIMITER AS ',' NULL as ''" % (column_research,), f)
                    logger.info('Data copied to file')
                    cur.execute("drop table research_data")
                    conn.commit()
                    user_id = str(session_event_id[0])
                    cont_write = 'biometrix-research-data'
                    f.seek(0)
                    S3.Bucket(cont_write).put_object(Key=sub_folder+user_id, Body=f)

        conn.close()

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
