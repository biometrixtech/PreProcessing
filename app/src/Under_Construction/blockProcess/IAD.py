# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 17:51:07 2016

@author: ankur
"""

import numpy as np
from sklearn.decomposition import PCA
from createFeaturesIAD import createWindow, createLabels
from sklearn.ensemble import RandomForestClassifier
from sklearn import preprocessing
import pickle
import pandas as pd


def splitLfHipRf(d, training):
    
    """
    Separate left foot, right foot and hip data to respective variables.
    
    Args:
        d: entire dataset
        training: True/False, if we are training the IAD model or not
        
    Returns:
        hz: sampling rate
        lfoot: all left foot data
        hipp: all hip data
        rfoot: all right foot data
        if Training == True:
            labels: activity ID labels, 1 for activity & 0 for non-activity
        
    """
        
    if training == False:
        hz = np.array(d['epoch_time'].copy())
        lfoot = np.array(d[['LaX', 'LaY', 'LaZ', 'LeX', 'LeY', 'LeZ']].copy())
        hipp = np.array(d[['HaX', 'HaY', 'HaZ', 'HeX', 'HeY', 'HeZ']].copy())
        rfoot = np.array(d[['RaX', 'RaY', 'RaZ', 'ReX', 'ReY', 'ReZ']].copy())
        
        return hz, lfoot, hipp, rfoot
    else:
        hz = np.array(d['epoch_time'].copy())
        lfoot = np.array(d[['LaX', 'LaY', 'LaZ', 'LeX', 'LeY', 'LeZ']].copy())
        hipp = np.array(d[['HaX', 'HaY', 'HaZ', 'HeX', 'HeY', 'HeZ']].copy())
        rfoot = np.array(d[['RaX', 'RaY', 'RaZ', 'ReX', 'ReY', 'ReZ']].copy())
        labels = np.array(d['ActivityID'].copy())
        
        return hz, lfoot, hipp, rfoot, labels
    
#FUNCTION TO CREATE SIGNALS 
    
def createSignals(sensorData):
    
    """
    Create signals from which features will be extracted.
    
    Args:
        sensorData: all left foot/hip/right foot data
        
    Returns:
        sig: acceleration and euler signals
    
    """
    
    pca = PCA(n_components = 1)  # defining the PCA function
    
    # Acceleration Signals
    sig = sensorData[:,0:3]  # copying aX, aY, aZ
    sig = np.hstack((sig, np.array(sensorData[:,0]**2 + sensorData[:,1]**2 
    + sensorData[:,2]**2).reshape(len(sensorData),1)))  # Acceleration 
    # magnitude
    sig = np.hstack((sig, np.array(
    pca.fit_transform(sensorData[:,0:3])).reshape(len(sensorData),1))) 
    # First principal component of aX, aY, aZ
    
    # Euler Signals
    sig = np.hstack((sig, np.array(
    sensorData[:,4]).reshape(len(sensorData),1)))  # copying eX, eY, eZ
    sig = np.hstack((sig, np.array(sensorData[:,3]**2 + sensorData[:,4]**2 
    + sensorData[:,5]**2).reshape(len(sensorData),1))) 
    # Euler angles magnitude
    sig = np.hstack((sig, np.array(pca.fit_transform(
    sensorData[:,3:6])).reshape(len(sensorData),1)))  # First principal 
    # component of eX, eY, eZ
    sig = np.hstack((sig, np.array(
    pca.fit_transform(sensorData[:,4:6])).reshape(len(sensorData),1))) 
    # First principal component of EulerY, EulerZ
        
    return sig
    
    
def preprocess_iad(data, training = False):
    
    """
    
    
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
    
    # split the sampling rate, hip data, left foot data and right foot data
    hz, lfoot, hipp, rfoot = splitLfHipRf(df, training)
    
    # create signals to extract features
    lfsig = createSignals(lfoot)  # left foot signals
    hipsig = createSignals(hipp)  # hip signals
    rfsig = createSignals(rfoot)  # right foot signals
    
    # define parameters
    # Parameters for the sampling window
    Fs = 250  # sampling frequency
    WindowTime = 5  # number of seconds to determine length of the sliding window
    windowSamples = int(Fs*WindowTime) #sliding window length
    nsecjump = 0.2 #number of seconds for the sliding window to jump
    overlapSamples = int(Fs*nsecjump)
    
    #Parameters for feature creation
    nfeatures = 28 #number of features
    #defining the parameters to determine the number of prominent peaks
    promMPD = 20 #minimum peak distance for prominent peaks
    promMPH = -1 #minimum peak height for prominent peaks
    promPeakThresh = 0.5 #height threshold for number of maximum peaks feature
    #defining the parameters to determine the number of weak peaks
    weakMPD = 20 #minimum peak distance for weak peaks
    weakMPH = -1 #minimum peak height for weak peaks
    weakPeakThresh = 0.3 #height threshold for number of minimum peaks feature
    
    #Parameters for labelling each window
    labelThresh = 0.5 #x% of window 
    
    # DETERMINING THE FEATURES AND LABELS FOR EACH WINDOW
    
    lfFeatureMatrix = createWindow(lfsig, Fs, windowSamples, overlapSamples, promMPD, promMPH, promPeakThresh, weakMPD, weakMPH, weakPeakThresh)
    hipFeatureMatrix = createWindow(hipsig, Fs, windowSamples, overlapSamples, promMPD, promMPH, promPeakThresh, weakMPD, weakMPH, weakPeakThresh)
    rfFeatureMatrix = createWindow(rfsig, Fs, windowSamples, overlapSamples, promMPD, promMPH, promPeakThresh, weakMPD, weakMPH, weakPeakThresh)
    
    combinedFeatureMatrix = np.concatenate((lfFeatureMatrix, hipFeatureMatrix), axis = 1)
#    combinedFeatureMatrix = preprocessing.normalize(combinedFeatureMatrix)
    
    if training == True:
        lab = createLabels(labels, windowSamples, overlapSamples, labelThresh)
        return combinedFeatureMatrix, lab
    else:
        return combinedFeatureMatrix
    
def trainIAD(data):
    
    combinedFeatureMatrix, lab = preprocess_iad(data)
    
    trainCombinedFeatureMatrix = combinedFeatureMatrix
    
    trainLab = lab
    
    clf = RandomForestClassifier(n_estimators = 20, max_depth = 10, criterion = 'entropy', max_features='auto', random_state = 1, n_jobs = -1)    
    fit = clf.fit(trainCombinedFeatureMatrix, trainLab.reshape((len(trainLab),)))
    
#    with open(path, 'w') as f:
#        pickle.dump(fit, f)   
        
def label_aggregation(predictedLabels):
    
    count = 0
    exercise_state = 0
    
    for j in range(1,len(predictedLabels)):
        if predictedLabels[j] == 1 and predictedLabels[j-1] == 1:
            count = 2
            exercise_state = 1
        elif predictedLabels[j] == 0 and predictedLabels[j-1] == 0:
            count = 0
            exercise_state = 0
        elif exercise_state == 1:
            if predictedLabels[j] == 0 and predictedLabels[j-1] == 1:
                count = 1
        elif exercise_state == 0:
            if predictedLabels[j] == 1 and predictedLabels[j-1] == 0:
                count = 1
        if exercise_state == 1 and count == 1 and predictedLabels[j] == 1:
            predictedLabels[j-1] = 1
            count = 2
        if exercise_state == 0 and count == 1 and predictedLabels[j] == 0:
            predictedLabels[j-1] = 0
            count = 0
            
    return predictedLabels
    
def mapping_labels_on_data(predictedLabels, len_data):
    
    test_map_labels = []
    for i in range(1,len(predictedLabels)):
        for j in range(50):
            if predictedLabels[i-1] == 0 and predictedLabels[i] == 0:
                test_map_labels.append(0)
            else:
                test_map_labels.append(1)
    
    if len_data > len(test_map_labels):            
        for k in range(len_data-len(test_map_labels)):
            test_map_labels.append(0)
    return np.array(test_map_labels)


if __name__ == "__main__":
    
    import pandas as pd
    import matplotlib.pyplot as plt
    import time
    
    datapath = 'C:\\Users\\court\\Desktop\\BioMetrix\\analytics execution (3)\\analytics execution\\subject4_bodyform.csv'
    
    data = np.genfromtxt(datapath, dtype = float, delimiter = ',', names=True)
    
    filename = 'C:\\Users\\court\\Desktop\\BioMetrix\\analytics execution (3)\\analytics execution\\iad_finalized model.sav'
    loaded_model = pickle.load(open(filename, 'rb'))
    x = preprocess_iad(data, training = False)
    x = combinedFeatureMatrix
    y = loaded_model.predict(x)
    predicted_labels = label_aggregation(y)
    activity_id = mapping_labels_on_data(predicted_labels, len(data))
    
#    comb_feat_matrix = preprocess_iad(data, training = False)
    
    plt.figure(1)
    plt.hist(y)
    plt.show()
    
    