# -*- coding: utf-8 -*-
"""
Created on Wed Jul 20 16:08:55 2016

@author: Brian
"""
import setUp as su
import numpy as np

def testTap(data):
    mag = []
    peaks = []
    for i in range(len(data.aX)):
        mag.append(np.sqrt(data.aX[i]**2+data.aY[i]**2+data.aZ[i]**2)) #calc magnitude 
        if mag[i]-mag[i-1] > 2000: #check if deriv of magnitude exceeds threshold
            peaks.append([i, mag[i]]) #add peak to peak list
            
    #check for the amount of peaks and assign success or failures
    if len(peaks) == 3:
        return True
    elif len(peaks) > 3:
        return 2
    elif 0 < len(peaks) < 3:
        return 3
    elif len(peaks) == 0:
        return False

class RunSensPlace(object):
    def __init__(self, path, hz, checkPlacement, sensorPlacement):
        self.status = ''
        self.sensorPlacement = sensorPlacement
        data = su.SensPlace(path, hz) #create object that holds data and sensor names
        
        #test for the amount of taps
        sens1 = data.lfdataset
        sens2 = data.hipdataset
        sens3 = data.rfdataset
        output1 = testTap(sens1)
        output2 = testTap(sens2)
        output3 = testTap(sens3)
        response = [output1, output2, output3]
        
        #interpret the amount of taps as a success or one of two failures
        if response.count(True) == 1 and response.count(False) == 2:
            sensor = response.index(True)
        elif response.count(False) == 3:
            self.status = 'failure2' #not enough detectable taps or no taps
        elif response.count(False) == 2 and response.count(3) == 1:
            self.status = 'failure2' #not enough detectable taps
        elif response.count(False) == 2 and response.count(2) == 1:
            self.status = 'failure2' #too many taps
        elif response.count(False) == 1 or response.count(False) == 0:
            self.status = 'failure3' #two or more sensors experiencing taps or similar at once
        
        if self.status not in ['failure2', 'failure3']:
            #find vertical orientation by averaging y-axis
            if sensor == 0:
                orient = np.mean(sens1.aY)
            elif sensor == 1:
                orient = np.mean(sens2.aY)
            elif sensor == 2:
                orient = np.mean(sens3.aY)
            
            #make sure orient is in line with expectation if not throw an error
            if checkPlacement == "H" and orient < 0:
                self.status = 'success'
                self.sensorPlacement[1] = data.prefix[sensor]
            elif checkPlacement == "H" and orient > 0:
                self.status = 'failure4'
            
            if checkPlacement == "R" and orient > 0:
                self.status = 'success'
                self.sensorPlacement[2] = data.prefix[sensor]
            elif checkPlacement == "R" and orient < 0:
                self.status = 'failure4'
                    
            if checkPlacement == "L" and orient > 0:
                self.status = 'success'
                self.sensorPlacement[0] = data.prefix[sensor]
            elif checkPlacement == "L" and orient < 0:
                self.status = 'failure4'
            
            #make sure one sensor doesn't get assigned to two placements
            dupes = [x for x in self.sensorPlacement if self.sensorPlacement.count(x) > 1]
            if len(dupes) > 0 and dupes[0] != 0:
                self.status = 'failure1'
            
        
        
        
        