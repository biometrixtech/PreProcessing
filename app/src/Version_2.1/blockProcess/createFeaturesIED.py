# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 09:55:20 2016

@author: ankur
"""

import numpy as np
from scipy.signal import periodogram
from scipy.stats import kurtosis

from dynamicSamplingRate import handle_dynamic_sampling, \
handle_dynamic_sampling_create_features


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
    
    for i in range(s.shape[1]):  # looping through each signal
        feature_matrix = np.zeros((1, 20))  # declaring feature matrix for 
        # each signal  
        overlap = [np.where(epoch_time-epoch_time[j] <= overlap_samples)\
        [-1][-1] - j for j in range(len(epoch_time))]
        k = 0
        while k < len(epoch_time)-1:
            epoch_time_subset = epoch_time[k:]
            w, fs = handle_dynamic_sampling_create_features(s[:, 2], 
                                                            epoch_time_subset, 
                                                            window_samples, k)
            feature_vector = _create_features(w, fs, prom_mpd, prom_mph, 
                                              prom_peak_thresh, weak_mpd, 
                                              weak_mph, weak_peak_thresh)
            feature_matrix = np.vstack((feature_matrix, feature_vector))
        
        feature_matrix = feature_matrix[1:, :]  # removing the first row of zeros
        i = i + overlap[i]
        break
    
    return feature_matrix


def _create_features(w, fs):
    
    """
    Create feature vector for each sampling window.
    
    Args:
        w: signal
        fs: sampling rate
        
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
    

def create_labels(labels, window_samples, overlap_samples, label_thresh,
                  epoch_time):
    
    """
    Create label for each sampling window.
    
    Args:
        labels: exercise labels
        window_samples: sliding window length
        overlap_samples: how many samples must the next window overlap of 
        the previous window
        label_thresh: threshold for labelling a window 
        epoch_time: an array, epoch time from sensor
        
    Returns:
        label_vector: a vector of labels for each window
    """
    
    label_vector = np.zeros(1)
    overlap = [np.where(epoch_time-epoch_time[i] <= overlap_samples)[-1][-1] - \
    i for i in range(len(epoch_time))]
    i = 0
    while i < len(epoch_time)-1:
        epoch_time_subset = epoch_time[i:]
        labwin = handle_dynamic_sampling(labels, epoch_time_subset, 
                                         window_samples, i)
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
            
        i = i + overlap[i]
            
    label_vector = label_vector[1:]
    
    return label_vector
        
  