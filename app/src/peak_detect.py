# -*- coding: utf-8 -*-
"""
Created on Tue May 17 11:15:23 2016

@author: Brian
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time

comp = 'EulerX'

def slope(data):
    data = data.reset_index() ##reset index for standardization
    slope = (data[comp].ix[0]-data[comp].ix[2])/2 #find slope
    return slope

def find_cv(data, cv, slope_thresh, mag_thresh):
    data = data.reset_index() #reset index for standardization
    sm_slope = np.mean(data['slope']) #smooth slope
    if abs(sm_slope) < slope_thresh and abs(data[comp].ix[20]-cv) > mag_thresh: #if smoothed slope and new cv far away from prev cv mark as new cv 
        cv = 1
        return cv

def minmax_search(data):
    data = data.reset_index() #reset index for standardization
    #determine if min or max and search for max or min around identified cv
    if data[comp].ix[0] - data[comp].ix[40] < 0:
        ind = np.argmax(data[comp].ix[40:])
#        if ind-40 > 0:
#            print("moved " + str(ind-40))
        return ind
    else:
        ind = np.argmin(data[comp].ix[40:])
#        if ind-40 > 0:
#            print("moved " + str(ind-40))
        return ind

def dynamic_threshold(cv, i, upper, lower):
    if i-cv <= 200: #don't change threshold
        return upper
    if 200 < i-cv <= 500: #linearly decrease threshold
        return upper-((i-cv-200)/300)*(upper-lower)
    if i-cv > 500: #set threshold at lower limit
        return lower

if __name__ == "__main__":
    root = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\lfdatabody.csv'
    
    shuttle = pd.DataFrame() #initiate dataframe
    rfdata = pd.read_csv(root)
    prelim = [0]
    conf_cv = [0]
    cv_val = []
    fin_i = []
    
    go = time.process_time()
    for i in range(len(rfdata)):
        shuttle = shuttle.append(rfdata.ix[i,:], ignore_index=True) #acrue data points in shuttle
        if len(shuttle) >= 3: #wait until 3 data points have come
            delta = slope(shuttle[-3:]) #find slope
            shuttle.ix[i-1, 'slope'] = delta #add slope to data vector
            if len(shuttle) >= 40: #wait until 40 data points have acrued
                cv= find_cv(shuttle.ix[i-40:i,:], shuttle[comp].ix[prelim[-1]], .0001, .025) #find critical value (cv)
                if cv == 1:
                    prelim.append(i) #add cv to prelim list
                else:
                    None
                j = 1
                while j < len(prelim)-1: #prelim should always have 3 points 
                    mag = dynamic_threshold(prelim[0], i, .05, .025) #adjust magnitude threshold
                    if len(shuttle) > prelim[j] + 100 and prelim[j] > 40: #make sure 100 points have gone beyond cv
                        cand = prelim[j]
                        prelim[j] = minmax_search(shuttle[cand-40:cand+100]) + cand - 40 #find minmax
                    if abs(shuttle[comp].ix[prelim[j+1]] - shuttle[comp].ix[prelim[j]]) < mag:
                        del prelim[j+1] #delete newest data point in prelim if doesnt pass threshold
                        break #return to next data point
                    if np.sign(shuttle[comp].ix[prelim[j-1]] - shuttle[comp].ix[prelim[j]]) == np.sign(shuttle[comp].ix[prelim[j]] - shuttle[comp].ix[prelim[j+1]]):                       
                        del prelim[j] #delete if not min/max
                    elif abs(shuttle[comp].ix[prelim[j-1]] - shuttle[comp].ix[prelim[j]]) >= mag:  #make sure meets magnitude threshold                    
                        conf_cv.append(prelim[j]) #add to confirmed cv list
                        j = j+1
                        if len(conf_cv) >= 2: #if there are enough cv's in list
                            cand = conf_cv[0]
                            fin_i.append(cand) #add to final cv list
                            cv_val.append(shuttle[comp].ix[cand]) #get associated variable value
                            if len(cv_val) >= 2:
                                if abs(cv_val[-1]-cv_val[-2]) >= .05: #double check to make sure mag threshold is satisfied
                                    print(cv_val[-1]-cv_val[-2])
                                    print("Max/min point at " +str(cand)+" detected at "+ str(i) + " diff of " + str(i-cand))
                            prelim.remove(cand)
                            del conf_cv[0] #remove cv from confirmed list and prelim list
                    else:
                        #print("mag not enough " + str(prelim[j]))
                        del prelim[j] #remove from prelim
            else:
                None
        else:
            None
    print(time.process_time()-go)
    
    #for plotting data
##    print(cv_val)
##    print(fin_i)    
#    comp1 = comp
#    comp2 = 'Exercise'
#    #comp3 = 'sm_slope'
#
#    data = rfdata
#    down = 1
#    data = data[down:]
#    fin_i = [x if x>down else down for x in fin_i]
#    
#    plt.plot(data[comp1], 'r') #plot component 1
#    plt.scatter(fin_i, cv_val)
#    #plt.plot(data[comp2], 'b') #plot component 2
#    #plt.plot(data[comp3], 'g') #plot component 3   
#    plt.xlabel('Elapsed Time')
#    plt.show()