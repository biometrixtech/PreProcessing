# -*- coding: utf-8 -*-
"""
Created on Thu Jun  2 14:01:46 2016

@author: Brian
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def Move(std, w): #inputs array of st. devs
    infl = .0001 #determines how sticky you want the mean and std to be
    
    new_u = np.mean(std[w:2*w]) #determine initial mean
    new_std = (np.std(std[w:2*w])) #determine initial mean
    store = [0]*(2*w) #initialize list with first 2*w terms = 0    
    for i in range(2*w, len(std)):
        if std[i] > new_u + 1*new_std and std[i] >1.2: #if data point exceeds 1 SD and is great than 1.2
            new_u = (new_u + infl*std[i])/(1+infl) #find new mean
            new_std = (new_std + infl*(np.sqrt((std[i]-new_u)**2))/(1+infl)) #find new SD
            store.append(1) #add to list
        else:
            new_u = (new_u + infl*std[i])/(1+infl) #find new mean
            new_std = (new_std + infl*(np.sqrt((std[i]-new_u)**2)))/(1+infl) #find new SD
            store.append(0) #add to list
    return store

def Grad_Move(u, w): #inputs array of data points
    infl = .00015 #determines how sticky you want mean and std to be
    
    new_u = np.mean(u[w:2*w]) #determine initial mean
    new_std = (np.std(u[w:2*w])) #determine initial mean
    store = [0]*(2*w)  #initialize list with first 2*w terms = 0  
    for i in range(2*w, len(u)):
        if (u[i] > new_u + 1*new_std or u[i] < new_u - 1*new_std) and abs(u[i]) > 1.5:#if data point exceeds 1 SD and is great than 1.5
            new_u = (new_u + infl*u[i])/(1+infl) #find new mean
            new_std = (new_std + infl*(np.sqrt((u[i]-new_u)**2))/(1+infl)) #find new SD
            store.append(1) #add to list
        else:
            new_u = (new_u + infl*u[i])/(1+infl) #find new mean
            new_std = (new_std + infl*(np.sqrt((u[i]-new_u)**2)))/(1+infl) #find new SD
            store.append(0) #add to list
    return store

def Comb_Move(move, gmove):
    lst = [] #initiate list
    for i in range(len(move)):
        if move[i] == 1 or gmove[i] == 1: #if either move functions = 1 then mark as moving
            lst.append(1) #add to list
        else:
            lst.append(0) #if neither function = 1 dont mark as moving
    return np.array(lst)

def Final(mscore):
    lst = [] #initiate list
    for i in range(len(mscore)):
        if mscore[i] > 0: #if score is greater than 0 mark as moving
            lst.append(1) #add to list
        else:
            lst.append(0) #marked as not moving
    return np.array(lst)

def Fix_Edges(df, edge):
    for i in range(1, len(df)):
        if df[i]-df[i-1] < 0: #if point is moving to non-moving fix right edge of moving region
            df[i-edge:i] = 0 #adjust array
        else:
            None
    return df

def Phase_Detect(series, hz):
    w = int(.08*hz) #define rolling mean and st dev window
    edge = int(.2*hz) #define window to average moving decisions over
    uaZ = pd.rolling_mean(series, window=w, center=True) #take rolling mean
    stdaZ = pd.rolling_std(series, window=w, center=True) #take rolling st dev
    
    move = Move(stdaZ, w) #determine if there is sudden move in data
    gmove = Grad_Move(uaZ, w) #determine if there is gradual move in data
    cmove = Comb_Move(move, gmove) #combine two types of moves
    mscore = pd.rolling_mean(cmove, window=edge) #take rolling mean of moves to handle discontinuities
    trans = Final(mscore) #determine if in data point is in moving phase
    final = Fix_Edges(trans, edge) #fix right edge since rolling mean wrongly extends moving regions
    return final #return array

def Body_Phase(right, left, hz):
    r = Phase_Detect(right, hz) #run phase detect on right foot
    l = Phase_Detect(left, hz) #run phase detect on left foot
    
    phase = [] #store body phase decisions
    for i in range(len(r)):
        if r[i] == 0 and l[i] == 0: #decide in balance phase
            phase.append(0) #append to list
        elif r[i] == 1 and l[i] == 0: #decide right foot off ground
            phase.append(10) #append to list
        elif r[i] == 0 and l[i] == 1: #decide left foot off ground
            phase.append(20) #append to list
        elif r[i] == 1 and l[i] == 1: #decide both feet off ground
            phase.append(30) #append to list
    
    return np.array(phase)
if __name__ == "__main__":    
#    rpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\BodyFrame walking\\RHeel_Gabby_walking_heeltoe_set1.csv'
#    lpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\BodyFrame walking\\LHeel_Gabby_walking_heeltoe_set1.csv'
#    hpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\BodyFrame walking\\hips_Gabby_walking_heeltoe_set1.csv'
    
    rpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\rfdatabody.csv'
    lpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\lfdatabody.csv'
    hpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\hipdatabody.csv'
    
    rdata = pd.read_csv(rpath)
    ldata = pd.read_csv(lpath)
    hdata = pd.read_csv(hpath)
    
    comp = 'AccZ'
    rdata = rdata[comp].values
    ldata = ldata[comp].values #input AccZ values!
    output = Body_Phase(rdata, ldata, 250)
    
    ###Plotting
    up = 2000
    down = 4000
    
    aseries = rdata[up:down]
    indic = output[up:down]
    
    plt.plot(indic)
    plt.plot(aseries)
    plt.title(comp)
