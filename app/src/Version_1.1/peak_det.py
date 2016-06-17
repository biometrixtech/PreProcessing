# -*- coding: utf-8 -*-
"""
Created on Tue May 31 10:26:09 2016

@author: Brian
"""
import pandas as pd

import matplotlib.pyplot as plt
from numpy import NaN, Inf, array

"""
#############################################INPUT/OUTPUT####################################################   
Inputs: v, data point (float); i, index of data point (int); mx, current local max value (float);
mn, current local min value (float); mxpos, indexof current local max (int); mnpos, index of
current local min (int); maxtab, list of lists containing previous absolute max values and 
indexes (list);mintab, list of lists containing previous absolute min values and indexes (list)

Outputs: maxtab, list of lists containing previous absolute max values and indexes (list); mintab,
list of lists containing previous absolute min valuesand indexes (list); mx, current local max value
(float); mn, current local min value (float); mxpos, index of current local max (int); mnpos, index
of current local min (int)
#############################################################################################################
"""

def peak_det(v, i, delta, mx, mn, mxpos, mnpos, maxtab, mintab):       
    this = v # value of current data point
    
    #check if new data point is more extreme than previous data point and assign        
    if this > mx:
        mx = this
        mxpos = i
    if this < mn:
        mn = this
        mnpos = i
    
    #check if max or min point (can't occur one data point after cv)
    if this < mx-delta and mx != Inf:
        maxtab.append([mxpos, mx]) #add index and value of max to lists
        mx = Inf #set new min and max to inf to force find a min
        mn = Inf
    if this > mn+delta and mn != -Inf:
        mintab.append([mnpos, mn]) #add index and value of min to lists
        mx = -Inf #set new min and max to -inf to force find a max
        mn = -Inf

    return maxtab, mintab, mx, mn, mxpos, mnpos
        
if __name__=="__main__":
    pos = 'lf'
    root = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\' + pos + 'databody.csv'
    #root = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\BodyFrame jumping\\Rheel_Gabby_jumping_quick_set1.csv'
    
    data = pd.read_csv(root)
    
    comp = 'EulerX'
    series = data[comp].ix[0:4000]
    mn, mx = Inf, -Inf # initiate min, max value variable
    mnpos, mxpos = NaN, NaN #initiate min, max index variable
    maxtab = []
    mintab = []
    
    for i in range(len(series)):
        maxtab, mintab, mx, mn, mxpos, mnpos = peak_det(series[i], i, .1, mx, mn, mxpos, mnpos, maxtab, mintab)
    
    print(mintab)
    plt.plot(series.values)
    plt.title(pos + '-' +comp)
    plt.scatter(array(maxtab)[:,0], array(maxtab)[:,1], color='blue')
    plt.scatter(array(mintab)[:,0], array(mintab)[:,1], color='red')
    plt.show()