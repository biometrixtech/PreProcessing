# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 11:57:32 2016

@author: Gautam
"""


from __future__ import division
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
import pickle


def prepareData(data, train = True):
    """Subset and transformation of the training data as well as defining features to be used
    Args:
        Data: data table with the acceleration, euler angle and quaternions, exerciseID and phase
    Returns:
        X : Predictors
        Y : Reponse (only if training)
    """
    #If we're subsetting data for different phases
    sub_data = data
    wd = pd.DataFrame()
    wd['LaX'] = np.array(sub_data['LaX'])
    wd['LaY'] = np.array(sub_data['LaY'])
    wd['LaZ']= np.array(sub_data['LaZ'])
    wd['LeX'] = np.array(sub_data['LeX'])
    wd['LeY'] = np.array(sub_data['LeY'])
    wd['LeZ'] = np.array(sub_data['LeZ'])
    wd['phaseL'] = np.array(sub_data['phaseL'])
    wd['RaX'] = np.array(sub_data['RaX'])
    wd['RaY'] = np.array(sub_data['RaY'])
    wd['RaZ'] = np.array(sub_data['RaZ'])
    wd['ReX'] = np.array(sub_data['ReX'])
    wd['ReY'] = np.array(sub_data['ReY'])
    wd['ReZ'] = np.array(sub_data['ReZ'])
    wd['phaseR'] = np.array(sub_data['phaseR'])
    wd['HaX'] = np.array(sub_data['HaX'])
    wd['HaY'] = np.array(sub_data['HaY'])
    wd['HaZ'] = np.array(sub_data['HaZ'])
    wd['HeX'] = np.array(sub_data['HeX'])
    wd['HeY'] = np.array(sub_data['HeY'])
    wd['HeZ'] = np.array(sub_data['HeZ'])
    
    total_columns = ['LaX', 'LaY', 'LaZ','RaX', 'RaY', 'RaZ','HaX', 'HaY', 'HaZ',
                     'LeX', 'LeY', 'LeZ','ReX', 'ReY', 'ReZ','HeX', 'HeY', 'HeZ']
    
    X = wd[total_columns].values
    if train==True:
        wd['totalLoad'] = np.array(sub_data.LFz) + np.array(sub_data.RFz)
        Y = wd['totalLoad'].values
        return X, Y
    else:
        return X
    
def modelFit(X,Y):
    """Fits Gradient boosting regressor on the training data and returns the fit object
    Args:
        X: matrix of predictors
        Y: list of response variables
    Returns:
        
    
    """
    params = {'n_estimators': 1000, 'max_depth': 4, 'min_samples_split': 1,
          'learning_rate': 0.01, 'loss': 'lad'}
    slr = GradientBoostingRegressor(**params)    
    fit = slr.fit(X,Y)
    
    return fit

def trainModel(data, path):
    """Run the model training and model fit to pickle
    Args:
        data: training data with transformed data 
        path: filepath where the fit object is pickled
        
    Returns:
        None: pickles the fit object to the path provided
    
    """
    
    X,Y = prepareData(data)
    fit = modelFit(X,Y)
    
    with open(path, 'w') as f:
        pickle.dump(fit, f)
    
if __name__ =='__main__':
    import matplotlib.pyplot as plt
    import os
    import numpy as np
    os.chdir('C:\\Users\\dipesh\\Desktop\\biometrix\\python_scripts')
    from phaseDetection import combine_phase
    path = 'C:\\Users\\dipesh\\Desktop\\biometrix\\'
    data0 = np.genfromtxt(path+"combined\\ivonna_combined_sensordata.csv", delimiter = ",",  names = True)
    sampl_rate = 250
    lf_phase, rf_phase = combine_phase(data0['LaZ'], data0['RaZ'], sampl_rate)
    data = pd.DataFrame(data0)
    data['phaseL'] = lf_phase
    data['phaseR'] = rf_phase
    
    trainModel(data, path+"fittedModel.pkl")
    
    with open(path + "fittedModel.pkl") as f:
        fit = pickle.load(f)
    X = prepareData(data,False)
    y_pred = fit.predict(X)
    y_true = (data['RFz']+data['LFz']).values
    diff = np.abs(y_true-y_pred)
    plt.plot(y_pred)
    



