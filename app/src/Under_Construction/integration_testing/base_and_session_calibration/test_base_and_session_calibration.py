# -*- coding: utf-8 -*-
"""
Created on Thu Dec 29 11:19:15 2016

@author: Gautam
"""

import unittest
from pyramid import testing
import psycopg2

from runBaseFeet import record_base_feet
from runSessionCalibration import run_calibration



conn = psycopg2.connect("""dbname='biometrix' user='ubuntu'
host='ec2-35-162-107-177.us-west-2.compute.amazonaws.com' 
password='d8dad414c2bb4afd06f8e8d4ba832c19d58e123f'""")
cur = conn.cursor()

class TestBaseAndSessionCalibration(unittest.TestCase):
    """Tests for Base and Session process
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
    def test_record_base_feet_no_file_db(self):
        self.assertRaises(IndexError, record_base_feet, "test", "test")

    # Testing with no data but filename exists in DB
    def test_record_base_feet_no_data(self):
        file_name = "team1_session1_trainingset_anatomicalCalibration.csv"
        self.assertRaises(IOError, record_base_feet, "test", file_name)

    # Testing with no file_name in db
    def test_session_calibration_no_file_db(self):
        self.assertRaises(IndexError, run_calibration, "test", "test")

    # Testing with no data but filename exists in DB
    def test_session_calibration_no_data(self):
        file_name = "team1_session1_trainingset_anatomicalCalibration.csv"
        self.assertRaises(IOError, run_calibration, "test", file_name)



    # Testing for expected test case
    def test_base_and_session_happy_path(self):
        sensor_data_base = "dipesh_baseAnatomicalCalibration.csv"
        file_name_base = "67fd2d25-3ac7-482d-a659-6c452acbe900"
        response = record_base_feet(sensor_data_base, file_name_base, aws=False)

        #Assert the process ran successfully!
        self.assertEqual(response, "Success!")

        #Read from base_calibration_events and make sure values are as expected
        read_from_base = """select feet_processed_sensor_data_filename,
                            feet_success from base_anatomical_calibration_events
                            where feet_sensor_data_filename = %s"""
        cur.execute(read_from_base, (file_name_base,))
        data_from_base = cur.fetchall()[0]
        self.assertIsNotNone(data_from_base[0])
        self.assertIsInstance(data_from_base[0], str)
        self.assertTrue(data_from_base[1])

        #Run session calibration and assert everything ran successfully
        sensor_data_session = "dipesh_sessionAnatomicalCalibration.csv"
        file_name_session = "8051538e-9046-4aac-acef-c37418d392e7"
        response2 = run_calibration(sensor_data_session, file_name_session)
        self.assertEqual(response2, "Success!")

        # Read from session_calibration events and make sure the values are as
        # expected
        read_from_base_2 = """select hip_success,
                            hip_pitch_transform,
                            hip_roll_transform,
                            lf_roll_transform,
                            rf_roll_transform
                            from base_anatomical_calibration_events
                            where feet_sensor_data_filename = %s"""
        cur.execute(read_from_base_2, (file_name_base,))
        data_from_base_2 = cur.fetchall()[0]
        self.assertTrue(data_from_base_2[0])
        self.assertIsNotNone(data_from_base_2[1])
        self.assertIsInstance(data_from_base_2[1], list)
        self.assertIsNotNone(data_from_base_2[2])
        self.assertIsInstance(data_from_base_2[2], list)
        self.assertIsNotNone(data_from_base_2[3])
        self.assertIsInstance(data_from_base_2[3], list)
        self.assertIsNotNone(data_from_base_2[4])
        self.assertIsInstance(data_from_base_2[4], list)

        read_from_session = """select success,
                            base_calibration,
                            hip_n_transform,
                            hip_bf_transform,
                            lf_n_transform,
                            lf_bf_transform,
                            rf_n_transform,
                            rf_bf_transform
                            from session_anatomical_calibration_events
                            where sensor_data_filename = %s"""
        cur.execute(read_from_session, (file_name_session,))
        data_from_session = cur.fetchall()[0]
        self.assertTrue(data_from_session[0])
        self.assertTrue(data_from_session[1])
        self.assertIsNotNone(data_from_session[2])
        self.assertIsInstance(data_from_session[2], list)
        self.assertIsNotNone(data_from_session[3])
        self.assertIsInstance(data_from_session[3], list)
        self.assertIsNotNone(data_from_session[4])
        self.assertIsInstance(data_from_session[4], list)
        self.assertIsNotNone(data_from_session[5])
        self.assertIsInstance(data_from_session[5], list)
        self.assertIsNotNone(data_from_session[6])
        self.assertIsInstance(data_from_session[6], list)
        self.assertIsNotNone(data_from_session[7])
        self.assertIsInstance(data_from_session[7], list)    

        # remove all the data written to the DB at the end of test
        remove_data_base= """update base_anatomical_calibration_events set 
                                hip_roll_transform = %s,
                                lf_roll_transform = %s,
                                rf_roll_transform = %s,
                                hip_pitch_transform = %s,
                                hip_success = Null,
                                feet_success = Null,
                                failure_type = Null,
                                feet_processed_sensor_data_filename = Null
                                where feet_sensor_data_filename = %s"""
        cur.execute(remove_data_base, ([],[],[],[], file_name_base))
        conn.commit()
        
        remove_data_session = """update session_anatomical_calibration_events
                                set
                                success = Null,
                                base_calibration = Null,
                                hip_bf_transform = %s,
                                lf_bf_transform = %s,
                                rf_bf_transform = %s,
                                hip_n_transform = %s,
                                lf_n_transform = %s,
                                rf_n_transform = %s
                                where sensor_data_filename = %s"""
        cur.execute(remove_data_session, ([],[],[],[],[],[], file_name_session))
        conn.commit()
        conn.close()
        
unittest.main()