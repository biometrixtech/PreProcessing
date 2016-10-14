# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 18:14:21 2016

@author: Gautam
"""
import pickle
from mechStressTraining import prepareData


def mechStress(data, path):
    """
    Args: 
        data: data to predict mechStress for
        path: path of pickle object with trained model
    Returns:
        mechStress: mechanical stress at each timepoint
    """
    with open(path) as f:
        fit = pickle.load(f)
    X = prepareData(data,False)
    mechStress = fit.predict(X)    
    
    return mechStress
    
if __name__ == '__main__':
    pass