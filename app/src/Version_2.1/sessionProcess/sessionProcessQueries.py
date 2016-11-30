# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 11:33:52 2016

@author: Gautam
"""

#quer_read_session_ids = """select id, session_id from session_events
#                         where sensor_data_filename = (%s)"""

quer_read_ids = """select * from fn_get_all_ids_from_sensor_data_filename((%s))"""

quer_read_offsets = """select hip_n_transform, hip_bf_transform,
    lf_n_transform, lf_bf_transform,
    rf_n_transform, lf_bf_transform from
    session_anatomical_calibration_events where
    id = (select session_anatomical_calibration_event_id 
    from session_events where id = (%s));"""

#quer_read_exercise_ids = """select exercise_id from blocks_exercises
#                            where block_id = (%s)"""
#
#quer_read_model = """select exercise_id_combinations, model_file,
#                label_encoding_model_file from exercise_training_models
#                where block_id = (%s)"""