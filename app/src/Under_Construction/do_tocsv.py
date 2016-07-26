# -*- coding: utf-8 -*-
"""
Created on Sun Jul 24 12:57:57 2016

@author: Brian
"""

import setUp as su
import coordinateFrameTransformation as prep
import numpy as np

def run_analytics(path, mass, extra_mass, hz, anatom=None):
    
    #Set up objects that hold raw datasets 
    data = su.Analytics(path, mass, extra_mass, hz, anatom)
        
    #Create Inertial Frame objects transformed data
    #hip databody
    hipbf = prep.TransformData(data.hipdataset)
    hipbf = hipbf.to_array()  
    
    #rfoot databody
    rfbf = prep.TransformData(data.rfdataset)
    rfbf = rfbf.to_array() 
    
    #lfoot databody
    lfbf = prep.TransformData(data.lfdataset)
    lfbf = lfbf.to_array()
    
    return hipbf, rfbf, lfbf
    
if __name__ == '__main__':
    
    import pandas as  pd
    import matplotlib.pyplot as plt
    
    path = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\Fixed_Trial4\\SensorData_062816_anacalib_dblsquat_set1.csv'

    hipbf, rfbf, lfbf = run_analytics(path, 75, 25, 250)
    final = np.concatenate((lfbf, hipbf), axis=1)
    final = np.concatenate((final, rfbf), axis=1)
    
    df = pd.DataFrame(final, columns=['LqW', 'LqX', 'LqY', 'LqZ', 'LEulerX', 'LEulerY', 'LEulerZ', 'LAccX' 'LAccY','LAccZ',
                                      'HqW', 'HqX', 'HqY', 'HqZ', 'HEulerX', 'HEulerY', 'HEulerZ', 'HAccX' 'HAccY','HAccZ',
                                      'RqW', 'RqX', 'RqY', 'RqZ', 'REulerX', 'REulerY', 'REulerZ', 'RAccX' 'RAccY','RAccZ'])
    
    df.to_csv('C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\Fixed_Trial4\\test.csv')
    
    plt.plot(df['LEulerX'])
    plt.plot(df['LEulerY'])
    plt.plot(df['LEulerZ'])
    plt.show()
    
    
    
    

