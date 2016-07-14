# -*- coding: utf-8 -*-
"""
Created on Tue Jul 12 12:00:16 2016

@author: Ankur
"""

import numpy as np
import matplotlib.pyplot as plt

rpath = 'C:\\Users\\Ankur\\python\\Biometrix\\Data analysis\\data exploration\\data files\\Subject5\\Subject5_rfdatabody_LESS.csv'
#rpath = 'C:\\Users\\Ankur\\python\\Biometrix\\Data analysis\\data exploration\\data files\\ChangeDirection\\Rheel_Gabby_changedirection_set1.csv'
#rpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Walking\Rheel_Gabby_walking_heeltoe_set1.csv'
#lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Walking\Lheel_Gabby_walking_heeltoe_set1.csv'   
#lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_lfdatabody_set1.csv'
#lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Stomp\Lheel_Gabby_stomp_set1.csv'
#lpath = 'C:\\Users\\Ankur\\python\\Biometrix\\Data analysis\\data exploration\\data files\\ChangeDirection\\Lheel_Gabby_changedirection_set1.csv'
lpath = 'C:\\Users\\Ankur\\python\\Biometrix\\Data analysis\\data exploration\\data files\\Subject5\Subject5_lfdatabody_LESS.csv'
#lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Jump\Lheel_Gabby_jumping_explosive_set2.csv'
#lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Walking\Lheel_Gabby_walking_heeltoe_set1.csv'
#hpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_hipdatabody_set1.csv'
hpath = 'C:\\Users\\Ankur\\python\\Biometrix\\Data analysis\\data exploration\\data files\\Subject5\\Subject5_hipdatabody_LESS.csv'

rdata = np.genfromtxt(rpath, delimiter = ",", dtype = float, names = True)
ldata = np.genfromtxt(lpath, delimiter = ",", dtype = float, names = True)
hdata = np.genfromtxt(hpath, delimiter = ",", dtype = float, names = True)

plt.figure(1)
#plt.plot(ldata['AccX'])
plt.plot(rdata['AccX'])
plt.show()

# In[]:

#This is the start of the algorithm to determine the balance phase

import pandas as pd

acc = 0
acc = rdata['AccX']
std_acc = 0
mean_acc = 0

#when sampling rate is 100Hz
hz = 100
win = int(0.2*hz)

#when sampling rate is 250Hz
hz = 250
win = int(0.4*hz)

#a = acc[:win]
mean_acc = pd.rolling_mean(acc, window = win, center=True)
std_acc = pd.rolling_std(acc, window = win, center=True)
sum_mean_std = [ i + j for i,j in zip(mean_acc, std_acc) ]
dist_sum_mean = np.array([ abs(i-j) for i,j in zip(mean_acc, sum_mean_std) ])
dist_sum_mean[np.isnan(dist_sum_mean)] = 0

print(dist_sum_mean, len(dist_sum_mean), len(acc))

plt.figure(2)
plt.plot(mean_acc)
plt.plot(sum_mean_std)
plt.plot(rdata['AccZ'])
plt.show()

# In[]:

dummy_start_bal = []

for i in range(len(dist_sum_mean)-5):
    count = 0
    for j in range(5):
        if 0 < dist_sum_mean[i+j] <= 2:
            count = count + 1
    if count == 5:
        for k in range(5):
            dummy_start_bal.append(i+k)
            
start_bal = np.unique(dummy_start_bal)
        
print(start_bal)

#This is the end of the algorithm to determine the balance phase

# In[]:

bal_phase = []
bal_phase = [10]*len(acc)

for i in start_bal:
    bal_phase[i] = 0
    
plt.figure(3)
plt.plot(bal_phase)
plt.plot(rdata['AccZ'])
plt.show()

# In[]:

#plt.figure(4)
#plt.plot(ldata['AccZ'])
#plt.plot(hdata['AccZ'])
#plt.legend()
#plt.show()
    
    
    


    
