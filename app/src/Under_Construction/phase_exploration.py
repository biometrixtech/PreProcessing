# -*- coding: utf-8 -*-
"""
Created on Thu Jun  2 14:01:46 2016

@author: Brian
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
#import peak_det
import time

#def Slope(arr):
#    lst = []
#    for i in range(1, len(arr)):
#        lst.append(abs(arr[i]-arr[i-1]))
#    return lst

def Move(std, pitch, w): #inputs array of st. devs
    infl = .0001 #determines how sticky you want the mean and std to be
    new_u = np.mean(std[int(.5*w):int(1.5*w)]) #determine initial mean
    print(new_u)
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
    
#def FreeFall(move, u):
#    lst = [] #initiate list
#    for i in range(len(move)):
#        if move[i] == 0 and -11.5 <= u[i] <= -8.5: #if sudden move = 0 and accZ falls in range mark as in free fall
#            lst.append(-1) #add to list (term is NEGATIVE!)
#        else:
#            lst.append(0) #add to list
#    return np.array(lst)
#
#def FFinal(score):
#    lst = []
#    for i in range(len(score)):
#        if score[i] < 0: #if score is less than 0 mark as in free fall
#            lst.append(-10) #add to list
#        else:
#            lst.append(0) #add to list
#    return np.array(lst)
#
#def Combine(fff, final):
#    for i in range(len(fff)):
#        if fff[i] == -10: #translate free fall decisions onto final array
#            final[i] = 20 #add to final array as 20
#    return final
#        
#def FF_Impact(arr, series):
#    for i in range(len(arr)-1):
#        j=0 
#        if arr[i] == 20 and arr[i+1] == 10: #find point where transition from free fall to moving
#            j = 1
#            while arr[i+j] == 10:
#                arr[i+j] = 30 #change following points to "impact"
#                j = j+1 #keep running tally of points in "impact" phase
#                if i+j == len(arr)-1:
#                    break #exit loop if at end of array
#            maxtab, mintab = peak_det.peakdet(series[i:i+j], 10) #peak detect "impact" region
#            if len(mintab) == 0 and i+j == len(arr)-1: #exit for loop if at end of array and no mins 
#                arr[i:i+j] = 20 #reset new "impact" region to free fall
#                break
#            if len(mintab) == 0: #exit for loop if no min (false alarm for end of free fall)
#                arr[i:i+j] = 20 #reset new "impact" region
#                continue
#            impact = mintab[0][0] #find first min
#            arr[i:i+impact] = 20 #reset "impact" region in front of min
#        i = i+j #skip ahead
#    return arr
#            
#def Impact(arr, series, hz):
#    for i in range(len(arr)-1):
#        j=0
#        if arr[i] == 10 and arr[i+1] == 0: #find point where transition from moving to still
#            print(i)
#            j = 1
#            while arr[i-j] == 10:
#                j=j+1 #keep running tally of points in "moving" phase
#            print(j)
#            maxtab, mintab = peak_det.peakdet(series[i-j:i], 10) #peak detect over moving phase
#            if len(mintab) == 0 or len(maxtab) == 0: #if no min/max that matches threshold
#                continue 
#            low_int = [ y for y in mintab[:,0] if y >= j-int(hz*.24)] #find min within defined window of transition from moving to still 
#            if len(low_int) == 0: #if no min
#                continue
#            peak_int = [ x for x in maxtab[:,0] if x > min(low_int)] #find maxs that follow earliest min
#            val = min(peak_int + low_int) #find min of combined array
#            arr[i-j+int(val):i] = 30 #set impact phase from min found to moving/still transition
#    return arr

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
    
#    ff = FreeFall(move, uaZ) #determine regions of free fall
#    ff_score = pd.rolling_mean(ff, window=8, center=True) #take rolling mean of free fall to handle discontinuities
#    ff_final = FFinal(ff_score) #make determinations on if in free fall or not
#    final = Combine(ff_final, final) #combine moving, free fall, and still phases
#    final = FF_Impact(final, series) #determine impact phases for post free fall states
#    final = Impact(final, series, hz) #determine impact phases for moving from moving to not moving
    return final #return array

def Body_Phase(right, left, rpitch, lpitch, hz):
    r = Phase_Detect(right, rpitch, hz) #run phase detect on right foot
    l = Phase_Detect(left, lpitch, hz) #run phase detect on left foot
    
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
    rpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\BodyFrame walking\\RHeel_Gabby_walking_heeltoe_set1.csv'
    lpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\BodyFrame walking\\LHeel_Gabby_walking_heeltoe_set1.csv'
    hpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\BodyFrame walking\\hips_Gabby_walking_heeltoe_set1.csv'
    
#    rpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\rfdatabody.csv'
#    lpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\lfdatabody.csv'
#    hpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\hipdatabody.csv'
    
    rdata = pd.read_csv(rpath)
    ldata = pd.read_csv(lpath)
    hdata = pd.read_csv(hpath)
    
    start = time.process_time()
    comp = 'AccZ'
    ptch = 'EulerY'
    racc = rdata[comp].values
    lacc = ldata[comp].values #input AccZ values!
    rpitch = rdata[ptch].values
    lpitch = ldata[ptch].values
    output = Body_Phase(racc, lacc, rpitch, lpitch,  100)
    #output = Phase_Detect(ldata, 250)
    print(time.process_time()-start)
    
    ###Plotting
    up = 0
    down = len(rdata)
    
    aseries = ldata[up:down]
    indic = output[up:down]
    
    plt.plot(output)
    plt.plot(racc)
    plt.title(comp)
    plt.show()
