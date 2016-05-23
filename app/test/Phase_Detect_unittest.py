# -*- coding: utf-8 -*-
"""
Created on Mon May  9 14:26:17 2016

@author: Brian
"""

import unittest
import Phase_Detect as phase
import numpy as np
import pandas as pd
import data

path = 'C:\\Users\\Brian\\Documents\\GitHub\\PreProcessing\\app\\test\\data\\'

class TestInputZeroVel(unittest.TestCase):
    def setUp(self):
        self.file = pd.read_csv(data.postprocessed_unittest)
    
    def test_correctinputtype(self):
        self.right = self.file.ix[0:4,:]
        self.wrong = self.file.ix[0:4,:].as_matrix()
        self.assertRaises(phase.ObjectMismatchError, phase.Phase_Detect, self.wrong, self.right, 25)
        self.assertRaises(phase.ObjectMismatchError, phase.Phase_Detect, self.right, self.wrong, 25)
        self.assertRaises(phase.ObjectMismatchError, phase.Zero_Detect, self.wrong, 'GLRT', 5)
        self.assertRaises(phase.ObjectMismatchError, phase.GLRT, self.wrong, 5)        
        
    def test_correctinputlength(self):
        self.long = self.file.ix[0:5,:]
        self.short =  self.file.ix[0:1,:]
        self.right = self.file.ix[0:4,:]
        self.assertRaises(phase.ObjectMismatchError, phase.Zero_Detect, self.long, 'GLRT', 5)
        self.assertRaises(phase.ObjectMismatchError, phase.Zero_Detect, self.short, 'GLRT', 5)
        self.assertRaises(phase.ObjectMismatchError, phase.GLRT, self.long, 5)
        self.assertRaises(phase.ObjectMismatchError, phase.GLRT, self.short, 5)
        
    def test_correctinputvalues(self):
        self.right = self.file.ix[0:4,:]
        self.assertRaises(phase.DataOmissionError, phase.Zero_Detect, self.right.ix[:, ['AccX', 'gyrZ']], 'GLRT', 5)
        self.assertRaises(phase.DataOmissionError, phase.GLRT, self.right.ix[:, ['AccX', 'gyrZ']], 5)
        self.assertRaises(phase.DataOmissionError, phase.Phase_Detect, self.right.ix[:, ['AccX', 'gyrZ']], self.right, 25)
        self.assertRaises(phase.DataOmissionError, phase.Phase_Detect, self.right, self.right.ix[:, ['AccX', 'gyrZ']], 25)
        self.assertRaises(phase.DataOmissionError, phase.Phase_Detect, self.right.ix[:, ['AccX', 'gyrZ']], self.right.ix[:, ['AccX', 'gyrZ']], 25)
    
    def test_correcttestvar(self):
        self.right = self.file.ix[0:4,:]
        self.assertRaises(phase.InvalidTestError, phase.Zero_Detect,self.right, '', 5)
        self.assertRaises(phase.InvalidTestError, phase.Zero_Detect, self.right, 12, 5)
    
    def test_hzCorrectInput(self):
        self.right = self.file.ix[0:4,:]
        self.left = self.file.ix[5:9,:]
        self.assertRaises(phase.InvalidWindowInput, phase.Phase_Detect,self.left, self.right,32)

class TestOutputZeroVel(unittest.TestCase):
    def setUp(self):
        self.file = pd.read_csv(data.postprocessed_unittest.csv)
    
    def testDiscreteOutput(self):
        self.right = self.file.ix[0:4,:]
        self.left = self.file.ix[5:9,:]
        self.assertTrue(phase.Phase_Detect(self.left, self.right, 25) in [0,1,2])
        self.assertTrue(phase.Zero_Detect(self.left, 'GLRT', 5) in [0,1])
            
if __name__ == '__main__':
    unittest.main(exit=False)
        
    
    