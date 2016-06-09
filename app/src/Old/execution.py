# -*- coding: utf-8 -*-
"""
Created on Fri Apr 15 10:23:44 2016

@author: Brian
"""

import numpy as np
import pandas as pd
import Data_Processing as prep
import Exercise_Filter as exer
import Phase_Detect as phase
import time
import matplotlib.pyplot as plt
import scipy.stats as stat

class ObjectMismatchError(ValueError):
    pass

if __name__ == "__main__":
    root = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\' #root path for data folder...reset to your own path
    exercise = "SnglSquat" #Look at file name to find equiv for single squat, double, and LESS
    subject = "Subject1" #Subject you want to look at
    num = 1 #which set you want to evaluate
    sens_loc = ["hips", "rightheel", "leftheel"] #list holding sensor location
    hz = 250 #smapling rate
    #concatenated paths for all sensors
    pathip = root + subject + '_' + sens_loc[0] + '_42116_' + exercise + '.csv'
    pathrf = root + subject + '_' + sens_loc[1] + '_42116_' + exercise + '.csv'
    pathlf = root + subject + '_' + sens_loc[2] + '_42116_' + exercise + '.csv'
    
    #output path...I just keep it in the same folder with a generic name...you could always run through all of them and place in new folder.
    #Might be worth it instead of having to run this everytime you change the dataset
    outhipp = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\hipdatabody.csv'
    outrfp = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\rfdatabody.csv'
    outlfp = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\By Exercise\\lfdatabody.csv'    
    
    #read all datasets in
    hip = pd.read_csv(pathip)
    lfoot = pd.read_csv(pathlf)
    rfoot = pd.read_csv(pathrf)
    
    #filter out non-set data
    hip = hip[hip['set'] == num]
    lfoot = lfoot[lfoot['set'] == num]
    rfoot = rfoot[rfoot['set'] == num]
    
    #make sure all datasets are off same length
    if len(hip) != len(lfoot) or len(hip) != len(rfoot):
        lens = [len(hip), len(lfoot), len(rfoot)] #list of dataset lengths
        lenmin = np.min(lens) #find min length of datasets
        #find diff between min and dataset size. If no diff do nothing, if there is take off end of dataset        
        hdiff = len(hip) - lenmin
        if hdiff > 0:
            hip = hip[:-hdiff]
        ldiff = len(lfoot) - lenmin
        if ldiff > 0:
            lfoot = lfoot[:-ldiff]
        rdiff = len(rfoot) - lenmin
        if rdiff > 0:
            rfoot = rfoot[:-rdiff]
    
    start = time.process_time()
    #columns resulting from frame transformation
    cols = ["qW", "qX", "qY", "qZ", "EulerX", "EulerY", "EulerZ", "AccX", "AccY", "AccZ", "gyrX", "gyrY", "gyrZ", "magX", "magY", "magZ"]
    #initiate lists that will hold resulting data
    hipbf, hipsf, rfbf, rfsf, lfbf, lfsf, hipfinal, rffinal, lffinal = [[] for i in range(9)]    
    iters = len(hip) #find how many data vectors
    
    #yaw offsets for various sensors
    hq0 = np.matrix([hip.ix[0,'qW_raw'], hip.ix[0,'qX_raw'], hip.ix[0,'qY_raw'], hip.ix[0,'qZ_raw']]) #t=0 quaternion
    hyaw_fix = prep.yaw_offset(hq0) #uses yaw offset function above to compute yaw offset quaternion
    hyfix_c = prep.QuatConj(hyaw_fix) #uses quaternion conjugate function to return conjugate of yaw offset
    
    lq0 = np.matrix([lfoot.ix[0,'qW_raw'], lfoot.ix[0,'qX_raw'], lfoot.ix[0,'qY_raw'], lfoot.ix[0,'qZ_raw']]) #t=0 quaternion
    lyaw_fix = prep.yaw_offset(lq0) #uses yaw offset function above to compute yaw offset quaternion
    lyfix_c = prep.QuatConj(lyaw_fix) #uses quaternion conjugate function to return conjugate of yaw offset
        
    rq0 = np.matrix([rfoot.ix[0,'qW_raw'], rfoot.ix[0,'qX_raw'], rfoot.ix[0,'qY_raw'], rfoot.ix[0,'qZ_raw']]) #t=0 quaternion
    ryaw_fix = prep.yaw_offset(rq0) #uses yaw offset function above to compute yaw offset quaternion
    ryfix_c = prep.QuatConj(ryaw_fix) #uses quaternion conjugate function to return conjugate of yaw offset
           
    for i in range(iters):
        #frame transforms for all sensors (returns sensor frame data as well but not very relevant)
        hipbod, hipsen = prep.FrameTransform(hip.ix[i,:], hyfix_c)
        lfbod, lfsen = prep.FrameTransform(lfoot.ix[i,:], lyfix_c)
        rfbod, rfsen = prep.FrameTransform(rfoot.ix[i,:], ryfix_c) 
        #create nested lists containing resulting data vectors
        hipbf.append(hipbod[0,:]) #body frame hip
        hipsf.append(hipsen[0,:]) #sensor frame hip
        lfbf.append(lfbod[0,:]) #body frame left
        lfsf.append(lfsen[0,:]) #sensor frame left
        rfbf.append(rfbod[0,:]) #body frame right
        rfsf.append(rfsen[0,:]) #sensor frame right

        ###how to deal with edge points where insufficient data to run exercise filter
        if len(hipbf) < hz*.4 + 1:
            if i%2 != 0:
                hipfinal.append(np.append(hipbf[int((i-1)/2)],1)) #assume person not performing exercise at the edge
            else:
                None
        else:
            data = pd.DataFrame(hipbf[int(i-hz*.4):i+1], columns=cols) #create dataframe of relevant data to be put into exercise filter
            hipfinal.append(np.append(hipbf[int(i-hz*.2)], exer.Exercise_Filter(data, 'Double', hz))) #run exercise filt on point and append result to list
        
        #####how to deal with endpoints
        if i < hz*.2:
            None
        else:
            ldata = pd.DataFrame(lfbf[int(i-hz*.2):i], columns=cols) #relevant df for left foot
            rdata = pd.DataFrame(rfbf[int(i-hz*.2):i], columns=cols) #relevant df for right foot
            indic = phase.Phase_Detect(ldata, rdata, hz) #find phase indicator
            lffinal.append(np.append(lfbf[int(i-hz*.2)],indic)) #append result from phase to list
            rffinal.append(np.append(rfbf[int(i-hz*.2)],indic)) #append result from phase to list
    print(time.process_time()-start)
    #create df for all datasets
    hipcols = ["qW", "qX", "qY", "qZ", "EulerX", "EulerY", "EulerZ", "AccX", "AccY", "AccZ", "gyrX", "gyrY", "gyrZ", "magX", "magY", "magZ","Exercise"]
    ftcols = ["qW", "qX", "qY", "qZ", "EulerX", "EulerY", "EulerZ", "AccX", "AccY", "AccZ", "gyrX", "gyrY", "gyrZ", "magX", "magY", "magZ", "Phase"]
    hipdata = pd.DataFrame(hipfinal, columns = hipcols)
    lfdata =  pd.DataFrame(lffinal, columns = ftcols)  
    rfdata = pd.DataFrame(rffinal, columns = ftcols)   
    #add in column that was missing from being added above
    hipdata['Phase'] = lfdata['Phase']
    rfdata['Exercise'] = hipdata['Exercise']
    lfdata['Exercise'] = hipdata['Exercise']
    #save as csv
    hipdata.to_csv(outhipp, index=False)  
    rfdata.to_csv(outrfp, index=False)
    lfdata.to_csv(outlfp, index=False)
    
    #if you want to plot variable when you run the script
    comp1 = 'EulerX'
#    comp2 = 'Phase'
#    comp3 = 'EulerX'
    comp4 = 'Exercise'
#    up = 4000
#    low = 6000
##    hipdata = hipdata[up:low]
##    lfdata = lfdata[up:low]
##    rfdata = rfdata[up:low]
    data = hipdata
    plt.plot(data[comp1], 'r') #plot component 1
#    plt.plot(data[comp2], 'b') #plot component 2
#    #plt.plot(hipdata[comp3], 'g') #plot component 3
    plt.plot(hipdata[comp4], 'purple') #plot component 4      
    plt.xlabel('Elapsed Time')
    plt.show()




#output_X = np.zeros((len(sens_loc), len(cme)))
#output_Y = np.zeros((len(sens_loc), len(cme)))
#output_Z = np.zeros((len(sens_loc), len(cme)))
#for j in range(0,len(sens_loc)):
#    for i in range(0,len(cme)):
#        arr = prep.main(exercise, sens_loc[j], cme[i], feats)
#        output_X[j,i] = arr[0,0]
#        output_Y[j,i] = arr[0,1]
#        output_Z[j,i] = arr[0,2]
#
#df_x = pd.DataFrame(output_X, index=sens_loc, columns=cme)
#df_y = pd.DataFrame(output_Y, index=sens_loc, columns=cme)
#df_z = pd.DataFrame(output_Z, index=sens_loc, columns=cme)
#
#df_x = df_x.div(df_x.Normal, axis = 'index')
#df_y = df_y.div(df_y.Normal, axis = 'index')
#df_z = df_z.div(df_z.Normal, axis = 'index')
#
#print(df_x)
#print(df_y)
#print(df_z)