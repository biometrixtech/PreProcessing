# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 17:51:07 2016

@author: ankur
"""

import pickle

import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
import pandas as pd

from createFeaturesIAD import create_window, create_labels


def preprocess_iad(data, training=False):
    
    """
    Create signals, features to train/predict labels.
    
    Args:
        data: sensor data
        training: True/False, train the IAD system or just predicting
        
    Returns:
        combined_feature_matrix: features obtained from the different signals
        if training == True:
            lab: activity ID when training the IAD model, 1's & 0's
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
    if training is False:
        hz, lfoot, hipp, rfoot = _split_lf_hip_rf(df, training)
    else:
        hz, lfoot, hipp, rfoot, labels = _split_lf_hip_rf(df, training)
    
    # create signals to extract features
    lfsig = _create_signals(lfoot)  # left foot signals
    hipsig = _create_signals(hipp)  # hip signals
    rfsig = _create_signals(rfoot)  # right foot signals
    
    # define parameters
    # Parameters for the sampling window
#    fs = 250  # sampling frequency
    window_time = 5*1000  # number of milli seconds to determine length of
    # sliding window
    window_samples = window_time #int(fs*window_time)  # sliding window length
    nsecjump = 0.2*1000  # number of milli seconds for the sliding window
    # to jump
    overlap_samples = nsecjump  # int(fs*nsecjump)
    
    # Parameters for feature creation
    nfeatures = 28  # number of features
    
    # defining the parameters to determine the number of prominent peaks
    prom_mpd = 20  # minimum peak distance for prominent peaks
    prom_mph = -1  # minimum peak height for prominent peaks
    prom_peak_thresh = 0.5  # height threshold for number of maximum peaks
    # feature
    
    # defining the parameters to determine the number of weak peaks
    weak_mpd = 20  # minimum peak distance for weak peaks
    weak_mph = -1  # minimum peak height for weak peaks
    weak_peak_thresh = 0.3  # height threshold for number of minimum peaks
    # feature
    
    # Parameters for labelling each window
    label_thresh = 0.5  # x% of window
    
    # determine the features and labels for each window
    lf_feature_matrix = create_window(lfsig, data.epoch_time, window_samples,
                                      overlap_samples, prom_mpd, prom_mph,
                                      prom_peak_thresh, weak_mpd, weak_mph,
                                      weak_peak_thresh)
    hip_feature_matrix = create_window(hipsig, data.epoch_time, window_samples,
                                       overlap_samples, prom_mpd,
                                       prom_mph, prom_peak_thresh,
                                       weak_mpd, weak_mph, weak_peak_thresh)
    rf_feature_matrix = create_window(rfsig, data.epoch_time, window_samples,
                                      overlap_samples, prom_mpd, prom_mph,
                                      prom_peak_thresh, weak_mpd, weak_mph,
                                      weak_peak_thresh)
    
    # combine the left foot, hip and/or right foot feature matrices
    combined_feature_matrix = np.concatenate((lf_feature_matrix,
                                              hip_feature_matrix), axis=1)
    
    # check if training is true/false
    if training is True:
        lab = create_labels(labels, window_samples, overlap_samples,
                            label_thresh, data.epoch_time)
        return combined_feature_matrix, lab
    else:
        return combined_feature_matrix



def _split_lf_hip_rf(data, training):
    
    """
    Separate left foot, right foot and hip data to respective variables.
    
    Args:
        data: entire dataset
        training: True/False, if we are training the IAD model or not
        
    Returns:
        hz: sampling rate
        lfoot: all left foot data
        hipp: all hip data
        rfoot: all right foot data
        if Training == True:
            labels: activity ID labels, 1 for activity & 0 for non-activity
    """
        
    if training is False:
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
    
    pca = PCA(n_components=1)  # defining the PCA function
    
    # Acceleration Signals
    sig = sensor_data[:, 0:3]  # copying aX, aY, aZ
    sig = np.hstack((sig, np.array(sensor_data[:, 0]**2 + \
        sensor_data[:, 1]**2 + sensor_data[:, 2]**2).reshape(
            len(sensor_data), 1)))  # Acceleration
    # magnitude
    sig = np.hstack((sig, np.array(
        pca.fit_transform(sensor_data[:, 0:3])).reshape(len(sensor_data), 1)))
    # First principal component of aX, aY, aZ
    
    # Euler Signals
    sig = np.hstack((sig, np.array(
        sensor_data[:, 4]).reshape(len(sensor_data), 1)))  # copying eX, eY, eZ
    sig = np.hstack((sig, np.array(sensor_data[:, 3]**2 + \
        sensor_data[:, 4]**2 + sensor_data[:, 5]**2).reshape(len(
            sensor_data), 1)))
    # Euler angles magnitude
    sig = np.hstack((sig, np.array(pca.fit_transform(
        sensor_data[:, 3:6])).reshape(len(sensor_data), 1)))  # First principal
    # component of eX, eY, eZ
    sig = np.hstack((sig, np.array(
        pca.fit_transform(sensor_data[:, 4:6])).reshape(len(sensor_data), 1)))
    # First principal component of EulerY, EulerZ
        
    return sig
        
    
def train_iad(data):
    
    """
    Create features and labels for each window. Train the IAD model.
    
    Args:
        data: sensor data
        
    Returns:
        fit: trained IAD model
    """
    
    # create the feature matrix and labels for the window
    combined_feature_matrix, lab = preprocess_iad(data)
    traincombined_feature_matrix = combined_feature_matrix
    train_lab = lab
    
    # train the classification model
    clf = RandomForestClassifier(n_estimators=20, max_depth=10,
                                 criterion='entropy', max_features='auto',
                                 random_state=1, n_jobs=-1)
    fit = clf.fit(traincombined_feature_matrix, train_lab.reshape((
        len(train_lab),)))
    
    return fit
    
        
def label_aggregation(predicted_labels):
    
    """
    Aggregating the labels for each window after predicting the labels.
    Reduce number of false negatives.
    
    Args:
        predicted_labels: array of labels predicted for each window
        
    Returns:
        predicted_labels: aggregated labels
    """
    
    # initialize variables
    count = 0
    exercise_state = 0
    
    # aggregating the labels to reduce false negatives
    for j in range(1, len(predicted_labels)):
        if predicted_labels[j] == 1 and predicted_labels[j-1] == 1:
            count = 2
            exercise_state = 1
        elif predicted_labels[j] == 0 and predicted_labels[j-1] == 0:
            count = 0
            exercise_state = 0
        elif exercise_state == 1:
            if predicted_labels[j] == 0 and predicted_labels[j-1] == 1:
                count = 1
        elif exercise_state == 0:
            if predicted_labels[j] == 1 and predicted_labels[j-1] == 0:
                count = 1
        if exercise_state == 1 and count == 1 and predicted_labels[j] == 1:
            predicted_labels[j-1] = 1
            count = 2
        if exercise_state == 0 and count == 1 and predicted_labels[j] == 0:
            predicted_labels[j-1] = 0
            count = 0
            
    return predicted_labels
    
    
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
    for i in range(1, len(predicted_labels)):
        for _ in range(50):
            if predicted_labels[i-1] == 0 and predicted_labels[i] == 0:
                test_map_labels.append(0)
            else:
                test_map_labels.append(1)
    
    # check if length of mapped data is the same as that of the sensor data
    if len_data > len(test_map_labels):
        for _ in range(len_data-len(test_map_labels)):
            test_map_labels.append(0)
            
    return np.array(test_map_labels)


if __name__ == "__main__":
    
    import pandas as pd
    import matplotlib.pyplot as plt
    import time
    
    datapath = '''C:\\Users\\court\\Desktop\\BioMetrix\\analytics execution (3)\\
                analytics execution\\subject4_bodyform.csv'''
    
    data = np.genfromtxt(datapath, dtype=float, delimiter=',', names=True)
    
    filename = '''C:\\Users\\court\\Desktop\\BioMetrix\\
        analytics execution (3)\\analytics execution\\iad_finalized model.sav'''
    loaded_model = pickle.load(open(filename, 'rb'))
    x = preprocess_iad(data, training=False)
    x = combined_feature_matrix
    y = loaded_model.predict(x)
    predicted_labels = label_aggregation(y)
    activity_id = mapping_labels_on_data(predicted_labels, len(data))
    
#    comb_feat_matrix = preprocess_iad(data, training = False)
    
    plt.figure(1)
    plt.hist(y)
    plt.show()
    
    