# -*- coding: utf-8 -*-
"""
Created on Thu Jun  2 14:01:46 2016

@author: Brian
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def Move(std, w):
    infl = .0001
    
    std = std.values
    new_u = np.mean(std[w:2*w])
    new_std = (np.std(std[w:2*w])) 
    store = [0]*(2*w)    
    for i in range(2*w, len(std)):
        if std[i] > new_u + 1*new_std and std[i] >2:
            new_u = (new_u + infl*std[i])/(1+infl)
            new_std = (new_std + infl*(np.sqrt((std[i]-new_u)**2))/(1+infl))
            store.append(1)
        else:
            new_u = (new_u + infl*std[i])/(1+infl)
            new_std = (new_std + infl*(np.sqrt((std[i]-new_u)**2)))/(1+infl)
            store.append(0)
    return store

def Grad_Move(u, w):
    infl = .00015
    
    u = u.values
    new_u = np.mean(u[w:2*w])
    new_std = (np.std(u[w:2*w])) 
    store = [0]*(2*w)    
    for i in range(2*w, len(u)):
        if (u[i] > new_u + 1*new_std or u[i] < new_u - 1*new_std) and abs(u[i]) > 2:
            new_u = (new_u + infl*u[i])/(1+infl)
            new_std = (new_std + infl*(np.sqrt((u[i]-new_u)**2))/(1+infl))
            store.append(1)
        else:
            new_u = (new_u + infl*u[i])/(1+infl)
            new_std = (new_std + infl*(np.sqrt((u[i]-new_u)**2)))/(1+infl)
            store.append(0)
    return store

def Comb_Move(row):
    if row['Move'] == 1 or row['Grad_Move'] == 1:
        return 40
    else:
        return 0
    
def FreeFall(row):
    if row['Move'] == 0 and -11.5 <= row['mean_aZ'] <= -8.5:
        return -10
    else:
        return 0

def Fill():
    pass    
    
##Subject 3 LESS
rpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\rfdatabody.csv'
lpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\lfdatabody.csv'
hpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\hipdatabody.csv'

rdata = pd.read_csv(rpath)
ldata = pd.read_csv(lpath)
hdata = pd.read_csv(hpath)

w = 20
comp = 'AccZ'
data = ldata
seriesx = data['AccX'].ix[:]
seriesy = data['AccY'].ix[:]
seriesz = data['AccZ'].ix[:]
data['mean_aX'] = pd.rolling_mean(seriesx, window=w, center=True)
data['mean_aY'] = pd.rolling_mean(seriesy, window=w, center=True)
data['mean_aZ'] = pd.rolling_mean(seriesz, window=w, center=True)
data['std_aX'] = pd.rolling_std(seriesx, window=w, center=True)
data['std_aY'] = pd.rolling_std(seriesy, window=w, center=True)
data['std_aZ'] = pd.rolling_std(seriesz, window=w, center=True)

data['Move'] = Move(data['std_aZ'], w)
data['Grad_Move'] = Grad_Move(data['mean_aZ'], w)
data['Comb_Move'] = data.apply(Comb_Move, axis=1)
#data['Move'] = Move(data[['std_aX', 'std_aY', 'std_aZ']])
#data['Free Fall'] = data.apply(FreeFall, axis=1)
up = 6000
down = 8000

mseries = data[comp].ix[up:down]
#topseries = data['+2sd'].ix[up:down]
#botseries = data['-2sd'].ix[up:down]
#indic = data['Move'].ix[up:down]
ff = data['Comb_Move'].ix[up:down]

plt.plot(mseries.values)
#plt.plot(topseries.values)
#plt.plot(botseries.values)
#plt.plot(indic.values)
plt.plot(ff.values)
plt.title(comp)
