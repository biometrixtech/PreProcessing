# -*- coding: utf-8 -*-
"""
Created on Thu Jun  2 14:01:46 2016

@author: Brian
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def Move(std, w, new_u, new_std): #inputs array of st. devs    
    if std > new_u + 1*new_std and std >1.2: #if data point exceeds 1 SD and is great than 1.2
        return 1 #add to list
    else:
        return 0 #add to list

def Grad_Move(u, w, new_u, new_std): #inputs array of data points 
    if (u > new_u + 1*new_std or u < new_u - 1*new_std) and abs(u) > 1.5:#if data point exceeds 1 SD and is great than 1.5
        return 1 #add to list
    else:
        return 0 #add to list
            
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

def Body_Phase(right, left):
    phase = [] #store body phase decisions
    for i in range(len(right)):
        if right[i] == 0 and left[i] == 0: #decide in balance phase
            phase.append(0) #append to list
        elif right[i] == 1 and left[i] == 0: #decide right foot off ground
            phase.append(10) #append to list
        elif right[i] == 0 and left[i] == 1: #decide left foot off ground
            phase.append(20) #append to list
        elif right[i] == 1 and left[i] == 1: #decide both feet off ground
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
    
