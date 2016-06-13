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
Inputs: AccZ data (float) from right and left heel sensors 
Outputs: array, len(Accz dataset), contains impact phase decisions 
#############################################################################################################
"""

def impact_phase(az): #input: array of data points
    
    az_mean = np.mean(az) #determining the mean of the AccZ data points
    az_std = np.std(az) #determining the standard deviation of the AccZ data points
    
    #detecting the start and end points of an impact phase    
    start_imp = [] #stores the index of the start of the impact phase
    end_imp = []   #stores the index of the end of the impact phase 
    w = 20 #a window of 20 data points to determine impact phase
    
    numbers = iter(range(len(az)-3)) #creating an iterator variable. iter() returns an iterator object. Subtracting 3 else, error: 'Index out of range' in the following for loop.
    
    for i in numbers:
        if az[i] > 2*az_std+az_mean or az[i+1] > 2*az_std+az_mean or az[i+2] > 2*az_std+az_mean or az[i+3] > 2*az_std+az_mean: #checking if atleast one of the data points from AccZ[i] to AccZ[i+4] is greater than 2 times the standard deviation of AccZ
            start_imp.append(i) #storing the index (i) when the impact phase begins
            end_imp.append(i+w) #storing the index (i+w; w=20) of when the impact phase ends
            next(islice(numbers, w, 1 ), None) #skip the next 'w' iterations
        
    #combining the impact phases that are really close to eachother (within 20-40 data points) in order to obtain a continuous impact phase
    cstart_imp = [] #stores the new index of the start of a combined impact phase
    cend_imp = [] #stores the new index of the end of a combined impact phase
    cw = 30 #number of data points within which impact phases are combined
    s = 10 #a value is assigned when impact phase is detected. 
    
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
        
    #eliminating false impact phases
    thresh = 3 #setting a threshold value to eliminate false impact phases        
        
    for k,l in zip(cstart_imp[:], cend_imp[:]):
        dummy = [] #initiating a dummy list
        for i in range(10, 16):
            dummy.append(az[k-i]) #storing 6 data points (before the start of an impact phase) in the dummy list 
        if abs(np.mean(dummy)) < thresh: #if the mean of the dummy list is lesser than the threshold, then the phase is not a true impact phase
            h[k:l] = 0
            
    return np.array(h)
    
if __name__ == '__main__':
    
    import matplotlib.pyplot as plt    
    
    rpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Stomp\Rheel_Gabby_stomp_set1.csv'
    lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject3\Subject3_lfdatabody_LESS.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Stomp\Lheel_Gabby_stomp_set1.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\ChangeDirection\Lheel_Gabby_changedirection_set1.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Jump\Lheel_Gabby_jumping_explosive_set2.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Walking\Lheel_Gabby_walking_heeltoe_set1.csv'
    hpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Stomp\hips_Gabby_stomp_set1.csv'

    rdata = pd.read_csv(rpath)
    ldata = pd.read_csv(lpath)
    hdata = pd.read_csv(hpath)
    
    comp = 'AccZ'
    rdata = rdata[comp].values
    ldata = ldata[comp].values #input AccZ values!
    output = impact_phase(ldata)
    
    plt.plot(output)
    plt.plot(ldata)
    plt.show()
