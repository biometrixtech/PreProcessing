# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 09:55:20 2016

@author: ankur
"""

import numpy as np
from itertools import *
from findPeaks import detect_peaks
from scipy.signal import periodogram
from scipy.stats import kurtosis

# FUNCTION THAT WILL CREATE FEATURES FOR EACH SAMPLING WINDOW
def createFeatures(W, Fs, promMPD, promMPH, promPeakThresh, weakMPD, weakMPH, weakPeakThresh):
    
    featureVector = np.sqrt(np.mean(np.square(W)))
    featureVector = np.hstack((featureVector, np.mean(W)))
    featureVector = np.hstack((featureVector, np.std(W)))
    featureVector = np.hstack((featureVector, np.array(kurtosis(W))))
    
    # interquartile feature
    q75, q25 = np.percentile(W, [75, 25])
    featureVector = np.hstack((featureVector, np.array(q75 - q25)))
        
    #autocorrelation
    c = np.correlate(W, W, 'full') #determining the autocorrelation of the sampled window
    c = c[len(W):] #only reading autocorrelation values with greater than zero lag
    c = (2*(c - min(c))/(max(c) - min(c))) - 1 #normalizing the autocorrelation values 
    
    n = 5 # numbr of equaly spaced bins
    featureVector = np.hstack((featureVector, np.array(np.sum(c[:(len(c)/n)]))))
    featureVector = np.hstack((featureVector, np.array(np.sum(c[len(c)/n:2*(len(c)/n)]))))
    featureVector = np.hstack((featureVector, np.array(np.sum(c[2*(len(c)/n):3*(len(c)/n)]))))
    featureVector = np.hstack((featureVector, np.array(np.sum(c[3*(len(c)/n):4*(len(c)/n)]))))
    featureVector = np.hstack((featureVector, np.array(np.sum(c[4*(len(c)/n):5*(len(c)/n)]))))
                
    #Power band
    fband = np.linspace(0.1, 25, 11)
    f, pxx = periodogram(W, Fs)
    for m in range(len(fband)-1):
        dummyPxx = pxx[f <= fband[m+1]]
        featureVector = np.hstack((featureVector, np.array(np.mean(dummyPxx[f[:len(dummyPxx)] >= fband[m]]))))
   
    return featureVector
    
# FUNCTION TO CREATE A SLIDING WINDOW
def createWindow(s, Fs, windowSamples, overlapSamples, promMPD, promMPH, promPeakThresh, weakMPD, weakMPH, weakPeakThresh):

    
    for i in range(s.shape[1]): #looping through each signal
        featureMatrix = np.zeros((1,20))  # declaring feature matrix for each signal      
        for j in islice(count(), 0, len(s)-windowSamples, overlapSamples): #looping through each window
            W = s[j:j+windowSamples,2]            
            featureVector = createFeatures(W, Fs, promMPD, promMPH, promPeakThresh, weakMPD, weakMPH, weakPeakThresh)
            featureMatrix = np.vstack((featureMatrix, featureVector))
        
        featureMatrix = featureMatrix[1:,:]  # removing the first row of zeros
        break
    
    return featureMatrix

# FUNCTION TO CREATE LABELS FOR EACH WINDOW    
def createLabels(labels, windowSamples, overlapSamples, labelThresh):
    
    labelVector = np.zeros(1)
    
    for n in islice(count(), 0, len(labels)-windowSamples, overlapSamples):
        labwin = labels[n:n+windowSamples]
        if float(len(labwin[labwin == 1]))/len(labwin) >= labelThresh:
            labelVector = np.vstack((labelVector, np.array([1])))
        elif float(len(labwin[labwin == 2]))/len(labwin) >= labelThresh:
            labelVector = np.vstack((labelVector, np.array([2])))
        elif float(len(labwin[labwin == 3]))/len(labwin) >= labelThresh:
            labelVector = np.vstack((labelVector, np.array([3])))
        elif float(len(labwin[labwin == 4]))/len(labwin) >= labelThresh:
            labelVector = np.vstack((labelVector, np.array([4])))
        elif float(len(labwin[labwin == 5]))/len(labwin) >= labelThresh:
            labelVector = np.vstack((labelVector, np.array([5])))
        elif float(len(labwin[labwin == 6]))/len(labwin) >= labelThresh:
            labelVector = np.vstack((labelVector, np.array([6])))
        elif float(len(labwin[labwin == 7]))/len(labwin) >= labelThresh:
            labelVector = np.vstack((labelVector, np.array([7])))
        elif float(len(labwin[labwin == 8]))/len(labwin) >= labelThresh:
            labelVector = np.vstack((labelVector, np.array([8])))
        elif float(len(labwin[labwin == 9]))/len(labwin) >= labelThresh:
            labelVector = np.vstack((labelVector, np.array([9])))
        elif float(len(labwin[labwin == 10]))/len(labwin) >= labelThresh:
            labelVector = np.vstack((labelVector, np.array([10])))
        elif float(len(labwin[labwin == 15]))/len(labwin) >= labelThresh:
            labelVector = np.vstack((labelVector, np.array(15)))
        else:
            labelVector = np.vstack((labelVector, np.array([0])))
            
    labelVector = labelVector[1:]
    
    return labelVector
        
  