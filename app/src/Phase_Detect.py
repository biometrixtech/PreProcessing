# -*- coding: utf-8 -*-
"""
Created on Mon May  9 14:25:37 2016

@author: Brian
"""

import numpy as np
import pandas as pd

class ObjectMismatchError(ValueError):
    pass

class InvalidTestError(ValueError):
    pass

class DataOmissionError(ValueError):
    pass

class InvalidWindowInput(ValueError):
    pass
    
def GLRT(data, W):
    sigma_a = .778 #assign real values
    sigma_g = 2.6 #assign real values
    Tk = 0
    
    if isinstance(data, pd.DataFrame) == False:
        raise ObjectMismatchError    
    
    if len(data) != W:
        raise ObjectMismatchError
        
    if set(['AccX', 'AccY', 'AccZ', 'gyrX', 'gyrY', 'gyrZ']).issubset(set(data.columns.values)) == False:
        raise DataOmissionError
    
    data = data[['AccX', 'AccY', 'AccZ', 'gyrX', 'gyrY', 'gyrZ']]    
    ya_m = np.mean(data.ix[:,['AccX', 'AccY', 'AccZ']])
    ya_m = ya_m/np.linalg.norm(ya_m) ##gravity?
    mean = np.tile(ya_m, (W,1))
    acc = data[['AccX', 'AccY', 'AccZ']].as_matrix()
    tmp = acc-mean
    gyr = data[['gyrX', 'gyrY', 'gyrZ']].as_matrix()
    Tk = np.trace(gyr.dot(gyr.transpose())/sigma_g) + np.trace(tmp.dot(tmp.transpose())/sigma_a)
    
    T = Tk/W
    return T
    

def Zero_Detect(data, test, W):
    gamma = 33000
    
    if isinstance(data, pd.DataFrame) == False:
        raise ObjectMismatchError
        
    if len(data) != W:
        raise ObjectMismatchError
    
    if test not in ['GLRT', 'MV', 'MAG','ARE']:
        raise InvalidTestError
        
    if set(['AccX', 'AccY', 'AccZ', 'gyrX', 'gyrY', 'gyrZ']).issubset(set(data.columns.values)) == False:
        raise DataOmissionError
        
    T = GLRT(data, W)
    if T < gamma:
        return 1
    else:
        return 0

def Phase_Detect(lfoot, rfoot, hz):
    W = hz*.2
    
    if isinstance(lfoot, pd.DataFrame) == False or isinstance(rfoot, pd.DataFrame) == False:
        raise ObjectMismatchError
        
    if W != len(lfoot) or W!= len(rfoot):
        raise InvalidWindowInput
    
    if set(['AccX', 'AccY', 'AccZ', 'gyrX', 'gyrY', 'gyrZ']).issubset(set(lfoot.columns.values)) == False:
        raise DataOmissionError
    
    if set(['AccX', 'AccY', 'AccZ', 'gyrX', 'gyrY', 'gyrZ']).issubset(set(rfoot.columns.values)) == False:
        raise DataOmissionError
        
    left = Zero_Detect(lfoot, 'GLRT', W)
    right = Zero_Detect(rfoot, 'GLRT', W)
    
    if left + right == 2:
        return 0
    elif left + right == 1:
        return 1
    else:
        return 2
    

if __name__ == '__main__':
    rpath = ''
    lpath = ''
    rdata = pd.read_csv(rpath)
    ldata = pd.read_csv(lpath)    
    hz = 250
    window = hz*.2
       
    pd_out = np.zeros((len(rdata),1))
    for i in range(len(rdata)):
        if i+window <= len(rdata) - 1:
            tempr = rdata.ix[i:i+window-1,:].reset_index()
            templ = ldata.ix[i:i+window-1,:].reset_index()
            pd_out[i,0] = Phase_Detect(templ, tempr, hz)
        else:
            pd_out[i,0] = 0
    rdata['Phase'] = pd_out
    ldata['Phase'] = pd_out
    
    
    
    
