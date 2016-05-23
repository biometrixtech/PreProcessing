# -*- coding: utf-8 -*-
"""
Created on Thu May  5 12:25:16 2016

@author: Brian
"""

import unittest
import numpy as np
import pandas as pd
import Exercise_Filter as exfilt 
import data

class ExFilt_badinput(unittest.TestCase):
    def setUp(self):
        self.file = pd.read_csv(data.postprocessed_unittest.csv)
        self.right = self.file.ix[0:100,:]
    
    def test_correctsize(self):
        self.lst = [25,50,100,250]
        for i in range(len(self.lst)):
            self.upind = .4*self.lst[i]
            self.right = self.file.ix[0:self.upind,:]
            self.high = self.file
            self.low = self.file.ix[0:self.upind-1,:]
            self.assertRaises(exfilt.ObjectMismatchError, exfilt.Exercise_Filter, self.high, "Double", self.lst[i])
            self.assertRaises(exfilt.ObjectMismatchError, exfilt.Exercise_Filter, self.low, "Double", self.lst[i])
            self.assertTrue(len(self.right) == self.upind+1)
        
    def test_correctdata(self):
        self.cols = self.file.columns.values
        self.col_dict = {0:['AccZ', 'EulerY'], 1:['AccY', 'EulerX'], 2:['AccX', 'EulerY']}
        for i in range(len(self.col_dict)):
            self.badcols = self.right.ix[:, self.col_dict[i]]
            self.assertRaises(exfilt.DataOmissionError, exfilt.Exercise_Filter, self.badcols, "Double", 250)
    
    def test_exerciseinput(self):
        self.binputs = ['single', 'Triple', '']
        for i in range(len(self.binputs)):
            self.assertRaises(exfilt.InvalidExerciseInput, exfilt.Exercise_Filter, self.right, self.binputs[i], 250)
    
    def test_hzvalidinput(self):
        self.right = self.file.ix[0:10, :]
        self.assertRaises(exfilt.InvalidFreqInput, exfilt.Exercise_Filter, self.right, "Double", 30)
        
    def test_movingaverageinput(self):
        pass
    
class ExFilt_BadOutput(unittest.TestCase):
    def setUp(self):
        self.file = pd.read_csv(data.postprocessed_unittest)
        self.right = self.file.ix[0:100,:]
    
    def test_binaryoutput(self):
        self.assertTrue(exfilt.Exercise_Filter(self.right, 'Double', 250) in [0,1])
        
class ExFilt_KnownValues(unittest.TestCase):
    def setUp(self):
        self.correct = pd.read_csv(data.known_value_exercise)
        self.test = pd.read_csv(data.postprocessed_unittest)

    def test_known_values(self):
        self.window = 50
        for i in range(50,len(self.correct)-50):
            self.assertTrue(exfilt.Exercise_Filter(self.test.ix[i-self.window:i+self.window,:].reset_index(), 'Double', 250) == self.correct.ix[i-1,0])
            
if __name__ == '__main__':
    unittest.main(exit=False)