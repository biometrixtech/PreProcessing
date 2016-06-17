# -*- coding: utf-8 -*-
"""
Created on Mon Jun 13 12:12:39 2016

@author: Ankur
"""

from itertools import islice #'islice' helps to skip specified number of iterations in 'for' loop
import numpy as np
import pandas as pd

"""
#############################################INPUT/OUTPUT####################################################
Inputs: AccZ data (float) from right or left heel sensors & the sampling rate
Outputs: array, len(Accz dataset), contains impact phase decisions 
Datsets: impact_input.csv -> impact_phase(data, 100) -> impact_output.csv
#############################################################################################################
"""
    
def impact_phase(az, sampl_rate): #input: array of data points & the sampling rate
    
    az_mean = np.mean(az) #determining the mean of the AccZ data points
    az_std = np.std(az) #determining the standard deviation of the AccZ data points
    
    #detecting the start and end points of an impact phase    
    start_imp = [] #stores the index of the start of the impact phase
    end_imp = []   #stores the index of the end of the impact phase 
    w = int(0.08*sampl_rate) #a rolling window to determine impact phase
    
    numbers = iter(range(len(az)-3)) #creating an iterator variable. iter() returns an iterator object. Subtracting 3 else, error: 'Index out of range' in the following for loop.
    
    for i in numbers:
        if az[i] > 2*az_std+az_mean or az[i+1] > 2*az_std+az_mean or az[i+2] > 2*az_std+az_mean or az[i+3] > 2*az_std+az_mean: #checking if atleast one of the data points from AccZ[i] to AccZ[i+3] is greater than 2 times the standard deviation of AccZ
            start_imp.append(i) #storing the index (i) when the impact phase begins
            end_imp.append(i+w) #storing the index (i+w) of when the impact phase ends
            next(islice(numbers, w, 1 ), None) #skip the next 'w' iterations
        
    #combining the impact phases that are close to eachother in order to obtain a continuous impact phase
    cstart_imp = [] #stores the new index of the start of a combined impact phase
    cend_imp = [] #stores the new index of the end of a combined impact phase
    cw = 0.12*sampl_rate #number of data points within which impact phases are combined
    s = 1 #a value is assigned when impact phase is detected. 
    
    for i,j in zip(range(1, len(start_imp[:])), range(len(end_imp[:])-1)):
        if abs(start_imp[i] - end_imp[j]) <= cw: #consider only those impact phases that are within 'cw' data points of eachother
            cstart_imp.append(start_imp[i-1]) #storing the index of the start of the combined impact phase
            cend_imp.append(end_imp[j+1]) #storing the index of the end of the combined impact phase
        else:
            cstart_imp.append(start_imp[i-1])
            cend_imp.append(end_imp[j])

    h = np.zeros(len(az)) #creating an array of zeros of length  = len(az)

    for i, j in zip(cstart_imp, cend_imp):
        h[i:j] = s #assigning a value to the index points of an impact phase
        
    #eliminating false positives
    thresh = 3 #setting a threshold value to eliminate false positives        
        
    for k,l in zip(cstart_imp[:], cend_imp[:]):
        dummy = [] #initiating a dummy list
        for i in range(10, 16):
            dummy.append(az[k-i]) #storing 6 data points (before the start of an impact phase) in the dummy list 
        if abs(np.mean(dummy)) < thresh: #if the mean of the dummy list is lesser than the threshold, then the phase is not a true impact phase
            h[k:l] = 0
            
    return np.array(h)
    
if __name__ == '__main__':
    path = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\BodyFrame jumping\\hips_Gabby_jumping_explosive_set2.csv'

    data = pd.read_csv(path)
    
    comp = 'AccZ'
    acc = data[comp].values #input AccZ values!
    sampl_rate = 100 #sampling rate, remember to change it when using data sets of different sampling rate
    output = impact_phase(acc, sampl_rate) #passing an array of data points and the sampling rate  
