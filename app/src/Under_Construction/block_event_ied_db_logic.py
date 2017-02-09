# -*- coding: utf-8 -*-
"""
Created on Fri Nov 04 13:30:18 2016

@author: court
"""

import numpy as np
import pickle
#import re
import sys
import boto3
import cStringIO
import psycopg2

import prePreProcessing as ppp
import dataObject as do
import phaseDetection as phase
import IAD
import IED
import coordinateFrameTransformation as coord
from mechStressTraining import prepareData
import movementAttrib as matrib
import balanceCME as cmed
import quatConvs as qc
import impactCME as impact
from controlScore import controlScore
from scoring import score
import createTables as ct


# connect to AWS s3 container
s3 = boto3.resource('s3')

# define container to read from
cont_read = 'biometrix-blockcontainer'

# define container to write to
cont_write = 'biometrix-blockprocessedcontainer'
#out_file = "processed_"+file_name

# define container to read models from
cont_read_models = 'biometrix-globalmodels'

data_obj = s3.Bucket(cont_read_models).Object('iad_finalized_model.sav')
data_fileobj = data_obj.get()
data_body = data_fileobj["Body"].read()

# connect to the database
try:
    conn = psycopg2.connect("""dbname='biometrix' user='paul' 
    host='ec2-52-36-42-125.us-west-2.compute.amazonaws.com' 
    password='063084cb3b65802dbe01030756e1edf1f2d985ba'""")
except:
    result = 'Fail! Unable to connect to database'
    sys.exit()

cur = conn.cursor()

#Query to read user_id and exercise_idlinked to the given data_filename
quer_block_event_id = """select id from block_events where 
            sensor_data_filename = (%s);"""

quer_read_ids = """select * from 
            fn_get_all_ids_from_block_event_id(%s);"""
            

quer_read_offsets = """select hip_n_transform, hip_bf_transform,
            lf_n_transform, lf_bf_transform,
            rf_n_transform, lf_bf_transform from
            session_anatomical_calibration_events where
            block_event_id = (select id 
            from block_events where sensor_data_filename = (%s));"""
            
quer_find_ex_ids = """select exercise_id from exercise_logs where 
            block_event_id = (%s);"""
            
quer_check_for_id_combo = """select id from exercise_training_models where
            exercise_id_combinations = (%s);"""
            
quer_pull_model_for_existing_combo = """select model_file from 
            exercise_training_models where id = (%s);"""
            
quer_find_training_data = """select id from session_events where 
            training_session_log_id = (select training_session_log_id from 
            block_events where sensor_data_filename = (%s));"""
            
quer_grab_coach_data = """select sensor_data_filename from session_events 
            where id = (%s);"""
            

quer_success = """update block_events set
            complete = (%s),
            where sensor_data_filename = (%s);"""

# read the block_event_id
cur.execute(quer_block_event_id, (file_name,))
block_event_id = cur.fetchall()[0]
block_event_id = block_event_id[0]

# read the rest of the IDs
cur.execute(quer_read_ids, (block_event_id,))
ids_read = cur.fetchall()[0]     

# read transformation offset values
cur.execute(quer_read_offsets, (file_name,))
offsets_read = cur.fetchall()[0]
hip_n_transform = np.array(offsets_read[0]).reshape(-1,1)
hip_bf_transform = np.array(offsets_read[1]).reshape(-1,1)
lf_n_transform = np.array(offsets_read[2]).reshape(-1,1)
lf_bf_transform = np.array(offsets_read[3]).reshape(-1,1)
rf_n_transform = np.array(offsets_read[4]).reshape(-1,1)
rf_bf_transform = np.array(offsets_read[5]).reshape(-1,1)

# read the exercise_ids from logged exercises
cur.execute(quer_find_ex_ids, (file_name,))
read_exerc_ids = cur.fetchall()[0]
exerc_ids_array = np.array(read_exerc_ids).reshape(-1,1)

# check find where system has been trained for specific id combo
cur.execute(quer_check_for_id_combo, (exerc_ids_array,))
read_relevant_models = cur.fetchall()[0]
relevant_models = np.array(read_relevant_models).reshape(-1,1)

# if relevant models exist, save them as read_models
if len(relevant_models[0].shape) != 0:
    cur.execute(quer_pull_model_for_existing_combo, (relevant_models,))
    read_models = cur.fetchall()[0]
    
# if relevant models don't exist, create them
else:
    
    # find appropriate training data from the coach
    cur.execute(quer_find_training_data, (file_name,))
    read_training_data = cur.fetchall()[0]
    cur.execute(quer_grab_coach_data, (read_training_data,))
    read_coach_data = cur.fetchall()[0]
    
    
    # concatenate all of the coach's data files
    
    read_models = 1
    
# predict exercise ID
ied_features = IED.preprocess_ied(self.data, training = False)
ied_labels = loaded_model.predict(ied_features)
ied_exercise_id = IED.mapping_labels_on_data(ied_labels, len(
                                         self.data.LaX)).astype(int)
self.data.exercise_id = loaded_label_model.inverse_transform(
                                         ied_exercise_id)