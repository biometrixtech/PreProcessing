# -*- coding: utf-8 -*-
"""
Created on Tue Jul 12 12:00:16 2016

@author: Ankur
"""

import numpy as np
import matplotlib.pyplot as plt

#rpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\PhaseDetect\\Subject5_rfdatabody_LESS.csv'
#lpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\PhaseDetect\\Subject5_lfdatabody_LESS.csv'
#hpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\PhaseDetect\\Subject5_hipdatabody_LESS.csv'

rpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\PhaseDetect\\Rheel_Gabby_changedirection_set1.csv'
lpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\PhaseDetect\\Lheel_Gabby_changedirection_set1.csv'
hpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\PhaseDetect\\hips_Gabby_changedirection_set1.csv'


rdata = np.genfromtxt(rpath, delimiter = ",", dtype = float, names = True)
ldata = np.genfromtxt(lpath, delimiter = ",", dtype = float, names = True)
hdata = np.genfromtxt(hpath, delimiter = ",", dtype = float, names = True)

# In[]:

#This is the start of the algorithm to determine the balance phase

import pandas as pd

acc = 0
acc = rdata['AccX']
orient = rdata['EulerY']
#acc = rdata['AccZ']
#acc = np.sqrt(rdata['AccX']**2+.1*rdata['AccZ']**2)
std_acc = 0
mean_acc = 0

#when sampling rate is 100Hz
hz = 100
win = int(0.2*hz)

##when sampling rate is 250Hz
#hz = 250
#win = int(0.4*hz)


mean_acc = pd.rolling_mean(acc, window = win, center=True)
std_acc = pd.rolling_std(acc, window = win, center=True)
std_orient = pd.rolling_std(orient, window=win, center=True)
sum_mean_std = [ i + j for i,j in zip(mean_acc, std_acc) ]
dist_sum_mean = np.array([ abs(i-j) for i,j in zip(mean_acc, sum_mean_std) ])
dist_sum_mean[np.isnan(dist_sum_mean)] = 0


# In[]:

dummy_start_bal = []

for i in range(len(dist_sum_mean)-5):
    count = 0
    for j in range(5):
        if 0 < dist_sum_mean[i+j] <= 2:
            count = count + 1
    if count == 5:
        for k in range(5):
            if orient[i] < .3 and std_orient[i] < .1:
                dummy_start_bal.append(i+k)
            
start_bal = np.unique(dummy_start_bal)


# In[]:

bal_phase = []
bal_phase = [10]*len(acc)

for i in start_bal:
    bal_phase[i] = 0
    
#This is the end of the algorithm to determine the balance phase
up = 500
down = 950    
plt.figure(3)
plt.plot(bal_phase[up:down])
plt.plot(rdata['AccZ'][up:down])
#plt.plot(std_acc[up:down])
plt.plot(std_orient[up:down])
plt.show()

# In[]:

#plt.figure(4)
#plt.plot(ldata['AccZ'])
#plt.plot(hdata['AccZ'])
#plt.legend()
#plt.show()
    
    
    


    
