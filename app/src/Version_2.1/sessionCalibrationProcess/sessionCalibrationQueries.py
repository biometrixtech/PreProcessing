# -*- coding: utf-8 -*-
"""
Created on Thu Feb 23 10:51:18 2017

@author: Gautam
"""

# Read relevant information from base_anatomical_calibration_events
# based on provided sensor_data_filename and
# base_anatomical_calibration_event_id tied to the filename
quer_read = """select user_id,
                      expired,
                      user_success,
                      base_ac_success,
                      feet_processed_sensor_data_filename,
                      hip_pitch_transform,
                      hip_roll_transform,
                      lf_roll_transform,
                      rf_roll_transform
            from base_anatomical_calibration_events where
            id = (select base_anatomical_calibration_event_id from
                    session_anatomical_calibration_events where 
                    sensor_data_filename = (%s));"""

# Update anatomical_calibration_events in case the tests fail
quer_fail = """update session_anatomical_calibration_events set
            user_success = (%s),
            session_ac_success = (%s),
            failure_type = (%s),
            base_calibration = (%s),
            updated_at = now()
            where sensor_data_filename=(%s);"""

# For base calibration, update base_anatomical_calibration_events
quer_base_succ = """update  base_anatomical_calibration_events set
            base_ac_success = (%s),
            hip_pitch_transform = (%s),
            hip_roll_transform = (%s),
            lf_roll_transform = (%s),
            rf_roll_transform = (%s),
            expired = (%s),
            updated_at = now()
            where id  = (select base_anatomical_calibration_event_id from
                        session_anatomical_calibration_events where
                        sensor_data_filename = (%s));"""

# For both base and session calibration, update
# session_anatomical_calibration_events with relevant info
# for base calibration, session calibration follows base calibration
# for session calibration, it's independent and uses values read earlier
quer_session_succ = """update session_anatomical_calibration_events set
                user_success = (%s),
                session_ac_success = (%s),
                base_calibration = (%s),
                hip_n_transform = (%s),
                hip_bf_transform = (%s),
                lf_n_transform = (%s),
                lf_bf_transform = (%s),
                rf_n_transform = (%s),
                rf_bf_transform = (%s),
                updated_at = now(),
                processed_at = now(),
                failure_type = 0
                where sensor_data_filename  = (%s);"""

#    quer_rpush = "select fn_send_push_notification(%s, %s, %s)"
quer_check_status = """ select * 
            from fn_get_processing_status_from_sa_event_filename((%s))"""
