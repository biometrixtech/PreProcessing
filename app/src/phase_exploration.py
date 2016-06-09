# -*- coding: utf-8 -*-
"""
Created on Thu Jun  2 14:01:46 2016

@author: Brian
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import peak_det
import time

def Slope(arr):
    lst = []
    for i in range(1, len(arr)):
        lst.append(abs(arr[i]-arr[i-1]))
    return lst

def Move(std, w):
    infl = .0001
    
    new_u = np.mean(std[w:2*w])
    new_std = (np.std(std[w:2*w])) 
    store = [0]*(2*w)    
    for i in range(2*w, len(std)):
        if std[i] > new_u + 1*new_std and std[i] >1:
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
    
    new_u = np.mean(u[w:2*w])
    new_std = (np.std(u[w:2*w])) 
    store = [0]*(2*w)    
    for i in range(2*w, len(u)):
        if (u[i] > new_u + 1*new_std or u[i] < new_u - 1*new_std) and abs(u[i]) > 1.5:
            new_u = (new_u + infl*u[i])/(1+infl)
            new_std = (new_std + infl*(np.sqrt((u[i]-new_u)**2))/(1+infl))
            store.append(1)
        else:
            new_u = (new_u + infl*u[i])/(1+infl)
            new_std = (new_std + infl*(np.sqrt((u[i]-new_u)**2)))/(1+infl)
            store.append(0)
    return store

def Comb_Move(move, gmove):
    lst = []
    for i in range(len(move)):
        if move[i] == 1 or gmove[i] == 1:
            lst.append(1)
        else:
            lst.append(0)
    return np.array(lst)

def Final(mscore):
    lst = []
    for i in range(len(mscore)):
        if mscore[i] > 0:
            lst.append(10)
        else:
            lst.append(0)
    return np.array(lst)

def Fix_Edges(df, edge):
    for i in range(1, len(df)):
        if df[i]-df[i-1] < 0:
            df[i-edge:i] = 0
        else:
            None
    return df
    
def FreeFall(move, u):
    lst = []
    for i in range(len(move)):
        if move[i] == 0 and -11.5 <= u[i] <= -8.5:
            lst.append(-1)
        else:
            lst.append(0)
    return np.array(lst)

def FFinal(score):
    lst = []
    for i in range(len(score)):
        if score[i] < 0:
            lst.append(-10)
        else:
            lst.append(0)
    return np.array(lst)

def Combine(fff, final):
    for i in range(len(fff)):
        if fff[i] == -10:
            final[i] = 20
    return final
        
def FF_Impact(arr, series):
    for i in range(len(arr)-1):
        j=0
        if arr[i] == 20 and arr[i+1] == 10:
            print(i)
            j = 1
            while arr[i+j] == 10:
                arr[i+j] = 30
                j = j+1
                if i+j == len(arr)-1:
                    continue
            print(j)
            maxtab, mintab = peak_det.peakdet(seriesz[i:i+j], 10)
            print(mintab)
            if len(mintab) == 0:
                arr[i:i+j] = 20
                continue
            impact = mintab[0][0]
            arr[i:i+impact] = 20
        i = i+j
    return arr
            
def Impact(arr, series):
    for i in range(len(arr)-1):
        j=0
        if arr[i] == 10 and arr[i+1] == 0:
            j = 1
            while arr[i-j] == 10:
                j=j+1
            maxtab, mintab = peak_det.peakdet(seriesz[i-j:i], 10)
            if len(mintab) == 0 or len(maxtab) == 0:
                continue
            low_int = [ y for y in mintab[:,0] if y > j-50]
            if len(low_int) == 0:
                continue
            peak_int = [ x for x in maxtab[:,0] if x > min(low_int)]
            val = min(peak_int + low_int)
            #print(i-j+int(val))
            arr[i-j+int(val):i] = 30
    return arr

#def Impact(arr, series):
#    for i in range(len(arr)):
#        j=0
#        if arr[i] == 10 and arr[i+1] ==0:
#            print(i)
#            j=1
#            while arr[i-j] == 10:
#                j=j+1
#            
#    return arr
    
##Subject 3 LESS
#rpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\BodyFrame jumping\\Rheel_Gabby_jumping_quick_set1.csv'
#lpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\BodyFrame jumping\\Lheel_Gabby_jumping_explosive_set2.csv'
#hpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\BodyFrame jumping\\hips_Gabby_jumping_quick_set1.csv'

rpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\rfdatabody.csv'
lpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\lfdatabody.csv'
hpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\hipdatabody.csv'

rdata = pd.read_csv(rpath)
ldata = pd.read_csv(lpath)
hdata = pd.read_csv(hpath)

start = time.process_time()
w = 20
edge = 50 
comp = 'AccZ'
data = ldata
#seriesx = data['AccX'].ix[:]
#seriesy = data['AccY'].ix[:]
seriesz = data['AccZ'].values
#data['mean_aX'] = pd.rolling_mean(seriesx, window=w, center=True)
#data['mean_aY'] = pd.rolling_mean(seriesy, window=w, center=True)
uaZ = pd.rolling_mean(seriesz, window=w, center=True)
daZ = Slope(seriesz)
#data['std_aX'] = pd.rolling_std(seriesx, window=w, center=True)
#data['std_aY'] = pd.rolling_std(seriesy, window=w, center=True)
stdaZ = pd.rolling_std(seriesz, window=w, center=True)

move = Move(stdaZ, w)
gmove = Grad_Move(uaZ, w)
cmove = Comb_Move(move, gmove)
mscore = pd.rolling_mean(cmove, window=edge)
trans = Final(mscore)
final = Fix_Edges(trans, edge)

ff = FreeFall(move, uaZ)
ff_score = pd.rolling_mean(ff, window=8, center=True)
ff_final = FFinal(ff_score)
final = Combine(ff_final, final)
final = FF_Impact(final, seriesz)
final = Impact(final, seriesz)
print(time.process_time()-start)

###Plotting
up = 8000
down =10000

aseries = data[comp].ix[up:down]
mseries = final[up:down]
indic = final[up:down]
#ff = data['FF_Final'].ix[up:down]

plt.plot(mseries)
plt.plot(indic)
plt.plot(aseries.values)
plt.title(comp)
