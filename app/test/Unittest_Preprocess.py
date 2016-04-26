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

class TestQuatProd_KnownValues(unittest.TestCase):
    pass    
    
class TestQuatProd_badinput(unittest.TestCase):
    quats = {0:np.matrix([0,0,1]), 1:np.matrix([0,0,1,0]), 2:np.array([0,0,1]), 3:[0,0,1], 4:'string', 5:5}
    def test_shape(self):
        for i in range(1,len(self.quats)):
            self.assertRaises(prep.QuatFormError, prep.QuatProd, self.quats[i-1], self.quats[i])
            
    def test_magnitude(self):
        self.assertRaises(prep.DivideByZeroError, prep.QuatProd, np.matrix([0,0,0,0]), np.matrix([1,0,0,0]))
        self.assertRaises(prep.DivideByZeroError, prep.QuatProd, np.matrix([1,0,0,0]), np.matrix([0,0,0,0]))
        
class TestQuatProd_badoutput(unittest.TestCase):
    def test_wrongtype(self):
        self.assertTrue(str(type(prep.QuatProd(np.matrix([1,0,0,0]), np.matrix([1,0,1,0])))) == "<class 'numpy.matrixlib.defmatrix.matrix'>")
        
class Testq2dcm_KnownValues(unittest.TestCase):
    quats = {0:np.matrix([1,0,0,0]), 1:np.matrix([2,0,2,0]), 2:np.matrix([.5, .5, 0, 0]), 3:np.matrix([-1, 0, 0, 1])}
    mats = {0:np.identity(3), 1:np.matrix([[0,0,1],[0,1,0], [-1,0,0]]), 2:np.matrix([[1,0,0],[0,0,-1], [0,1,0]]), 3:np.matrix([[0,1,0],[-1,0,0], [0,0,1]])}
    def test_known_values(self):
        for i in range(len(self.quats)):
            #print(prep.q2dcm(self.quats[i]))
            self.assertTrue(np.allclose(prep.q2dcm(self.quats[i]), self.mats[i]), msg ='quat {0} is false'.format(i))

class Testq2dcm_badinput(unittest.TestCase):
    quats = {0:np.matrix([0,0,1]), 1:np.array([0,0,1]), 2:[0,0,1], 3:'string', 4:5}
    def test_shape(self):
        for i in range(len(self.quats)):
            self.assertRaises(prep.QuatFormError, prep.q2dcm, self.quats[i])
    
    def test_magnitude(self):
        self.assertRaises(prep.DivideByZeroError, prep.q2dcm, np.matrix([0,0,0,0]))

class Testq2dcm_badoutput(unittest.TestCase):
    def test_wrongtype(self):
        self.assertTrue(str(type(prep.q2dcm(np.matrix([1,0,0,0])))) == "<class 'numpy.matrixlib.defmatrix.matrix'>")

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
            
class TestQuatConj_badinput(unittest.TestCase):
    quats = {0:np.matrix([0,0,1]), 1:np.array([0,0,1]), 2:[0,0,1], 3:'string', 4:5}
    def test_shape(self):
        for i in range(len(self.quats)):
            self.assertRaises(prep.QuatFormError, prep.QuatConj, self.quats[i])
    
    def test_magnitude(self):
        self.assertRaises(prep.DivideByZeroError, prep.QuatConj, np.matrix([0,0,0,0]))

class TestQuatConj_badoutput(unittest.TestCase):
    def test_wrongtype(self):
        self.assertTrue(str(type(prep.QuatConj(np.matrix([1,0,0,0])))) == "<class 'numpy.matrixlib.defmatrix.matrix'>")

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
            
class TestYawOffset_badinput(unittest.TestCase):
    quats = {0:np.matrix([0,0,1]), 1:np.array([0,0,1]), 2:[0,0,1], 3:'string', 4:5}
    def test_shape(self):
        for i in range(len(self.quats)):
            self.assertRaises(prep.QuatFormError, prep.yaw_offset, self.quats[i])
    
    def test_magnitude(self):
        self.assertRaises(prep.DivideByZeroError, prep.yaw_offset, np.matrix([0,0,0,0]))

class TestYawOffset_badoutput(unittest.TestCase):
    def test_wrongtype(self):
        self.assertTrue(str(type(prep.yaw_offset(np.matrix([1,0,0,0])))) == "<class 'numpy.matrixlib.defmatrix.matrix'>")

if __name__ == '__main__':
    unittest.main(exit=False)
