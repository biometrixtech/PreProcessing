# -*- coding: utf-8 -*-
"""
Created on Thu Dec 29 11:19:15 2016

@author: Gautam
"""

import sys
import unittest
from pyramid import testing
import psycopg2
import boto3

sys.path.insert(0, '..\\baseFeetProcess')
from runBaseFeet import record_base_feet

sys.path.insert(0, '..\\sessionCalibrationProcess')
from runSessionCalibration import run_calibration

conn = psycopg2.connect("""dbname='biometrix' user='ubuntu'
host='ec2-35-162-107-177.us-west-2.compute.amazonaws.com' 
password='d8dad414c2bb4afd06f8e8d4ba832c19d58e123f'""")
cur = conn.cursor()

S3 = boto3.resource('s3')
cont_base = 'biometrix-baseanatomicalcalibrationprocessedcontainer'
cont_session = 'biometrix-sessionanatomicalcalibrationprocessedcontainer'

class TestBaseAndSessionCalib(unittest.TestCase):
    """Tests for Base and Session process
    -IO error for missing file
    -IndexError for file_name missing in DB
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
        file_name = "67fd2d25-3ac7-482d-a659-6c452acbe900"
        self.assertRaises(IOError, record_base_feet, "test", file_name)

    # Testing with no file_name in db
    def test_session_calibration_no_file_db(self):
        self.assertRaises(IndexError, run_calibration, "test", "test")

    # Testing with no data but filename exists in DB
    def test_session_calibration_no_data(self):
        file_name = "8051538e-9046-4aac-acef-c37418d392e7"
        self.assertRaises(IOError, run_calibration, "test", file_name)
    # Testing with no data but filename exists in DB
    def test_base_calibration_bad_magn(self):
        file_name = "1d2b14d4-1da7-4833-9afe-6c21cc6fbb95"
        sensor_data_base = '1d2b14d4-1da7-4833-9afe-6c21cc6fbb95.csv'
        response = record_base_feet(sensor_data_base, file_name)
        self.assertEqual(response, "Fail!")
        quer_read = """select
                        feet_success,
                        failure_type,
                        feet_processed_sensor_data_filename
                        from base_anatomical_calibration_events where
                        feet_sensor_data_filename = %s"""
        cur.execute(quer_read, (file_name,))
        data_read = cur.fetchall()[0]
        self.assertFalse(data_read[0])
        self.assertEqual(data_read[1], 1)
        self._remove_data(file_name, "none", table="base")

    def test_session_calibration_bad_magn(self):
        file_name = "d3ef003e-68e9-47fa-a459-ce118bf917e5"
        sensor_data_base = 'd3ef003e-68e9-47fa-a459-ce118bf917e5.csv'
        response = run_calibration(sensor_data_base, file_name)
        self.assertEqual(response, "Fail!")
        quer_read = """select
                        success,
                        failure_type
                        from session_anatomical_calibration_events where
                        sensor_data_filename = %s"""
        cur.execute(quer_read, (file_name,))
        data_read = cur.fetchall()[0]
        self.assertFalse(data_read[0])
        self.assertEqual(data_read[1], 1)
        self._remove_data("none", file_name, table="session")

    # Testing for expected test case
    def test_base_and_session_happy_path(self):
        """Tests Included:
        1) Successful run of baseFeetProcess
        2) processed_file_name written to baseanatomicalcalibrationevents
        3) processed_file_name is string
        4) feet_success is True in baseanatomicalcalibrationevents
        5) Successful run of sessionCalibration
            -This implies that the file was written to
                baseanatomicalcalibrationprocessedcontainer
        6) hip_success is True in baseanatomicalcalibrationevents
        7) All four transform values are present and of type list and length 4
            in baseanatomicalcalibrationevents
        8) success is True in sessionanatomicalcalibrationevents
        9) base_calibration is True in sessionanatomicalcalibrationevents
        10) All 6 transform values are present and of type list and length 4 in
            sessionanatomicalcalibrationevents
        11) Assert processed file written to
            baseanatomicalcalibrationprocessedcontainer
            and sessionanatomicalcalibrationprocessedcontainer
        Note: Data deleted from BaseAnatomicalCalibrationEvents and
              SessionAnatomicalCalibrationEvents at the start of the run. Left
              at the end of the run as it might be called to test sessionProcess
              Processed files written to s3 deleted at the end.
        """
        sensor_data_base = "dipesh_baseAnatomicalCalibration.csv"
        file_name_base = "67fd2d25-3ac7-482d-a659-6c452acbe900"
        sensor_data_session = "dipesh_sessionAnatomicalCalibration.csv"
        file_name_session = "8051538e-9046-4aac-acef-c37418d392e7"

        # Make sure no unnecessary data is present in DB
        self._remove_data(file_name_base, file_name_session)

        #Assert the process ran successfully!
        response = record_base_feet(sensor_data_base, file_name_base, aws=False)
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
        response2 = run_calibration(sensor_data_session, file_name_session,
                                    aws=False)
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
        self.assertEqual(len(data_from_base_2[1]), 4)
        self.assertIsNotNone(data_from_base_2[2])
        self.assertIsInstance(data_from_base_2[2], list)
        self.assertEqual(len(data_from_base_2[2]), 4)
        self.assertIsNotNone(data_from_base_2[3])
        self.assertIsInstance(data_from_base_2[3], list)
        self.assertEqual(len(data_from_base_2[3]), 4)
        self.assertIsNotNone(data_from_base_2[4])
        self.assertIsInstance(data_from_base_2[4], list)
        self.assertEqual(len(data_from_base_2[4]), 4)

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
        self.assertEqual(len(data_from_session[2]), 4)
        self.assertIsNotNone(data_from_session[3])
        self.assertIsInstance(data_from_session[3], list)
        self.assertEqual(len(data_from_session[3]), 4)
        self.assertIsNotNone(data_from_session[4])
        self.assertIsInstance(data_from_session[4], list)
        self.assertEqual(len(data_from_session[4]), 4)
        self.assertIsNotNone(data_from_session[5])
        self.assertIsInstance(data_from_session[5], list)
        self.assertEqual(len(data_from_session[5]), 4)
        self.assertIsNotNone(data_from_session[6])
        self.assertIsInstance(data_from_session[6], list)
        self.assertEqual(len(data_from_session[6]), 4)
        self.assertIsNotNone(data_from_session[7])
        self.assertIsInstance(data_from_session[7], list)
        self.assertEqual(len(data_from_session[7]), 4)

        files_base_calib_processed = []
        for obj in S3.Bucket(cont_base).objects.all():
            files_base_calib_processed.append(obj.key)
        self.assertIn('processed_'+file_name_base, files_base_calib_processed)
        files_session_processed = []
        for obj in S3.Bucket(cont_session).objects.all():
            files_session_processed.append(obj.key)
        self.assertIn('processed_'+file_name_session, files_session_processed)

        # remove all the data written to the DB at the end of test
#        S3.Object(cont_base, 'processed_'+file_name_base).delete()
        S3.Object(cont_session, 'processed_'+file_name_session).delete()
#        self._remove_data(file_name_base, file_name_session)
#        conn.close()
        
    def _remove_data(self, file_name_base, file_name_session, table="both"):
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
        if table == "base" or table == "both":
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
        if table == "session" or table == "both":
            cur.execute(remove_data_session, ([],[],[],[],[],[], file_name_session))
            conn.commit()
        
if __name__ == "__main__":      
    unittest.main(module=TestBaseAndSessionCalib.test_base_and_session_happy_path,
                  verbosity=2)

