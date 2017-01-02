# -*- coding: utf-8 -*-
"""
Created on Fri Dec 30 15:50:58 2016

@author: Gautam
"""

import sys
import unittest
from pyramid import testing
import psycopg2
import boto3
import cStringIO
import pandas as pd

sys.path.insert(0, '..\\sessionProcess')
from runAnalytics import run_session
#import sessionProcessQueries as sessionqueries
sys.path.insert(0, '..\\scoringProcess')
from runScoring import run_scoring
#import scoringProcessQueries as scoringqueries


conn = psycopg2.connect("""dbname='biometrix' user='ubuntu'
host='ec2-35-162-107-177.us-west-2.compute.amazonaws.com' 
password='d8dad414c2bb4afd06f8e8d4ba832c19d58e123f'""")
cur = conn.cursor()
S3 = boto3.resource('s3')
cont_scoring = 'biometrix-scoringcontainer'
cont_sess = 'biometrix-sessionprocessedcontainer'

class TestSessionAndScoring(unittest.TestCase):
    """Tests for Session and Scoring processes
    -IO error for missing file
    -IndexError for file_name missing in DB
    -Return 'Success!' for test case
    -Written to correct fields in base_anatomical_calibration_events
    -Written to correct fields in session_anatomical_calibration_events
    
    """
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    # Testing with no file_name in db
    def test_run_session_no_file_db(self):
        response = run_session("test", "test")
        self.assertEqual(response, "Fail!")

#    # Testing with no data but filename exists in DB
    def test_run_session_no_data(self):
        file_name = "46d2f70d-7866-41a0-aae4-e5478ae9d4f3"
        self.assertRaises(IOError, run_session, "test", file_name)
#
    # Testing with no file_name in db
    def test_run_scoring_no_file_db(self):
        self.assertRaises(IOError, run_scoring, "test", "test", aws=False)
#
#    # Testing with no data but filename exists in DB
    def test_run_scoring_no_data(self):
        file_name = "46d2f70d-7866-41a0-aae4-e5478ae9d4f3"
        self.assertRaises(IOError, run_scoring, "test", file_name, aws=False)
#
#
    # Testing for expected test case
    def test_session_and_scoring_happy_path(self):
        sensor_data = "dipesh_merged_II.csv"
        data = pd.read_csv(sensor_data)
        file_name = "46d2f70d-7866-41a0-aae4-e5478ae9d4f3"
        response = run_session(sensor_data, file_name)
        #Assert the process ran successfully!
        self.assertEqual(response, "Success!")

        #Assert file was written to scoring container
        files_scoring = []
        for obj in S3.Bucket(cont_scoring).objects.all():
            files_scoring.append(obj.key)
        self.assertIn(file_name, files_scoring)


        obj = S3.Bucket(cont_scoring).Object(file_name)
        fileobj = obj.get()
        body = fileobj["Body"].read()
        scoring_data = cStringIO.StringIO(body)
        response_scoring = run_scoring(scoring_data, file_name)
        self.assertEqual(response_scoring, "Success!")

        # Assert processed file and movement table written to processed cont
        files_session_processed = []
        for obj in S3.Bucket(cont_sess).objects.all():
            files_session_processed.append(obj.key)
        self.assertIn('processed_'+file_name, files_session_processed)
        self.assertIn('movement_'+file_name, files_session_processed)


        # Assert there's no missing data in movement table
        quer_read_id = """select id from session_events where
                            sensor_data_filename = %s"""
        cur.execute(quer_read_id, (file_name,))
        session_event_id = cur.fetchall()[0][0]
        quer_read_mov = """select count(*) from movement
                            where session_event_id = %s"""
        cur.execute(quer_read_mov, (session_event_id,))
        count = cur.fetchall()[0][0]
        self.assertEqual(count, len(data))

        #Remove file from scoringcontainer
        S3.Object(cont_scoring, file_name).delete()
        #Remove data from movement table
        quer_delete = """delete from movement where session_event_id = %s"""
        cur.execute(quer_delete, (session_event_id,))
        conn.commit()
        conn.close()
        
#        #Read from base_calibration_events and make sure values are as expected
#        read_from_base = """select feet_processed_sensor_data_filename,
#                            feet_success from base_anatomical_calibration_events
#                            where feet_sensor_data_filename = %s"""
#        cur.execute(read_from_base, (file_name_base,))
#        data_from_base = cur.fetchall()[0]
#        self.assertIsNotNone(data_from_base[0])
#        self.assertIsInstance(data_from_base[0], str)
#        self.assertTrue(data_from_base[1])

        #Run session calibration and assert everything ran successfully
#        scoring_data = "dipesh_sessionAnatomicalCalibration.csv"
#        response2 = run_scoring(scoring_data, file_name, aws=False)
#        self.assertEqual(response2, "Success!")

#        # Read from session_calibration events and make sure the values are as
#        # expected
#        read_from_base_2 = """select hip_success,
#                            hip_pitch_transform,
#                            hip_roll_transform,
#                            lf_roll_transform,
#                            rf_roll_transform
#                            from base_anatomical_calibration_events
#                            where feet_sensor_data_filename = %s"""
#        cur.execute(read_from_base_2, (file_name_base,))
#        data_from_base_2 = cur.fetchall()[0]
#        self.assertTrue(data_from_base_2[0])
#        self.assertIsNotNone(data_from_base_2[1])
#        self.assertIsInstance(data_from_base_2[1], list)
#        self.assertIsNotNone(data_from_base_2[2])
#        self.assertIsInstance(data_from_base_2[2], list)
#        self.assertIsNotNone(data_from_base_2[3])
#        self.assertIsInstance(data_from_base_2[3], list)
#        self.assertIsNotNone(data_from_base_2[4])
#        self.assertIsInstance(data_from_base_2[4], list)
#
#        read_from_session = """select success,
#                            base_calibration,
#                            hip_n_transform,
#                            hip_bf_transform,
#                            lf_n_transform,
#                            lf_bf_transform,
#                            rf_n_transform,
#                            rf_bf_transform
#                            from session_anatomical_calibration_events
#                            where sensor_data_filename = %s"""
#        cur.execute(read_from_session, (file_name_session,))
#        data_from_session = cur.fetchall()[0]
#        self.assertTrue(data_from_session[0])
#        self.assertTrue(data_from_session[1])
#        self.assertIsNotNone(data_from_session[2])
#        self.assertIsInstance(data_from_session[2], list)
#        self.assertIsNotNone(data_from_session[3])
#        self.assertIsInstance(data_from_session[3], list)
#        self.assertIsNotNone(data_from_session[4])
#        self.assertIsInstance(data_from_session[4], list)
#        self.assertIsNotNone(data_from_session[5])
#        self.assertIsInstance(data_from_session[5], list)
#        self.assertIsNotNone(data_from_session[6])
#        self.assertIsInstance(data_from_session[6], list)
#        self.assertIsNotNone(data_from_session[7])
#        self.assertIsInstance(data_from_session[7], list)    

#        # remove all the data written to the DB at the end of test
#        remove_data_base= """update base_anatomical_calibration_events set 
#                                hip_roll_transform = %s,
#                                lf_roll_transform = %s,
#                                rf_roll_transform = %s,
#                                hip_pitch_transform = %s,
#                                hip_success = Null,
#                                feet_success = Null,
#                                failure_type = Null,
#                                feet_processed_sensor_data_filename = Null
#                                where feet_sensor_data_filename = %s"""
#        cur.execute(remove_data_base, ([],[],[],[], file_name_base))
#        conn.commit()
#        
#        remove_data_session = """update session_anatomical_calibration_events
#                                set
#                                success = Null,
#                                base_calibration = Null,
#                                hip_bf_transform = %s,
#                                lf_bf_transform = %s,
#                                rf_bf_transform = %s,
#                                hip_n_transform = %s,
#                                lf_n_transform = %s,
#                                rf_n_transform = %s
#                                where sensor_data_filename = %s"""
#        cur.execute(remove_data_session, ([],[],[],[],[],[], file_name_session))
#        conn.commit()
#        conn.close()
#%%
if __name__ == "__main__":      
    unittest.main(TestSessionAndScoring.test_run_session_no_file_db)