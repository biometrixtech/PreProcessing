# -*- coding: utf-8 -*-
"""
Created on Thu Jul  7 12:34:12 2016

@author: Brian
"""
import runAnalytics as ra
import runAnatomical as rana
#import executionScore as exec_score

"""
#############################################INPUT/OUTPUT####################################################   
Inputs: filepath to anatomical calibration and analytics datasets, sampling rates for each, mass, and extra mass
Outputs: object holding anatomical corrections, object with CMEs, execution score
#############################################################################################################
"""

if __name__ == "__main__":
    anatom_root = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\Alignment test\\bow13comb.csv'
    data_root = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\Fixed_By_Exercise\\Subject1_DblSquat.csv' #root path for data folder...reset to your own path
    
    anatom = rana.RunAnatomical(anatom_root, 100) #(filepath, sampling rate)
    cme = ra.RunAnalytics(data_root, 75, 0, 250, anatom)  #(filepath, weight, extra weight, sampling rate, anatomical calibration results) 
    #Execution Score
    #score = exec_score.weight_load(cme.nr_contra, cme.nl_contra, cme.nr_prosup, cme.nl_prosup, cme.nr_hiprot, cme.nl_hiprot, cme.nrdbl_hiprot, cme.nldbl_hiprot, cme.n_landtime, cme.n_landpattern, cme.load)
