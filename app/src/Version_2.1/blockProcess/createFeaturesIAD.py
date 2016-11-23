# -*- coding: utf-8 -*-
"""
Created on Tue Oct  4 14:03:32 2016

@author: ankurmanikandan
"""

import numpy as np
from scipy.signal import periodogram

from findPeaks import detect_peaks
from dynamicSamplingRate import handle_dynamic_sampling, \
handle_dynamic_sampling_create_features, max_boundary


def create_window(s, epoch_time, window_samples, overlap_samples, prom_mpd, 
                  prom_mph, prom_peak_thresh, weak_mpd, weak_mph, 
                  weak_peak_thresh):
    
    """
    Create sampling windows with specified size to determine features.
    
    Args:
        s: left foot/hip/right foot signals
        epoch_time: an array, epoch time from sensor
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

    feature_matrix = np.zeros((1, 28))  # declaring feature matrix for 
    # each signal      
    max_bound_overlap = max_boundary(overlap_samples)
    max_bound_win = max_boundary(window_samples)
    
    overlap = [np.where(epoch_time[i:i+max_bound_overlap]-epoch_time[i] <= \
        overlap_samples)[-1][-1] for i in range(len(epoch_time))]
    i = 0
    while i < len(epoch_time)-1:
        epoch_time_subset = epoch_time[i:i+max_bound_win]
        w, fs = handle_dynamic_sampling_create_features(s[:, 2], 
                                                        epoch_time_subset, 
                                                        window_samples, i)
       
        feature_vector = _create_features(w, fs, prom_mpd, prom_mph, 
                                          prom_peak_thresh, weak_mpd, 
                                          weak_mph, weak_peak_thresh)
        feature_matrix = np.vstack((feature_matrix, feature_vector))
        
        i = i + overlap[i]
        
    feature_matrix = feature_matrix[1:, :]  # removing the first row of zeros

    return feature_matrix


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
        len(detect_peaks(c, show=False)))))  # number of autocorrelation peaks
    
    # maximum autocorrelation value
    if np.array(detect_peaks(c, show=False)).size == 0:
        feature_vector = np.hstack((feature_vector, np.array([0])))
    else:
        feature_vector = np.hstack((feature_vector, np.array(
            max(c[detect_peaks(c, show=False)]))))
    
    # height of the first autocorrelation peak after zero crossing
    for k in range(len(c)-1):
        if c[k] <= 0 and c[k+1] > 0:
            pks = np.array(detect_peaks(c[k+1:], show=False))
            break
        elif c[k] >= 0 and c[k+1] < 0:
            pks = np.array(detect_peaks(c[k+1:], show=False))
            break
        else:
            pks = np.array([])
    
    if pks.size == 0:
        feature_vector = np.hstack((feature_vector, np.array([0])))
    else:
        feature_vector = np.hstack((feature_vector, np.array(c[pks[0]])))
        
    # Prominent peaks
    max_peak_count = 0
    if np.array(detect_peaks(c, mph=prom_mph, mpd=prom_mpd)).size == 0:
        feature_vector = np.hstack((feature_vector, np.array([0])))
    elif len(detect_peaks(c, mph=prom_mph, mpd=prom_mpd)) == 1:
        feature_vector = np.hstack((feature_vector, np.array([1])))
    else:
        pks = np.array(c[detect_peaks(c, mph=prom_mph, mpd=prom_mpd)])
        for l in range(len(pks)-1):
            if abs(pks[l] - pks[l+1]) >= prom_peak_thresh:
                max_peak_count = max_peak_count + 1
        feature_vector = np.hstack((feature_vector, np.array(max_peak_count)))
        
    # Weak peaks
    max_weak_peak_count = 0
    if np.array(detect_peaks(c, mph=weak_mph, mpd=weak_mpd)).size == 0:
        feature_vector = np.hstack((feature_vector, np.array([0])))
    elif len(detect_peaks(c, mph=weak_mph, mpd=weak_mpd)) == 1:
        feature_vector = np.hstack((feature_vector, np.array([1])))
    else:
        pks = np.array(c[detect_peaks(c, mph=weak_mph, mpd=weak_mpd)])
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
    

def create_labels(labels, window_samples, overlap_samples, label_thresh,
                  epoch_time):
    
    """
    Create label for each sampling window.
    
    Args:
        labels: activity labels, 1's & 0's
        window_samples: sliding window length
        overlap_samples: how many samples must the next window overlap of 
        the previous window
        label_thresh: threshold for labelling a window 1 or 0
        epoch_time: an array, epoch time from sensor
        
    Returns:
        label_vector: a vector of labels for each window
    """
    
    label_vector = np.zeros(1)
    max_bound_overlap = max_boundary(overlap_samples)
    max_bound_win = max_boundary(window_samples)
    
    overlap = [np.where(epoch_time[i:i+max_bound_overlap]-epoch_time[i] <= \
    overlap_samples)[-1][-1] for i in range(len(epoch_time))]
    i = 0
    while i < len(epoch_time)-1:
        epoch_time_subset = epoch_time[i:i+max_bound_win]
        labwin = handle_dynamic_sampling(labels, epoch_time_subset, 
                                         window_samples, i)
        if float(len(labwin[labwin == 1]))/len(labwin) >= label_thresh:
            label_vector = np.vstack((label_vector, np.array([1])))
        else:
            label_vector = np.vstack((label_vector, np.array([0])))
           
        i = i + overlap[i]
            
    label_vector = label_vector[1:]
    
    return label_vector
        
  