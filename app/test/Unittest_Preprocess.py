# -*- coding: utf-8 -*-
"""
Created on Thu Apr 21 17:22:15 2016

@author: Brian
"""

import unittest
import numpy as np
import Data_Processing as prep

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
    quats = {0:np.matrix([1,0,0,0]), 1:np.matrix([.3,.4,.2,.1]), 2:np.matrix([0,0,1,0])}
    ans = {0:np.matrix([1,0,0,0]), 1:np.matrix([.3,-.4,-.2,-.1]), 2:np.matrix([0,0,-1,0])}
    def test_known_vlaues(self):
        for i in range(len(self.quats)):
            self.assertTrue(np.allclose(prep.QuatConj(self.quats[i]), self.ans[i]), msg ='quat {0} is false'.format(i))

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
           
if __name__ == '__main__':
    unittest.main(exit=False)
