# -*- coding: utf-8 -*-
"""
Created on Thu Apr 21 17:22:15 2016

@author: Brian
"""

import unittest
import numpy as np
import pandas as pd
import Data_Processing as prep

path = 'C:\\Users\\Brian\\Documents\\GitHub\\PreProcessing\\app\\test\\data\\' 

class TestSingleQuat_badinput(unittest.TestCase):
    quats = {0:np.matrix([0,0,1]), 1:np.array([0,0,1]), 2:[0,0,1], 3:'string', 4:5}
    def test_shape(self):
        for i in range(len(self.quats)):
            self.assertRaises(prep.QuatFormError, prep.yaw_offset, self.quats[i])
            self.assertRaises(prep.QuatFormError, prep.QuatConj, self.quats[i])
            self.assertRaises(prep.QuatFormError, prep.q2dcm, self.quats[i])
            self.assertRaises(prep.QuatFormError, prep.Calc_Euler, self.quats[i])
    
    def test_magnitude(self):
        self.assertRaises(prep.DivideByZeroError, prep.yaw_offset, np.matrix([0,0,0,0]))
        self.assertRaises(prep.DivideByZeroError, prep.QuatConj, np.matrix([0,0,0,0]))
        self.assertRaises(prep.DivideByZeroError, prep.q2dcm, np.matrix([0,0,0,0]))
        self.assertRaises(prep.DivideByZeroError, prep.Calc_Euler, np.matrix([0,0,0,0]))

class TestQuatFunc_badoutput(unittest.TestCase):
    def test_wrongtype(self):
        self.assertTrue(str(type(prep.yaw_offset(np.matrix([1,0,0,0])))) == "<class 'numpy.matrixlib.defmatrix.matrix'>")
        self.assertTrue(str(type(prep.QuatConj(np.matrix([1,0,0,0])))) == "<class 'numpy.matrixlib.defmatrix.matrix'>")
        self.assertTrue(str(type(prep.q2dcm(np.matrix([1,0,0,0])))) == "<class 'numpy.matrixlib.defmatrix.matrix'>")
        self.assertTrue(str(type(prep.QuatProd(np.matrix([1,0,0,0]), np.matrix([1,0,1,0])))) == "<class 'numpy.matrixlib.defmatrix.matrix'>")
        self.assertTrue(str(type(prep.Calc_Euler(np.matrix([1,0,0,0])))) == "<class 'list'>")
        self.assertTrue(str(type(prep.rotate_quatdata(np.matrix([0,0,0,1000]),np.matrix([1,0,0,0]), RemoveGrav=True))) == "<class 'list'>")
        
class TestQuatProd_KnownValues(unittest.TestCase):
    def setUp(self):
        self.qp_file = pd.read_csv(path + 'matlab_quatprod.csv', header=None)
        self.qp_file = self.qp_file.as_matrix()
        self.file = pd.read_csv(path + 'Preprocess_unittest.csv') 
        self.file = self.file.as_matrix()
    
    def test_known_values(self):
        self.q1 = self.file[0:50, 9:13]
        self.q2 = self.file[50:100, 9:13]
        for i in range(len(self.q1)):
            self.pred = prep.QuatProd(np.matrix(self.q1[i,:]), np.matrix(self.q2[i,:]))
            self.data = np.matrix([0, self.file[i,0], self.file[i,1], self.file[i,2]])
            self.datpred = prep.QuatProd(self.data, np.matrix(self.q1[i,:]))
            self.assertTrue(np.allclose(self.pred, self.qp_file[i+50,:], atol=1e-04))
            self.assertTrue(np.allclose(self.datpred, self.qp_file[i,:], atol=1e-02))
    
class TestTwoQuat_badinput(unittest.TestCase):
    quats = {0:np.matrix([0,0,1]), 1:np.matrix([0,0,1,0]), 2:np.array([0,0,1]), 3:[0,0,1], 4:'string', 5:5}
    def test_shape(self):
        for i in range(1,len(self.quats)):
            self.assertRaises(prep.QuatFormError, prep.QuatProd, self.quats[i-1], self.quats[i])
            self.assertRaises(prep.QuatFormError, prep.rotate_quatdata, self.quats[i-1], self.quats[i])
            
    def test_magnitude(self):
        self.assertRaises(prep.DivideByZeroError, prep.QuatProd, np.matrix([0,0,0,0]), np.matrix([1,0,0,0]))
        self.assertRaises(prep.DivideByZeroError, prep.QuatProd, np.matrix([1,0,0,0]), np.matrix([0,0,0,0]))
        self.assertRaises(prep.DivideByZeroError, prep.rotate_quatdata, np.matrix([0,0,0,0]), np.matrix([1,0,0,0]))
        self.assertRaises(prep.DivideByZeroError, prep.rotate_quatdata, np.matrix([1,0,0,0]), np.matrix([0,0,0,0]))
        
class Testq2dcm_KnownValues(unittest.TestCase):
    quats = {0:np.matrix([1,0,0,0]), 1:np.matrix([2,0,2,0]), 2:np.matrix([.5, .5, 0, 0]), 3:np.matrix([-1, 0, 0, 1])}
    mats = {0:np.identity(3), 1:np.matrix([[0,0,1],[0,1,0], [-1,0,0]]), 2:np.matrix([[1,0,0],[0,0,-1], [0,1,0]]), 3:np.matrix([[0,1,0],[-1,0,0], [0,0,1]])}
    def test_known_values(self):
        for i in range(len(self.quats)):
            #print(prep.q2dcm(self.quats[i]))
            self.assertTrue(np.allclose(prep.q2dcm(self.quats[i]), self.mats[i]), msg ='quat {0} is false'.format(i))

class TestQuatConj_KnownValues(unittest.TestCase):
    def setUp(self):
        self.file = pd.read_csv(path + 'quatonly_unittest.csv') 
        self.file = self.file.as_matrix()
        
    def test_known_values(self):
        for i in range(len(self.file)):
            self.quat = np.matrix(self.file[i,:])
            self.norm_in = self.quat/np.linalg.norm(self.quat)
            self.out = prep.QuatConj(self.quat)
            self.diff = self.norm_in + self.out
            #print(self.diff[0,0], 2*self.quat[0,0])
            self.assertTrue(np.allclose(self.diff[0,0], 2*self.quat[0,0]/np.linalg.norm(self.quat)), msg="quat {0}/{1} first terms do not add up".format(i, len(self.file)))
            self.assertTrue(np.allclose(self.diff[0,1:4], np.matrix([0,0,0])), msg="quat {0}/{1} zero terms were not equal".format(i, len(self.file)))

class TestYawOffset_KnownValues(unittest.TestCase):
    def setUp(self):
        self.file = pd.read_csv(path + 'quatonly_unittest.csv') 
        self.file = self.file.as_matrix()
        
    def test_known_values(self):
        for i in range(len(self.file)):
            self.quat = np.matrix(self.file[i,:])
            self.dcm = prep.q2dcm(self.quat)
            self.yaw1 = np.arctan2(self.dcm[1,0], self.dcm[0,0])
            self.yquat = prep.yaw_offset(self.quat)
            self.dcm2 = prep.q2dcm(self.yquat)
            self.yaw2 = np.arctan2(self.dcm2[1,0], self.dcm2[0,0])
            self.roll = np.arctan2(self.dcm2[2,1], self.dcm2[2,2])
            self.pitch = np.arcsin(-self.dcm2[2,0])
            self.assertTrue(np.isclose(self.yaw1, self.yaw2), msg="yaw values not equal on {0}".format(i))
            self.assertTrue(self.roll == 0, msg="roll is not zero on {0}".format(i))
            self.assertTrue(self.pitch == 0, msg="pitch is not zero on {0}".format(i))
            
class TestEulerCalc_KnownValue(unittest.TestCase):
    def setUp(self):
        self.eul_file = pd.read_csv(path + 'matlab_euler.csv', header=None)
        self.eul_file = self.eul_file.as_matrix()
        self.file = pd.read_csv(path + 'quatonly_unittest.csv') 
        self.file = self.file.as_matrix()
        
    def test_known_values(self):
        for i in range(0,len(self.eul_file)):
            self.eul = prep.Calc_Euler(np.matrix(self.file[i,:]))
            self.assertTrue(np.isclose(self.eul[0],self.eul_file[i,2], atol=1e-04), msg="roll values not equal on {0}".format(i))
            self.assertTrue(np.isclose(self.eul[1],self.eul_file[i,1], atol=1e-04), msg="pitch values not equal on {0}".format(i))
            self.assertTrue(np.isclose(self.eul[2],self.eul_file[i,0], atol=1e-04), msg="yaw values not equal on {0}".format(i))
    
class TestRotateQuatData_KnownValue(unittest.TestCase):
    def setUp(self):
        self.rot_file = pd.read_csv(path + 'matlab_rotate.csv', header=None)
        self.rot_file = self.rot_file.as_matrix()
        self.file = pd.read_csv(path + 'Preprocess_unittest.csv')
        self.file = self.file.as_matrix()
    
    def test_known_valuesacc(self):
        for i in range(0,len(self.rot_file)):
            self.acc = np.matrix([0, self.file[i,0], self.file[i,1], self.file[i,2]])
            self.rot = prep.rotate_quatdata(self.acc, np.matrix(self.file[i,9:13]), RemoveGrav=True)
            self.assertTrue(np.allclose(self.rot, self.rot_file[i,0:3], atol=1e-04))
    
    def test_known_valuesgyr(self):
        for i in range(0,len(self.rot_file)):
            self.acc = np.matrix([0, self.file[i,3], self.file[i,4], self.file[i,5]])
            self.rot = prep.rotate_quatdata(self.acc, np.matrix(self.file[i,9:13]))
            self.assertTrue(np.allclose(self.rot, self.rot_file[i,3:6], atol=1e-03))            
    
if __name__ == '__main__':
    unittest.main(exit=False)