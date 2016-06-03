# -*- coding: utf-8 -*-
"""
Created on Thu Jun  2 14:01:46 2016

@author: Brian
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def Move(row):
    if row['+2sd'] - row['-2sd'] > 10:
        return 40
    else:
        return 0

def FreeFall(row):
    if row['Move'] == 0 and -11.5 <= row['mean_aZ'] <= -8.5:
        return -10
    else:
        return 0

##Subject 3 LESS
rpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\rfdatabody.csv'
lpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\lfdatabody.csv'
hpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\hipdatabody.csv'

rdata = pd.read_csv(rpath)
ldata = pd.read_csv(lpath)
hdata = pd.read_csv(hpath)

comp = 'AccZ'
data = ldata
series = data[comp].ix[:]
data['mean_aZ'] = pd.rolling_mean(series, window=20, center=True)
data['std_aZ'] = pd.rolling_std(series, window=20, center=True)
data['+2sd'] = data['mean_aZ'] + 2*data['std_aZ']
data['-2sd'] = data['mean_aZ'] - 2*data['std_aZ']
#data['Move'] = data.apply(lambda row: Move(row), axis=1) 
data['Move'] = data.apply(Move, axis=1)
data['Free Fall'] = data.apply(FreeFall, axis=1)
up = 3300
down = 4000

mseries = data[comp].ix[up:down]
topseries = data['+2sd'].ix[up:down]
botseries = data['-2sd'].ix[up:down]
indic = data['Move'].ix[up:down]
ff = data['Free Fall'].ix[up:down]

plt.plot(mseries.values)
plt.plot(topseries.values)
plt.plot(botseries.values)
plt.plot(indic.values)
plt.plot(ff.values)
plt.title(comp)
