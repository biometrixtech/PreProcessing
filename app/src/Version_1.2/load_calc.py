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
        
    #determining the load during the balance phase    
    for i in range(len(hip)):
        res_hipacc = np.sqrt( hip['AccX'][i]**2 + hip['AccY'][i]**2 + hip['AccZ'][i]**2) #magnitude of the resultant acceleration vector of the hip during the balance phase
        if hip['Phase'][i] == 0: #checking if both feet are on the ground
            rf_bal.append(calc_force(m/2, em/2, res_hipacc))
            lf_bal.append(calc_force(m/2, em/2, res_hipacc))
        elif hip['Phase'][i] == 1: #checking if the right foot is off the ground
            rf_bal.append(0)
            lf_bal.append(calc_force(m, em, res_hipacc))
        elif hip['Phase'][i] == 2: #checking if the left foot is off the ground
            rf_bal.append(calc_force(m, em, res_hipacc))
            lf_bal.append(0)  
        elif hip['Phase'][i] == 3: #checking if both feet are off the ground
            rf_bal.append(0)
            lf_bal.append(0)
            
    load = [ [i, j, k, k] for i, j, k in zip(rf_bal, lf_bal, hip['Phase']) ] #creating a single array with right load, left load, right foot phase, left foot phase
    load = np.array(load)
    
    #adding in the impact phases     
    for i in range(len(hip)):
        if rf['Impact'][i] == 1:
            load[i,0] = 5 #assigning a load value for when impact phase occurs (future work would involved determining the actual impact load)
            load[i,2] = 4 #assigning the 4 to indicate an impact phase
        elif lf['Impact'][i] == 1:
            load[i,1] = 5
            load[i,3] = 4        
        
    return load
    
if __name__ == '__main__':
    
    import matplotlib.pyplot as plt   
    import pe_v1
    from impact_phase import impact_phase
    
    rpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_rfdatabody_snglsquat_set1.csv'
    lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_lfdatabody_snglsquat_set1.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Stomp\Lheel_Gabby_stomp_set1.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\ChangeDirection\Lheel_Gabby_changedirection_set1.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Jump\Lheel_Gabby_jumping_explosive_set2.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Walking\Lheel_Gabby_walking_heeltoe_set1.csv'
    hpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_hipdatabody_snglsquat_set1.csv'

    rdata = pd.read_csv(rpath)
    ldata = pd.read_csv(lpath)
    hdata = pd.read_csv(hpath)
    
    #acc = ['AccX', 'AccY', 'AccZ']
    #rdata = rdata[acc]
    #ldata = ldata[acc]
    #hdata = hdata[acc]
    
    sampl_rate = 250
    
    ph = pe_v1.Body_Phase(rdata['AccZ'], ldata['AccZ'], 250) #array containing the full body moving decisions
    rdata['Phase'] = ph
    ldata['Phase'] = ph
    hdata['Phase'] = ph 
    
    lf_impact = impact_phase(ldata['AccZ'], sampl_rate)
    rf_impact = impact_phase(rdata['AccZ'], sampl_rate)
    rdata['Impact'] = rf_impact
    ldata['Impact'] = lf_impact
    
    print len(lf_impact), len(rf_impact)
    
    print len(ldata)

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
    
    print len(hdata), len(ld), len(ph)
    print ld
    
    #plt.figure(3)
    #plt.hist(ld[:,1])
    #plt.show()
    
    