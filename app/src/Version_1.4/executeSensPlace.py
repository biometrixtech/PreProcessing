# -*- coding: utf-8 -*-
"""
Created on Fri Jul 22 11:40:05 2016

@author: Brian
"""

import runSensPlace as rsp
class SensorPlacementFailure(ValueError):
    pass


if __name__ == "__main__":
    sens_root = 'C:\\Users\\Brian\\Documents\\Biometrix\Data\\Collected Data\\Sensor Placement test\\Full\\Good_hip.csv'
    sensorPlacement = [0,0,0] #initiate sensor placement list
    failures = ['failure1', 'failure2', 'failure3', 'failure4'] #list of possible failures
    sens1 = rsp.RunSensPlace(sens_root, 100, "H", sensorPlacement) #run sens place on first sensor
    if sens1.status in failures: #check for failures
        raise SensorPlacementFailure
    else:
        sens_root = 'C:\\Users\\Brian\\Documents\\Biometrix\Data\\Collected Data\\Sensor Placement test\\Full\\Good_rfoot.csv'
        sens2 = rsp.RunSensPlace(sens_root, 100, "R", sens1.sensorPlacement) #run sens place on second sensor
        if sens2.status in failures: #check for failures
            print(sens2.status)
            raise SensorPlacementFailure
        else:
            print(sens2.sensorPlacement)
            sens_root = 'C:\\Users\\Brian\\Documents\\Biometrix\Data\\Collected Data\\Sensor Placement test\\Full\\Good_rfoot.csv'
            sens3 = rsp.RunSensPlace(sens_root, 100, "L", sens2.sensorPlacement) #run sens place on third sensor
            if sens3.status in failures: #check for failure
                print(sens3.status)
                raise SensorPlacementFailure
            else:
                output = sens3.sensorPlacement #output final sensor palcements