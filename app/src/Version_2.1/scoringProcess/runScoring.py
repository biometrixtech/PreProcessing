# -*- coding: utf-8 -*-
"""
Created on Tues Nov 29 13:45:56 2016

@author: dipesh

Execution script to run scoring. Takes movement quality features and performance
variables and returns scores for control, symmetry and consistency of movement.

Input data:
MQF and PV: tbd
historical MQF and PV: from s3 container (to be changed later)

Output data stored in TrainingEvents or BlockEvents table.

"""
#import sys
import gc
import cStringIO
import logging
import os
#import numpy as np
import pandas as pd
import psycopg2
import psycopg2.extras
import boto3
import math
#from itertools import islice, count
from base64 import b64decode
#import matplotlib.pyplot as plt
#from matplotlib.backends.backend_pdf import PdfPages
#import requests

from controlScore import control_score
from scoring import score
import scoringProcessQueries as queries
import columnNames as cols

logger = logging.getLogger()
psycopg2.extras.register_uuid()


def run_scoring(sensor_data, file_name, aws=True):
    """Creates object attributes according to block analysis process.

    Args:
        sensor_data: Processed data that's output of sessionProcess.
        file_name: sensor_data_filename associated with the data in DB
        aws: Boolean indicator for aws/local run

    Returns:
        result: string signifying success or failure.
        Note: In case of completion for local run, returns movement table.
    """
    global AWS
    global COLUMNS_RESEARCH
    global COLUMN_SCORING_OUT
    global VARS_FOR_SCORING
    global KMS
    global SUB_FOLDER
    AWS = aws
    VARS_FOR_SCORING = cols.vars_for_scoring
    COLUMN_SCORING_OUT = cols.column_scoring_out
    COLUMNS_RESEARCH = cols.columns_research
    KMS = boto3.client('kms')
    # Read subfolder and api url from environ var
    SUB_FOLDER = os.environ['sub_folder']+'/'
#    url = os.environ['db_write_url']


    # Define containers to read and write
    cont_write = 'biometrix-sessionprocessedcontainer'
    cont_read = 'biometrix-scoringhist'

    # Connect to the database
    conn, cur, s3 = _connect_db_s3()

#   Read team_id to separate research data from user data
    try:
        cur.execute(queries.quer_read_team_id, (file_name,))
        team_id = str(cur.fetchone()[0])
        _logger(team_id)
    except:
        _logger('No associated team_id found for the given file')
        return 'Fail!'

    # Read data. Only readin relevant columns in
    if team_id == '65fb2565-3a13-400c-92ed-17d7f7d57804':
#    if team_id == '2214b4f1-5fb1-444f-aa65-af402e2db013':
        data = pd.read_csv(sensor_data['Body'], usecols=COLUMNS_RESEARCH)
        f = cStringIO.StringIO()
        data.to_csv(f, index=False)
        key = data.user_id[0]+'_'+str(pd.to_datetime(data.time_stamp[0]).date())
        cont_research = 'biometrix-research-data'
        f.seek(0)
        s3.Bucket(cont_research).put_object(Key=SUB_FOLDER+key, Body=f)
        return 'Success!'

    else:
        data = pd.read_csv(sensor_data['Body'], usecols=VARS_FOR_SCORING)
        _logger('Data Read')
        del sensor_data
    
#        # Make API call to write data from scoring container to DB
#        _logger('Starting DB write request')
#    #    url = "http://writing-env.us-west-2.elasticbeanstalk.com/"
#        r = requests.post(url+file_name)
#        _logger('Finished DB write request')
#        _logger(r.status_code)


        session_event_id = data.session_event_id[0]
        user_id = data.user_id[0]
        # CONTROL SCORE
        data['control'], data['hip_control'], data['ankle_control'], data['control_lf'],\
                data['control_rf'] = control_score(data.LeX, data.ReX, data.HeX,
                                                data.ms_elapsed, data.phase_lf,
                                                data.phase_rf)

        _logger('DONE WITH CONTROL SCORES!')
        # SCORING
        # Symmetry, Consistency, Destructive/Constructive Multiplier and
        # Duration
        # At this point we need to load the historical data for the subject

        # read historical data
        try:
            objs = list(s3.Bucket(cont_read).objects.filter(Prefix=SUB_FOLDER+user_id))
            if len(objs) == 1:
                obj = s3.Bucket(cont_read).Object(SUB_FOLDER+user_id)
                fileobj = obj.get()
                body = fileobj["Body"]
                user_hist = pd.read_csv(body)
                del body
                user_hist.columns = cols.columns_hist
            elif len(data.LeX) > 50000:
                user_hist = data
            else:
                _logger("There's no historical data and current data isn't long enough!")
                # Can't complete scoring, delete data from movement table and exit
#                cur.execute(queries.quer_delete, (session_event_id, ))
#                conn.commit()
                conn.close()
                return "Fail!"
        except Exception as error:
            if AWS:
                _logger("Cannot read historical user data from s3!", info=False)
                raise error
            else:
                try:
                    user_hist = pd.read_csv("user_hist.csv")
                except:
                    raise IOError("User history not found in s3/local directory")

        _logger("user history captured")
        gc.collect()

        mech_stress_scale = 1000000
        data['consistency'], data['hip_consistency'], \
            data['ankle_consistency'], data['consistency_lf'], \
            data['consistency_rf'], data['symmetry'], \
            data['hip_symmetry'], data['ankle_symmetry'], \
            data['destr_multiplier'], data['dest_mech_stress'], \
            data['const_mech_stress'], data['block_duration'], \
            data['session_duration'], data['block_mech_stress_elapsed'], \
            data['session_mech_stress_elapsed'] = score(data, user_hist,
                                                     mech_stress_scale)
        del user_hist
        _logger("DONE WITH SCORING!")
        gc.collect()

        data.mech_stress = data.mech_stress/mech_stress_scale
    #    _logger(data.columns)
        # Round the data to 6th decimal point
        data = data.round(6)


        # write to s3 in parts
        file_name = "movement_"+file_name
        try:
            s3 = boto3.client('s3')
            mp = s3.create_multipart_upload(Bucket=cont_write,
                                            Key=SUB_FOLDER+file_name)

            # Use only a set of rows each time to write to fileobj
            batch_size = len(data)  # number of rows durin each batch upload
            size = len(data)
            batches = int(math.ceil(size/float(batch_size)))

        #    _logger('number of parts to be uploaded' + str(rows_set_count))
            _logger('Number of parts to be uploaded: '+ str(batches))
            # Initialize counter to the count number of parts uploaded in the loop below
            counter = 0
            # Send the file parts, using FileChunkIO to create a file-like object
    #        batches = 1
            for i in range(batches):
                counter = counter + 1
                subset_size = min([len(data), batch_size])

                _logger('Passing Batch:'+str(counter))
                _logger('length of subset: '+str(subset_size))

                if counter == 1:
                    # Write first part to s3 with the header
                    fileobj = cStringIO.StringIO()
                    data.to_csv(fileobj, index=False, na_rep='',
                                         columns=COLUMN_SCORING_OUT,
                                         nrows=subset_size)
        #            del movement_data_subset
                    fileobj.seek(0)
                    part = s3.upload_part(Bucket=cont_write,
                                          Key=SUB_FOLDER+file_name,
                                          PartNumber=counter,
                                          UploadId=mp['UploadId'], Body=fileobj)
                    Parts = [{'PartNumber':counter, 'ETag': part['ETag']}]
                    del fileobj

                else:
                    # Other parts are written without header
                    fileobj = cStringIO.StringIO()
                    data.to_csv(fileobj, index=False, header=False, na_rep='',
                                         columns=COLUMN_SCORING_OUT,
                                         nrows=subset_size)
                    fileobj.seek(0)
                    part = s3.upload_part(Bucket=cont_write,
                                          Key=SUB_FOLDER+file_name,
                                          PartNumber=counter,
                                          UploadId=mp['UploadId'], Body=fileobj)
                    Parts.append({'PartNumber':counter, 'ETag': part['ETag']})
                    del fileobj

            part_info = {'Parts': Parts}
            s3.complete_multipart_upload(Bucket=cont_write,
                                         Key=SUB_FOLDER+file_name,
                                         UploadId=mp['UploadId'],
                                         MultipartUpload=part_info)

        except Exception as error:
            conn.close()
            raise error
        else:
            cur.execute(queries.quer_update_session_events, (session_event_id,))
            conn.commit()
            conn.close()

        _logger("DONE WRITING TO S3")

        return "Success!"


def _connect_db_s3():
    """Start a connection to the database and to s3 resource.
    """
    # Read encrypted environment variables for db connection
    db_name = os.environ['db_name']
    db_host = os.environ['db_host']
    db_username = os.environ['db_username']
    db_password = os.environ['db_password']

    # Decrypt the variables
#    db_name = KMS.decrypt(CiphertextBlob=b64decode(db_name))['Plaintext']
    db_host = KMS.decrypt(CiphertextBlob=b64decode(db_host))['Plaintext']
    db_username = KMS.decrypt(CiphertextBlob=b64decode(db_username))['Plaintext']
    db_password = KMS.decrypt(CiphertextBlob=b64decode(db_password))['Plaintext']

    try:
        conn = psycopg2.connect(dbname=db_name, user=db_username, host=db_host,
                                password=db_password)
        cur = conn.cursor()
        # Connect to AWS s3 container
        s3 = boto3.resource('s3')
    except psycopg2.Error as error:
        logger.warning("Cannot connect to DB")
        raise error
    except boto3.exceptions as error:
        logger.warning("Cannot connect to s3!")
        raise error
    else:
        return conn, cur, s3


def _logger(message, info=True):
    if AWS:
        if info:
            logger.info(message)
        else:
            logger.warning(message)
    else:
        print message


if __name__ == "__main__":
    data = 'C:\\Users\\dipesh\\Desktop\\biometrix\\aws\\7803f828-bd32-4e97-860c-34a995f08a9e_3'
    file_name = '7803f828-bd32-4e97-860c-34a995f08a9e'
    out_data = run_scoring(data, file_name, aws=False)
#    sdata = pd.read_csv(data)
    pass

