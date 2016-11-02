# -*- coding: utf-8 -*-
"""
Created on Wed Jun 22 12:11:52 2016

@author: Ankur
"""

import numpy as np
from phaseID import phase_id


def imp_start_time(imp_time): 
    
    """
    Determine the beginning of each impact.
    
    Args:
        imp_time: right'left foot phase
        
    Returns:
        s: a list containing the first instance of impact for right/left foot
    
    """
    
    s = []  # initializing a list
    count = 0  # initializing a count variable
    for i in range(len(imp_time)):
        if imp_time[i] == phase_id.lf_imp.value \
        or imp_time[i] == phase_id.rf_imp.value:  # checking if an impact 
        # phase exists (4 for left foot; 5 for right foot)
            if count < 1:
                s.append(i)  # appending the first instance of an impact phase 
                count = count + 1
        elif imp_time[i] == phase_id.rflf_ground.value \
        or imp_time[i] == phase_id.lf_ground.value \
        or imp_time[i] == phase_id.rf_ground.value \
        or imp_time[i] == phase_id.rflf_offground.value:
            count = 0
                        
    return s 
    
    
def sync_time(imp_rf, imp_lf, sampl_rate): 

    """  
    Determine the land time on impact for right and left feet.
    
    Args:
        imp_rf: right foot phase
        imp_lf: left foot phase
        sampl_rate: sampling rate
        
    Returns:
        diff: time difference between right and left feet impacts
        
    """
        
    rf_start = imp_start_time(imp_rf)  # obtaining the first instant of the 
                                        # impact phases of the right foot
    lf_start = imp_start_time(imp_lf)  # obtaining the first instant of the 
                                        # impact phases of the left foot

    # initialize variables
    diff = []  # initializing a list to store the difference in impact times

    # determine false impacts
    for i in range(len(rf_start)):
        for j in range(len(lf_start)):
            if abs(lf_start[j] - rf_start[i]) <= 0.3*sampl_rate:  # checking 
            # for false impact phases
                if lf_start[j] > rf_start[i]:  # check if left foot 
                # impacts first
                    diff.append(-(lf_start[j] - rf_start[i])\
                    /float(sampl_rate)*1000) 
                    # appending the difference of time of impact between  
                    # left and right feet, dividing by the sampling rate to 
                    # convert the time difference to milli seconds
                elif lf_start[j] < rf_start[j]:  # check if right foot
                # impacts first
                    diff.append((rf_start[j] - lf_start[i])\
                    /float(sampl_rate)*1000) 
                elif lf_start[j] == rf_start[j]:  # check impact time of 
                # right foot equals left foot
                    diff.append(0.0)
                
    return np.array(diff).reshape(-1,1)
    
    
def landing_pattern(rf_euly, lf_euly, land_time): 
    
    """
    Determine the pitch angle of the right and left feet on impact.
    
    Args:
        rf_euly: right foot pitch angles
        lf_euly: left foot pitch angles
        land_time: right and left landing times on impact
        
    Returns:
        out_pattern: 2D list, right and left feet pitch angles on impact
    
    """
        
    out_pattern = []
    
    for i in land_time:
        out_pattern.append([np.rad2deg(rf_euly[int(land_time[i,0])]), 
                            np.rad2deg(lf_euly[int(land_time[i,1])])])
                            # right and left feet pitch angles on impact
    
    return np.array(out_pattern) 
    
    
def continuous_values(land_pattern, land_time, n):
    
    rf_quick_pattern = []
    rf_quick_time = []
    lf_quick_pattern = []
    lf_quick_time = []
    
    count = 0
    for i in range(n):
        if i in land_time[:,0]:
            rf_quick_pattern.append(land_pattern[count,2])
            rf_quick_time.append(land_time[count,2])
            count = count + 1
        else:
            rf_quick_pattern.append(np.nan)
            rf_quick_time.append(np.nan)
                
    count = 0
    for i in range(n):
        if i in land_time[:,0]:
            lf_quick_pattern.append(land_pattern[count,3])
            lf_quick_time.append(land_time[count,3])
            count = count + 1
        else:
            lf_quick_pattern.append(np.nan)
            lf_quick_time.append(np.nan)
    
    final_landtime = []
    final_landpattern = []        
    for i,j,k,l in zip(lf_quick_time, rf_quick_time, lf_quick_pattern, rf_quick_pattern):
        final_landtime.append([j,i])
        final_landpattern.append([l,k])        
            
    return np.array(final_landtime), np.array(final_landpattern)

if __name__ == '__main__':
    
    import pandas as pd
    import matplotlib.pyplot as plt
    import sys
    #from impact_phase import impact_phase
    from phaseDetection import combine_phase
    
    rpath = 'C:\\Users\\Ankur\\python\\Biometrix\\Data analysis\\data exploration\\data files\\Subject5\\Subject5_rfdatabody_LESS.csv'
    #rpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\ChangeDirection\Rheel_Gabby_changedirection_set1.csv'
    #rpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Walking\Rheel_Gabby_walking_heeltoe_set1.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Walking\Lheel_Gabby_walking_heeltoe_set1.csv'   
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_lfdatabody_set1.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Stomp\Lheel_Gabby_stomp_set1.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\ChangeDirection\Lheel_Gabby_changedirection_set1.csv'
    lpath = 'C:\\Users\\Ankur\\python\\Biometrix\\Data analysis\\data exploration\\data files\\Subject5\Subject5_lfdatabody_LESS.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Jump\Lheel_Gabby_jumping_explosive_set2.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Walking\Lheel_Gabby_walking_heeltoe_set1.csv'
    #hpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_hipdatabody_set1.csv'
    hpath = 'C:\\Users\\Ankur\\python\\Biometrix\\Data analysis\\data exploration\\data files\\Subject5\\Subject5_hipdatabody_LESS.csv'

#    rdata1 = np.genfromtxt(rpath, delimiter = ",", dtype = float, names = True)
#    ldata1 = np.genfromtxt(lpath, delimiter = ",", dtype = float, names = True)
#    hdata1 = np.genfromtxt(hpath, delimiter = ",", dtype = float, names = True)
    
    datapath = '/home/ankur/Documents/BioMetrix/Data analysis/data exploration/data files/Paul dataset/Subject5_LESS_Transformed_Data.csv'
    data = np.genfromtxt(datapath, delimiter = ",", dtype = float, names = True)
    
    #rdata1 = pd.read_csv(rpath)
    #ldata1 = pd.read_csv(lpath)
    #hdata1 = pd.read_csv(hpath)
    
    #reading the test datasets
    #rdata1 = pd.read_csv('C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\impact cme\sym_impact_input_rfoot.csv')
    #ldata1 = pd.read_csv('C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\impact cme\sym_impact_input_lfoot.csv')

    sampl_rate = 250
    #comp = 'AccZ'
#    ptch = 'EulerY'
    #racc = rdata[comp].values
    #lacc = ldata[comp].values #input AccZ values!
#    rpitch = rdata1[ptch]
#    lpitch = ldata1[ptch]
    #ph = Body_Phase(racc, lacc, rpitch, lpitch, sampl_rate)
    
    lf_phase, rf_phase = combine_phase(data['LaZ'], data['RaZ'], sampl_rate)
    
#    rdata1['Phase'] = rf_phase
#    ldata1['Phase'] = lf_phase

    #comp = 'AccZ'
    #rdata = rdata1[comp].values
    #ldata = ldata1[comp].values
    #hdata = hdata1[comp].values
    #comp2 = 'EulerY'
    #erf = rdata1[comp2].values
    #elf = ldata1[comp2].values
    #sampl_rate = 250 #sampling rate, remember to change it when using data sets of different sampling rate
    
    #output_lf = impact_phase(ldata, sampl_rate)
    #output_rf = impact_phase(rdata, sampl_rate)
    
#    cme_dict_imp = {'landtime':[0.2, 0.25], 'landpattern':[12, 50]}
    
    output = sync_time(rf_phase, lf_phase, sampl_rate)
    if len(output) != 0:
        pdiff = landing_pattern(data['ReY'], data['LeY'], output)
    else:
        print 'No impacts detected. Cannot determine land time and land pattern'
        sys.exit()
    
    print output, 'sync_time'
    print pdiff, 'landing_pattern'
    
    ltime, lpattern = continuous_values(pdiff, output, len(data))
    
#    rf_quick_pattern = []
#    rf_quick_time = []
#    lf_quick_pattern = []
#    lf_quick_time = []
#    
#    count = 0
#    for i in range(len(data)):
#        if i in output[:,0]:
#            rf_quick_pattern.append(pdiff[count,2])
#            rf_quick_time.append(output[count,2])
#            count = count + 1
#            print count
#        else:
#            rf_quick_pattern.append(np.nan)
#            rf_quick_time.append(np.nan)
#                
#    count = 0
#    for i in range(len(data)):
#        if i in output[:,0]:
#            lf_quick_pattern.append(pdiff[count,3])
#            lf_quick_time.append(output[count,3])
#            count = count + 1
#        else:
#            lf_quick_pattern.append(np.nan)
#            lf_quick_time.append(np.nan)
#                
#    df = pd.DataFrame(data)
#    df['landPatternL'] = pd.Series(lf_quick_pattern)
#    df['landPatternR'] = pd.Series(rf_quick_pattern)
#    df['landTimeL'] = pd.Series(lf_quick_time)
#    df['landTimeR'] = pd.Series(rf_quick_time)
#    df.to_csv('/home/ankur/Documents/BioMetrix/Data analysis/data exploration/data files/Paul dataset/impactCME_Subject5_LESS_Transformed_Data.csv')
    
#    landPatternL	landPatternR	landTimeL	landTimeR

                
    
    #plt.figure(1)
    #plt.plot(output_lf)
    #plt.hist(ldata, bins = 20)
    #plt.figure(2)
    #plt.plot(elf)
    #plt.show()
    
    #plt.figure(2)
    #plt.plot(output_rf)
    #plt.plot(rdata)
    #plt.show()
    
