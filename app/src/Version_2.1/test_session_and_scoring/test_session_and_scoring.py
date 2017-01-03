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
        """Tests Included:
        1) Successful run of run_session with "Success!" returned
        2) File written to scoringcontainer
        3) Successful run of run_scoring with "Success!" returned
        4) File written to sessionprocessedcontainer by run_session
        5) File written to sessionprocessedcontainer by run_scoring
        6) Data written to movement table is same length as data being fed in
        
        Note: Data written to movement table is deleted at the end of run.
              Files written to scoringcontainer and sessionprocessedcontainer
              also deleted at the end of run.
        
        
        """
        sensor_data = "dipesh_merged_II.csv"
        data = pd.read_csv(sensor_data)
        file_name = "46d2f70d-7866-41a0-aae4-e5478ae9d4f3"
        quer_read_id = """select id from session_events where
                            sensor_data_filename = %s"""
        quer_delete = """delete from movement where session_event_id = %s"""
        cur.execute(quer_read_id, (file_name,))
        session_event_id = cur.fetchall()[0][0]
        # Delete all rows for the given session from previous failed runs
        cur.execute(quer_delete, (session_event_id,))
        conn.commit()

        #Assert session process ran successfully!
        response = run_session(sensor_data, file_name, aws=False)
        self.assertEqual(response, "Success!")

        #Assert file was written to scoring container
        files_scoring = []
        for obj in S3.Bucket(cont_scoring).objects.all():
            files_scoring.append(obj.key)
        self.assertIn(file_name, files_scoring)

        # Run scoring and assert process ran successfully!
        obj = S3.Bucket(cont_scoring).Object(file_name)
        fileobj = obj.get()
        body = fileobj["Body"].read()
        scoring_data = cStringIO.StringIO(body)
        response_scoring = run_scoring(scoring_data, file_name, aws=False)
        self.assertEqual(response_scoring, "Success!")

        # Assert processed file and movement table written to processed cont
        files_session_processed = []
        for obj in S3.Bucket(cont_sess).objects.all():
            files_session_processed.append(obj.key)
        self.assertIn('processed_'+file_name, files_session_processed)
        self.assertIn('movement_'+file_name, files_session_processed)

        # Assert there's no missing data in movement table
        quer_read_mov = """select count(*) from movement
                            where session_event_id = %s"""
        cur.execute(quer_read_mov, (session_event_id,))
        count = cur.fetchall()[0][0]
        self.assertEqual(count, len(data))

        #Remove file from scoringcontainer and sessionprocessedcontainer
        S3.Object(cont_scoring, file_name).delete()
        S3.Object(cont_sess, 'processed_'+file_name).delete()
        S3.Object(cont_sess, 'movement_'+file_name).delete()
        
        #Remove data from movement table
        cur.execute(quer_delete, (session_event_id,))
        conn.commit()
        conn.close()

#%%
if __name__ == "__main__":      
    unittest.main(TestSessionAndScoring.test_run_session_no_file_db,
                  verbosity=2)
