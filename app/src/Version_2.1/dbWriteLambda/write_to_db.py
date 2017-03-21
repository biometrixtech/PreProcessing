# -*- coding: utf-8 -*-
"""
Created on Mon Mar 13 17:15:53 2017

@author: Gautam
"""

from __future__ import print_function

import json
import urllib
import boto3
import logging
#import cStringIO
import psycopg2
import os
from base64 import b64decode

column_scoring_out = ['user_id', 'session_event_id', 'obs_index',
                      'mech_stress', 'const_mech_stress', 'dest_mech_stress',
                      'session_duration','session_mech_stress_elapsed',
                      'destr_multiplier',
                      'symmetry','hip_symmetry', 'ankle_symmetry',
                      'consistency', 'hip_consistency', 'ankle_consistency', 'consistency_lf', 'consistency_rf',
                      'control', 'hip_control', 'ankle_control', 'control_lf', 'control_rf']


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
                                where sensor_data_filename = (%s)"""
# finally drop the temp table
quer_drop = "DROP TABLE temp_mov"
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.info('Loading DBWriteProcess')


def lambda_handler(event, context):
    KMS = boto3.client('kms')
    # Read encrypted environment variables for db connection
    db_name = os.environ['db_name']
    db_host = os.environ['db_host']
    db_username = os.environ['db_username']
    db_password = os.environ['db_password']
    SUB_FOLDER = os.environ['sub_folder']+'/'
    cont_write = 'biometrix-userhistcreate'

    # Decrypt the variables
    db_host = KMS.decrypt(CiphertextBlob=b64decode(db_host))['Plaintext']
    db_username = KMS.decrypt(CiphertextBlob=b64decode(db_username))['Plaintext']
    db_password = KMS.decrypt(CiphertextBlob=b64decode(db_password))['Plaintext']

    conn = psycopg2.connect(dbname=db_name, user=db_username, host=db_host,
                            password=db_password)
    cur = conn.cursor()

    logger.info('Received event: ' + json.dumps(event, indent=2))
    
    try:
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key']).encode('utf8')
        s3r = boto3.resource('s3')
        logger.info('Obtained S3 Resource')
        obj = s3r.Bucket(bucket).Object(key)
        key = key.split('_')[1]
        logger.info('Obtained Key')        
        fileobj = obj.get()
        logger.info('Got Fileobj')
        content = fileobj['Body']
        cur.execute(quer_create)
        logger.info('temp table created')
        #content.seek(0)
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
        cur.execute(quer_update_session_events, (key,))
        conn.commit()
        conn.close()
        logger.info('Updated data for file:'+ key)
        #SUB_FOLDER = 'dev/'
        s3r.Bucket(cont_write).put_object(Key=SUB_FOLDER+'mov_'+key, Body='nothing')
        logger.info('Success!')
        
    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise e
