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
    sigma_a = .778 #declare standard deviation of accel noise
    sigma_g = 2.6 #declare standard deviation of gyro noise
    Tk = 0
    
    if isinstance(data, pd.DataFrame) == False:
        raise ObjectMismatchError    
    
    if len(data) != W:
        raise ObjectMismatchError
        
    if set(['AccX', 'AccY', 'AccZ', 'gyrX', 'gyrY', 'gyrZ']).issubset(set(data.columns.values)) == False:
        raise DataOmissionError
    
    data = data[['AccX', 'AccY', 'AccZ', 'gyrX', 'gyrY', 'gyrZ']]   #trim dataset to include only relevant problems 
    ya_m = np.mean(data.ix[:,['AccX', 'AccY', 'AccZ']])  #find mean of accel vector for dataset
    ya_m = ya_m/np.linalg.norm(ya_m) #normalize acceleration vector
    mean = np.tile(ya_m, (W,1)) #create matrix that has mean accel vector on every row
    acc = data[['AccX', 'AccY', 'AccZ']].as_matrix() #turn accel data into matrix
    tmp = acc-mean #calculate distance from mean for each accel data point
    gyr = data[['gyrX', 'gyrY', 'gyrZ']].as_matrix() #turn gyro data into matrix
    Tk = np.trace(gyr.dot(gyr.transpose())/sigma_g) + np.trace(tmp.dot(tmp.transpose())/sigma_a) #add mag of gyro vector/gyro noise and mag of distance vec div by accel noise, do this by multiplying matrices and adding their trace
    
    T = Tk/W #find per point average of Tk, return statistic
    return T
    

def Zero_Detect(data, test, W):
    gamma = 33000 #threshold for determining if foot on ground or not
    
    if isinstance(data, pd.DataFrame) == False:
        raise ObjectMismatchError
        
    if len(data) != W:
        raise ObjectMismatchError
    
    if test not in ['GLRT', 'MV', 'MAG','ARE']:
        raise InvalidTestError
        
    if set(['AccX', 'AccY', 'AccZ', 'gyrX', 'gyrY', 'gyrZ']).issubset(set(data.columns.values)) == False:
        raise DataOmissionError
        
    T = GLRT(data, W) #find statistic using GLRT function
    if T < gamma: #if less than threshold determine foot on ground
        return 1 #foot on ground
    else:
        return 0 #foot not on ground

def Phase_Detect(lfoot, rfoot, hz):
    W = hz*.2 #window is .2* sampling rate
    
    if isinstance(lfoot, pd.DataFrame) == False or isinstance(rfoot, pd.DataFrame) == False:
        raise ObjectMismatchError
        
    if W != len(lfoot) or W!= len(rfoot):
        raise InvalidWindowInput
    
    if set(['AccX', 'AccY', 'AccZ', 'gyrX', 'gyrY', 'gyrZ']).issubset(set(lfoot.columns.values)) == False:
        raise DataOmissionError
    
    if set(['AccX', 'AccY', 'AccZ', 'gyrX', 'gyrY', 'gyrZ']).issubset(set(rfoot.columns.values)) == False:
        raise DataOmissionError
    
    #run zero velocity algo for each foot
    left = Zero_Detect(lfoot, 'GLRT', W)
    right = Zero_Detect(rfoot, 'GLRT', W)
    
    #determine if person standing on one or two legs...or floating
    if left + right == 2:
        return 0 #both feet on ground
    elif left + right == 1:
        return 1 #one foot on ground (not differentiating which one)
    else:
        return 2 #no feet on the ground...wheeeeee
    

if __name__ == '__main__':
    rpath = ''
    lpath = ''
    rdata = pd.read_csv(rpath)
    ldata = pd.read_csv(lpath)    
    hz = 250 #sampling rate
    window = hz*.2 #window size
    
    #in implementation will need window number of points to go before starting analysis on point zero
    pd_out = np.zeros((len(rdata),1))
    for i in range(len(rdata)):
        if i+window <= len(rdata) - 1: #determine if window length 
            tempr = rdata.ix[i:i+window-1,:].reset_index() #cut data down to analyze window length at a time
            templ = ldata.ix[i:i+window-1,:].reset_index() #cut data down to analyze window length at a time
            pd_out[i,0] = Phase_Detect(templ, tempr, hz) #run phase detect algo
        else:
            pd_out[i,0] = 0
    rdata['Phase'] = pd_out
    ldata['Phase'] = pd_out
    
    
    
    
