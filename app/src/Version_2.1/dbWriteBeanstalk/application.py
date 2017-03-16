
import psycopg2
import requests
import boto3
import logging
import logging.handlers
import time
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

    s3 = boto3.resource('s3')
    if method == 'POST':
        conn = psycopg2.connect(dbname=db_name, user=db_username, host=db_host,
                            password=db_password)
        cur = conn.cursor()
        file_name = path.split('/')[1]
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
