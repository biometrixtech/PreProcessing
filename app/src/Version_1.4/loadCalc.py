# -*- coding: utf-8 -*-
"""
Created on Fri Jun 24 14:59:52 2016

@author: Ankur
"""

import numpy as np
from phaseID import phase_id

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

def load_bal_imp(rfPhase, lfPhase, hipAccX, hipAccY, hipAccZ, m, em):

    rf_bal = [] #load on the right foot during balance phase is determined in Kilonewtons
    lf_bal = [] #load on the left foot during balance phase is determined in Kilonewtons
        
    #determining the load during the balance and impact phases for the right foot    
    for i in range(len(rfPhase)):
        res_hipacc = np.sqrt(hipAccX[i]**2 + hipAccY[i]**2 + hipAccZ[i]**2) #magnitude of the resultant acceleration vector of the hip during the balance phase
        if rfPhase[i] == phase_id.rflf_ground.value: #checking if both feet are on the ground
            rf_bal.append(calc_force(m/2, em/2, res_hipacc))
        elif rfPhase[i] == phase_id.lf_ground.value: #checking if the left foot is on the ground
            rf_bal.append(0)
        elif rfPhase[i] == phase_id.rf_ground.value: #checking if the right foot is on the ground
            rf_bal.append(calc_force(m, em, res_hipacc))
        elif rfPhase[i] == phase_id.rflf_offground.value: #checking if both feet are off the ground
            rf_bal.append(0)
        elif rfPhase[i] == phase_id.rf_imp.value: #checking for right foot impact
            rf_bal.append(5) #assigning a load value for when impact phase occurs (future work would involved determining the actual impact load)
        
    #determining the load during the balance and impact phases for the left foot     
    for i in range(len(lfPhase)):
        res_hipacc = np.sqrt(hipAccX[i]**2 + hipAccY[i]**2 + hipAccZ[i]**2) #magnitude of the resultant acceleration vector of the hip during the balance phase
        if lfPhase[i] == phase_id.rflf_ground.value: #checking if both feet are on the ground
            lf_bal.append(calc_force(m/2, em/2, res_hipacc))
        elif lfPhase[i] == phase_id.lf_ground.value: #checking if the left foot is on the ground
            lf_bal.append(calc_force(m, em, res_hipacc))
        elif lfPhase[i] == phase_id.rf_ground.value: #checking if the right foot is on the ground
            lf_bal.append(0)  
        elif lfPhase[i] == phase_id.rflf_offground.value: #checking if both feet are off the ground
            lf_bal.append(0)
        elif lfPhase[i] == phase_id.lf_imp.value: #checking for left foot impact
            lf_bal.append(5) #assigning a load value for when impact phase occurs (future work would involved determining the actual impact load)
        
    
    load = [ [i, j, k, l] for i, j, k, l in zip(rf_bal, lf_bal, rfPhase, lfPhase) ] #creating a single array with right load, left load, right foot phase, left foot phase
    load = np.array(load)
        
    return load
    
if __name__ == '__main__':
    
    import matplotlib.pyplot as plt   
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

    rdata = np.genfromtxt(rpath, delimiter = ",", dtype = float, names = True)
    ldata = np.genfromtxt(lpath, delimiter = ",", dtype = float, names = True)
    hdata = np.genfromtxt(hpath, delimiter = ",", dtype = float, names = True)     
    
    #rdata = pd.read_csv(rpath)
    #ldata = pd.read_csv(lpath)
    #hdata = pd.read_csv(hpath)
    
    sampl_rate = 250
    comp = 'AccZ'
    ptch = 'EulerY'
    racc = rdata[comp]
    lacc = ldata[comp] #input AccZ values!
    rpitch = rdata[ptch]
    lpitch = ldata[ptch]
    #ph = Body_Phase(racc, lacc, rpitch, lpitch, sampl_rate)
    
    lf_phase, rf_phase = combine_phase(ldata['AccZ'], rdata['AccZ'], rpitch, lpitch, sampl_rate)
    
    rdata['Phase'] = rf_phase
    ldata['Phase'] = lf_phase
    
    print(len(rf_phase), len(rdata), len(ldata))

    mass = 75 #in kilograms
    exmass = 0 #in kilograms
    ld = load_bal_imp(rdata['Phase'], ldata['Phase'], hdata['AccX'], hdata['AccY'], hdata['AccZ'], mass, exmass) #passing the hip, user mass and extra mass data
    
    #load_check = pd.DataFrame(ld)
    #load_check.to_csv('C:\\Users\\Ankur\\Desktop\\loadCalc\\output_loadCalc.csv')    
    
    #plt.figure(4) 
    #plt.plot(ld[:,0])
    #plt.plot(ld[:,1])
    #plt.figure(2)
    #plt.plot(ldata['AccZ'])
    #plt.plot(ph)
    #plt.show()
    
    print(len(ldata), len(ld), len(lf_phase), len(rf_phase))
    print(ld)
    
    #plt.figure(3)
    #plt.hist(ld[:,1])
    #plt.show()
    
    