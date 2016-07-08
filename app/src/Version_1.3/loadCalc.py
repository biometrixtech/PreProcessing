# -*- coding: utf-8 -*-
"""
Created on Fri Jun 24 14:59:52 2016

@author: Ankur
"""

import numpy as np
import pandas as pd

g = 9.80665 #acceleration due to gravity (m/s^2), global variable

"""
#############################################INPUT/OUTPUT####################################################
Inputs: the mass of the user, in kilograms; any extra mass the user has strapped on, in kilograms; a single 
        acceleration value (float)
Outputs: a single force value (float)
#############################################################################################################
"""

def calc_force(ma, ema, a):
    
    f = (((ma + ema)*g) + abs((ma + ema)*a))/1000 #dividing by a 1000 to convert Newton to Kilonewton
    
    return f
    
"""
#############################################INPUT/OUTPUT####################################################
Inputs: The right foot, left foot and hip data; the mass of the user in kilograms; any extra mass the user 
        has strapped on in kilograms
Outputs: an array of the load during balance and impact phases, on the right foot, left foot, right foot phase
         id and left foot phase id
#############################################################################################################
"""

def load_bal_imp(rf, lf, hip, m, em):

    rf_bal = [] #load on the right foot during balance phase is determined in Kilonewtons
    lf_bal = [] #load on the left foot during balance phase is determined in Kilonewtons
        
    #determining the load during the balance and impact phases for the right foot    
    for i in range(len(rf)):
        res_hipacc = np.sqrt( hip['AccX'][i]**2 + hip['AccY'][i]**2 + hip['AccZ'][i]**2) #magnitude of the resultant acceleration vector of the hip during the balance phase
        if rf['Phase'][i] == 0: #checking if both feet are on the ground
            rf_bal.append(calc_force(m/2, em/2, res_hipacc))
        elif rf['Phase'][i] == 1: #checking if the right foot is off the ground
            rf_bal.append(0)
        elif rf['Phase'][i] == 2: #checking if the left foot is off the ground
            rf_bal.append(calc_force(m, em, res_hipacc))
        elif rf['Phase'][i] == 3: #checking if both feet are off the ground
            rf_bal.append(0)
        elif rf['Phase'][i] == 5: #checking for right foot impact
            rf_bal.append(5) #assigning a load value for when impact phase occurs (future work would involved determining the actual impact load)
    
    #determining the load during the balance and impact phases for the left foot     
    for i in range(len(lf)):
        res_hipacc = np.sqrt( hip['AccX'][i]**2 + hip['AccY'][i]**2 + hip['AccZ'][i]**2) #magnitude of the resultant acceleration vector of the hip during the balance phase
        if lf['Phase'][i] == 0: #checking if both feet are on the ground
            lf_bal.append(calc_force(m/2, em/2, res_hipacc))
        elif lf['Phase'][i] == 1: #checking if the right foot is off the ground
            lf_bal.append(calc_force(m, em, res_hipacc))
        elif lf['Phase'][i] == 2: #checking if the left foot is off the ground
            lf_bal.append(0)  
        elif lf['Phase'][i] == 3: #checking if both feet are off the ground
            lf_bal.append(0)
        elif lf['Phase'][i] == 4: #checking for left foot impact
            lf_bal.append(5) #assigning a load value for when impact phase occurs (future work would involved determining the actual impact load)
        
    
    load = [ [i, j, k, l] for i, j, k, l in zip(rf_bal, lf_bal, rf['Phase'], lf['Phase']) ] #creating a single array with right load, left load, right foot phase, left foot phase
    load = np.array(load)
        
    return load
    
if __name__ == '__main__':
    
    import matplotlib.pyplot as plt   
    from phaseDetection import *
    
    rpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_rfdatabody_LESS.csv'
    #rpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\ChangeDirection\Rheel_Gabby_changedirection_set1.csv'
    #rpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Walking\Rheel_Gabby_walking_heeltoe_set1.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Walking\Lheel_Gabby_walking_heeltoe_set1.csv'   
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_lfdatabody_set1.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Stomp\Lheel_Gabby_stomp_set1.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\ChangeDirection\Lheel_Gabby_changedirection_set1.csv'
    lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_lfdatabody_LESS.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Jump\Lheel_Gabby_jumping_explosive_set2.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Walking\Lheel_Gabby_walking_heeltoe_set1.csv'
    #hpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_hipdatabody_set1.csv'
    hpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_hipdatabody_LESS.csv'

    rdata = pd.read_csv(rpath)
    ldata = pd.read_csv(lpath)
    hdata = pd.read_csv(hpath)
    
    sampl_rate = 250
    comp = 'AccZ'
    ptch = 'EulerY'
    racc = rdata[comp].values
    lacc = ldata[comp].values #input AccZ values!
    rpitch = rdata[ptch].values
    lpitch = ldata[ptch].values
    #ph = Body_Phase(racc, lacc, rpitch, lpitch, sampl_rate)
    
    lf_phase, rf_phase = combine_phase(ldata['AccZ'].values, rdata['AccZ'].values, rpitch, lpitch, sampl_rate)
    
    rdata['Phase'] = rf_phase
    ldata['Phase'] = lf_phase
    
    print len(rf_phase), len(rdata), len(ldata)
    
    #for i in range(len(rdata)):
    #    if rdata['Phase'][i] == 5:
    #        print 'hello'

    mass = 75 #in kilograms
    exmass = 0 #in kilograms
    ld = load_bal_imp(rdata, ldata, hdata, mass, exmass) #passing the hip, user mass and extra mass data
    
    #load_check = pd.DataFrame()
    #load_check = pd.Series(ld[:,0])
    #load_check.to_csv('C:\Users\Ankur\Desktop\load_calc.csv')
    
    #plt.figure(4) 
    #plt.plot(ld[:,0])
    #plt.plot(ld[:,1])
    #plt.figure(2)
    #plt.plot(ldata['AccZ'])
    #plt.plot(ph)
    #plt.show()
    
    print len(ldata), len(ld), len(lf_phase), len(rf_phase)
    print ld
    
    #plt.figure(3)
    #plt.hist(ld[:,1])
    #plt.show()
    
    