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


def prepare_data(data, train = True):
    """Subsets and transforms the training data as well as define features
    to be used
    Args:
        Data: pandas dataframe or RawFrame object with the acceleration, euler
        train: boolean to indicate if we're training or predicting on the data
        Note: if train is True, data should contain grf data
    Returns:
        X : Predictors
        Y : Reponse (only if training)
    """
    #Extract relevant variables
    data_pd = pd.DataFrame()
    data_pd['LaX'] = np.array(data.LaX.reshape(-1,))
    data_pd['LaY'] = np.array(data.LaY)
    data_pd['LaZ']= np.array(data.LaZ)
    data_pd['LeX'] = np.array(data.LeX)
    data_pd['LeY'] = np.array(data.LeY)
    data_pd['LeZ'] = np.array(data.LeZ)
    data_pd['phase_l'] = np.array(data.phase_l)
    data_pd['RaX'] = np.array(data.RaX)
    data_pd['RaY'] = np.array(data.RaY)
    data_pd['RaZ'] = np.array(data.RaZ)
    data_pd['ReX'] = np.array(data.ReX)
    data_pd['ReY'] = np.array(data.ReY)
    data_pd['ReZ'] = np.array(data.ReZ)
    data_pd['phase_r'] = np.array(data.phase_r)
    data_pd['HaX'] = np.array(data.HaX)
    data_pd['HaY'] = np.array(data.HaY)
    data_pd['HaZ'] = np.array(data.HaZ)
    data_pd['HeX'] = np.array(data.HeX)
    data_pd['HeY'] = np.array(data.HeY)
    data_pd['HeZ'] = np.array(data.HeZ)
    
    total_columns = ['LaX', 'LaY', 'LaZ','RaX', 'RaY', 'RaZ','HaX','HaY', 'HaZ',
                     'LeX', 'LeY', 'LeZ','ReX', 'ReY', 'ReZ','HeX','HeY', 'HeZ']
    
    X = data_pd[total_columns].values
    if train==True:
        data_pd['totalLoad'] = np.array(data.LFz) + np.array(data.RFz)
        Y = data_pd['totalLoad'].values
        return X, Y
    else:
        return X
    
def modelFit(X,Y):
    """Fits Gradient boosting regressor on the training data and returns the
    fit object

    Args:
        X: matrix of predictors
        Y: list of response variables
    Returns:
        Fitted model
    """
    params = {'n_estimators': 1000, 'max_depth': 4, 'min_samples_split': 1,
          'learning_rate': 0.01, 'loss': 'lad'}
    slr = GradientBoostingRegressor(**params)    
    fit = slr.fit(X,Y)
    
    return fit

def trainModel(data, path):
    """Run the model training and model fit to pickle
    Args:
        data: 
        path: filepath where the fit object is pickled
        
    Returns:
        None: pickles the fit object to the path provided
    
    """
    
    X,Y = prepare_data(data)
    fit = modelFit(X,Y)
    
    with open(path, 'wb') as f:
        pickle.dump(fit, f)
    
if __name__ =='__main__':
    import matplotlib.pyplot as plt
    import os
    import numpy as np
    import time
#    os.chdir('C:\\Users\\dipesh\\Desktop\\biometrix\\python_scripts')
    from phaseDetection import combine_phase
    path = 'C:\\Users\\dipesh\\Desktop\\biometrix\\'
    data0 = np.genfromtxt(path+"combined\\sensor&grfdata.csv", delimiter = ",",
                          names = True)
    sampl_rate = 250
    lf_phase, rf_phase = combine_phase(data0['LaZ'], data0['RaZ'], sampl_rate)
    data = pd.DataFrame(data0)
    data['phase_l'] = lf_phase
    data['phase_r'] = rf_phase
    s = time.time()
    trainModel(data, path+"ms_trainmodel.pkl")
    print "it took", time.time()-s, "to train the model"
#    with open(path + "fittedModel.pkl") as f:
#        fit = pickle.load(f)
#    X = prepareData(data,False)
#    y_pred = fit.predict(X)
#    y_true = (data['RFz']+data['LFz']).values
#    diff = np.abs(y_true-y_pred)
#    plt.plot(y_pred)
    


