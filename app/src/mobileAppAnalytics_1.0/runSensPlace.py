# -*- coding: utf-8 -*-
"""
Created on Wed Jul 20 16:08:55 2016

@author: Brian
"""
import setUp as su
import numpy as np


"""
#############################################INPUT/OUTPUT####################################################   
Inputs: dataset, checkPlacement string, sensorPlacement vector

Outputs: status check (string), and checkPlacement vector holding sensor palcement decisions

Datasets: failure1_rfoot -> RunSensPlace(data, "R", [0,'58',0]) -> failure1
          failure2_hip -> RunSensPlace(data, "H", [0,0,0]) -> failure2
          failure3_rfoot -> RunSensPlace(data, "R", [0,0,0]) -> failure3
          failure4_lfoot -> RunSensPlace(data, "L", [0,0,0]) -> failure4
          success_hip -> RunSensPlace(data, "H", [0,0,0]) -> success, [0,'75',0]
          success_lfoot -> RunSensPlace(data, "L", [0,0,0]) -> success, ['58',0,0]
          success_rfoot -> RunSensPlace(data, "R", [0,0,0]) -> success, [0,0,'80']
#############################################################################################################
"""

def sensNames(columns):
    prefix = []
    for i in range(len(columns)):
        name = columns[i]
        name = name[:-2]
        if name not in prefix:
            prefix.append(name)
    return prefix

def testTap(data, sens):
    mag = []
    peaks = []
    for i in range(len(data)):
        mag.append(np.sqrt(data[sens+'aX'].ix[i]**2+data[sens+'aY'].ix[i]**2+data[sens+'aZ'].ix[i]**2)) #calc magnitude 
        if mag[i]-mag[i-1] > 2000: #check if deriv of magnitude exceeds threshold
            peaks.append([i, mag[i]]) #add peak to peak list
            
    #check for the amount of peaks and assign success or failures
    if len(peaks) >= 3:
        return True
    elif 0 < len(peaks) < 3:
        return 3
    elif len(peaks) == 0:
        return False

class RunSensPlace(object):
    def __init__(self, data, checkPlacement, sensorPlacement):
        self.status = ''
        self.sensorPlacement = sensorPlacement
        columns = data.columns.values[1:]
        prefix = sensNames(columns)

        #test for the amount of taps
        sens1 = data.ix[:,0:7]
        sens2 = data.ix[:,7:14]
        sens3 = data.ix[:,14:21]
        output1 = testTap(sens1, prefix[0])
        output2 = testTap(sens2, prefix[1])
        output3 = testTap(sens3, prefix[2])
        response = [output1, output2, output3]

        #interpret the amount of taps as a success or one of two failures
        if response.count(True) == 1 and response.count(False) == 2:
            sensor = response.index(True)
        elif response.count(False) == 3:
            self.status = 'failure2' #not enough detectable taps or no taps
        elif response.count(False) == 2 and response.count(3) == 1:
            self.status = 'failure2' #not enough detectable taps
        elif response.count(False) == 1 or response.count(False) == 0:
            self.status = 'failure3' #two or more sensors experiencing taps or similar at once
        
        if self.status not in ['failure2', 'failure3']:
            #find vertical orientation by averaging y-axis
            if sensor == 0:
                orient = np.mean(sens1[prefix[0]+'aY'])
            elif sensor == 1:
                orient = np.mean(sens2[prefix[1]+'aY'])
            elif sensor == 2:
                orient = np.mean(sens3[prefix[2]+'aY'])
            
            #make sure orient is in line with expectation if not throw an error
            if checkPlacement == "H" and orient > 0:
                self.status = 'success'
                self.sensorPlacement[1] = prefix[sensor]
            elif checkPlacement == "H" and orient < 0:
                self.status = 'failure4'
            
            if checkPlacement == "R" and orient > 0:
                self.status = 'success'
                self.sensorPlacement[2] = prefix[sensor]
            elif checkPlacement == "R" and orient < 0:
                self.status = 'failure4'
                    
            if checkPlacement == "L" and orient > 0:
                self.status = 'success'
                self.sensorPlacement[0] = prefix[sensor]
            elif checkPlacement == "L" and orient < 0:
                self.status = 'failure4'
            
            #make sure one sensor doesn't get assigned to two placements
            dupes = [x for x in self.sensorPlacement if self.sensorPlacement.count(x) > 1]
            if len(dupes) > 0 and dupes[0] != 0:
                self.status = 'failure1'
            
        
        
        
        
