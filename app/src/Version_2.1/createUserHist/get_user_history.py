from __future__ import print_function

import json
import urllib
import boto3
import logging
import cStringIO
import psycopg2
import os
from base64 import b64decode
#import uuid
##import zipfile as zf
#
##import runAnalytics as ra
#import input_data_in_batches as idb
create_temp_table = """CREATE TEMP TABLE hist AS SELECT mech_stress, total_accel,
                     contra_hip_drop_lf, contra_hip_drop_rf,
                     ankle_rot_lf, ankle_rot_rf,
                     land_pattern_lf, land_pattern_rf, land_time,
                     foot_position_lf, foot_position_rf
                     FROM movement where session_event_id in %s"""
get_user_id = 'select user_id from session_events where sensor_data_filename = (%s)'
get_session_events = 'select * from fn_get_session_event_id_hist((%s))'
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.info('Loading sessionProcess')
    
def lambda_handler(event, context):
    KMS = boto3.client('kms')
    # Read encrypted environment variables for db connection
    db_name = os.environ['db_name']
    db_host = os.environ['db_host']
    db_username = os.environ['db_username']
    db_password = os.environ['db_password']
    cont_write = os.environ['cont_write']

    # Decrypt the variables
    db_name = KMS.decrypt(CiphertextBlob=b64decode(db_name))['Plaintext']
    db_host = KMS.decrypt(CiphertextBlob=b64decode(db_host))['Plaintext']
    db_username = KMS.decrypt(CiphertextBlob=b64decode(db_username))['Plaintext']
    db_password = KMS.decrypt(CiphertextBlob=b64decode(db_password))['Plaintext']
    cont_write = KMS.decrypt(CiphertextBlob=b64decode(cont_write))['Plaintext']

    conn = psycopg2.connect(dbname=db_name, user=db_username, host=db_host,
                            password=db_password)
    cur = conn.cursor()
    S3 = boto3.resource('s3')

    logger.info('Received event: ' + json.dumps(event, indent=2))
    
    try:
        key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key']).encode('utf8')
        file_name = key.split('_')[1] 
        cur.execute(get_user_id, (file_name,))
        user_id = cur.fetchall()[0]
        logger.info('user_id retrieved')
        cur.execute(get_session_events, (user_id,))
        session_event_ids = cur.fetchall()
        session_ids = tuple(zip(*session_event_ids)[0])
        logger.info('Relevant session_event_ids retrieved')
        logger.info(session_ids)
        cur.execute(create_temp_table, (session_ids,))
        logger.info('Temp table created')
        f = cStringIO.StringIO()
        cur.copy_to(f, 'hist', sep=',', null = '')
        logger.info('Data copied to file')
        cur.execute("drop table hist")
        conn.commit()
        conn.close()
        user_id = str(user_id[0])
        logger.info(user_id)
        f.seek(0)
        S3.Bucket(cont_write).put_object(Key=user_id, Body=f)
        logger.info('Data written to s3')        
        
    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise e
