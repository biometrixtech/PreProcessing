# -*- coding: utf-8 -*-
"""
Created on Thu Jan 18 09:51:01 2018

@author: court
"""

import unittest
import numpy as np
import pandas as pd
import copy

import quatOps as qo
import quatConvs as qc
import extractGeometry as eg
import movementAttrib as ma
import balanceCME as cmed
import runRelativeCME as rcme
import impactCME as imp
import dataObject as do
import phaseDetection as phd
import detectImpactPhaseIntervals as di
import detectTakeoffPhaseIntervals as dt

class TestQuatOps(unittest.TestCase):
    """
    Testing all quatOps functions.

    Tests included:
        --quat_prod
            -Output data is same shape as input
            -Product of a quaternion with its conjugate is unit quaternion
            -Multiplying by unit quaternion returns input
        --quat_norm
            -Output data is same shape as input
            -Magnitude of all quaternions is 1 after normalizing
        --find_rot
            -Output data is same shape as input
            -Rotation between self is [1,0,0,0]
            -Rotation between input and -input os [-1,0,0,0]
            -Rotation between input and [1,0,0,0] is input
        --quat_conj
            -Output data is same shape as input
            -quat_conj(quat_cont(input)) is quat_norm(input)
        --vect_rot
            -Output data is same shape as v
            -Rotating by unit quaternion returns v
            -Rotating 90 deg 4 times about axis returns v
        --quat_avg
            -Output data has same number of columns as input
            -Output data's columns are averages of the values within
                respective columns
        --quat_multi_prod
            -output value is the same shape as each input
            -using this function gives the same result as individually run
                quat_prod functions
            -if input has no len, raise error
        --quat_force_euler_angle
            -output data is the same shape as input
            -output data is quaternion representation of input data, where
                specified axes have been replaced with specified values


    """

    def test_quat_prod(self):
        '''
        Tests included:

            -Output data is same shape as input
            -Product of a quaternion with its conjugate is unit quaternion
            -Multiplying by unit quaternion returns input

        '''
        eye = np.array([[1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 0, 0]])
        z90 = np.array([[1, 0, 0, 0], [np.sqrt(2)/2, 0, 0, np.sqrt(2)/2], [0.44807362, 0, 0, 0.89399666]])
        eye_shape = eye.shape
        eye_prod = qo.quat_prod(eye, eye)
        eye_prod_shape = eye_prod.shape
        z90_conj = qo.quat_conj(z90)
        z90_z90_conj_prod = qo.quat_prod(z90, z90_conj)
        eye_z90_prod = qo.quat_prod(eye, z90)

        # output data is same shape as input
        self.assertEqual(eye_prod_shape, eye_shape)

        # product of a quaternion with its conjugate is unit quaternion
        self.assertTrue(np.allclose(z90_z90_conj_prod, eye))

        # multiplying by a unit quaternion returns input
        self.assertTrue(np.allclose(eye_prod, eye))
        self.assertTrue(np.allclose(eye_z90_prod, z90))


    def test_quat_norm(self):
        '''
        Tests included:

            -Output data is same shape as input
            -Magnitude of all quaternions is 1 after normalizing

        '''
        eye = np.array([[1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 0, 0]])
        skewed = eye + np.array([[0, 0, 0, 0.4]])
        skewed_shape = skewed.shape
        skewed_norm = qo.quat_norm(skewed)
        skewed_norm_shape = skewed_norm.shape
        mag_skewed_norm = np.sqrt(np.sum(skewed_norm**2, axis=1))

        # output data is same shape as input
        self.assertEqual(skewed_shape, skewed_norm_shape)

        # magnitude of quaternions is 1 after normalizing
        self.assertTrue(np.allclose(mag_skewed_norm, np.array([1, 1, 1])))

    def test_find_rot(self):
        '''
        Tests included:

            -Output data is same shape as inputs
            -Rotation between self is [1, 0, 0, 0]
            -Rotation between input and -input is [-1, 0, 0, 0]
            -Rotation between input and [1, 0, 0, 0] is input

        '''
        eye = np.array([[1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 0, 0]])
        z90 = np.array([[1, 0, 0, 0], [np.sqrt(2)/2, 0, 0, np.sqrt(2)/2], [0.44807362, 0, 0, 0.89399666]])
        z90_shape = z90.shape
        z90_z90_rot = qo.find_rot(z90, z90)
        z90_z90_rot_shape = z90_z90_rot.shape
        z90_nz90_rot = qo.find_rot(z90, -z90)
        z90_eye_rot = qo.find_rot(eye, z90)

        # output data is same shape as inputs
        self.assertEqual(z90_z90_rot_shape, z90_shape)

        # rotation between self is [1, 0, 0, 0]
        self.assertTrue(np.allclose(z90_z90_rot, eye))

        # rotation between input and -input is [-1, 0, 0, 0]
        self.assertTrue(np.allclose(z90_nz90_rot, -eye))

        # rotation between [1, 0, 0, 0] and input is input
        self.assertTrue(np.allclose(z90_eye_rot, z90))

    def test_quat_conj(self):
        '''
        Tests include:

            -Output data is same shape as input
            -quat_conj(quat_conj(input)) is quat_norm(input)

        '''

        z90 = np.array([[1, 0, 0, 0], [np.sqrt(2)/2, 0, 0, np.sqrt(2)/2], [0.44807362, 0, 0, 0.89399666]])
        z90_shape = z90.shape
        z90_conj = qo.quat_conj(z90)
        z90_conj_shape = z90_conj.shape
        z90_norm = qo.quat_norm(z90)
        z90_conj_conj = qo.quat_conj(z90_conj)

        # output data is same shape as input
        self.assertEqual(z90_shape, z90_conj_shape)

        # quat_conj(quat_conj(input)) is quat_norm(input)
        self.assertTrue(np.allclose(z90_conj_conj, z90_norm))

    def test_vect_rot(self):
        '''
        Tests include:

            -Output data is same shape as v
            -Rotating by unit quaternion returns v
            -Rotating 90 deg 4 times about axis returns v

        '''

        vect = np.array([[1, 0, 0], [1, 0, 0], [1, 0, 0]])
        eye = np.array([[1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 0, 0]])
        z90 = np.array([[1, 0, 0, 0], [np.sqrt(2)/2, 0, 0, np.sqrt(2)/2], [np.sqrt(2)/2, 0, 0, np.sqrt(2)/2]])
        vect_shape = vect.shape
        vect_eye_rot = qo.vect_rot(vect, eye)
        vect_eye_rot_shape = vect_eye_rot.shape
        rot_4 = qo.vect_rot(qo.vect_rot(qo.vect_rot(qo.vect_rot(vect, z90), z90), z90), z90)

        # output data is same shape as v
        self.assertEqual(vect_shape, vect_eye_rot_shape)

        # rotating by unit quaternion returns v
        self.assertTrue(np.allclose(vect, vect_eye_rot))

        # rotating 90 deg 4 times about axis returns v
        self.assertTrue(np.allclose(vect, rot_4))

    def test_quat_avg(self):
        '''
        Tests include:
            -Output data has same number of columns as input
            -Output data's columns are normalized averages of the values within
                respective columns

        '''

        z90 = np.array([[1, 0, 0, 0], [np.sqrt(2)/2, 0, 0, np.sqrt(2)/2], [0.44807362, 0, 0, 0.89399666]])
        z90_avg = qo.quat_avg(z90)
        z90_shape = z90.shape
        z90_avg_shape = z90_avg.shape
        z90_np_avg = qo.quat_norm([np.sum(z90, axis=0)/3])

        # output has same number of columns as input
        self.assertEqual(z90_shape[1], z90_avg_shape[1])

        # output columns are normed avgs of the vals within respective input cols
        self.assertTrue(np.allclose(z90_avg, z90_np_avg))


    def test_quat_multi_prod(self):
        '''
        Tests included:

            -output value is the same shape as each input
            -using this function gives the same result as individually run
                quat_prod functions
            -if input has no len, raise error

        '''

        z90 = np.array([[1, 0, 0, 0], [np.sqrt(2)/2, 0, 0, np.sqrt(2)/2], [0.44807362, 0, 0, 0.89399666]])
        y45 = np.array([[1, 0, 0, 0], [ 0.92387953, 0, -0.38268343, 0], [np.sqrt(2)/2, 0, np.sqrt(2)/2, 0]])
        z90_shape = z90.shape
        z90_3_prod = qo.quat_multi_prod(z90, z90, z90)
        y45_y45_z90 = qo.quat_multi_prod(y45, y45, z90)
        z90_3_prod_shape = z90_3_prod.shape
        z90_prod_prod = qo.quat_prod(qo.quat_prod(z90, z90), z90)
        y45_y45_z90_prod = qo.quat_prod(qo.quat_prod(y45, y45), z90)

        # output value is the same shape as each input
        self.assertEqual(z90_shape, z90_3_prod_shape)

        # output is same as layered quat_prod functions
        self.assertTrue(np.allclose(z90_3_prod, z90_prod_prod))
        self.assertTrue(np.allclose(y45_y45_z90, y45_y45_z90_prod))

        # if input has no len, raise error
        with self.assertRaises(ValueError) as context:
            qo.quat_multi_prod()

        self.assertTrue('Must supply at least one argument' in context.exception)

    def test_quat_force_euler_angle(self):
        '''
        Tests include:

            -output data is the same shape as input
            -output data is quaternion representation of input data, where
                specified axes have been replaced with specified values

        '''

        x90 = np.array([[np.sqrt(2)/2, np.sqrt(2)/2, 0, 0], [np.sqrt(2)/2, np.sqrt(2)/2, 0, 0], [np.sqrt(2)/2, np.sqrt(2)/2, 0, 0]])
        y90 = np.array([[np.sqrt(2)/2, 0, np.sqrt(2)/2, 0], [np.sqrt(2)/2, 0, np.sqrt(2)/2, 0], [np.sqrt(2)/2, 0, np.sqrt(2)/2, 0]])
        z90 = np.array([[1, 0, 0, 0], [np.sqrt(2)/2, 0, 0, np.sqrt(2)/2], [0.44807362, 0, 0, 0.89399666]])
        eye = np.array([[1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 0, 0]])
        z90_from_eye = np.array([[np.sqrt(2)/2, 0, 0, np.sqrt(2)/2], [np.sqrt(2)/2, 0, 0, np.sqrt(2)/2], [np.sqrt(2)/2, 0, 0, np.sqrt(2)/2]])
        z90_shape = z90.shape
        z90_to_eye = qo.quat_force_euler_angle(z90, psi=0)
        z90_to_eye_shape = z90_to_eye.shape
        eye_to_x90 = qo.quat_force_euler_angle(eye, phi=90*np.pi/180)
        eye_to_y90 = qo.quat_force_euler_angle(eye, theta=90*np.pi/180)
        eye_to_z90 = qo.quat_force_euler_angle(eye, psi=90*np.pi/180)

        # output data is same shape as input
        self.assertEqual(z90_shape, z90_to_eye_shape)

        # output data is quaternion representation of input data, where
            # specified axes have been replaced with specified values
        self.assertTrue(np.allclose(z90_to_eye, eye))
        self.assertTrue(np.allclose(eye_to_x90, x90))
        self.assertTrue(np.allclose(eye_to_y90, y90))
        self.assertTrue(np.allclose(eye_to_z90, z90_from_eye))


class TestQuatConvs(unittest.TestCase):
    '''
    Testing all quatConvs functions.

    Tests included:
        --quat_to_euler
            -output has same number of rows as input
            -specific examples
        --euler_to_quat
            -output has same number of rows as input
            -specific examples

    '''

    def test_euler_to_quat(self):
        '''
        Tests include:
            -output has same number of rows as input
            -specific examples

        '''
        z90eul = np.array([[0, 0, 90*np.pi/180]])
        z90eul_shape = z90eul.shape
        z90quat = qc.euler_to_quat(z90eul)
        z90quat_shape = z90quat.shape

        # output only has same number of rows as input
        self.assertEqual(z90eul_shape[0], z90quat_shape[0])
        self.assertNotEqual(z90eul_shape[1], z90quat_shape[1])

        # specific examples
        self.assertTrue(np.allclose(z90quat, np.array([[0.70710678, 0, 0,
                        0.70710678]])) or np.allclose(z90quat,
                        np.array([[-0.70710678, 0, 0, -0.70710678]])))

    def test_quat_to_euler(self):
        '''
        Tests include:
            -output has same number of rows as input
            -specific examples

        '''

        z90quat = np.array([[np.sqrt(2)/2, 0, 0, np.sqrt(2)/2]])
        z90nquat = np.array([[-np.sqrt(2)/2, 0, 0, -np.sqrt(2)/2]])
        z90quat_shape = z90quat.shape
        z90eul = qc.quat_to_euler(z90quat)
        z90eul_shape = z90eul.shape
        z90neul = qc.quat_to_euler(z90nquat)

        # output has same number of rows as input
        self.assertEqual(z90quat_shape[0], z90eul_shape[0])
        self.assertNotEqual(z90quat_shape[1], z90eul_shape[1])

        # specific examples
            # complementary quats pointing to same eul set
        self.assertTrue(np.allclose(z90eul, np.array([[0, 0, 1.57079633]])))
        self.assertTrue(np.allclose(z90neul, np.array([[0, 0, 1.57079633]])))

            # cases of imaginary pitch returned as real pitch
        y90quatimag = np.array([[0, 0, 1, 0]])
        y90eulimag = qc.quat_to_euler(y90quatimag)

        self.assertTrue(np.allclose(y90eulimag, np.array([[0, np.pi, 0]])))


class TestExtractGeometry(unittest.TestCase):
    '''
    Tests included:
        --extract_geometry
            -outputs are properly formatted for use later in processing
            -output matches expectation when assumptions of placement are valid

    '''
    def test_extract_geometry(self):
        '''
        Tests include:
            -outputs are properly formatted for use later in processing
            -output matches expectation when assumptions of placement are valid
                -good quality data
                -data whose values cross quadrants does not include Euler angle error

        '''
        test_file1 = 'a1bf8bad_short_orientation.csv'
        test_data1 = pd.read_csv(test_file1)
        test1_l_quats = np.hstack((np.hstack((np.hstack((
                                  test_data1.LqW.values.reshape(-1, 1),
                                  test_data1.LqX.values.reshape(-1, 1))),
                                  test_data1.LqY.values.reshape(-1, 1))),
                                  test_data1.LqZ.values.reshape(-1, 1)))
        test1_h_quats = np.hstack((np.hstack((np.hstack((
                                  test_data1.HqW.values.reshape(-1, 1),
                                  test_data1.HqX.values.reshape(-1, 1))),
                                  test_data1.HqY.values.reshape(-1, 1))),
                                  test_data1.HqZ.values.reshape(-1, 1)))
        test1_r_quats = np.hstack((np.hstack((np.hstack((
                                  test_data1.RqW.values.reshape(-1, 1),
                                  test_data1.RqX.values.reshape(-1, 1))),
                                  test_data1.RqY.values.reshape(-1, 1))),
                                  test_data1.RqZ.values.reshape(-1, 1)))
        a_L1, f_L1, a_H1, f_H1, a_R1, f_R1 = eg.extract_geometry(test1_l_quats,
                                                                 test1_h_quats,
                                                                 test1_r_quats)
        test1_LeX = test_data1.LeX
        test1_HeX = test_data1.HeX
        test1_ReX = test_data1.ReX
        test1_LeY = test_data1.LeY
        test1_HeY = test_data1.HeY
        test1_ReY = test_data1.ReY
        test_file2 = 'e0deb549_short_raw.csv'
        test_data2 = pd.read_csv(test_file2)
        test2_l_quats = np.hstack((np.hstack((np.hstack((
                                  test_data2.LqW.values.reshape(-1, 1),
                                  test_data2.LqX.values.reshape(-1, 1))),
                                  test_data2.LqY.values.reshape(-1, 1))),
                                  test_data2.LqZ.values.reshape(-1, 1)))
        test2_h_quats = np.hstack((np.hstack((np.hstack((
                                  test_data2.HqW.values.reshape(-1, 1),
                                  test_data2.HqX.values.reshape(-1, 1))),
                                  test_data2.HqY.values.reshape(-1, 1))),
                                  test_data2.HqZ.values.reshape(-1, 1)))
        test2_r_quats = np.hstack((np.hstack((np.hstack((
                                  test_data2.RqW.values.reshape(-1, 1),
                                  test_data2.RqX.values.reshape(-1, 1))),
                                  test_data2.RqY.values.reshape(-1, 1))),
                                  test_data2.RqZ.values.reshape(-1, 1)))
        a_L2, f_L2, a_H2, f_H2, a_R2, f_R2 = eg.extract_geometry(test2_l_quats,
                                                                 test2_h_quats,
                                                                 test2_r_quats)
        test2_l_euls = qc.quat_to_euler(test2_l_quats)
        test2_h_euls = qc.quat_to_euler(test2_h_quats)
        test2_r_euls = qc.quat_to_euler(test2_r_quats)
        test_file3 = '8cc60460_short_raw.csv'
        test_data3 = pd.read_csv(test_file3)
        test3_l_quats = np.hstack((np.hstack((np.hstack((
                                  test_data3.LqW.values.reshape(-1, 1),
                                  test_data3.LqX.values.reshape(-1, 1))),
                                  test_data3.LqY.values.reshape(-1, 1))),
                                  test_data3.LqZ.values.reshape(-1, 1)))
        test3_h_quats = np.hstack((np.hstack((np.hstack((
                                  test_data3.HqW.values.reshape(-1, 1),
                                  test_data3.HqX.values.reshape(-1, 1))),
                                  test_data3.HqY.values.reshape(-1, 1))),
                                  test_data3.HqZ.values.reshape(-1, 1)))
        test3_r_quats = np.hstack((np.hstack((np.hstack((
                                  test_data3.RqW.values.reshape(-1, 1),
                                  test_data3.RqX.values.reshape(-1, 1))),
                                  test_data3.RqY.values.reshape(-1, 1))),
                                  test_data3.RqZ.values.reshape(-1, 1)))
        a_L3, f_L3, a_H3, f_H3, a_R3, f_R3 = eg.extract_geometry(test3_l_quats,
                                                                 test3_h_quats,
                                                                 test3_r_quats)
        test3_LeX = test_data3.LeX
        test3_HeX = test_data3.HeX
        test3_ReX = test_data3.ReX
        test3_LeY = test_data3.LeY
        test3_HeY = test_data3.HeY
        test3_ReY = test_data3.ReY
        a_L4, f_L4, a_H4, f_H4, a_R4, f_R4 = eg.extract_geometry(test3_r_quats,
                                                                 test3_h_quats,
                                                                 test3_l_quats)

        # outputs are properly formatted for use later in processing
        self.assertEqual(a_L1.shape, (len(test_data1),))
        self.assertEqual(f_L1.shape, (len(test_data1),))
        self.assertEqual(a_H1.shape, (len(test_data1),))
        self.assertEqual(f_H1.shape, (len(test_data1),))
        self.assertEqual(a_R1.shape, (len(test_data1),))
        self.assertEqual(f_R1.shape, (len(test_data1),))

        # output matches expectation when assumptions of placement are valid
            # good quality data
        self.assertTrue(np.allclose(a_L1, test1_LeX, rtol = 1e-04, atol = 1e-04))
        self.assertTrue(np.allclose(a_H1, test1_HeX, rtol = 1e-04, atol = 1e-04))
        self.assertTrue(np.allclose(a_R1, test1_ReX, rtol = 1e-04, atol = 1e-04))
        self.assertTrue(np.allclose(f_L1, test1_LeY, rtol = 1e-04, atol = 1e-04))
        self.assertTrue(np.allclose(f_H1, test1_HeY, rtol = 1e-04, atol = 1e-04))
        self.assertTrue(np.allclose(f_R1, test1_ReY, rtol = 1e-04, atol = 1e-04))

            # results from data whose values cross quadrants (in expected ways,
            # ie, pitch divots) do not include Euler angle error
        self.assertFalse(np.allclose(a_L2, test2_l_euls[:, 0], rtol = 1e-04, atol = 1e-04))
        self.assertFalse(np.allclose(a_H2, test2_h_euls[:, 0], rtol = 1e-04, atol = 1e-04))
        self.assertFalse(np.allclose(a_R2, test2_r_euls[:, 0], rtol = 1e-04, atol = 1e-04))
        self.assertFalse(np.allclose(f_L2, test2_l_euls[:, 1], rtol = 1e-04, atol = 1e-04))
        self.assertFalse(np.allclose(f_H2, test2_h_euls[:, 1], rtol = 1e-04, atol = 1e-04))
        self.assertFalse(np.allclose(f_R2, test2_r_euls[:, 1], rtol = 1e-04, atol = 1e-04))

        # improper placement assumptions result in some erroneous values
            # untransformed data
                # divots in left foot
        self.assertFalse(np.allclose(a_L3, test3_LeX, rtol = 1e-04, atol = 1e-04)
                         and np.allclose(f_L3, test3_LeY, rtol = 1e-04, atol = 1e-04))
        self.assertFalse(np.allclose(a_H3, test3_HeX, rtol = 1e-04, atol = 1e-04)
                         and np.allclose(f_H3, test3_HeY, rtol = 1e-04, atol = 1e-04))
        self.assertFalse(np.allclose(a_R3, test3_ReX, rtol = 1e-04, atol = 1e-04)
                         and np.allclose(f_R3, test3_ReY, rtol = 1e-04, atol = 1e-04))
                # divots in right foot
        self.assertFalse(np.allclose(a_L4, test3_ReX, rtol = 1e-04, atol = 1e-04)
                         and np.allclose(f_L4, test3_ReY, rtol = 1e-04, atol = 1e-04))
        self.assertFalse(np.allclose(a_H4, test3_HeX, rtol = 1e-04, atol = 1e-04)
                         and np.allclose(f_H4, test3_HeY, rtol = 1e-04, atol = 1e-04))
        self.assertFalse(np.allclose(a_R4, test3_LeX, rtol = 1e-04, atol = 1e-04)
                         and np.allclose(f_R4, test3_LeY, rtol = 1e-04, atol = 1e-04))


class TestMovementAttributes(unittest.TestCase):
    '''
    Tests include:
        --plane_analysis
            -format of output is appropriate (don't care about integrity of
            values right now)
        --run_stance_analysis
        --standing_or_not
        --sort_phases
        --_num_runs
        --total_accel
        --enumerate_stance
        
    '''
    def test_plane_analysis(self):
        '''
        Tests include:
            - shape of output is appropriate (don't care about integrity of
            values right now, since muting results in dash)
        '''
        test_file = 'e0deb549_short_raw.csv'
        test_data = pd.read_csv(test_file)
        quats = np.hstack((np.hstack((np.hstack((
                          test_data.LqW.values.reshape(-1, 1),
                          test_data.LqX.values.reshape(-1, 1))),
                          test_data.LqY.values.reshape(-1, 1))),
                          test_data.LqZ.values.reshape(-1, 1)))
        euls = qc.quat_to_euler(quats)
        acc = np.hstack((np.hstack((
                        test_data.LaX.values.reshape(-1, 1),
                        test_data.LaY.values.reshape(-1, 1))),
                        test_data.LaZ.values.reshape(-1, 1)))
        ms_elapsed = np.vstack((np.array([[0]]),
                               np.ediff1d(test_data.epoch_time).reshape(-1, 1)))
        lat, vert, horz, rot, lat_binary, vert_binary, horz_binary,\
           rot_binary, stationary_binary, accel_mag = ma.plane_analysis(acc, euls, ms_elapsed)

        # shape of output is appropriate
        self.assertEqual(lat.shape, (len(test_data), 1))
        self.assertEqual(vert.shape, (len(test_data), 1))
        self.assertEqual(horz.shape, (len(test_data), 1))
        self.assertEqual(rot.shape, (len(test_data), 1))
        self.assertEqual(lat_binary.shape, (len(test_data), 1))
        self.assertEqual(vert_binary.shape, (len(test_data), 1))
        self.assertEqual(horz_binary.shape, (len(test_data), 1))
        self.assertEqual(rot_binary.shape, (len(test_data), 1))
        self.assertEqual(stationary_binary.shape, (len(test_data), 1))
        self.assertEqual(accel_mag.shape, (len(test_data), 1))

    def test_run_stance_analysis(self):
        '''
        Tests include:
            -output is correct format
            -validity of results according to known input are proven via
            sub-function testing
        '''
        test_file = 'stance_phase_a1bf8bad_transformed_short.csv'
        test_data = pd.read_csv(test_file)
        stance = ma.run_stance_analysis(test_data)
        stance_exp = test_data.stance.values.reshape(-1, 1)

        # output is correct format
        self.assertEqual(stance.shape, stance_exp.shape)


    def test_standing_or_not(self):
        '''
        Tests include:
            -outputs have appropriate formatting
            -outputs have expected results according to known input
                - short interruptions of standing are smoothed over
                - long interruptions of standing are judged as not standing
            -data is classified either as standing OR not standing
        '''
        hz = 2
        hip_eul = np.array([[0, -180, 0], [0, -165, 0], [0, -150, 0], [0, -135, 0],
                            [0, -120, 0], [0, -105, 0], [0, -90, 0], [0, -75, 0],
                            [0, -60, 0], [0, -45, 0], [0, -30, 0], [0, -180, 0],
                            [0, 0, 0], [0, 15, 0], [0, 30, 0], [0, 45, 0], [0, 60, 0],
                            [0, 75, 0], [0, 90, 0], [0, 105, 0], [0, 120, 0],
                            [0, 135, 0], [0, 150, 0], [0, 165, 0], [0, 180, 0]])
        hip_eul2 = np.array([[0, -180, 0], [0, -165, 0], [0, -150, 0], [0, -135, 0],
                            [0, -120, 0], [0, -105, 0], [0, -90, 0], [0, -75, 0],
                            [0, -60, 0], [0, -45, 0], [0, -100, 0], [0, -180, 0],
                            [0, 0, 0], [0, 15, 0], [0, 30, 0], [0, 45, 0], [0, 60, 0],
                            [0, 75, 0], [0, 90, 0], [0, 105, 0], [0, 120, 0],
                            [0, 135, 0], [0, 150, 0], [0, 165, 0], [0, 180, 0]])
        hip_eul = hip_eul * np.pi / 180
        hip_eul2 = hip_eul2 * np.pi / 180
        standing, not_standing = ma.standing_or_not(hip_eul, hz)
        standing2, not_standing2 = ma.standing_or_not(hip_eul2, hz)
        standing_exp = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1,
                                 1, 1, 1, 1, 0, 0, 0, 0, 0, 0]).reshape(-1, 1).astype(float)
        not_standing_exp = np.zeros((standing_exp.shape))
        not_standing_exp[standing_exp == 0] = 1
        summed_results = standing + not_standing

        # outputs have appropriate formatting
        self.assertEqual(standing.shape, (len(hip_eul), 1))
        self.assertEqual(not_standing.shape, (len(hip_eul), 1))

        # outputs have expected results according to known input
            # variety of positions, standing interrupted by position short
            # enough to be deemed noise w.r.t. frequency
        self.assertTrue(np.allclose(standing, standing_exp))
        self.assertTrue(np.allclose(not_standing, not_standing_exp))
            # variety of positions, standing interrupted by position long
            # enough to be deemed not_standing in middle
        self.assertFalse(np.allclose(standing2, standing_exp))
        self.assertFalse(np.allclose(not_standing2, not_standing_exp))

        # data is classified either as standing OR not standing
        self.assertTrue(np.all(summed_results == 1))

    def test_sort_phases(self):
        '''
        Tests include:
            -outputs are correct format
            -outputs are expected given known inputs
                - single leg balance, take offs, and impacts are appropriately
                detected, with some exceptions if double leg
                - when single leg activities overlap or occur within a radius
                of 3 samples of each other (within same category), double leg
                activity is registered
                - feet eliminated is recognized
                - not standing data is recognized
        '''
        hz = 4
        lf_ph = np.array([0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 2, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1,
                          2, 3, 1, 1, 2, 0, 0, 0, 0, 1, 0, 0, 0, 3, 0, 0, 1, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 3]).reshape(-1, 1)
        rf_ph = np.array([1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 2,
                          2, 1, 3, 1, 1, 0, 0, 0, 0, 2, 0, 0, 0, 1, 0, 0, 3, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 1]).reshape(-1, 1)
        not_standing = np.array([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                                 0,0,0,0,0,0,1,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                                 0,0,0,0,0]).reshape(-1, 1)
        hacc = np.ones(not_standing.shape)
        hacc[6] = 3
        LDB, RDB, DDB, LSB, RSB, DSB, LI, RI, DI, LT, RT, DT, FE = ma.sort_phases(lf_ph, rf_ph, not_standing, hz, hacc)

        fe_exp = np.array([0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,1,0,0,0,0,
                           0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                           0,0]).reshape(-1, 1)
        ldb_exp = np.array([1,1,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,	0,0,0]).reshape(-1, 1)
        rdb_exp = np.array([0,0,1,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0]).reshape(-1, 1)
        ddb_exp = np.array([0,0,0,0,0,0,0,0,0,0,1,1,0,0,1,1,1,1,1,1,0,0,1,1,1,
                            0,0,0,0,0,0,1,0,0,0,0,1,1,1,0,1,1,0,1,1,1,1,0,1,1,
                            1,1,1,0]).reshape(-1, 1)
        lsb_exp = np.array([0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0]).reshape(-1, 1)
        rsb_exp = np.array([0,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0]).reshape(-1, 1)
        dsb_exp = np.array([0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,0,0,1,1,1,
                            0,0,0,0,0,0,1,0,0,0,1,1,1,1,0,0,0,0,1,1,1,1,1,1,1,
                            1,1,1,1]).reshape(-1, 1)
        li_exp = np.array([0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,
                           1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                           0,0]).reshape(-1, 1)
        ri_exp = np.array([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,
                           1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                           0,0]).reshape(-1, 1)
        di_exp = np.array([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,
                           1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                           0,0]).reshape(-1, 1)
        lt_exp = np.array([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                           0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,
                           0,1]).reshape(-1, 1)
        rt_exp = np.array([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                           0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,
                           0,0]).reshape(-1, 1)
        dt_exp = np.array([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                           ,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,
                           0,0,0]).reshape(-1, 1)

        # outputs are correct format
        self.assertEqual(LDB.shape, lf_ph.shape)
        self.assertEqual(RDB.shape, lf_ph.shape)
        self.assertEqual(DDB.shape, lf_ph.shape)
        self.assertEqual(LSB.shape, lf_ph.shape)
        self.assertEqual(RSB.shape, lf_ph.shape)
        self.assertEqual(DSB.shape, lf_ph.shape)
        self.assertEqual(LI.shape, lf_ph.shape)
        self.assertEqual(RI.shape, lf_ph.shape)
        self.assertEqual(DI.shape, lf_ph.shape)
        self.assertEqual(LT.shape, lf_ph.shape)
        self.assertEqual(RT.shape, lf_ph.shape)
        self.assertEqual(DT.shape, lf_ph.shape)
        self.assertEqual(FE.shape, lf_ph.shape)
        
        # output has expected results given known inputs
        self.assertTrue(np.allclose(LDB, ldb_exp))
        self.assertTrue(np.allclose(RDB, rdb_exp))
        self.assertTrue(np.allclose(DDB, ddb_exp))
        self.assertTrue(np.allclose(LSB, lsb_exp))
        self.assertTrue(np.allclose(RSB, rsb_exp))
        self.assertTrue(np.allclose(DSB, dsb_exp))
        self.assertTrue(np.allclose(LI, li_exp))
        self.assertTrue(np.allclose(RI, ri_exp))
        self.assertTrue(np.allclose(DI, di_exp))
        self.assertTrue(np.allclose(LT, lt_exp))
        self.assertTrue(np.allclose(RT, rt_exp))
        self.assertTrue(np.allclose(DT, dt_exp))
        self.assertTrue(np.allclose(FE, fe_exp))

    def test_num_runs(self):
        '''
        Tests include:
            -output appropriately indexes runs of consecutive repetitions of
            the chosen value
        '''
        test = np.array([1, 1, 1, 2, 3, 2, 2, 2, 1, 0, 5, 3, 3, 5, 5, 0])
        runs_0 = ma._num_runs(test, 0)
        runs_1 = ma._num_runs(test, 1)
        runs_2 = ma._num_runs(test, 2)
        runs_3 = ma._num_runs(test, 3)
        runs_5 = ma._num_runs(test, 5)
        
        # output matches expectation of known array
        self.assertTrue(np.allclose(runs_0, np.array([[9, 10], [15, 16]])))
        self.assertTrue(np.allclose(runs_1, np.array([[0, 3], [8, 9]])))
        self.assertTrue(np.allclose(runs_2, np.array([[3, 4], [5, 8]])))
        self.assertTrue(np.allclose(runs_3, np.array([[4, 5], [11, 13]])))
        self.assertTrue(np.allclose(runs_5, np.array([[10, 11], [13, 15]])))

    def test_total_accel(self):
        '''
        Tests include:
            -output matches expectation of known input vectors
        '''
        test1 = np.array([[0, 0, 1], [0, 1, 0], [1, 0, 0]])
        test1mag = ma.total_accel(test1)
        test1exp = np.array([[1], [1], [1]])
        test0 = np.array([[0, 0, 0], [0, 0, 0], [0, 0, 0]])
        test0mag = ma.total_accel(test0)
        test0exp = np.array([[0], [0], [0]])
        test1_v2 = np.array([[1/np.sqrt(2), 0, 1/np.sqrt(2)],
                            [1/np.sqrt(2), 1/np.sqrt(2), 0],
                            [0, 1/np.sqrt(2), 1/np.sqrt(2)]])
        test1mag_v2 = ma.total_accel(test1_v2)
        test1_v3 = np.array([[1/np.sqrt(3), 1/np.sqrt(3), 1/np.sqrt(3)],
                            [1/np.sqrt(3), 1/np.sqrt(3), 1/np.sqrt(3)],
                            [1/np.sqrt(3), 1/np.sqrt(3), 1/np.sqrt(3)]])
        test1mag_v3 = ma.total_accel(test1_v3)
        
        # output matches expectation of known input vectors
        self.assertTrue(np.allclose(test1mag, test1exp))
        self.assertTrue(np.allclose(test0mag, test0exp))
        self.assertTrue(np.allclose(test1mag_v2, test1exp))
        self.assertTrue(np.allclose(test1mag_v3, test1exp))

    def test_enumerate_stance(self):
        '''
        Tests include:
            - output is properly formatted
            - results are expected given known input
        '''
        hz = 4
        lf_ph = np.array([0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 2, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1,
                          2, 3, 1, 1, 2, 0, 0, 0, 0, 1, 0, 0, 0, 3, 0, 0, 1, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 3]).reshape(-1, 1)
        rf_ph = np.array([1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 2,
                          2, 1, 3, 1, 1, 0, 0, 0, 0, 2, 0, 0, 0, 1, 0, 0, 3, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 1]).reshape(-1, 1)
        not_standing = np.array([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                                 0,0,0,0,0,0,1,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                                 0,0,0,0,0]).reshape(-1, 1)
        hacc = np.ones(not_standing.shape)
        hacc[6] = 3
        LDB, RDB, DDB, LSB, RSB, DSB, LI, RI, DI, LT, RT, DT, FE = ma.sort_phases(lf_ph, rf_ph, not_standing, hz, hacc)
        stance = ma.enumerate_stance(LDB, RDB, DDB, LSB, RSB, DSB, LI, RI, DI, LT, RT, DT, FE)
        stance_exp = np.array([2,2,2,2,4,4,2,4,4,4,3,3,2,1,5,5,5,5,5,5,1,1,5,5,
                               5,3,3,2,2,1,2,5,0,0,0,2,5,5,5,2,3,3,2,5,5,5,5,3,
                               5,5,5,5,5,2]).reshape(-1, 1)
        # output is properly formatted
        self.assertEqual(stance.shape, lf_ph.shape)

        # output is expected given known input
        self.assertTrue(np.allclose(stance, stance_exp))


class TestBalanceCME(unittest.TestCase):
    '''
    Tests include:
        --test_calculate_rot_CMEs
            -output formatting is correct
            -output matches expected results given known arrays
                - when measure should be made against 'neutral' position
                - when measuure should be taken as is
        --test__cont_rot_CME
            -output formatting is appropriate
            -output matches expected results given known arrays
        --test__filt_rot_CME
            -output formatting is appropriate
            -output matches expected results given known arrays
    '''

    def test_calculate_rot_CMEs(self):
        '''
        Tests include:
            -output formatting is correct
            -output matches expected results given known arrays
                - when measure should be made against 'neutral' position
                - when measuure should be taken as is
        '''
        measure = qc.euler_to_quat(np.array([[0, 0, 45], [0, 45, 0], [45, 0, 0],
                                   [0, 0, 45], [0, 45, 0], [45, 0, 0], [0, 0, 45],
                                   [0, 45, 0], [45, 0, 0], [0, 0, 45], [0, 45, 0],
                                   [45, 0, 0], [0, 0, 0], [0, 0, 0],
                                   [-15, -30, -75]]) * np.pi/180)
        phase_lf = np.array([[0], [0], [0], [0], [0], [0], [1], [1], [1], [2], [2],
                          [2], [0], [3], [2]])
        phase_rf = np.array([[0], [0], [0], [1], [1], [1], [0], [0], [0], [1], [1],
                          [1], [0], [1], [1]])
        result = np.array([[0, 0, 45], [0, 45, 0], [45, 0, 0], [0, 0, 45],
                           [0, 45, 0], [45, 0, 0], [np.nan, np.nan, np.nan],
                           [np.nan, np.nan, np.nan], [np.nan, np.nan, np.nan],
                           [0, 0, 45], [0, 45, 0], [45, 0, 0], [0, 0, 0],
                           [np.nan, np.nan, np.nan], [-15, -30, -75]])
        targ_contra_hd_lf = -np.array([0, 0, 45, 0, 0, 45, np.nan, np.nan,
                                       np.nan, 0, 0, 45, 0, 0, -15])
        targ_ankle_rot_lf = targ_contra_hd_lf
        targ_contra_hd_rf = np.array([0, 0, 45, np.nan, np.nan, np.nan, 0, 0,
                                      45, np.nan, np.nan, np.nan, 0, np.nan, np.nan])
        targ_ankle_rot_rf = targ_contra_hd_rf
        targ_foot_pos_lf = -np.array([0, 0, 0, 0, 0, 0, np.nan, np.nan, np.nan,
                                      0, 0, 0, 0, 0, 0])
        targ_foot_pos_rf = np.array([0, 0, 0, np.nan, np.nan, np.nan, 0, 0, 0,
                                     np.nan, np.nan, np.nan, 0, np.nan, np.nan])
        contra_hd_lf, contra_hd_rf, ankle_rot_lf, ankle_rot_rf, foot_pos_lf, \
        foot_pos_rf = cmed.calculate_rot_CMEs(measure, measure, measure, phase_lf,
                                              phase_rf)

        # output formatting is correct
        self.assertEqual(contra_hd_lf.shape, result[:, 0].shape)
        self.assertEqual(contra_hd_rf.shape, result[:, 0].shape)
        self.assertEqual(ankle_rot_lf.shape, result[:, 0].shape)
        self.assertEqual(ankle_rot_rf.shape, result[:, 0].shape)
        self.assertEqual(foot_pos_lf.shape, result[:, 0].shape)
        self.assertEqual(foot_pos_rf.shape, result[:, 0].shape)

        # output matches expected results given known arrays
        self.assertTrue(np.allclose(targ_contra_hd_lf, contra_hd_lf, equal_nan=True))
        self.assertTrue(np.allclose(targ_contra_hd_rf, contra_hd_rf, equal_nan=True))
        self.assertTrue(np.allclose(targ_ankle_rot_lf, ankle_rot_lf, equal_nan=True))
        self.assertTrue(np.allclose(targ_ankle_rot_rf, ankle_rot_rf, equal_nan=True))
        self.assertTrue(np.allclose(targ_foot_pos_lf, foot_pos_lf, equal_nan=True))
        self.assertTrue(np.allclose(targ_foot_pos_rf, foot_pos_rf, equal_nan=True))

    def test__cont_rot_CME(self):
        '''
        Tests include:
            -output formatting is appropriate
            -output matches expected results given known arrays
        '''
        measure = qc.euler_to_quat(np.array([[0, 0, 45], [0, 45, 0], [0, 0, 0],
                                   [0, 0, 45], [0, 45, 0], [45, 0, 0], [0, 0, 45],
                                   [0, 45, 0], [45, 0, 0], [0, 0, 45], [0, 45, 0],
                                   [45, 0, 0], [0, 0, 0], [0, 0, 0],
                                   [-15, -30, -75]]) * np.pi/180)
        phase = np.array([[0], [0], [0], [0], [0], [0], [1], [1], [1], [2], [2],
                          [2], [0], [3], [2]])
        neutral = qc.euler_to_quat(np.array([[0, 0, 0], [0, 30, 0], [0, 0, -10],
                                   [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0],
                                   [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0],
                                   [0, 0, 0], [0, 0, 0], [0, 0, 0],
                                   [-15, -30, -75]]) * np.pi/180)
        result = np.array([[0, 0, -45], [0, -15, 0], [0, 0, -10], [0, 0, -45],
                           [0, -45, 0], [-45, 0, 0], [np.nan, np.nan, np.nan],
                           [np.nan, np.nan, np.nan], [np.nan, np.nan, np.nan],
                           [0, 0, -45], [0, -45, 0], [-45, 0, 0], [0, 0, 0],
                           [np.nan, np.nan, np.nan], [0, 0, 0]])
        test = cmed._cont_rot_CME(measure, phase, [0, 2], neutral)

        # output formatting is appropriate
        self.assertTrue(test.shape, result.shape)

        # output matches expected results given known arrays
        self.assertTrue(np.allclose(test, result, equal_nan=True))

    def test__filt_rot_CME(self):
        '''
        Tests include:
            -output formatting is appropriate
            -output matches expected results given known arrays
        '''
        measure = qc.euler_to_quat(np.array([[0, 0, 45], [0, 45, 0], [45, 0, 0],
                                   [0, 0, 45], [0, 45, 0], [45, 0, 0], [0, 0, 45],
                                   [0, 45, 0], [45, 0, 0], [0, 0, 45], [0, 45, 0],
                                   [45, 0, 0], [0, 0, 0], [0, 0, 0],
                                   [-15, -30, -75]]) * np.pi/180)
        phase = np.array([[0], [0], [0], [0], [0], [0], [1], [1], [1], [2], [2],
                          [2], [0], [3], [2]])
        result = np.array([[0, 0, 45], [0, 45, 0], [45, 0, 0], [0, 0, 45],
                           [0, 45, 0], [45, 0, 0], [np.nan, np.nan, np.nan],
                           [np.nan, np.nan, np.nan], [np.nan, np.nan, np.nan],
                           [0, 0, 45], [0, 45, 0], [45, 0, 0], [0, 0, 0],
                           [np.nan, np.nan, np.nan], [-15, -30, -75]])
        test = cmed._filt_rot_CME(measure, phase, [0, 2])

        # output formatting is appropriate
        self.assertTrue(test.shape, result.shape)

        # output matches expected results given known arrays
        self.assertTrue(np.allclose(test, result, equal_nan=True))


class TestRunRelativeCMEs(unittest.TestCase):
    '''
    Tests included:
        --test_run_relative_CMEs
            -properly executes full data file. subfunction operations are
                tested individually below
            -relative CME columns added
        --test__drift_agnostic_CMES
            -output is appropriately formatted
            -output matches expectation given known input
               -values align
               -values filled where relevant
               -values = nan where irrelevant
        --test__driftless_CMS
            -output is appropriately formatted
            -output matches expectation given known input
               -values align
               -values filled where relevant
               -values = nan where irrelevant
        --test__norm_range_of_motion
            -ouput is appropriately formatted
            -output matches expectation given known input
        --test__norm_motion_covered
            -ouput is appropriately formatted
            -output matches expectation given known input
        --test__rough_contact_duration
            -ouput is appropriately formatted
            -output matches expectation knowing known input
                - contact and non contact stretches, all possible stances
                represented
        --test__num_runs
            -output appropriately indexes runs of consecutive repetitions of
            the chosen value
        --test__detect_long_dynamic
            -output is appropriately formatted
            -output matches expectation given known input
        --test__zero_runs
            -output is appropriately formatted
            -output matches expectation given known input
        --test__filter_data
            -output is appropriately formatted
            -output matches expectation given known input
        --test__remove_filtered_ends
            -output is formatted appropriately
            -output matches expectation when given known inputs
                -trims rows when dynamic activity ends near end
                -splits rows when dynamic activity ends in middle
                -retains rows when no dynamic activity change
                -deletes rows when too short to trim or split

        
    '''
    def test_run_relative_CMEs(self):
        '''
        Tests include:
            -properly executes full data file. subfunction operations are
                tested individually below.
            -relative CME columns added
        '''
        test_file = 'stance_phase_a1bf8bad_transformed_short.csv'
        test_data = pd.read_csv(test_file)
        columns = test_data.columns
        data = do.RawFrame(copy.deepcopy(test_data), columns)
        data = rcme.run_relative_CMEs(data)

        # relative cme columns added
        self.assertFalse(test_data.__dict__ == data.__dict__)

    def test__drift_agnostic_CMES(self):
        '''
        Tests include:
            -output is appropriately formatted
            -output matches expectation given known input
               -values align
               -values filled where relevant
               -values = nan where irrelevant
        '''
        cme = np.empty(10).reshape(-1, 1) * np.nan
        ranges = np.array([[0, 2], [6, 9]])
        stance = np.ones((10, 1)) + 3
        calc_cme = rcme._drift_agnostic_CMES(cme, ranges, stance)
        exp_cme = np.array([2, 2, np.nan, np.nan, np.nan, np.nan, 3, 3, 3,
                            np.nan]).reshape(-1, 1)/1000.0
        # output is appropriately formatted
        self.assertEqual(calc_cme.shape, exp_cme.shape)

        # output matches expectation given known input
            # values align and filled only where relevant
        self.assertTrue(np.allclose(calc_cme, exp_cme, equal_nan=True))

    def test__driftless_CMS(self):
        '''
        Tests include:
            -output is appropriately formatted
            -output matches expectation given known input
        '''
        data = np.array([0, 1, 2, 4, 6, 3, -2, -6, -2, 5])
        cov = np.empty(10).reshape(-1, 1) * np.nan
        cov_pos = np.empty(10).reshape(-1, 1) * np.nan
        cov_neg = np.empty(10).reshape(-1, 1) * np.nan
        ran = np.empty(10).reshape(-1, 1) * np.nan
        ranges = np.array([[0, 2], [4, 9]])
        time = np.ones((10, 1)) + 9
        calc_mot_abs, calc_mot_pos, calc_mot_neg, calc_range = rcme._driftless_CMES(data, ranges, time, cov, cov_pos, cov_neg, ran)
        targ_mot_abs = np.array([50, 50, np.nan, np.nan, 320, 320, 320, 320,
                             320, np.nan]).reshape(-1, 1)
        targ_mot_pos = np.array([50, 50, np.nan, np.nan, 80, 80, 80, 80,
                             80, np.nan]).reshape(-1, 1)
        targ_mot_neg = np.array([0, 0, np.nan, np.nan, -240, -240, -240, -240,
                                 -240, np.nan]).reshape(-1, 1)
        targ_range = np.array([50, 50, np.nan, np.nan, 240, 240, 240, 240, 240,
                               np.nan]).reshape(-1, 1)

        # output is appropriately formatted
        self.assertEqual(calc_mot_abs.shape, targ_mot_abs.shape)
        self.assertEqual(calc_mot_pos.shape, targ_mot_pos.shape)
        self.assertEqual(calc_mot_neg.shape, targ_mot_neg.shape)
        self.assertEqual(calc_range.shape, targ_range.shape)

        # output matches expectation given known input
        self.assertTrue(np.allclose(calc_mot_abs, targ_mot_abs, equal_nan=True))
        self.assertTrue(np.allclose(calc_mot_pos, targ_mot_pos, equal_nan=True))
        self.assertTrue(np.allclose(calc_mot_neg, targ_mot_neg, equal_nan=True))
        self.assertTrue(np.allclose(calc_range, targ_range, equal_nan=True))

    def test__norm_range_of_motion(self):
        '''
        Tests include:
            -ouput is appropriately formatted
            -output matches expectation given known input
        '''
        data1 = np.array([1, 1, 1, 1, 1]).reshape(-1, 1)
        data2 = np.array([1, 2, 3, 2, 5]).reshape(-1, 1)
        data3 = np.array([0, 0, 0, 0, 0]).reshape(-1, 1)
        data4 = np.array([np.nan, np.nan, np.nan, np.nan, np.nan]).reshape(-1, 1)
        time = np.array([10., 10., 10., 10., 10.]).reshape(-1, 1)
        res1 = rcme._norm_range_of_motion(data1, time)
        res2 = rcme._norm_range_of_motion(data2, time)
        res3 = rcme._norm_range_of_motion(data3, time)
        res4 = rcme._norm_range_of_motion(data4, time)
        targ1 = data3
        targ2 = np.array([80, 80, 80, 80, 80]).reshape(-1, 1)
        targ3 = data3
        targ4 = data4

        # output is appropriately formatted
        self.assertEqual(data1.shape, res1.shape)

        # output matches expectation given known input
        self.assertTrue(np.allclose(res1, targ1))
        self.assertTrue(np.allclose(res2, targ2))
        self.assertTrue(np.allclose(res3, targ3))
        self.assertTrue(np.allclose(res4, targ4, equal_nan=True))

    def test__norm_motion_covered(self):
        '''
        Tests include:
            -ouput is appropriately formatted
            -output matches expectation given known input
        '''
        data1 = np.array([1, 1, 1, 1, 1]).reshape(-1, 1)
        data2 = np.array([1, 2, 3, 2, 5]).reshape(-1, 1)
        data3 = np.array([0, 0, 0, 0, 0]).reshape(-1, 1)
        time = np.array([10., 10., 10., 10., 10.]).reshape(-1, 1)
        res1 = rcme._norm_motion_covered(data1, time, 'abs')
        res2 = rcme._norm_motion_covered(data2, time, 'abs')
        res3 = rcme._norm_motion_covered(data3, time, 'abs')
        targ1 = data3
        targ2 = np.array([120, 120, 120, 120, 120]).reshape(-1, 1)
        targ3 = data3

        # output is appropriately formatted
        self.assertEqual(data1.shape, res1.shape)

        # output matches expectation given known input
        self.assertTrue(np.allclose(res1, targ1))
        self.assertTrue(np.allclose(res2, targ2))
        self.assertTrue(np.allclose(res3, targ3))

    def test__rough_contact_duration(self):
        '''
        Tests include:
            -ouput is appropriately formatted
            -output matches expectation knowing known input
                - contact and non contact stretches, all possible stances
                represented
        '''
        stance = np.array([0, 0, 1, 0, 0, 3, 3, 3, 2, 2, 4, 4, 0, 3, 5, 5, 5,
                           5, 5, 2, 1, 0, 2, 2, 3, 2, 2, 2, 3, 1, 1, 3]).reshape(-1, 1)
        targ = np.array([np.nan, np.nan, np.nan, np.nan, np.nan, 7, 7, 7, 7,
                         7, 7, 7, np.nan, 7, 7, 7, 7, 7, 7, 7, np.nan, np.nan,
                         7, 7, 7, 7, 7, 7, 7, np.nan, np.nan,
                         1]).reshape(-1, 1)/1000.0
        test = rcme._rough_contact_duration(stance)

        # output is formatted appropriately
        self.assertEqual(stance.shape, test.shape)
        # output matches expectation given known input
        self.assertTrue(np.allclose(test, targ, equal_nan=True))

    def test__num_runs(self):
        '''
        Tests include:
            -output appropriately indexes runs of consecutive repetitions of
            the chosen value
        '''
        test = np.array([1, 1, 1, 2, 3, 2, 2, 2, 1, 0, 5, 3, 3, 5, 5, 0])
        runs_0 = rcme._get_ranges(test, 0)
        runs_1 = rcme._get_ranges(test, 1)
        runs_2 = rcme._get_ranges(test, 2)
        runs_3 = rcme._get_ranges(test, 3)
        runs_5 = rcme._get_ranges(test, 5)
        
        # output matches expectation of known array
        self.assertTrue(np.allclose(runs_0, np.array([[9, 10]])))
        self.assertTrue(np.allclose(runs_1, np.array([[0, 3], [8, 9]])))
        self.assertTrue(np.allclose(runs_2, np.array([[3, 4], [5, 8]])))
        self.assertTrue(np.allclose(runs_3, np.array([[4, 5], [11, 13]])))
        self.assertTrue(np.allclose(runs_5, np.array([[10, 11], [13, 15]])))

    def test__detect_long_dynamic(self):
        '''
        Tests include:
            -output appropriately formatted
            -output matches expectations given known inputs
        '''
        flag1 = np.zeros((100000, 1))
        flag1[5:8] = 8
        flag1[15:18] = 8
        flag1[25:28] = 8
        flag1[35:38] = 8
        flag1[45:48] = 8
        calc_range1 = rcme._detect_long_dynamic(flag1)
        flag2 = flag1
        flag2[1000:2000] = 8
        flag2[2500:5000] = 8
        flag2[10000:30000] = 8
        calc_range2 = rcme._detect_long_dynamic(flag2)
        exp_range2 = np.array([[1000, 2000], [2500, 5000], [10000, 30000]])
        
        # output appropriately formatted
        self.assertEqual(exp_range2.shape[1], 2)
        
        # output matches expectations given known inputs
        self.assertTrue(calc_range1.size == 0)
        self.assertTrue(np.allclose(calc_range2, exp_range2))

    def test__zero_runs(self):
        '''
        Tests include:
            -output is appropriately formatted
            -output matches expectation given known input
        '''
        data1 = np.array([0, 0, np.nan, 1, 1, 1, 2, 1, 1, 0]).reshape(-1, 1)
        data2 = np.array([1, 0, 0, 1, 1, 1, 2, 1, 1, 1]).reshape(-1, 1)
        ranges1, length1 = rcme._get_ranges(data1, 1, True)
        ranges2, length2 = rcme._get_ranges(data2, 1, True)
        targ_ranges1 = np.array([[3, 6], [7, 9]])
        targ_len1 = np.array([3, 2])
        targ_ranges2 = np.array([[0, 1], [3, 6], [7, 9]])
        targ_len2 = np.array([1, 3, 2])

        # output is appropriately formatted
        self.assertEqual(ranges1.shape, targ_ranges1.shape)
        self.assertEqual(len(ranges1), len(length1))

        # output matches expectation given known input
        self.assertTrue(np.allclose(ranges1, targ_ranges1, equal_nan=True))
        self.assertTrue(np.allclose(length1, targ_len1, equal_nan=True))
        self.assertTrue(np.allclose(ranges2, targ_ranges2, equal_nan=True))
        self.assertTrue(np.allclose(length2, targ_len2, equal_nan=True))

    def test__filter_data(self):
        '''
        Tests include:
            -output is appropriately formatted
            -output matches expectation given known input
        '''
        import numpy.polynomial.polynomial as poly

        Fs = 100
        x = np.arange(500)
        s0_01 = np.sin(2*np.pi*0.01*x/Fs)
        s0_1 = np.sin(2*np.pi*0.1*x/Fs)
        s0_5 = np.sin(2*np.pi*0.5*x/Fs)
        s1 = np.sin(2*np.pi*1*x/Fs)
        s5 = np.sin(2*np.pi*5*x/Fs)
        s20 = np.sin(2*np.pi*20*x/Fs)
        s30 = np.sin(2*np.pi*30*x/Fs)
        fs0_01 = rcme._filter_data(s0_01).reshape(1, len(x))
        fs0_1 = rcme._filter_data(s0_1).reshape(1, len(x))
        fs0_5 = rcme._filter_data(s0_5).reshape(1, len(x))
        fs1 = rcme._filter_data(s1).reshape(1, len(x))
        fs5 = rcme._filter_data(s5).reshape(1, len(x))
        fs20 = rcme._filter_data(s20).reshape(1, len(x))
        fs30 = rcme._filter_data(s30).reshape(1, len(x))
        lfs0_1 = rcme._filter_data(s0_1, filt='low').reshape(1, len(x))
        
        def _polyfit(x, y, degree):
            results = {}
            coeffs = poly.polyfit(x.T, y.T, degree)
            results['polynomial'] = coeffs.tolist()
            return results

        res0_01 = _polyfit(x, fs0_01, 1)
        slopes0_01 = np.abs(np.array(res0_01['polynomial'][1]))
        res0_1 = _polyfit(x, fs0_1, 1)
        slopes0_1 = np.abs(np.array(res0_1['polynomial'][1]))
        res0_5 = _polyfit(x, fs0_5, 1)
        slopes0_5 = np.abs(np.array(res0_5['polynomial'][1]))
        res1 = _polyfit(x, fs1, 1)
        slopes1 = np.abs(np.array(res1['polynomial'][1]))
        res5 = _polyfit(x, fs5, 1)
        slopes5 = np.abs(np.array(res5['polynomial'][1]))
        res20 = _polyfit(x, fs20, 1)
        slopes20 = np.abs(np.array(res20['polynomial'][1]))
        res30 = _polyfit(x, fs30, 1)
        slopes30 = np.abs(np.array(res30['polynomial'][1]))

        # output is appropriately formatted
        self.assertEqual(rcme._filter_data(s0_01).shape, x.shape)

        # output matches expectation given known input
            # signals with frequencies to be rejected are smoothed by filter
        self.assertTrue(slopes0_01 < 0.00055)
        self.assertTrue(slopes0_1 < 0.00055)
        self.assertFalse(slopes0_5 < 0.00055)
        self.assertFalse(slopes1 < 0.00055)
        self.assertFalse(slopes5 < 0.00055)
        self.assertTrue(slopes20 < 0.00055)
        self.assertTrue(slopes30 < 0.00055)
        self.assertFalse(np.allclose(lfs0_1.reshape(-1, 1), fs0_1))
        self.assertTrue(np.max(s0_1-lfs0_1) < 0.0005)

    def test__remove_filtered_ends(self):
        '''
        Tests include:
            -output is formatted appropriately
            -output matches expectation when given known inputs
                -trims rows when dynamic activity ends near end
                -splits rows when dynamic activity ends in middle
                -retains rows when no dynamic activity change
                -deletes rows when too short to trim or split
        '''
        data_range = np.array([[0, 5], [15, 25], [30, 40], [50, 60], [67, 75],
                               [80, 82], [85, 100]])
        dyn_range = np.array([[3, 16], [25, 30], [35, 56], [79, 81], [90, 99]])
        trimmed_ends = rcme._remove_filtered_ends(data_range, dyn_range)
        exp_trim = np.array([[0, 5], [18, 25], [33, 40], [50, 54], [58, 60],
                             [67, 75], [85, 97]])

        # output is formatted appropriately
        self.assertEqual(trimmed_ends.shape[1], 2)
        
        # output matches expectations given known inputs
            #    -trims rows when dynamic activity ends near end
            #    -splits rows when dynamic activity ends in middle
            #    -retains rows when no dynamic activity change
            #    -deletes rows when too short to trim or split
        self.assertTrue(np.allclose(trimmed_ends, exp_trim))


class TestImpactCMEs(unittest.TestCase):
    '''
    Tests include:
        --test_sync_time
            -output is appropriately formatted
            -output matches expectation given known input
                -impacts within (1/3) sampling rate ordered, others ignored
        --test_landing_pattern
        --test_continuous_values
    '''
    def test_sync_time(self):
        '''
        Tests include:
            -output is appropriately formatted
            -output matches expectation given known input
                -impacts within (1/3) sampling rate ordered, others ignored
        '''
        rf_start = np.array([0., 100., 200., 300., 400., 500., 600., 700., 800., 900., 1000.])
        lf_start = np.array([5., 95., 200., 350., 490., 510., 599., 601., 705., 797., 907., 993.])
        sampl_rate = 100
        diff, ltime_index, lf_rf_imp_indicator = imp.sync_time(rf_start, lf_start, sampl_rate)
        exp_diff = np.array([-50, 50, 0, 100, -100, 10, -10, -50, 30, -70, 70]).reshape(-1, 1)
        exp_ltime_index = np.array([0, 95, 200, 490, 500, 599, 600, 700, 797,
                                    900, 993]).reshape(-1, 1)
        exp_lf_rf_imp_indicator = np.array(['r', 'l', 'n', 'l', 'r', 'l', 'r',
                                            'r', 'l', 'r', 'l'])

        # output is appropriately formatted
        self.assertEqual(len(diff), len(ltime_index))
        self.assertEqual(len(diff), len(lf_rf_imp_indicator))
        self.assertEqual(diff.shape[1], 1)
        self.assertEqual(ltime_index.shape[1], 1)
        self.assertEqual(lf_rf_imp_indicator.shape[1], 1)

        # output matches expectation given known input
        self.assertTrue(np.allclose(diff, exp_diff))
        self.assertTrue(np.allclose(ltime_index, exp_ltime_index))
        self.assertTrue(set(lf_rf_imp_indicator.reshape(len(
                lf_rf_imp_indicator), )).issubset(exp_lf_rf_imp_indicator))
        self.assertTrue(set(exp_lf_rf_imp_indicator).issubset(
                lf_rf_imp_indicator.reshape(len(lf_rf_imp_indicator), )))

    def test_landing_pattern(self):
        '''
        Tests include:
            -output is appropriately formatted
            -output matches expectation given known input

        '''
        rf_start = np.array([0., 100., 200., 300., 400., 500., 600., 700., 800., 900., 1000.])
        lf_start = np.array([5., 95., 200., 350., 490., 510., 599., 601., 705., 797., 907., 993.])
        sampl_rate = 100
        diff, ltime_index, lf_rf_imp_indicator = imp.sync_time(rf_start, lf_start, sampl_rate)
        rfy1 = np.zeros((1100,)) + np.pi/4
        lfy1 = np.zeros((1100,)) + np.pi/3
        pat1 = imp.landing_pattern(rfy1, lfy1, ltime_index, lf_rf_imp_indicator,
                                   sampl_rate, diff)
        # output is formatted appropriately
        self.assertEqual(pat1.shape, (len(diff), 2))

        # output has correct values given known input
        self.assertTrue(np.all(pat1[:, 0] == np.pi/4 * 180 / np.pi))
        self.assertTrue(np.all(pat1[:, 1] == np.pi/3 * 180 / np.pi))

    def test_continuous_values(self):
        '''
        Tests include:
            -output is appropriately formatted
            -output matches expectation given known input

        '''
        rf_start = np.array([0., 100., 200., 300., 400., 500., 600., 700., 800., 900., 1000.])
        lf_start = np.array([5., 95., 200., 350., 490., 510., 599., 601., 705., 797., 907., 993.])
        sampl_rate = 100
        diff, ltime_index, lf_rf_imp_indicator = imp.sync_time(rf_start, lf_start, sampl_rate)
        rfy1 = np.zeros((1100,)) + np.pi/4
        lfy1 = np.zeros((1100,)) + np.pi/3
        pat1 = imp.landing_pattern(rfy1, lfy1, ltime_index, lf_rf_imp_indicator,
                                   sampl_rate, diff)
        flt, flp = imp.continuous_values(pat1, diff, np.array([1100]), ltime_index)

        # output is appropriately formatted
        self.assertEqual(len(flt), 1100)
        self.assertEqual(len(flp), 1100)
        self.assertEqual(flp.shape[1], 2)

        # output is correct given known inputs
            # nan where expected
        self.assertTrue(np.where(np.isnan(flp[:, 0])), np.where(np.isnan(flp[:, 1])))
        self.assertTrue(np.where(np.isnan(flp[:, 0])), np.where(np.isnan(flt)))
            # values are appropriately maintained
        self.assertTrue(np.all(flp[np.where(~np.isnan(flp[:, 0])), 0] == np.pi/4 * 180 / np.pi))
        self.assertTrue(np.all(flp[np.where(~np.isnan(flp[:, 1])), 1] == np.pi/3 * 180 / np.pi))


class TestPhaseDetection(unittest.TestCase):
    '''
    Tests include:
        --test_combine_phase
            -rf and lf outputs appropriately formatted
            -output matches expectation given known input
        --test_body_phase
            -output appropriately formatted
            -output matches some level of expectation given known inputs
        --test__phase_detect
            -output appropriately formatted
            -output matches expectation given known input
                -smoothes false motion
                -does not smooth true motion
        --test__impact_detect
        --test__final_phases
            -output formatted appropriately
            -output matches expectation given known inputs
        --test__filter_data
            -output is appropriately formatted
            -output matches expectation given known input
    '''
    def test_combine_phase(self):
        '''
        Tests include:
            -rf and lf outputs appropriately formatted
            -output matches expectation given known input
        '''
        test_file = 'stance_phase_a1bf8bad_transformed_short.csv'
        test_data = pd.read_csv(test_file)
        raz = test_data.RaZ.values.reshape(-1, 1)
        laz = test_data.LaZ.values.reshape(-1, 1)
        rax = test_data.RaX.values.reshape(-1, 1)
        lax = test_data.LaX.values.reshape(-1, 1)
        laz[5] = np.nan
        raz[5] = np.nan
        ray = test_data.RaY.values.reshape(-1, 1)
        lay = test_data.LaY.values.reshape(-1, 1)
        rp = test_data.ReY.values.reshape(-1, 1)
        lp = test_data.LeY.values.reshape(-1, 1)
        hz = 100
        la = np.hstack((np.hstack((lax, lay)), laz))
        la_magn = ma.total_accel(la)
        ra = np.hstack((np.hstack((rax, ray)), raz))
        ra_magn = ma.total_accel(ra)
        lf, rf = phd.combine_phase(laz, raz, la_magn, ra_magn, lp, rp, hz)
        l0 = len(np.where(lf==0)[0])
        l1 = len(np.where(lf==1)[0])
        l2 = len(np.where(lf==2)[0])
        l3 = len(np.where(lf==3)[0])
        r0 = len(np.where(rf==0)[0])
        r1 = len(np.where(rf==1)[0])
        r2 = len(np.where(rf==2)[0])
        r3 = len(np.where(rf==3)[0])

        # assert lf and rf are the same, proper length
        self.assertEqual(len(lf), len(rf))
        self.assertEqual(len(lf), len(laz))

        # for this file, assume that all phases are triggered (takeoff:3 is calculated later)
        self.assertFalse(l0==0)
        self.assertFalse(l1==0)
        self.assertFalse(l2==0)
        # self.assertFalse(l3==0)
        self.assertFalse(r0==0)
        self.assertFalse(r1==0)
        self.assertFalse(r2==0)
        # self.assertFalse(r3==0)


    def test__body_phase(self):
        '''
        Tests included:
            -output appropriately formatted
            -output matches some level of expectation given known inputs
        '''
        test_file = 'stance_phase_a1bf8bad_transformed_short.csv'
        test_data = pd.read_csv(test_file)
        raz = test_data.RaZ.values.reshape(-1, 1)
        laz = test_data.LaZ.values.reshape(-1, 1)
        hz = 100
        phase_l, phase_r, sm_l, em_l, sm_r, em_r = phd._body_phase(raz, laz, hz)
        p0 = len(np.where(phase_l == 0)[0])
        p1 = len(np.where(phase_l == 1)[0])
        p2 = len(np.where(phase_l == 2)[0])
        p3 = len(np.where(phase_l == 3)[0])

        # for this file, all basic phases should be triggered
        self.assertFalse(p0 == 0)
        self.assertFalse(p1 == 0)
        self.assertTrue(p2 == 0)
        self.assertTrue(p3 == 0)

        p0 = len(np.where(phase_r == 0)[0])
        p1 = len(np.where(phase_r == 1)[0])
        p2 = len(np.where(phase_r == 2)[0])
        p3 = len(np.where(phase_r == 3)[0])

        # for this file, all basic phases should be triggered
        self.assertFalse(p0 == 0)
        self.assertFalse(p1 == 0)
        self.assertTrue(p2 == 0)
        self.assertTrue(p3 == 0)

    def test__phase_detect(self):
        '''
        Tests included:
            -output appropriately formatted
            -output matches expectation given known input
                -smoothes false motion
                -does not smooth true motion
        '''
        acc = np.ones((200, 1))
        acc[50] = 5
        acc[100:] = 5
        hz = 200
        bal = phd._phase_detect(acc, hz)
        targ = np.zeros((200, 1))
        targ[100:] = 1

        # output formatted appropriately
        self.assertEqual(len(bal), 200)
        # output matches expectation given known input
        self.assertTrue(np.allclose(bal, targ.reshape(1, -1)))


    def test__impact_detect(self):
        '''
        Tests include:
            -second column of indices always greater than first column
            
        '''
        test_file = 'stance_phase_a1bf8bad_transformed_short.csv'
        test_data = pd.read_csv(test_file)
        raz = test_data.RaZ.values.reshape(-1, 1)
        laz = test_data.LaZ.values.reshape(-1, 1)
        rp = test_data.ReY.values.reshape(-1, 1)
        lp = test_data.LeY.values.reshape(-1, 1)
        hz = 100
        phase_lf, phase_rf, sm_l, em_l, sm_r, em_r = phd._body_phase(raz, laz, hz)
        rimp = phd._impact_detect(sm_r, em_r, raz, rp, hz)
        limp = phd._impact_detect(sm_l, em_l, laz, lp, hz)
        rdiffpos = len(np.where((rimp[:, 1] - rimp[:, 0]) >= 0)[0])
        ldiffpos = len(np.where((limp[:, 1] - limp[:, 0]) >= 0)[0])

        # second column of indices always greater than first column
        self.assertEqual(rdiffpos, len(rimp))
        self.assertEqual(ldiffpos, len(limp))

    # def test__final_phases(self):
    #     '''
    #     Tests include:
    #         -output formatted appropriately
    #         -output matches expectation given known inputs
    #     '''
    #     lf1 = [0, 1, 2, 3, 4, 5]
    #     rf1 = [0, 1, 2, 3, 4, 5, 6]
    #     rf2 = [3, 1, 2, 3, 4, 5]
    #     lf2 = [4, 1, 2, 3, 4, 5]
    #     rf3 = [1, 1, 2, 3, 4, 5]
    #     lf4 = [3, 1, 2, 3, 4, 5]
    #     rf4 = [5, 1, 2, 3, 4, 5]
    #     lf5 = [2, 1, 2, 3, 4, 5]
    #     res1l, res1r = phd._final_phases(rf1, lf1)
    #     res2l, res2r = phd._final_phases(lf1, lf1)
    #     res3l, res3r = phd._final_phases(rf2, lf2)
    #     res4l, res4r = phd._final_phases(rf4, lf4)
    #
    #     # output formatted appropriately
    #     self.assertEqual(len(rf1), len(res1r))
    #     self.assertEqual(len(lf1), len(res1l))
    #
    #     # output matches expectation given known inputs
    #     self.assertTrue(np.allclose(res1r, rf1))
    #     self.assertTrue(np.allclose(res1l, lf1))
    #     self.assertTrue(np.allclose(res2l, lf1))
    #     self.assertTrue(np.allclose(res2r, lf1))
    #     self.assertTrue(np.allclose(res3l, lf2))
    #     self.assertTrue(np.allclose(res3r, rf3))
    #     self.assertTrue(np.allclose(res4l, lf5))
    #     self.assertTrue(np.allclose(res4r, rf4))
    #
        

    def test__filter_data(self):
        '''
        Tests include:
            -output is appropriately formatted
            -output matches expectation given known input
        '''
        import numpy.polynomial.polynomial as poly

        Fs = 100
        x = np.arange(500)
        s0_01 = np.sin(2*np.pi*0.01*x/Fs)
        s0_1 = np.sin(2*np.pi*0.1*x/Fs)
        s0_5 = np.sin(2*np.pi*0.5*x/Fs)
        s1 = np.sin(2*np.pi*1*x/Fs)
        s5 = np.sin(2*np.pi*5*x/Fs)
        s20 = np.sin(2*np.pi*20*x/Fs)
        s30 = np.sin(2*np.pi*30*x/Fs)
        fs0_01 = phd._filter_data(s0_01).reshape(1, len(x))
        fs0_1 = phd._filter_data(s0_1).reshape(1, len(x))
        fs0_5 = phd._filter_data(s0_5).reshape(1, len(x))
        fs1 = phd._filter_data(s1).reshape(1, len(x))
        fs5 = phd._filter_data(s5).reshape(1, len(x))
        fs20 = phd._filter_data(s20).reshape(1, len(x))
        fs30 = phd._filter_data(s30).reshape(1, len(x))
        lfs0_1 = phd._filter_data(s0_1, filt='low').reshape(1, len(x))
        
        def _polyfit(x, y, degree):
            results = {}
            coeffs = poly.polyfit(x.T, y.T, degree)
            results['polynomial'] = coeffs.tolist()
            return results

        res0_01 = _polyfit(x, fs0_01, 1)
        slopes0_01 = np.abs(np.array(res0_01['polynomial'][1]))
        res0_1 = _polyfit(x, fs0_1, 1)
        slopes0_1 = np.abs(np.array(res0_1['polynomial'][1]))
        res0_5 = _polyfit(x, fs0_5, 1)
        slopes0_5 = np.abs(np.array(res0_5['polynomial'][1]))
        res1 = _polyfit(x, fs1, 1)
        slopes1 = np.abs(np.array(res1['polynomial'][1]))
        res5 = _polyfit(x, fs5, 1)
        slopes5 = np.abs(np.array(res5['polynomial'][1]))
        res20 = _polyfit(x, fs20, 1)
        slopes20 = np.abs(np.array(res20['polynomial'][1]))
        res30 = _polyfit(x, fs30, 1)
        slopes30 = np.abs(np.array(res30['polynomial'][1]))

        # output is appropriately formatted
        self.assertEqual(rcme._filter_data(s0_01).shape, x.shape)

        # output matches expectation given known input
            # signals with frequencies to be rejected are smoothed by filter
        self.assertTrue(slopes0_01 < 0.00055)
        self.assertTrue(slopes0_1 < 0.00055)
        self.assertFalse(slopes0_5 < 0.00055)
        self.assertFalse(slopes1 < 0.00055)
        self.assertFalse(slopes5 < 0.00055)
        self.assertTrue(slopes20 < 0.00055)
        self.assertTrue(slopes30 < 0.00055)
        self.assertFalse(np.allclose(lfs0_1.reshape(-1, 1), fs0_1))
        self.assertTrue(np.max(s0_1-lfs0_1) < 0.0005)


class TestDetectImpactPhaseIntervals(unittest.TestCase):
    '''
    Tests include:
        --test_detect_start_end_imp_phase
            -outputs appropriately formatted
            -outputs match expectation given known inputs
        --test__zero_runs
            -output is appropriately formatted
            -output matches expectation given known input

    '''
    def test_detect_start_end_imp_phase(self):
        '''
        Tests include:
            -outputs appropriately formatted
            -outputs match expectation given known inputs
        '''
        test_file = 'stance_phase_a1bf8bad_transformed_short.csv'
        test_data = pd.read_csv(test_file)
        raz = test_data.RaZ.values.reshape(-1, 1)
        laz = test_data.LaZ.values.reshape(-1, 1)
        rax = test_data.RaX.values.reshape(-1, 1)
        lax = test_data.LaX.values.reshape(-1, 1)
        ray = test_data.RaY.values.reshape(-1, 1)
        lay = test_data.LaY.values.reshape(-1, 1)
        rp = test_data.ReY.values.reshape(-1, 1)
        lp = test_data.LeY.values.reshape(-1, 1)
        hz = 100
        la = np.hstack((np.hstack((lax, lay)), laz))
        la_magn = ma.total_accel(la)
        ra = np.hstack((np.hstack((rax, ray)), raz))
        ra_magn = ma.total_accel(ra)
        lf, rf = phd.combine_phase(laz, raz, la_magn, ra_magn, lp, rp, hz)
        lp[5:7] = np.nan
        l_start_stop, r_start_stop, l_range, r_range = di.detect_start_end_imp_phase(lf, rf)
        rdiffpos = len(np.where((r_range[:, 1] - r_range[:, 0]) >= 0)[0])
        ldiffpos = len(np.where((l_range[:, 1] - l_range[:, 0]) >= 0)[0])

        # second column of range indices always greater than first column
        self.assertEqual(rdiffpos, len(r_range))
        self.assertEqual(ldiffpos, len(l_range))
        
        # start_stop lists correspond to range arrays directly
        for i in range(len(l_range)):
            self.assertTrue(np.all(l_start_stop[l_range[i, 0]:l_range[i, 1]]))
        for i in range(len(r_range)):
            self.assertTrue(np.all(r_start_stop[r_range[i, 0]:r_range[i, 1]]))


    def test__zero_runs(self):
        '''
        Tests include:
            -output is appropriately formatted
            -output matches expectation given known input
        '''
        data1 = np.array([0, 0, np.nan, 1, 1, 1, 2, 1, 1, 0]).reshape(-1, 1)
        data2 = np.array([1, 0, 0, 1, 1, 1, 2, 1, 1, 1]).reshape(-1, 1)
        ranges1 = di._zero_runs(data1, 1)
        ranges2 = di._zero_runs(data2, 1)
        targ_ranges1 = np.array([[3, 6], [7, 9]])
        targ_ranges2 = np.array([[0, 1], [3, 6], [7, 10]])

        # output is appropriately formatted
        self.assertEqual(ranges1.shape, targ_ranges1.shape)

        # output matches expectation given known input
        self.assertTrue(np.allclose(ranges1, targ_ranges1, equal_nan=True))
        self.assertTrue(np.allclose(ranges2, targ_ranges2, equal_nan=True))


class TestDetectTakeoffPhaseIntervals(unittest.TestCase):
    '''
    Tests include:
        --detect_start_end_takeoff_phase
            -outputs appropriately formatted
            -outputs match expectation given known inputs
        --test__zero_runs
            -output is appropriately formatted
            -output matches expectation given known input

    '''
    def detect_start_end_takeoff_phase(self):
        '''
        Tests include:
            --outputs appropriately formatted
            -outputs match expectation given known inputs
        '''
        test_file = 'stance_phase_a1bf8bad_transformed_short.csv'
        test_data = pd.read_csv(test_file)
        raz = test_data.RaZ.values.reshape(-1, 1)
        laz = test_data.LaZ.values.reshape(-1, 1)
        rax = test_data.RaX.values.reshape(-1, 1)
        lax = test_data.LaX.values.reshape(-1, 1)
        ray = test_data.RaY.values.reshape(-1, 1)
        lay = test_data.LaY.values.reshape(-1, 1)
        rp = test_data.ReY.values.reshape(-1, 1)
        lp = test_data.LeY.values.reshape(-1, 1)
        hz = 100
        la = np.hstack((np.hstack((lax, lay)), laz))
        la_magn = ma.total_accel(la)
        ra = np.hstack((np.hstack((rax, ray)), raz))
        ra_magn = ma.total_accel(ra)
        lf, rf = phd.combine_phase(laz, raz, la_magn, ra_magn, lp, rp, hz)
        lp[5:7] = np.nan
        l_start_stop, r_start_stop, l_range, r_range = dt.detect_start_end_takeoff_phase(lf, rf)
        rdiffpos = len(np.where((r_range[:, 1] - r_range[:, 0]) >= 0)[0])
        ldiffpos = len(np.where((l_range[:, 1] - l_range[:, 0]) >= 0)[0])

        # second column of range indices always greater than first column
        self.assertEqual(rdiffpos, len(r_range))
        self.assertEqual(ldiffpos, len(l_range))
        
        # start_stop lists correspond to range arrays directly
        for i in range(len(l_range)):
            self.assertTrue(np.all(l_start_stop[l_range[i, 0]:l_range[i, 1]]))
        for i in range(len(r_range)):
            self.assertTrue(np.all(r_start_stop[r_range[i, 0]:r_range[i, 1]]))


    def test__zero_runs(self):
        '''
        Tests include:
            -output is appropriately formatted
            -output matches expectation given known input
        '''
        data1 = np.array([0, 0, np.nan, 1, 1, 1, 2, 1, 1, 0]).reshape(-1, 1)
        data2 = np.array([1, 0, 0, 1, 1, 1, 2, 1, 1, 1]).reshape(-1, 1)
        ranges1 = dt._zero_runs(data1, 1)
        ranges2 = dt._zero_runs(data2, 1)
        targ_ranges1 = np.array([[3, 6], [7, 9]])
        targ_ranges2 = np.array([[0, 1], [3, 6], [7, 10]])

        # output is appropriately formatted
        self.assertEqual(ranges1.shape, targ_ranges1.shape)

        # output matches expectation given known input
        self.assertTrue(np.allclose(ranges1, targ_ranges1, equal_nan=True))
        self.assertTrue(np.allclose(ranges2, targ_ranges2, equal_nan=True))



def session2_suite():
    session2_suite = unittest.TestLoader().loadTestsFromTestCase(TestQuatOps)
    session2_suite.addTest(TestQuatConvs('test_euler_to_quat'))
    session2_suite.addTest(TestQuatConvs('test_quat_to_euler'))
    session2_suite.addTest(TestExtractGeometry('test_extract_geometry'))
    session2_suite.addTest(TestMovementAttributes('test_plane_analysis'))
    session2_suite.addTest(TestMovementAttributes('test_run_stance_analysis'))
    session2_suite.addTest(TestMovementAttributes('test_standing_or_not'))
    session2_suite.addTest(TestMovementAttributes('test_sort_phases'))
    session2_suite.addTest(TestMovementAttributes('test_num_runs'))
    session2_suite.addTest(TestMovementAttributes('test_total_accel'))
    session2_suite.addTest(TestMovementAttributes('test_enumerate_stance'))
    session2_suite.addTest(TestBalanceCME('test_calculate_rot_CMEs'))
    session2_suite.addTest(TestBalanceCME('test__cont_rot_CME'))
    session2_suite.addTest(TestBalanceCME('test__filt_rot_CME'))
    session2_suite.addTest(TestRunRelativeCMEs('test_run_relative_CMEs'))
    session2_suite.addTest(TestRunRelativeCMEs('test__drift_agnostic_CMES'))
    session2_suite.addTest(TestRunRelativeCMEs('test__driftless_CMS'))
    session2_suite.addTest(TestRunRelativeCMEs('test__norm_range_of_motion'))
    session2_suite.addTest(TestRunRelativeCMEs('test__norm_motion_covered'))
    session2_suite.addTest(TestRunRelativeCMEs('test__rough_contact_duration'))
    session2_suite.addTest(TestRunRelativeCMEs('test__num_runs'))
    session2_suite.addTest(TestRunRelativeCMEs('test__detect_long_dynamic'))
    session2_suite.addTest(TestRunRelativeCMEs('test__zero_runs'))
    session2_suite.addTest(TestRunRelativeCMEs('test__filter_data'))
    session2_suite.addTest(TestRunRelativeCMEs('test__remove_filtered_ends'))
    session2_suite.addTest(TestImpactCMEs('test_sync_time'))
    session2_suite.addTest(TestImpactCMEs('test_landing_pattern'))
    session2_suite.addTest(TestImpactCMEs('test_continuous_values'))
    session2_suite.addTest(TestPhaseDetection('test_combine_phase'))
    session2_suite.addTest(TestPhaseDetection('test__body_phase'))
    session2_suite.addTest(TestPhaseDetection('test__phase_detect'))
    session2_suite.addTest(TestPhaseDetection('test__impact_detect'))
    session2_suite.addTest(TestPhaseDetection('test__final_phases'))
    session2_suite.addTest(TestPhaseDetection('test__filter_data'))
    session2_suite.addTest(TestDetectImpactPhaseIntervals('test_detect_start_end_imp_phase'))
    session2_suite.addTest(TestDetectImpactPhaseIntervals('test__zero_runs'))
    session2_suite.addTest(TestDetectTakeoffPhaseIntervals('detect_start_end_takeoff_phase'))
    session2_suite.addTest(TestDetectTakeoffPhaseIntervals('test__zero_runs'))

    return session2_suite

if __name__ == '__main__':

    session2_suite = session2_suite()
    unittest.main(defaultTest='session2_suite')
