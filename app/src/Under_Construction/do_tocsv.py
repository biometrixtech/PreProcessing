# -*- coding: utf-8 -*-
"""
Created on Sun Jul 24 12:57:57 2016

@author: Brian
"""

import setUp as su
import coordinateFrameTransformation as prep
import numpy as np

def stack_data(data):
    
    output = np.zeros((len(data.qX),1))
    output = np.column_stack((output, data.qW))
    output = np.column_stack((output, data.qX))
    output = np.column_stack((output, data.qY))
    output = np.column_stack((output, data.qZ))
    output = np.column_stack((output, data.AccX))
    output = np.column_stack((output, data.AccY))
    output = np.column_stack((output, data.AccZ))
    output = np.column_stack((output, data.EulerX))
    output = np.column_stack((output, data.EulerY))
    output = np.column_stack((output, data.EulerZ))
    
    return output

def run_analytics(path, mass, extra_mass, hz, anatom=None):
    
    #Set up objects that hold raw datasets 
    data = su.Analytics(path, mass, extra_mass, hz, anatom)
        
    #Create Inertial Frame objects transformed data
    #hip databody
    hipbf = prep.TransformData(data.hipdataset)
    hipbf = stack_data(hipbf)
    
    #rfoot databody
    rfbf = prep.TransformData(data.rfdataset)
    rfbf = stack_data(rfbf)
    
    #lfoot databody
    lfbf = prep.TransformData(data.lfdataset)
    lfbf = stack_data(lfbf)
    
    return hipbf, rfbf, lfbf
    
if __name__ == '__main__':
    
    import pandas as  pd
    
    path = 'C:\\Users\\Ankur\\python\\Biometrix\\Data analysis\\data exploration\\data files\\GRF Data _Abigail\\Sensor Data\\test.csv'

    hipdata, rdata, ldata = run_analytics(path, 75, 25, 250)
    

