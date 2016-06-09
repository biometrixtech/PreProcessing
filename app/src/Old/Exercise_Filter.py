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
    if hz not in [25,50,100,250]: #make sure sampling frequency is known
        raise InvalidFreqInput
       
    rwindow = int(0.4*hz + 1) #based on sampling rate determine number of points used for regression analysis
    lbound = round(((rwindow-1)/4),0) #create lower bound of moving average window should be about .25*rwindow
    ubound = lbound*3 + 1 #create upper bound of moving average window should be about .75*rwindow
    
    #make sure the dataset that's read in is of equal length to what is expected based on the sampling rate
    if len(body) > rwindow:
        print("Dataset too long for analysis.")
        raise ObjectMismatchError
    elif len(body) < rwindow:
        print("Dataset too short for analysis.")
        raise ObjectMismatchError
    
    #make sure relevant columns are in dataset
    if set(['AccZ', 'EulerX']).issubset(set(body.columns.values)) == False:
        raise DataOmissionError
    
    #dictionary housing thresholds for different exercises    
    act_dict = {'Double':[.001,.02,.4], 'Single':[.001,.02,.4]}
    
    if exercise not in act_dict:
        raise InvalidExerciseInput
    
    c_thresh = act_dict[exercise][0] #threshold to check euler angle regression against
    a_thresh = act_dict[exercise][1] #threshold to check accel regression against
    ma_tresh = act_dict[exercise][2] #threshold to check euler ma against
    
    regr = linear_model.LinearRegression()  #initiate regression object for euler
    aregr = linear_model.LinearRegression() #initiate regression object for accel
    rollm = np.mean(body.ix[lbound:ubound, 'AccZ']) #find mean of euler angle with point of interest at the center
    regr.fit(np.arange(0,rwindow,1).reshape(rwindow,1), body['EulerX'].values.reshape((rwindow, 1))) ##fit euler regression
    aregr.fit(np.arange(0,rwindow,1).reshape(rwindow,1), body['AccZ'].values.reshape((rwindow, 1))) ##fit accel regression
    if abs(regr.coef_) < c_thresh and abs(rollm) < ma_tresh and abs(aregr.coef_)<a_thresh:
        indic = 1 #determine that the athlete is not doing an exercise 
    else:
        indic = 0 #determine the athlete is doing an exercise
    return indic
    
if __name__ == '__main__':
    path = ''
    data = pd.read_csv(path) #read in data; csv read in is just a stand in for now
    hz = 250 #sampling rate
    window = hz*.2 #calc .5 the size of the dataset to be entered in fxn, half on one side, half on the other
    exercise = 'Double'
    
    ##for loop might not exist in architecture...there might be a "master" for loop that houses all function relevant to analysis doing one point at a time
    for i in range(len(data)):
        if i-window >= 0 and i+window <= len(data)-1:
            temp = data.ix[i-window:i+window,:] #create dataset, in implementation will probably be an if..then statement checking to see if there are enough samples to do analysis
            temp = temp.reset_index() #if a dataframe object reset the index so it number 0:2*window
            data.ix[i, 'exercise'] = Exercise_Filter(temp, exercise, hz) #run exercise filter
        else:
            data.ix[i, 'exercise'] = 1  #for now just a stand in if there isn't enough data is to say no exercise is being performed