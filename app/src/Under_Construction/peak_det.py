# -*- coding: utf-8 -*-
"""
Created on Tue May 31 10:26:09 2016

@author: Brian
"""
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from numpy import NaN, Inf, arange, isscalar, asarray, array
    
def peakdet(v, delta, x = None):
    """
    Converted from MATLAB script at http://billauer.co.il/peakdet.html
    
    Returns two arrays
    
    function [maxtab, mintab]=peakdet(v, delta, x)
    %PEAKDET Detect peaks in a vector
    %        [MAXTAB, MINTAB] = PEAKDET(V, DELTA) finds the local
    %        maxima and minima ("peaks") in the vector V.
    %        MAXTAB and MINTAB consists of two columns. Column 1
    %        contains indices in V, and column 2 the found values.
    %      
    %        With [MAXTAB, MINTAB] = PEAKDET(V, DELTA, X) the indices
    %        in MAXTAB and MINTAB are replaced with the corresponding
    %        X-values.
    %
    %        A point is considered a maximum peak if it has the maximal
    %        value, and was preceded (to the left) by a value lower by
    %        DELTA.
    
    % Eli Billauer, 3.4.05 (Explicitly not copyrighted).
    % This function is released to the public domain; Any use is allowed.
    
    """
    #initiate lists used to store critical values    
    maxtab = []
    mintab = []
    
    #create index array
    if x is None:
        x = arange(len(v))
    
    #create value array
    v = asarray(v)
    
    if len(v) != len(x):
        sys.exit('Input vectors v and x must have same length')
    
    if not isscalar(delta):
        sys.exit('Input argument delta must be a scalar')
    
    if delta <= 0:
        sys.exit('Input argument delta must be positive')
    
    mn, mx = Inf, -Inf # initiate min, max value variable
    mnpos, mxpos = NaN, NaN #initiate min, max index variable
    
    for i in arange(len(v)):
        this = v[i] # value of current data point
        
        #check if new data point is more extreme than previous data point and assign        
        if this > mx:
            mx = this
            mxpos = x[i]
        if this < mn:
            mn = this
            mnpos = x[i]
        
        #check if max or min point (can't occur one data point after cv)
        if this < mx-delta and mx != Inf:
            maxtab.append((mxpos, mx)) #add index and value of max to lists
            mx = Inf #set new min and max to inf to force find a min
            mn = Inf
        if this > mn+delta and mn != -Inf:
            mintab.append((mnpos, mn)) #add index and value of min to lists
            mx = -Inf #set new min and max to -inf to force find a max
            mn = -Inf

    return array(maxtab), array(mintab)
        
if __name__=="__main__":
    pos = 'lf'
    root = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\' + pos + 'databody.csv'
    #root = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\BodyFrame jumping\\Rheel_Gabby_jumping_quick_set1.csv'
    
    data = pd.read_csv(root)
    
    comp = 'AccZ'
    series = data[comp].ix[4456:4528]
    maxtab, mintab = peakdet(series,5)
    plt.plot(series.values)
    plt.title(pos + '-' +comp)
#    print(mintab)
    plt.scatter(array(maxtab)[:,0], array(maxtab)[:,1], color='blue')
    plt.scatter(array(mintab)[:,0], array(mintab)[:,1], color='red')
    plt.show()