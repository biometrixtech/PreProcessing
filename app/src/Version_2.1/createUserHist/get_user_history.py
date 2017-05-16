from __future__ import print_function


import urllib
import boto3
import logging
import cStringIO
import psycopg2
import os
from base64 import b64decode
import pandas as pd

columns_hist = ['mech_stress', 'total_accel',
                'contra_hip_drop_lf', 'contra_hip_drop_rf',
                'ankle_rot_lf', 'ankle_rot_rf',
                'land_pattern_lf', 'land_pattern_rf', 'land_time',
                'foot_position_lf', 'foot_position_rf']

get_user_id = 'select user_id from session_events where sensor_data_filename = (%s)'
get_filenames = 'select * from fn_get_sensor_data_filename_hist((%s))'
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.info('Starting User History Creation')
#    
def lambda_handler(event, context):
    KMS = boto3.client('kms')
    # Read encrypted environment variables for db connection
    db_name = os.environ['db_name']
    db_host = os.environ['db_host']
    db_username = os.environ['db_username']
    db_password = os.environ['db_password']
    sub_folder = os.environ['sub_folder']+'/'


    # Decrypt the variables
#    db_name = KMS.decrypt(CiphertextBlob=b64decode(db_name))['Plaintext']
    db_host = KMS.decrypt(CiphertextBlob=b64decode(db_host))['Plaintext']
    db_username = KMS.decrypt(CiphertextBlob=b64decode(db_username))['Plaintext']
    db_password = KMS.decrypt(CiphertextBlob=b64decode(db_password))['Plaintext']
#    sub_folder = KMS.decrypt(CiphertextBlob=b64decode(sub_folder))['Plaintext']+'/'

    cont_read = 'biometrix-scoringcontainer'
    cont_write = 'biometrix-scoringhist'

    conn = psycopg2.connect(dbname=db_name, user=db_username, host=db_host,
                            password=db_password)
    cur = conn.cursor()
    S3 = boto3.resource('s3')

#    logger.info('Received event: ' + json.dumps(event, indent=2))
    
    try:
        key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key']).encode('utf8')
        try:
            file_name = key.split('_')[1]
        except Exception as e:
            logger.info('Incorrect filename formatting!')
        try:
            cur.execute(get_user_id, (file_name,))
            user_id = cur.fetchall()[0]
            logger.info(user_id)
            logger.info('user_id retrieved')
            cur.execute(get_filenames, (user_id,))
            files = cur.fetchall()
            conn.close()
        except Exception as e:
            logger.info('user_id associated with the file not found!')
        else:
            if len(files) != 0:
                hist_files = tuple(zip(*files)[0])
                logger.info('Relevant sensor_data_filenames retrieved')
                logger.info(hist_files)
                hist_out = pd.DataFrame()
                for file_name in hist_files:
                    obj = S3.Bucket(cont_read).Object('prod/'+file_name).get()
                    data_part = pd.read_csv(obj['Body'], usecols=columns_hist)
                    hist_out = pd.concat([hist_out, data_part], axis=0,
                                         ignore_index=True)
                f = cStringIO.StringIO()
                hist_out.to_csv(f, index=False, na_rep='')
                user_id = str(user_id[0])
                logger.info(user_id)
                f.seek(0)
                S3.Bucket(cont_write).put_object(Key=sub_folder+user_id, Body=f)
                logger.info('Data written to s3')
            else:
                logger.info('No files associated with the given user found!')

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise e

if __name__=='__main__':
    hist = lambda_handler('a', 'b')    
