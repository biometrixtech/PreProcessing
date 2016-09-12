# -*- coding: utf-8 -*-
"""
Created on Thu Jul  7 12:34:12 2016

@author: Brian
"""
import runAnalytics as ra
#import runAnatomical as rana
#import executionScore as exec_score
import numpy as np
import StringIO as io
import psycopg2
import sys
import datetime
"""
#############################################INPUT/OUTPUT####################################################   
Inputs: filepath to anatomical calibration and analytics datasets, sampling rates for each, mass, and extra mass
Outputs: object holding anatomical corrections, object with CMEs, execution score
#############################################################################################################
"""

if __name__ == "__main__":
    try: 
        start = datetime.datetime.now()         
       #anatom_root = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\Alignment test\\bow13comb.csv'
        #data_root = '/Users/shagun/Desktop/combined_Subject2_LESS_synced_1470668910202.csv'
        data_root = 'C:\\Repos\\PreProcessing\\data\\combined_Subject2_LESS_synced_1470668910202.csv' #root path for data folder...reset to your own path
            
        #anatom = rana.RunAnatomical(anatom_root, 100) #(filepath, sampling rate)
        cme = ra.RunAnalytics(data_root, 75, 0, 250, None)  #(filepath, weight, extra weight, sampling rate, anatomical calibration results) 
        analyticsEnd = datetime.datetime.now()
        diff = analyticsEnd - start
        print('Analytics time:' , diff.total_seconds())  
        obsCount = len(cme.load)    
        userId = np.full((obsCount),116,np.int32)
        exerciseId = np.full((obsCount),1,np.int32)
        obsIndex = np.arange(obsCount)
        merged = np.vstack((userId, exerciseId,obsIndex, cme.cont_contra[:,1],cme.cont_hiprot[:,1],cme.load[:,0],cme.load[:,1],cme.load[:,2],cme.load[:,3],cme.contr_prosup[:,1],cme.contl_prosup[:,1],cme.timestamp, cme.cont_contra[:,2],cme.cont_hiprot[:,2], cme.contr_prosup[:,2], cme.contl_prosup[:,2]))
        f = io.StringIO()
        np.savetxt(f, merged.transpose(), delimiter="\t",fmt="%i\t%i\t%i\t%1.3f\t%1.3f\t%1.3f\t%1.3f\t%1.3f\t%1.3f\t%1.3f\t%1.3f\t%i\t%1.3f\t%1.3f\t%1.3f\t%1.3f")    
        f.seek(0) #put the position of the buffer at the beginning
        conn = psycopg2.connect("dbname='Analytics' user='biometrix' host='localhost' password='ButThisGoes211'")
        cur = conn.cursor()
        cur.copy_from(file=f, table='movement2',sep='\t', columns=('"userId"', '"exerciseId"','"obsIndex"','"hipDrop"','"hipRot"','"loadR"','"loadL"','"phaseR"','"phaseL"','"pronR"','"pronL"','"epochTime"','"nHipDrop"','"nHipRot"','"nPronR"','"nPronL"'))
        conn.commit()    
        conn.close()
        end = datetime.datetime.now()
        c = end - start
        print('Total time:', c.total_seconds())
    
    #Execution Score
    #score = exec_score.weight_load(cme.nr_contra, cme.nl_contra, cme.nr_prosup, cme.nl_prosup, cme.nr_hiprot, cme.nl_hiprot, cme.nrdbl_hiprot, cme.nldbl_hiprot, cme.n_landtime, cme.n_landpattern, cme.load)
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise    