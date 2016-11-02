# -*- coding: utf-8 -*-
"""
Created on Mon Oct 17 17:33:37 2016

@author: ankur
"""

import numpy as np
from sklearn.decomposition import PCA
from createFeaturesIED import create_window, create_labels
from sklearn.ensemble import RandomForestClassifier
import pickle
import pandas as pd


def _split_lf_hip_rf(data, training):
    
    """
    Separate left foot, right foot and hip data to respective variables.
    
    Args:
        data: entire dataset
        training: True/False, if we are training the IED model or not
        
    Returns:
        hz: sampling rate
        lfoot: all left foot data
        hipp: all hip data
        rfoot: all right foot data
        if Training == True:
            labels: exercise ID labels
    """
        
    if training == False:
        hz = np.array(data['epoch_time'].copy())
        lfoot = np.array(data[['LaX', 'LaY', 'LaZ', 'LeX', 'LeY', 'LeZ']]\
                        .copy())
        hipp = np.array(data[['HaX', 'HaY', 'HaZ', 'HeX', 'HeY', 'HeZ']]\
                        .copy())
        rfoot = np.array(data[['RaX', 'RaY', 'RaZ', 'ReX', 'ReY', 'ReZ']]\
                        .copy())
        
        return hz, lfoot, hipp, rfoot
    else:
        hz = np.array(data['epoch_time'].copy())
        lfoot = np.array(data[['LaX', 'LaY', 'LaZ', 'LeX', 'LeY', 'LeZ']]\
                        .copy())
        hipp = np.array(data[['HaX', 'HaY', 'HaZ', 'HeX', 'HeY', 'HeZ']]\
                        .copy())
        rfoot = np.array(data[['RaX', 'RaY', 'RaZ', 'ReX', 'ReY', 'ReZ']]\
                        .copy())
        labels = np.array(data['ActivityID'].copy())
        
        return hz, lfoot, hipp, rfoot, labels
    
    
def _create_signals(sensor_data):
    
    """
    Create signals from which features will be extracted.
    
    Args:
        sensor_data: all left foot/hip/right foot data
        
    Returns:
        sig: acceleration and euler signals
    
    """
    
    pca = PCA(n_components = 1)  # defining the PCA function
    
    # Acceleration Signals
    sig = sensor_data[:,0:3]  # copying aX, aY, aZ
    sig = np.hstack((sig, np.array(sensor_data[:,0]**2 + sensor_data[:,1]**2 
    + sensor_data[:,2]**2).reshape(len(sensor_data),1))) 
    # Acceleration magnitude
    sig = np.hstack((sig, np.array(pca.fit_transform(
    sensor_data[:,0:3])).reshape(len(sensor_data),1)))  # First principal 
    # component of aX, aY, aZ
    
    # Euler Signals
    sig = np.hstack((sig, np.array(sensor_data[:,4]).reshape(
    len(sensor_data),1)))  # copying eX, eY, eZ
    sig = np.hstack((sig, np.array(sensor_data[:,3]**2 + sensor_data[:,4]**2 
    + sensor_data[:,5]**2).reshape(len(sensor_data),1))) 
    # Euler angle magnitude
    sig = np.hstack((sig, np.array(pca.fit_transform(
    sensor_data[:,3:6])).reshape(len(sensor_data),1)))  # First principal 
    # component of EulerX, EulerY, EulerZ
    sig = np.hstack((sig, np.array(pca.fit_transform(
    sensor_data[:,4:6])).reshape(len(sensor_data),1)))  # First principal 
    # component of EulerY, EulerZ
        
    return sig
    
    
def preprocess_ied(data, training = False):
    
    """
    Create signals, features to train/predict labels.
    
    Args: 
        data: sensor data
        training: True/False, train the IED system or just predicting
        
    Returns:
        combined_feature_matrix: features obtained from the different signals
        if training == True:
            lab: exercise ID when training the IED model
    """
    
    # Convert data to pandas dataframe
    df = pd.DataFrame(data.epoch_time)
    df.columns = ['epoch_time']
    df['LaX'] = data.LaX
    df['LaY'] = data.LaY
    df['LaZ'] = data.LaZ
    df['LeX'] = data.LeX
    df['LeY'] = data.LeY
    df['LeZ'] = data.LeZ
    
    df['HaX'] = data.HaX
    df['HaY'] = data.HaY
    df['HaZ'] = data.HaZ
    df['HeX'] = data.HeX
    df['HeY'] = data.HeY
    df['HeZ'] = data.HeZ
    
    df['RaX'] = data.RaX
    df['RaY'] = data.RaY
    df['RaZ'] = data.RaZ
    df['ReX'] = data.ReX
    df['ReY'] = data.ReY
    df['ReZ'] = data.ReZ
    
    # split sampling rate, hip data, left foot data and right foot data
    if training == False:
        hz, lfoot, hipp, rfoot = _split_lf_hip_rf(df, training)
    else:
        hz, lfoot, hipp, rfoot, labels = _split_lf_hip_rf(df, training)
    
    # create signals to extract features
    lfsig = _create_signals(lfoot)  # creating the left foot signals
    hipsig = _create_signals(hipp)  # creating the hip signals
    rfsig = _create_signals(rfoot)  # creating the right foot signals
    
    # define parameters
    # Parameters for the sampling window
    fs = 250  # sampling frequency
    window_time = 5  # number of seconds to determine length of sliding window
    window_samples = int(fs*window_time)  # sliding window length
    nsecjump = 0.2  # number of seconds for the sliding window to jump
    overlap_samples = int(fs*nsecjump)
    
    # Parameters for feature creation
    nfeatures = 20  # number of features
    
    # defining the parameters to determine the number of prominent peaks
    prom_mpd = 20  # minimum peak distance for prominent peaks
    prom_mph = -1  # minimum peak height for prominent peaks
    prom_peak_thresh = 0.5  # height threshold for number of maximum 
    # peaks feature
    
    # defining the parameters to determine the number of weak peaks
    weak_mpd = 20  # minimum peak distance for weak peaks
    weak_mph = -1  # minimum peak height for weak peaks
    weak_peak_thresh = 0.3  # height threshold for number of minimum 
    # peaks feature
    
    # Parameters for labelling each window
    label_thresh = 0.5  # x% of window 
    
    # determine the features and labels for each window
    lf_feature_matrix = create_window(lfsig, fs, window_samples, 
                                      overlap_samples, prom_mpd, prom_mph, 
                                      prom_peak_thresh, weak_mpd, weak_mph, 
                                      weak_peak_thresh)
    hip_feature_matrix = create_window(hipsig, fs, window_samples, 
                                       overlap_samples, prom_mpd, prom_mph, 
                                       prom_peak_thresh, weak_mpd, weak_mph, 
                                       weak_peak_thresh)
    rf_feature_matrix = create_window(rfsig, fs, window_samples, 
                                      overlap_samples, prom_mpd, prom_mph, 
                                      prom_peak_thresh, weak_mpd, weak_mph, 
                                      weak_peak_thresh)
    
    combined_feature_matrix = np.concatenate((lf_feature_matrix, 
                                              hip_feature_matrix), axis = 1)
    
    if training == True:
        lab = create_labels(labels, window_samples, overlap_samples, 
                            label_thresh)
        return combined_feature_matrix, lab
    else:
        return combined_feature_matrix


def train_ied(data):
    
    """
    Create features and labels for each window. Train the IED model.
    
    Args:
        data: sensor data
        
    Returns:
        fit: trained IED model
    """
    
    # create the feature matrix and labels for the window 
    combined_feature_matrix, lab = preprocess_ied(data)
    traincombined_feature_matrix = combined_feature_matrix
    train_lab = lab
    
    # train the classification model
    clf = RandomForestClassifier(n_estimators = 20, max_depth = 10, 
                                 criterion = 'entropy', max_features='auto', 
                                 random_state = 1, n_jobs = -1)    
    fit = clf.fit(traincombined_feature_matrix, 
                  train_lab.reshape((len(train_lab),)))
                  
    return fit
    
        
def mapping_labels_on_data(predicted_labels, len_data):
    
    """
    Map the labels for each window onto the sensor data. Length of the
    mapped labels must be the same as that of the sensor data.
    
    Args:
        predicted_labels: labels predicted from the IAD model
        len_data: length of the sensor data
        
    Returns:
        test_map_labels: mapped labels
    """
    
    test_map_labels = []
    for i in range(1,len(predicted_labels)):
        for j in range(50):
            test_map_labels.append(predicted_labels[i])
#            if predicted_labels[i-1] == 0 and predicted_labels[i] == 0:
#                test_map_labels.append(0)
#            elif (predicted_labels[i-1] == 0 and predicted_labels[i] == 1) or (predicted_labels[i-1] == 1 and predicted_labels[i] == 0) or (predicted_labels[i-1] == 1 and predicted_labels[i] == 1):
#                test_map_labels.append(1)
#            elif (predicted_labels[i-1] == 0 and predicted_labels[i] == 2) or (predicted_labels[i-1] == 2 and predicted_labels[i] == 0) or (predicted_labels[i-1] == 2 and predicted_labels[i] == 2):
#                test_map_labels.append(2)
#            elif (predicted_labels[i-1] == 0 and predicted_labels[i] == 3) or (predicted_labels[i-1] == 3 and predicted_labels[i] == 0) or (predicted_labels[i-1] == 3 and predicted_labels[i] == 3):
#                test_map_labels.append(3)
#            elif (predicted_labels[i-1] == 0 and predicted_labels[i] == 4) or (predicted_labels[i-1] == 4 and predicted_labels[i] == 0) or (predicted_labels[i-1] == 4 and predicted_labels[i] == 4):
#                test_map_labels.append(4)
#            elif (predicted_labels[i-1] == 0 and predicted_labels[i] == 5) or (predicted_labels[i-1] == 5 and predicted_labels[i] == 0) or (predicted_labels[i-1] == 5 and predicted_labels[i] == 5):
#                test_map_labels.append(5)
#            elif (predicted_labels[i-1] == 0 and predicted_labels[i] == 6) or (predicted_labels[i-1] == 6 and predicted_labels[i] == 0) or (predicted_labels[i-1] == 6 and predicted_labels[i] == 6):
#                test_map_labels.append(6)
#            elif (predicted_labels[i-1] == 0 and predicted_labels[i] == 7) or (predicted_labels[i-1] == 7 and predicted_labels[i] == 0) or (predicted_labels[i-1] == 7 and predicted_labels[i] == 7):
#                test_map_labels.append(7)
#            elif (predicted_labels[i-1] == 0 and predicted_labels[i] == 8) or (predicted_labels[i-1] == 8 and predicted_labels[i] == 0) or (predicted_labels[i-1] == 8 and predicted_labels[i] == 8):
#                test_map_labels.append(8)
#            elif (predicted_labels[i-1] == 0 and predicted_labels[i] == 9) or (predicted_labels[i-1] == 9 and predicted_labels[i] == 0) or (predicted_labels[i-1] == 9 and predicted_labels[i] == 9):
#                test_map_labels.append(9)
#            elif (predicted_labels[i-1] == 0 and predicted_labels[i] == 10) or (predicted_labels[i-1] == 10 and predicted_labels[i] == 0) or (predicted_labels[i-1] == 10 and predicted_labels[i] == 10):
#                test_map_labels.append(10)
#            elif (predicted_labels[i-1] == 0 and predicted_labels[i] == 15) or (predicted_labels[i-1] == 15 and predicted_labels[i] == 0) or (predicted_labels[i-1] == 15 and predicted_labels[i] == 15):
#                test_map_labels.append(15)

    # check if length of mapped data is the same as that of the sensor data
    if len_data > len(test_map_labels):            
        for k in range(len_data-len(test_map_labels)):
            test_map_labels.append(0)
        
    return np.array(test_map_labels)
    
if __name__ == "__main__":
    
    import pandas as pd
    import matplotlib.pyplot as plt
    import time






