# -*- coding: utf-8 -*-
"""
Created on Fri Jun 17 08:10:20 2016

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
    
    f = (((ma + ema)*g) + abs((ma + ema)*a))/1000
    
    return f
    
"""
#############################################INPUT/OUTPUT####################################################
Inputs: Acceleration and phase exploration data (AccX, AccY, AccZ, Phase) of the right heel, left heel and hip 
        sensors; the mass of the user in kilograms; any extra mass the user has strapped on in kilograms
Outputs: array of the load during balance phase, on the right foot (rf_bal) and on the left foot (lf_bal) 
#############################################################################################################
"""

def load_balance(rf, lf, hip, m, em):

    rf_bal = [] #load on the right foot during balance phase is determined in Kilonewtons
    lf_bal = [] #load on the left foot during balance phase is determined in Kilonewtons
    
    #determining the load during the balance phase    
    for i in range(len(rf)):
        res_hipacc = np.sqrt( hip['AccX'][i]**2 + hip['AccY'][i]**2 + hip['AccZ'][i]**2) #magnitude of the resultant acceleration vector of the hip during the balance phase
        if rf['Phase'][i] == 0: #checking if both feet are on the ground
            rf_bal.append(calc_force(m/2, em/2, res_hipacc))
            lf_bal.append(calc_force(m/2, em/2, res_hipacc))
        elif rf['Phase'][i] == 1: #checking if the right foot is off the ground
            lf_bal.append(calc_force(m, em, res_hipacc))
        elif rf['Phase'][i] == 2: #checking if the left foot is off the ground
            rf_bal.append(calc_force(m, em, res_hipacc))
            
    return np.array(rf_bal), np.array(lf_bal)
    
    
if __name__ == '__main__':
    
    import matplotlib.pyplot as plt   
    import pe
    
    rpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Walking\Rheel_Gabby_walking_heeltoe_set1.csv'
    lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Walking\Lheel_Gabby_walking_heeltoe_set1.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Stomp\Lheel_Gabby_stomp_set1.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\ChangeDirection\Lheel_Gabby_changedirection_set1.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Jump\Lheel_Gabby_jumping_explosive_set2.csv'
    #lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Walking\Lheel_Gabby_walking_heeltoe_set1.csv'
    hpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Walking\hips_Gabby_walking_heeltoe_set1.csv'

    rdata = pd.read_csv(rpath)
    ldata = pd.read_csv(lpath)
    hdata = pd.read_csv(hpath)
    
    acc = ['AccX', 'AccY', 'AccZ']
    rdata = rdata[acc]
    ldata = ldata[acc]
    hdata = hdata[acc]
    
    mass = 75 #in kilograms
    exmass = 0 #in kilograms
    ph = pe.Body_Phase(rdata['AccZ'], ldata['AccZ'], 100) #array containing the full body moving decisions
    rdata['Phase'] = ph
    ldata['Phase'] = ph
    hdata['Phase'] = ph    

    op_rf, op_lf = load_balance(rdata, ldata, hdata, mass, exmass) #passing an array of data points and the sampling rate
    
    plt.plot(op_rf)
    plt.plot(op_lf)
    #plt.plot(ldata['AccZ'])
    #plt.plot(ph)
    plt.show()
    
    
