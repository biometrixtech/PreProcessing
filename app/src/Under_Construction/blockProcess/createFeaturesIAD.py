# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 18:05:35 2016

@author: ankur
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Oct  4 14:03:32 2016

@author: ankurmanikandan
"""

import numpy as np
from itertools import *
from findPeaks import detect_peaks
from scipy.signal import periodogram

# FUNCTION THAT WILL CREATE FEATURES FOR EACH SAMPLING WINDOW
def createFeatures(W, Fs, promMPD, promMPH, promPeakThresh, weakMPD, weakMPH, weakPeakThresh):
    
    featureVector = np.sqrt(np.mean(np.square(W)))
    featureVector = np.hstack((featureVector, np.mean(W)))
    featureVector = np.hstack((featureVector, np.std(W)))
    featureVector = np.hstack((featureVector, np.var(W)))
    featureVector = np.hstack((featureVector, np.sqrt(np.mean(np.square(np.cumsum(W))))))
    featureVector = np.hstack((featureVector, np.sqrt(np.mean(np.square(W[:int(len(W)/2)])))))
    featureVector = np.hstack((featureVector, np.sqrt(np.mean(np.square(W[int(len(W)/2):])))))
    featureVector = np.hstack((featureVector, np.mean(W[:int(len(W)/2)])))
    featureVector = np.hstack((featureVector, np.mean(W[int(len(W)/2):])))
    featureVector = np.hstack((featureVector, np.std(W[:int(len(W)/2)])))
    featureVector = np.hstack((featureVector, np.std(W[int(len(W)/2):])))
    featureVector = np.hstack((featureVector, np.var(W[:int(len(W)/2)])))
    featureVector = np.hstack((featureVector, np.var(W[int(len(W)/2):])))
    
    #autocorrelation
    c = np.correlate(W, W, 'full') #determining the autocorrelation of the sampled window
    c = c[len(W):] #only reading autocorrelation values with greater than zero lag
    c = (2*(c - min(c))/(max(c) - min(c))) - 1 #normalizing the autocorrelation values 
        
    featureVector = np.hstack((featureVector, np.array(len(detect_peaks(c, show = False))))) #number of autocorrelation peaks
    
    #maximum autocorrelation value
    if np.array(detect_peaks(c, show = False)).size == 0:
        featureVector = np.hstack((featureVector, np.array([0])))
    else:
        featureVector = np.hstack((featureVector, np.array(max(c[detect_peaks(c, show = False)]))))
    
    #height of the first autocorrelation peak after zero crossing
    for k in range(len(c)-1):
        if c[k] <= 0 and c[k+1] > 0:
            pks = np.array(detect_peaks(c[k+1:], show = False))
            break
        elif c[k] >=0 and c[k+1] < 0:
            pks = np.array(detect_peaks(c[k+1:], show = False))
            break
        else:
            pks = np.array([])
    
    if pks.size == 0:
        featureVector = np.hstack((featureVector, np.array([0])))
    else:
        featureVector = np.hstack((featureVector, np.array(c[pks[0]])))
        
    #Prominent peaks
    maxPeakCount = 0
    if np.array(detect_peaks(c, mph = promMPH, mpd = promMPD)).size == 0:
        featureVector = np.hstack((featureVector, np.array([0])))
    elif len(detect_peaks(c, mph = promMPH, mpd = promMPD)) == 1:
        featureVector = np.hstack((featureVector, np.array([1])))
    else:
        pks = np.array(c[detect_peaks(c, mph = promMPH, mpd = promMPD)])
        for l in range(len(pks)-1):
            if abs(pks[l] - pks[l+1]) >= promPeakThresh:
                maxPeakCount = maxPeakCount + 1
        featureVector = np.hstack((featureVector, np.array(maxPeakCount)))
        
    #Weak peaks
    maxWeakPeakCount = 0
    if np.array(detect_peaks(c, mph = weakMPH, mpd = weakMPD)).size == 0:
        featureVector = np.hstack((featureVector, np.array([0])))
    elif len(detect_peaks(c, mph = weakMPH, mpd = weakMPD)) == 1:
        featureVector = np.hstack((featureVector, np.array([1])))
    else:
        pks = np.array(c[detect_peaks(c, mph = weakMPH, mpd = weakMPD)])
        for l in range(len(pks)-1):
            if abs(pks[l] - pks[l+1]) <= weakPeakThresh:
                maxWeakPeakCount = maxWeakPeakCount + 1
        featureVector = np.hstack((featureVector, np.array(maxWeakPeakCount)))
        
    #Power band
    fband = np.linspace(0.1, 25, 11)
    f, pxx = periodogram(W, Fs)
    for m in range(len(fband)-1):
        dummyPxx = pxx[f <= fband[m+1]]
        featureVector = np.hstack((featureVector, np.mean(dummyPxx[f[:len(dummyPxx)] >= fband[m]])))
   
    return featureVector
    
# FUNCTION TO CREATE A SLIDING WINDOW
def createWindow(s, Fs, windowSamples, overlapSamples, promMPD, promMPH, promPeakThresh, weakMPD, weakMPH, weakPeakThresh):

    featureMatrix = np.zeros((1,28))  # declaring feature matrix for each signal      
    for j in islice(count(), 0, len(s)-windowSamples, overlapSamples): #looping through each window
        W = s[j:j+windowSamples,2]            
        featureVector = createFeatures(W, Fs, promMPD, promMPH, promPeakThresh, weakMPD, weakMPH, weakPeakThresh)
        featureMatrix = np.vstack((featureMatrix, featureVector))
        
    featureMatrix = featureMatrix[1:,:]  # removing the first row of zeros

    return featureMatrix

# FUNCTION TO CREATE LABELS FOR EACH WINDOW    
def createLabels(labels, windowSamples, overlapSamples, labelThresh):
    
    labelVector = np.zeros(1)
    
    for n in islice(count(), 0, len(labels)-windowSamples, overlapSamples):
        labwin = labels[n:n+windowSamples]
        if float(len(labwin[labwin == 1]))/len(labwin) >= labelThresh:
            labelVector = np.vstack((labelVector, np.array([1])))
        else:
            labelVector = np.vstack((labelVector, np.array([0])))
            
    labelVector = labelVector[1:]
    
    return labelVector
        
  