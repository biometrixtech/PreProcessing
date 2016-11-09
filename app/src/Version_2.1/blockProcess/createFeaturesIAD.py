# -*- coding: utf-8 -*-
"""
Created on Tue Oct  4 14:03:32 2016

@author: ankurmanikandan
"""

import numpy as np
from itertools import *
from findPeaks import detect_peaks
from scipy.signal import periodogram


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
    feature_vector = np.hstack((feature_vector, np.var(w)))
    feature_vector = np.hstack((feature_vector, np.sqrt(np.mean(np.square(
    np.cumsum(w))))))
    feature_vector = np.hstack((feature_vector, np.sqrt(np.mean(np.square(
    w[:int(len(w)/2)])))))
    feature_vector = np.hstack((feature_vector, np.sqrt(np.mean(np.square(
    w[int(len(w)/2):])))))
    feature_vector = np.hstack((feature_vector, np.mean(w[:int(len(w)/2)])))
    feature_vector = np.hstack((feature_vector, np.mean(w[int(len(w)/2):])))
    feature_vector = np.hstack((feature_vector, np.std(w[:int(len(w)/2)])))
    feature_vector = np.hstack((feature_vector, np.std(w[int(len(w)/2):])))
    feature_vector = np.hstack((feature_vector, np.var(w[:int(len(w)/2)])))
    feature_vector = np.hstack((feature_vector, np.var(w[int(len(w)/2):])))
    
    # autocorrelation
    c = np.correlate(w, w, 'full')  # determining the autocorrelation of the 
    # sampled window
    c = c[len(w):]  # only reading autocorrelation values with greater than 
    # zero lag
    c = (2*(c - min(c))/(max(c) - min(c))) - 1  # normalizing the 
    # autocorrelation values 
        
    feature_vector = np.hstack((feature_vector, np.array(
    len(detect_peaks(c, show = False)))))  # number of autocorrelation peaks
    
    # maximum autocorrelation value
    if np.array(detect_peaks(c, show = False)).size == 0:
        feature_vector = np.hstack((feature_vector, np.array([0])))
    else:
        feature_vector = np.hstack((feature_vector, np.array(
        max(c[detect_peaks(c, show = False)]))))
    
    # height of the first autocorrelation peak after zero crossing
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
        feature_vector = np.hstack((feature_vector, np.array([0])))
    else:
        feature_vector = np.hstack((feature_vector, np.array(c[pks[0]])))
        
    # Prominent peaks
    max_peak_count = 0
    if np.array(detect_peaks(c, mph = prom_mph, mpd = prom_mpd)).size == 0:
        feature_vector = np.hstack((feature_vector, np.array([0])))
    elif len(detect_peaks(c, mph = prom_mph, mpd = prom_mpd)) == 1:
        feature_vector = np.hstack((feature_vector, np.array([1])))
    else:
        pks = np.array(c[detect_peaks(c, mph = prom_mph, mpd = prom_mpd)])
        for l in range(len(pks)-1):
            if abs(pks[l] - pks[l+1]) >= prom_peak_thresh:
                max_peak_count = max_peak_count + 1
        feature_vector = np.hstack((feature_vector, np.array(max_peak_count)))
        
    # Weak peaks
    max_weak_peak_count = 0
    if np.array(detect_peaks(c, mph = weak_mph, mpd = weak_mpd)).size == 0:
        feature_vector = np.hstack((feature_vector, np.array([0])))
    elif len(detect_peaks(c, mph = weak_mph, mpd = weak_mpd)) == 1:
        feature_vector = np.hstack((feature_vector, np.array([1])))
    else:
        pks = np.array(c[detect_peaks(c, mph = weak_mph, mpd = weak_mpd)])
        for l in range(len(pks)-1):
            if abs(pks[l] - pks[l+1]) <= weak_peak_thresh:
                max_weak_peak_count = max_weak_peak_count + 1
        feature_vector = np.hstack((feature_vector, 
                                    np.array(max_weak_peak_count)))
        
    # Power band
    fband = np.linspace(0.1, 25, 11)
    f, pxx = periodogram(w, fs)
    for m in range(len(fband)-1):
        dummy_pxx = pxx[f <= fband[m+1]]
        feature_vector = np.hstack((feature_vector, np.mean(
        dummy_pxx[f[:len(dummy_pxx)] >= fband[m]])))
   
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

    feature_matrix = np.zeros((1,28))  # declaring feature matrix for 
    # each signal      
    for j in islice(count(), 0, len(s)-window_samples, overlap_samples): 
    # looping through each window
        w = s[j:j+window_samples,2]            
        feature_vector = _create_features(w, fs, prom_mpd, prom_mph, 
                                          prom_peak_thresh, weak_mpd, 
                                          weak_mph, weak_peak_thresh)
        feature_matrix = np.vstack((feature_matrix, feature_vector))
        
    feature_matrix = feature_matrix[1:,:]  # removing the first row of zeros

    return feature_matrix


def create_labels(labels, window_samples, overlap_samples, label_thresh):
    
    """
    Create label for each sampling window.
    
    Args:
        labels: activity labels, 1's & 0's
        window_samples: sliding window length
        overlap_samples: how many samples must the next window overlap of 
        the previous window
        label_thresh: threshold for labelling a window 1 or 0
        
    Returns:
        label_vector: a vector of labels for each window
    """
    
    label_vector = np.zeros(1)
    
    for n in islice(count(), 0, len(labels)-window_samples, overlap_samples):
        labwin = labels[n:n+window_samples]
        if float(len(labwin[labwin == 1]))/len(labwin) >= label_thresh:
            label_vector = np.vstack((label_vector, np.array([1])))
        else:
            label_vector = np.vstack((label_vector, np.array([0])))
            
    label_vector = label_vector[1:]
    
    return label_vector
        
  