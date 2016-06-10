# -*- coding: utf-8 -*-
"""
Created on Thu Jun  9 14:46:17 2016

@author: Brian
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import phase_exploration as phase

if __name__ == "__main__":
    hz = 100
    edge = int(.2*hz)
    infl = .0001
    inflg = .00015
    w = int(hz*.08)
    movhold = [0]*int(1.5*w)
    gmovhold = [0]*int(1.5*w)
    
    rpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\BodyFrame walking\\RHeel_Gabby_walking_heeltoe_set1.csv'
    lpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\BodyFrame walking\\LHeel_Gabby_walking_heeltoe_set1.csv'
    hpath = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\BodyFrame walking\\hips_Gabby_walking_heeltoe_set1.csv'
    
    right = pd.read_csv(rpath).as_matrix()
    left = pd.read_csv(lpath).as_matrix()
    hip = pd.read_csv(hpath).as_matrix()
    
    for i in range(len(right)):
        rdata = right[0:i, :]
        ldata = left[0:i, :]
        if len(rdata) >= 2*w +1:
            larr = ldata[i-2*w+1:i+2, 9]
            #rarr = rdata[i-2*w+1:i+1, 9]
            uaZ = pd.rolling_mean(larr, window=w, center=True)
            stdaZ = pd.rolling_std(larr, window=w, center=True)
            uaZ = uaZ[~np.isnan(uaZ)]
            stdaZ = stdaZ[~np.isnan(stdaZ)]
            
            if i == 2*w+1:
                print(stdaZ)
                new_u = np.mean(stdaZ)
                print(new_u)
                new_std = np.std(stdaZ)
                gnew_u = np.mean(uaZ)
                gnew_std = np.std(uaZ)
            else:
                new_u = (new_u + infl*stdaZ[-1])/(1+infl) #find new mean
                new_std = (new_std + infl*(np.sqrt((stdaZ[-1]-new_u)**2))/(1+infl)) #find new SD
                gnew_u = (gnew_u + inflg*uaZ[-1])/(1+inflg) #find new mean
                gnew_std = (gnew_std + inflg*(np.sqrt((uaZ[-1]-gnew_u)**2))/(1+inflg)) #find new SD
            
            movhold.append(phase.Move(stdaZ[-1], w, new_u, new_std))
            gmovhold.append(phase.Grad_Move(uaZ[-1], w, gnew_u, gnew_std))
            cmove = phase.Comb_Move(movhold, gmovhold)
            mscore = pd.rolling_mean(cmove, window=edge)
            final = phase.Final(mscore)
            final = phase.Fix_Edges(final, edge)
    
    print([i for i in range(len(final)) if final[i] == 10])
    
    plt.plot(final)
    plt.plot(left[:, 9])
    plt.show()