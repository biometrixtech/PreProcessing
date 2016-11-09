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


def _create_features(w, fs, prom_mpd, prom_mph, prom_peak_thresh, weak_mpd, 
                     weak_mph, weak_peak_thresh):
    
    """
    Create feature vector for each sampling window.
    
    Args:
        w: signal
        fs: sampling rate
        prom_mpd: minimum peak distance for prominent peaks
        prom_mph: minimum peak height for prominent peaks
        prom_peak_thresh: height threshold for number of maximum peaks for
        prominent peaks
        weak_mpd: minimum peak distance for weak peaks
        weak_mph: minimum peak height for weak peaks
        weak_peak_thresh: height threshold for number of minimum peaks for
        weak peaks
        
    Returns:
        feature_vector: a vector of feature values
    """
    
    feature_vector = np.sqrt(np.mean(np.square(w)))
    feature_vector = np.hstack((feature_vector, np.mean(w)))
    feature_vector = np.hstack((feature_vector, np.std(w)))
    feature_vector = np.hstack((feature_vector, np.array(kurtosis(w))))
    
    # interquartile feature
    q75, q25 = np.percentile(w, [75, 25])
    feature_vector = np.hstack((feature_vector, np.array(q75 - q25)))
        
    #autocorrelation
    c = np.correlate(w, w, 'full')  # determining the autocorrelation of 
    # the sampled window
    c = c[len(w):]  # only reading autocorrelation values with greater 
    # than zero lag
    c = (2*(c - min(c))/(max(c) - min(c))) - 1  # normalizing the 
    # autocorrelation values 
    
    n = 5 # number of equaly spaced bins
    feature_vector = np.hstack((feature_vector, 
                                np.array(np.sum(c[:(len(c)/n)]))))
    feature_vector = np.hstack((feature_vector, 
                                np.array(np.sum(c[len(c)/n:2*(len(c)/n)]))))
    feature_vector = np.hstack((feature_vector, 
                                np.array(np.sum(c[2*(len(c)/n):3\
                                *(len(c)/n)]))))
    feature_vector = np.hstack((feature_vector, 
                                np.array(np.sum(c[3*(len(c)/n):4\
                                *(len(c)/n)]))))
    feature_vector = np.hstack((feature_vector, 
                                np.array(np.sum(c[4*(len(c)/n):5\
                                *(len(c)/n)]))))
                
    # Power band
    fband = np.linspace(0.1, 25, 11)
    f, pxx = periodogram(w, fs)
    for m in range(len(fband)-1):
        dummyPxx = pxx[f <= fband[m+1]]
        feature_vector = np.hstack((feature_vector, np.array(
        np.mean(dummyPxx[f[:len(dummyPxx)] >= fband[m]]))))
   
    return feature_vector
    
    
def create_window(s, fs, window_samples, overlap_samples, prom_mpd, prom_mph, 
                 prom_peak_thresh, weak_mpd, weak_mph, weak_peak_thresh):
                     
    """
    Create sampling windows with specified size to determine features.
    
    Args:
        s: left foot/hip/right foot signals
        fs: sampling rate
        window_samples: sliding window length
        overlap_samples: how many samples must the next window overlap of 
        the previous window
        prom_mpd: minimum peak distance for prominent peaks
        prom_mph: minimum peak height for prominent peaks
        prom_peak_thresh: height threshold for number of maximum peaks for
        prominent peaks
        weak_mpd: minimum peak distance for weak peaks
        weak_mph: minimum peak height for weak peaks
        weak_peak_thresh: height threshold for number of minimum peaks for
        weak peaks
        
    Returns:
        feature_matrix: left foot/hip/right foot feature matrix
    """
    
    for i in range(s.shape[1]):  # looping through each signal
        feature_matrix = np.zeros((1,20))  # declaring feature matrix for 
        # each signal      
        for j in islice(count(), 0, len(s)-window_samples, 
                        overlap_samples):  # looping through each window
            w = s[j:j+window_samples,2]            
            feature_vector = _create_features(w, fs, prom_mpd, prom_mph, 
                                              prom_peak_thresh, weak_mpd, 
                                              weak_mph, weak_peak_thresh)
            feature_matrix = np.vstack((feature_matrix, feature_vector))
        
        feature_matrix = feature_matrix[1:,:]  # removing the first row of zeros
        break
    
    return feature_matrix


def create_labels(labels, window_samples, overlap_samples, label_thresh):
    
    """
    Create label for each sampling window.
    
    Args:
        labels: exercise labels
        window_samples: sliding window length
        overlap_samples: how many samples must the next window overlap of 
        the previous window
        label_thresh: threshold for labelling a window 
        
    Returns:
        label_vector: a vector of labels for each window
    """
    
    label_vector = np.zeros(1)
    
    for n in islice(count(), 0, len(labels)-window_samples, overlap_samples):
        labwin = labels[n:n+window_samples]
        if float(len(labwin[labwin == 1]))/len(labwin) >= label_thresh:
            label_vector = np.vstack((label_vector, np.array([1])))
        elif float(len(labwin[labwin == 2]))/len(labwin) >= label_thresh:
            label_vector = np.vstack((label_vector, np.array([2])))
        elif float(len(labwin[labwin == 3]))/len(labwin) >= label_thresh:
            label_vector = np.vstack((label_vector, np.array([3])))
        elif float(len(labwin[labwin == 4]))/len(labwin) >= label_thresh:
            label_vector = np.vstack((label_vector, np.array([4])))
        elif float(len(labwin[labwin == 5]))/len(labwin) >= label_thresh:
            label_vector = np.vstack((label_vector, np.array([5])))
        elif float(len(labwin[labwin == 6]))/len(labwin) >= label_thresh:
            label_vector = np.vstack((label_vector, np.array([6])))
        elif float(len(labwin[labwin == 7]))/len(labwin) >= label_thresh:
            label_vector = np.vstack((label_vector, np.array([7])))
        elif float(len(labwin[labwin == 8]))/len(labwin) >= label_thresh:
            label_vector = np.vstack((label_vector, np.array([8])))
        elif float(len(labwin[labwin == 9]))/len(labwin) >= label_thresh:
            label_vector = np.vstack((label_vector, np.array([9])))
        elif float(len(labwin[labwin == 10]))/len(labwin) >= label_thresh:
            label_vector = np.vstack((label_vector, np.array([10])))
        elif float(len(labwin[labwin == 15]))/len(labwin) >= label_thresh:
            label_vector = np.vstack((label_vector, np.array(15)))
        else:
            label_vector = np.vstack((label_vector, np.array([0])))
            
    label_vector = label_vector[1:]
    
    return label_vector
        
  