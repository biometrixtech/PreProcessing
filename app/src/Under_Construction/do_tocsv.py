# -*- coding: utf-8 -*-
"""
Created on Sun Jul 24 12:57:57 2016

@author: Brian
"""

import setUp as su
import coordinateFrameTransformation as prep
import numpy as np

def stack_data(data):
    output = np.column_stack((data.qW, data.qX))
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
    import matplotlib.pyplot as plt
    
    path = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\Fixed_By_Exercise\\Subject1_DblSquat.csv'

    hipbf, rfbf, lfbf = run_analytics(path, 75, 25, 250)
    final = np.concatenate((lfbf, hipbf), axis=1)
    final = np.concatenate((final, rfbf), axis=1)
    
    df = pd.DataFrame(final, columns=['LqW', 'LqX', 'LqY', 'LqZ', 'LAccX', 'LAccY','LAccZ', 'LEulerX', 'LEulerY', 'LEulerZ',
                                      'HqW', 'HqX', 'HqY', 'HqZ', 'HAccX', 'HAccY','HAccZ', 'HEulerX', 'HEulerY', 'HEulerZ',
                                      'RqW', 'RqX', 'RqY', 'RqZ', 'RAccX', 'RAccY','RAccZ', 'REulerX', 'REulerY', 'REulerZ'])
    
    df.to_csv('C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\Fixed_By_Exercise\\test.csv')
    
    
    
    

