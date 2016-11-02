# -*- coding: utf-8 -*-
"""
Created on Mon Oct 17 17:33:37 2016

@author: ankur
"""

import numpy as np
from sklearn.decomposition import PCA
from createFeaturesIED import createWindow, createLabels
from sklearn.ensemble import RandomForestClassifier
from sklearn import preprocessing
import pickle
import pandas as pd

def splitLfHipRf(d, training):
    
#    hz = np.array(d.ms_elapsed).transpose()
#    lfoot = np.array([d.LaX, d.LaY, d.LaZ, d.LeX, d.LeY, d.LeZ]).transpose()
#    hipp = np.array([d.HaX, d.HaY, d.HaZ, d.HeX, d.HeY, d.HeZ]).transpose()
#    rfoot = np.array([d.RaX, d.RaY, d.RaZ, d.ReX, d.ReY, d.ReZ]).transpose()
#    labels = np.array(d['ActivityID'].copy())

    hz = np.array(d['epoch_time'].copy())
    lfoot = np.array(d[['LaX', 'LaY', 'LaZ', 'LeX', 'LeY', 'LeZ']].copy())
    hipp = np.array(d[['HaX', 'HaY', 'HaZ', 'HeX', 'HeY', 'HeZ']].copy())
    rfoot = np.array(d[['RaX', 'RaY', 'RaZ', 'ReX', 'ReY', 'ReZ']].copy())
#    labels = np.array(d['activity_id'].copy())
    
    if training == False:
        return hz, lfoot, hipp, rfoot
    else:
        return hz, lfoot, hipp, rfoot, labels
    
#FUNCTION TO CREATE SIGNALS 
    
def createSignals(sensorData):
    
    pca = PCA(n_components = 1) #defining the PCA function
    
    #Acceleration Signals
    sig = sensorData[:,0:3] #copying AccX, AccY, AccZ
    sig = np.hstack((sig, np.array(sensorData[:,0]**2 + sensorData[:,1]**2 + sensorData[:,2]**2).reshape(len(sensorData),1))) #Acceleration magnitude
    sig = np.hstack((sig, np.array(pca.fit_transform(sensorData[:,0:3])).reshape(len(sensorData),1))) #First principal component of AccX, AccY, AccZ
    
    #Euler Signals
    sig = np.hstack((sig, np.array(sensorData[:,4]).reshape(len(sensorData),1))) #copying EulerX, EulerY, EulerZ
    sig = np.hstack((sig, np.array(sensorData[:,3]**2 + sensorData[:,4]**2 + sensorData[:,5]**2).reshape(len(sensorData),1))) #Euler angles magnitude
    sig = np.hstack((sig, np.array(pca.fit_transform(sensorData[:,3:6])).reshape(len(sensorData),1))) #First principal component of EulerX, EulerY, EulerZ
    sig = np.hstack((sig, np.array(pca.fit_transform(sensorData[:,4:6])).reshape(len(sensorData),1))) #First principal component of EulerY, EulerZ
        
    return sig
    
def preprocess_ied(data, training = False):
    
    # CONVERT DATA TO PANDAS
    df = pd.DataFrame(data.epoch_time)
    df.columns = ['epoch_time']
#    print data.epoch_time
#    df['epoch_time'] = data.epoch_time
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
    
    # SPLITTING THE SAMPLING RATE, HIP DATA, LEFT FOOT DATA AND RIGHT FOOT DATA
    hz, lfoot, hipp, rfoot = splitLfHipRf(df, training)
    
    # CREATING SIGNALS TO EXTRACT FEATURES (EXTRACTING 9 SIGNALS FROM EACH SENSOR)

    lfsig = createSignals(lfoot) #creating the left foot signals
    hipsig = createSignals(hipp) #creating the hip signals
    rfsig = createSignals(rfoot) #creating the right foot signals
    
    # DEFINING THE PARAMETERS

    #Parameters for the sampling window
    Fs = 250 #sampling frequency
    WindowTime = 5 #number of seconds to determine length of the sliding window
    windowSamples = int(Fs*WindowTime) #sliding window length
    nsecjump = 0.2 #number of seconds for the sliding window to jump
    overlapSamples = int(Fs*nsecjump)
    
    #Parameters for feature creation
    nfeatures = 20 #number of features
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

def train_ied(data):
    
    combinedFeatureMatrix, lab = preprocess_iad(data)
        
    trainCombinedFeatureMatrix = combinedFeatureMatrix
    
    trainLab = lab
    
    clf = RandomForestClassifier(n_estimators = 20, max_depth = 10, criterion = 'entropy', max_features='auto', random_state = 1, n_jobs = -1)    
    fit = clf.fit(trainCombinedFeatureMatrix, trainLab.reshape((len(trainLab),)))
    
    with open(path, 'w') as f:
        pickle.dump(fit, f)   
        
def mapping_labels_on_data(predictedLabels, len_data):
    
    test_map_labels = []
    for i in range(1,len(predictedLabels)):
        for j in range(50):
            test_map_labels.append(predictedLabels[i])
#            if predictedLabels[i-1] == 0 and predictedLabels[i] == 0:
#                test_map_labels.append(0)
#            elif (predictedLabels[i-1] == 0 and predictedLabels[i] == 1) or (predictedLabels[i-1] == 1 and predictedLabels[i] == 0) or (predictedLabels[i-1] == 1 and predictedLabels[i] == 1):
#                test_map_labels.append(1)
#            elif (predictedLabels[i-1] == 0 and predictedLabels[i] == 2) or (predictedLabels[i-1] == 2 and predictedLabels[i] == 0) or (predictedLabels[i-1] == 2 and predictedLabels[i] == 2):
#                test_map_labels.append(2)
#            elif (predictedLabels[i-1] == 0 and predictedLabels[i] == 3) or (predictedLabels[i-1] == 3 and predictedLabels[i] == 0) or (predictedLabels[i-1] == 3 and predictedLabels[i] == 3):
#                test_map_labels.append(3)
#            elif (predictedLabels[i-1] == 0 and predictedLabels[i] == 4) or (predictedLabels[i-1] == 4 and predictedLabels[i] == 0) or (predictedLabels[i-1] == 4 and predictedLabels[i] == 4):
#                test_map_labels.append(4)
#            elif (predictedLabels[i-1] == 0 and predictedLabels[i] == 5) or (predictedLabels[i-1] == 5 and predictedLabels[i] == 0) or (predictedLabels[i-1] == 5 and predictedLabels[i] == 5):
#                test_map_labels.append(5)
#            elif (predictedLabels[i-1] == 0 and predictedLabels[i] == 6) or (predictedLabels[i-1] == 6 and predictedLabels[i] == 0) or (predictedLabels[i-1] == 6 and predictedLabels[i] == 6):
#                test_map_labels.append(6)
#            elif (predictedLabels[i-1] == 0 and predictedLabels[i] == 7) or (predictedLabels[i-1] == 7 and predictedLabels[i] == 0) or (predictedLabels[i-1] == 7 and predictedLabels[i] == 7):
#                test_map_labels.append(7)
#            elif (predictedLabels[i-1] == 0 and predictedLabels[i] == 8) or (predictedLabels[i-1] == 8 and predictedLabels[i] == 0) or (predictedLabels[i-1] == 8 and predictedLabels[i] == 8):
#                test_map_labels.append(8)
#            elif (predictedLabels[i-1] == 0 and predictedLabels[i] == 9) or (predictedLabels[i-1] == 9 and predictedLabels[i] == 0) or (predictedLabels[i-1] == 9 and predictedLabels[i] == 9):
#                test_map_labels.append(9)
#            elif (predictedLabels[i-1] == 0 and predictedLabels[i] == 10) or (predictedLabels[i-1] == 10 and predictedLabels[i] == 0) or (predictedLabels[i-1] == 10 and predictedLabels[i] == 10):
#                test_map_labels.append(10)
#            elif (predictedLabels[i-1] == 0 and predictedLabels[i] == 15) or (predictedLabels[i-1] == 15 and predictedLabels[i] == 0) or (predictedLabels[i-1] == 15 and predictedLabels[i] == 15):
#                test_map_labels.append(15)

    if len_data > len(test_map_labels):            
        for k in range(len_data-len(test_map_labels)):
            test_map_labels.append(0)
        
    return np.array(test_map_labels)
    
if __name__ == "__main__":
    
    import pandas as pd
    import matplotlib.pyplot as plt
    import time






