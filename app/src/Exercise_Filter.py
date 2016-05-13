# -*- coding: utf-8 -*-
"""
Created on Tue May  3 18:07:14 2016

@author: Brian
"""

import numpy as np
import pandas as pd
from sklearn import linear_model

#####Currently optimized for 250hz samples need to check if recalibration necessary for other freqs
class ObjectMismatchError(ValueError):
    pass

class DataOmissionError(ValueError):
    pass

class InvalidExerciseInput(ValueError):
    pass

class InvalidFreqInput(ValueError):
    pass

def Exercise_Filter(body, exercise, hz):
    if hz not in [25,50,100,250]:
        raise InvalidFreqInput
       
    rwindow = int(0.4*hz + 1)
    lbound = round(((rwindow-1)/4),0)
    ubound = lbound*3 + 1

    if len(body) > rwindow:
        print("Dataset too long for analysis.")
        raise ObjectMismatchError
    elif len(body) < rwindow:
        print("Dataset too short for analysis.")
        raise ObjectMismatchError
    
    if set(['AccZ', 'EulerX']).issubset(set(body.columns.values)) == False:
        raise DataOmissionError
        
    act_dict = {'Double':[.001,.02,.4], 'Single':[.001,.02,.4]}
    
    if exercise not in act_dict:
        raise InvalidExerciseInput
    
    c_thresh = act_dict[exercise][0] #threshold to check regression against
    a_thresh = act_dict[exercise][1]
    ma_tresh = act_dict[exercise][2]
    
    regr = linear_model.LinearRegression()  #initiate regression object
    aregr = linear_model.LinearRegression()
    rollm = np.mean(body.ix[lbound:ubound, 'AccZ'])
    regr.fit(np.arange(0,rwindow,1).reshape(rwindow,1), body['EulerX'].values.reshape((rwindow, 1))) ##fit regression
    aregr.fit(np.arange(0,rwindow,1).reshape(rwindow,1), body['AccZ'].values.reshape((rwindow, 1))) ##fit regression
    if abs(regr.coef_) < c_thresh and abs(rollm) < ma_tresh and abs(aregr.coef_)<a_thresh:
        indic = 1
    else:
        indic = 0
    return indic
    
if __name__ == '__main__':
    path = ''
    data = pd.read_csv(path) #read in data; csv read in is just a stand in for now
    hz = 250
    window = hz*.2
    exercise = 'Double'
    
    for i in range(len(data)):
        if i-window >= 0 and i+window <= len(data)-1:
            temp = data.ix[i-window:i+window,:]
            temp = temp.reset_index()
            data.ix[i, 'exercise'] = Exercise_Filter(temp, exercise, hz)
        else:
            data.ix[i, 'exercise'] = 1  