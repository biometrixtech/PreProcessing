# -*- coding: utf-8 -*-
"""
Created on Wed Jun 22 12:11:52 2016

@author: Ankur
"""

from itertools import islice #'islice' helps to skip specified number of iterations in 'for' loop
import numpy as np

"""
#############################################INPUT/OUTPUT####################################################
Function: sync_time
Inputs: impact phase data for the right and left foot; sampling rate
Outputs: difference between, the first instant (time point) of the impact phases, of the right and left feet;
         starting time of the impact phase of the right foot; starting time of the impact phase of the left foot;
         
Function: landing_pattern
Inputs: EulerY of the right and left feet; first instant (time point) of the impact phases of the right foot;
        first instant (time point) of the impact phases of the left foot;
Outputs: difference between EulerY of the right and left feet at the first instant of the impact phases
         
Datsets for both the functions: -> 2 input files (sym_impact_input_rfoot.csv; sym_impact_input_lfoot.csv
                                -> sync_time(rdata['Impact'], ldata['Impact'], 250); the starting points of 
                                the impact phases of the right and left feet are passed on to the landing_pattern
                                function.
                                -> landing_pattern(rdata['EulerY'], ldata['EulerY'], rf_time, lf_time)
                                -> 2 output files (sym_impact_output_time.csv; sym_impact_output_eulery.csv)
#############################################################################################################
"""

def imp_start_time(imp_time): #passing the impact phase data (its an array of 0's and 1's)
    
    s = [] #initializing a list
    count = 0 #initializing a count variable
    for i in range(len(imp_time)):
        if imp_time[i] == 1: #checking if an impact phase exists 
            if count < 1:
                s.append(i) #appending the first instant of an impact phase to a list
                count = count + 1
        elif imp_time[i] == 0:
            count = 0
            
    return s #returning the list that contains the first instant of the impact phases
    
def sync_time(imp_rf, imp_lf, sampl_rate): #passing the time intervals of the imapct phases of the right and left feet, and the sampling rate
    
    rf_start = imp_start_time(imp_rf) #obtaining the first instant of the impact phases of the right foot
    lf_start = imp_start_time(imp_lf) #obtaining the first instant of the impact phases of the left foot
    
    diff = [] #initializing a list to store the difference in impact times
    rf_time = [] #refined starting time of the impact phase for the right foot
    lf_time = [] #refined starting time of the impact phase for the left foot
    numbers = iter(range(len(lf_start))) #creating an iterator variable. iter() returns an iterator object. 
    
    for i,j in zip(numbers, range(len(rf_start))):
        if abs(lf_start[i] - rf_start[j]) <= 0.3*sampl_rate: #checking for false impact phases
            diff.append(abs(lf_start[i] - rf_start[j])/float(sampl_rate)) #appending the difference of the time of impact between the left and right feet, dividing by the sampling rate to convert the time difference to seconds
            rf_time.append(rf_start[j]) #refined starting time of the impact phase for the right foot (not in seconds)
            lf_time.append(lf_start[i]) #refined starting time of the impact phase for the left foot (not in seconds)
        else:
            for k in range(len(lf_start)): #this loop helps to compare relevant impact phases of the right and left feet
                if abs(lf_start[k] - rf_start[j]) <= 0.3*sampl_rate: #checking for false impact phases
                    diff.append(abs(lf_start[k] - rf_start[j])/float(sampl_rate))
                    rf_time.append(rf_start[j]) #refined starting time of the impact phase for the right foot (not in seconds)
                    lf_time.append(lf_start[i]) #refined starting time of the impact phase for the left foot (not in seconds)
                    break #if the relevant impact phase is found then break from the 'for' loop
            next(islice(numbers, k+1, 1 ), None) #skip the next 'k+1' iterations
            
    return diff, rf_time, lf_time #returning the difference in impact times, the starting point of the impact phase of the right foot, the starting point of the impact phase of the left foot
    
def landing_pattern(rf_euly, lf_euly, rft, lft): # passing the EulerY data of the right and left feet, and the refined first instances of impact phases of the right and left feet
    
    pitch_diff = [] #initializing a list to store the difference between the EulerY angles 
    
    for i, j in zip(rft, lft):
        pitch_diff.append(np.rad2deg(abs(rf_euly[i] - lf_euly[j]))) #appending the difference between the EulerY angles, converting radians to degrees
        
    return np.array(pitch_diff) #returning the differences between the EulerY angles
    
if __name__ == '__main__':
    
    import pandas as pd
    #import matplotlib.pyplot as plt
    #from impact_phase import impact_phase
    
    #rpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Jump\Rheel_Gabby_jumping_explosive_set2.csv'
    rpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_rfdatabody_LESS.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Jump\Lheel_Gabby_jumping_explosive_set2.csv'
    lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_lfdatabody_LESS.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Stomp\Lheel_Gabby_stomp_set1.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\ChangeDirection\Lheel_Gabby_changedirection_set1.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Jump\Lheel_Gabby_jumping_explosive_set2.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Walking\Lheel_Gabby_walking_heeltoe_set1.csv'
    hpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Stomp\hips_Gabby_stomp_set1.csv'

    #rdata1 = pd.read_csv(rpath)
    #ldata1 = pd.read_csv(lpath)
    hdata1 = pd.read_csv(hpath)
    
    #reading the test datasets
    rdata1 = pd.read_csv('C:\\Users\\Ankur\\Desktop\\sym_impact_input_rfoot.csv')
    ldata1 = pd.read_csv('C:\\Users\\Ankur\\Desktop\\sym_impact_input_lfoot.csv')

    comp = 'AccZ'
    rdata = rdata1[comp].values
    ldata = ldata1[comp].values
    hdata = hdata1[comp].values
    comp2 = 'EulerY'
    erf = rdata1[comp2].values
    elf = ldata1[comp2].values
    sampl_rate = 250 #sampling rate, remember to change it when using data sets of different sampling rate
    
    #output_lf = impact_phase(ldata, sampl_rate)
    #output_rf = impact_phase(rdata, sampl_rate)
    
    time_diff, rfoot_time, lfoot_time = sync_time(rdata1['Impact'], ldata1['Impact'], sampl_rate)
    pdiff = landing_pattern(rdata1['EulerY'], ldata1['EulerY'], rfoot_time, lfoot_time)
    
    print time_diff, pdiff
    
    #plt.figure(1)
    #plt.plot(output_lf)
    #plt.plot(ldata)
    
    #plt.figure(2)
    #plt.plot(output_rf)
    #plt.plot(rdata)
    #plt.show()
    
