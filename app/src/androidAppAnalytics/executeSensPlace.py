# -*- coding: utf-8 -*-
"""
Created on Fri Jul 22 11:40:05 2016

@author: Brian
"""

"""
#############################################INPUT/OUTPUT####################################################   
Inputs: 3 datasets (sequentially) corresponding to three different sensor detection tests

Outputs: output (a vector containing the sensor placement decision in <L, H, R> sequence)

Datasets: Good -> executeSensPlace -> ['BioMX58_', 'BioMX75_', 'BioMX80_']
          Double assign error -> executeSensPlace -> failure1
          Extra Movement Rfoot -> executeSensPlace -> failure3
          Extra taps Rfoot -> executeSensPlace -> failure2
          Upside down Hip -> executeSensPlace -> failure4
          Upside down Lfoot -> executeSensPlace -> failure4

#############################################################################################################
"""

import runSensPlace as rsp
import pandas as pd
class SensorPlacementFailure(ValueError):
    pass


if __name__ == "__main__":
    sens_root = 'C:\\Users\\Brian\\Documents\\GitHub\\PreProcessing\\app\\test\\data\\sensorPlacement\\Double assign sensor\\Good_hip.csv'
    data = pd.read_csv(sens_root)
    sensorPlacement = [0,0,0] #initiate sensor placement list
    failures = ['failure1', 'failure2', 'failure3', 'failure4'] #list of possible failures
    sens1 = rsp.RunSensPlace(data, "H", sensorPlacement) #run sens place on first sensor
    if sens1.status in failures: #check for failures
        print(sens1.status, 'sens1')
        raise SensorPlacementFailure
    else:
        sens_root = 'C:\\Users\\Brian\\Documents\\GitHub\\PreProcessing\\app\\test\\data\\sensorPlacement\\Double assign sensor\\Dupe_rfoot.csv'
        data = pd.read_csv(sens_root)
        sens2 = rsp.RunSensPlace(data, "R", sens1.sensorPlacement) #run sens place on second sensor
        if sens2.status in failures: #check for failures
            print(sens2.status, 'sens2')
            raise SensorPlacementFailure
        else:
            sens_root = 'C:\\Users\\Brian\\Documents\\GitHub\\PreProcessing\\app\\test\\data\\sensorPlacement\\Double assign sensor\\Good_lfoot.csv'
            data = pd.read_csv(sens_root)
            sens3 = rsp.RunSensPlace(data, "L", sens2.sensorPlacement) #run sens place on third sensor
            if sens3.status in failures: #check for failure
                print(sens3.status, 'sens3')
                raise SensorPlacementFailure
            else:
                output = sens3.sensorPlacement #output final sensor palcements