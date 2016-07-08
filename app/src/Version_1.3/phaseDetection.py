# -*- coding: utf-8 -*-
"""
Created on Thu Jul 07 16:27:47 2016

@author: Ankur
"""

"""
#############################################INPUT/OUTPUT####################################################
Function: combine_phase
Inputs: AccZ right and left feet; EulerY angles for right and left feet; sampling rate
Outputs: 2 arrays; left foot phase; right foot phase
#############################################################################################################
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from itertools import islice

def Move(std, pitch, w): #inputs array of st. devs
    infl = .0001 #determines how sticky you want the mean and std to be
    new_u = np.mean(std[int(.5*w):int(1.5*w)]) #determine initial mean
    #print(new_u)
    new_std = np.std(std[int(.5*w):int(1.5*w)]) #determine initial mean
    store = [0]*w #initialize list with first 2*w terms = 0    
    for i in range(w, len(std)):
        if std[i] > new_u + 1*new_std and std[i] >1.2: #if data point exceeds 1 SD and is great than 1.2
            new_u = (new_u + infl*std[i])/(1+infl) #find new mean
            new_std = (new_std + infl*(np.sqrt((std[i]-new_u)**2))/(1+infl)) #find new SD
            store.append(1) #add to list
        else:
            new_u = (new_u + infl*std[i])/(1+infl) #find new mean
            new_std = (new_std + infl*(np.sqrt((std[i]-new_u)**2)))/(1+infl) #find new SD
            if pitch[i] >= .9: 
                store.append(1) #add to list
            else:
                store.append(0)
    return store

def Grad_Move(u, pitch, w): #inputs array of data points
    infl = .00015 #determines how sticky you want mean and std to be
    
    new_u = np.mean(u[int(.5*w):int(1.5*w)]) #determine initial mean
    new_std = np.std(u[int(.5*w):int(1.5*w)]) #determine initial mean
    store = [0]*w  #initialize list with first 2*w terms = 0  
    for i in range(w, len(u)):
        if (u[i] > new_u + 1*new_std or u[i] < new_u - 1*new_std) and abs(u[i]) > 1.5:#if data point exceeds 1 SD and is great than 1.5
            new_u = (new_u + infl*u[i])/(1+infl) #find new mean
            new_std = (new_std + infl*(np.sqrt((u[i]-new_u)**2))/(1+infl)) #find new SD
            store.append(1) #add to list
        else:
            new_u = (new_u + infl*u[i])/(1+infl) #find new mean
            new_std = (new_std + infl*(np.sqrt((u[i]-new_u)**2)))/(1+infl) #find new SD
            if pitch[i] >= .9: 
                store.append(1) #add to list
            else:
                store.append(0)
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

def Phase_Detect(series, pitch, hz):
    w = int(.08*hz) #define rolling mean and st dev window
    edge = int(.2*hz) #define window to average moving decisions over
    uaZ = pd.rolling_mean(series, window=w, center=True) #take rolling mean
    stdaZ = pd.rolling_std(series, window=w, center=True) #take rolling st dev
    
    move = Move(stdaZ, pitch, w) #determine if there is sudden move in data
    gmove = Grad_Move(uaZ, pitch, w) #determine if there is gradual move in data
    cmove = Comb_Move(move, gmove) #combine two types of moves
    mscore = pd.rolling_mean(cmove, window=edge) #take rolling mean of moves to handle discontinuities
    trans = Final(mscore) #determine if in data point is in moving phase
    final = Fix_Edges(trans, edge) #fix right edge since rolling mean wrongly extends moving regions
    
    return final #return array

def Body_Phase(right, left, rpitch, lpitch, hz):
    r = Phase_Detect(right, rpitch, hz) #run phase detect on right foot
    l = Phase_Detect(left, lpitch, hz) #run phase detect on left foot
    
    phase = [] #store body phase decisions
    for i in range(len(r)):
        if r[i] == 0 and l[i] == 0: #decide in balance phase
            phase.append(0) #append to list
        elif r[i] == 1 and l[i] == 0: #decide right foot off ground
            phase.append(1) #append to list
        elif r[i] == 0 and l[i] == 1: #decide left foot off ground
            phase.append(2) #append to list
        elif r[i] == 1 and l[i] == 1: #decide both feet off ground
            phase.append(3) #append to list
    return np.array(phase)
    
def bound_det_lf(p):
    
    start_move = []
    end_move = []
    
    for i in range(len(p)-1):
        if p[i] == 0 and p[i+1] == 2:
            start_move.append(i+1)
        elif p[i] == 1 and p[i+1] == 2:
            start_move.append(i+1)
        elif p[i] == 0 and p[i+1] == 3:
            start_move.append(i+1)
        elif p[i] == 1 and p[i+1] == 3:
            start_move.append(i+1)
        elif p[i] == 2 and p[i+1] == 0:
            end_move.append(i)
        elif p[i] == 2 and p[i+1] == 1:
            end_move.append(i)
        elif p[i] == 3 and p[i+1] == 0:
            end_move.append(i)
        elif p[i] == 3 and p[i+1] == 1:
            end_move.append(i)
                        
    return start_move, end_move
    
def bound_det_rf(p):
    
    start_move = []
    end_move = [] 
    
    for i in range(len(p)-1):
        if p[i] == 0 and p[i+1] == 1:
            start_move.append(i+1)
        elif p[i] == 2 and p[i+1] == 1:
            start_move.append(i+1)
        elif p[i] == 0 and p[i+1] == 3:
            start_move.append(i+1)
        elif p[i] == 2 and p[i+1] == 3:
            start_move.append(i+1)
        elif p[i] == 1 and p[i+1] == 0:
            end_move.append(i)
        elif p[i] == 1 and p[i+1] == 2:
            end_move.append(i)
        elif p[i] == 3 and p[i+1] == 0:
            end_move.append(i)
        elif p[i] == 3 and p[i+1] == 2:
            end_move.append(i)
            
    return start_move, end_move
    
def impact_detect(start_move, end_move, az, hz):
    
    g = 9.80665 
    neg_thresh = -g/2 #negative threshold 
    pos_thresh = g #positive threshold 
    win = int(0.05*hz) #sampling window
    acc = 0
    start_imp = []
    end_imp = []

    for i,j in zip(start_move, end_move):
        arr_len = []
        dummy_start_imp = []
        acc = az[i:j]
        arr_len = range(len(acc)-win)
        numbers = iter(arr_len)
        for k in numbers:
            if acc[k] <= neg_thresh:
                for l in range(win):
                    if acc[k+l] >= pos_thresh:
                        dummy_start_imp.append(i+k)
                        break
                next(islice(numbers, win, 1 ), None) #skip 0.05*hz data points in the second 'for' loop
        if len(dummy_start_imp) == 1:
            start_imp.append(dummy_start_imp[0])
            end_imp.append(j)
        if len(dummy_start_imp) > 1:
            for m in range(len(dummy_start_imp)):
                if (((j-i)/2)+i) < dummy_start_imp[m] <= j:
                    start_imp.append(dummy_start_imp[m])
                    end_imp.append(j)
                    break
                
    imp = []
    imp = [ [i,j] for i,j in zip(start_imp, end_imp) ]
    
    return np.array(imp)

def combine_phase(laccz, raccz, rpitch, lpitch, hz):
    
    ph = Body_Phase(raccz, laccz, rpitch, lpitch, hz) #balance phase for both the right and left feet
    
    lf_ph = list(ph)
    rf_ph = list(ph)
    
    lf_sm, lf_em = bound_det_lf(lf_ph) #detecting the start and end points of the left foot movement phase
    rf_sm, rf_em = bound_det_rf(rf_ph) #detecting the start and end points of the right foot movement phase
    
    lf_imp = impact_detect(lf_sm, lf_em, laccz, hz) #starting and ending point of the impact phase for the left foot
    rf_imp = impact_detect(rf_sm, rf_em, raccz, hz) #starting and ending points of the impact phase for the right foot

    for i,j in zip(lf_imp[:,0], lf_imp[:,1]):
        lf_ph[i:j] = [4]*int(j-i) #decide impact phase for the left foot
    
    for x,y in zip(rf_imp[:,0], rf_imp[:,1]):
        rf_ph[x:y] = [5]*int(y-x) #decide impact phase for the right foot            
            
    return np.array(lf_ph), np.array(rf_ph)
    
if __name__ == "__main__":    
    
    rpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_rfdatabody_LESS.csv'
    #rpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\ChangeDirection\Rheel_Gabby_changedirection_set1.csv'
    #rpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Walking\Rheel_Gabby_walking_heeltoe_set1.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Walking\Lheel_Gabby_walking_heeltoe_set1.csv'   
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_lfdatabody_set1.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Stomp\Lheel_Gabby_stomp_set1.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\ChangeDirection\Lheel_Gabby_changedirection_set1.csv'
    lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_lfdatabody_LESS.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Jump\Lheel_Gabby_jumping_explosive_set2.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Walking\Lheel_Gabby_walking_heeltoe_set1.csv'
    #hpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_hipdatabody_set1.csv'
    hpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_hipdatabody_LESS.csv'

    rdata = pd.read_csv(rpath)
    ldata = pd.read_csv(lpath)
    hdata = pd.read_csv(hpath)
    
    sampl_rate = 250
    comp = 'AccZ'
    ptch = 'EulerY'
    racc = rdata[comp].values
    lacc = ldata[comp].values #input AccZ values!
    rpitch = rdata[ptch].values
    lpitch = ldata[ptch].values
    #ph = Body_Phase(racc, lacc, rpitch, lpitch, sampl_rate)
    
    lf_phase, rf_phase = combine_phase(ldata['AccZ'].values, rdata['AccZ'].values, rpitch, lpitch, sampl_rate)
    
    #print lf_phase
    #print rf_phase    
    
    ###Plotting
    up = 0
    down = len(rdata)
    
    aseries = ldata[up:down]
    #indic = phase[up:down]
    
    plt.figure(5)    
    plt.plot(lf_phase)
    plt.plot(ldata['AccZ'])
    #plt.title(comp)
    #plt.show()
