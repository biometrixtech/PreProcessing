# -*- coding: utf-8 -*-
"""
Created on Sun Oct 02 09:24:08 2016

@author: court
"""

import numpy as np

import quatOps as qo
import quatConvs as qc

#import setUp as su


"""
#############################################INPUT/OUTPUT####################################################
Inputs: Raw feet data for time of specialized sitting calibration and feet_yaw_transform (calculated in standing
        calibration by anatomicalCalibrationUpgrade.py)
Outputs: feet_roll_transform

Specialized sitting calib. Uses feet_yaw_transform to interpret foot position for this period.
Outputs roll value that should be deleted and recalculated every 3 mo's.
#############################################################################################################
"""

def sittingFeetCal(raw_feet_coordsj,feet_yaw_transform):
    ##### Import feet sensor frame data for special calibration phase

    # create storage for data
    feet_asfj=np.zeros((len(raw_feet_coordsj),4))
    feet_asfj_components=np.zeros((len(raw_feet_coordsj),3))
    feet_roll_transform_inst=np.zeros((len(raw_feet_coordsj),4))
    
    #### use yaw offset from hip_aif to determine feet_asf for this separate recording period
    for i in range(len(raw_feet_coordsj)):
        feet_asfj[i,:]=qo.quat_prod(raw_feet_coordsj.ix[i,:],feet_yaw_transform)
    
        #### Isolate roll offset
        feet_asfj_components[i,:] = qc.q2eul(feet_asfj[i,:])
        feet_roll_transform_inst[i,:] = qc.eul2q(feet_asfj_components[i,2],0,0)
    
    #### GET AVERAGE OF FEET_ROLL_TRANSFORM_INST DATA OVER RECORDING PERIOD
    feet_roll_transform = qo.quat_avg(feet_roll_transform_inst)
    
    return feet_roll_transform




if __name__ == '__main__':
    ####READ IN DATA ~ Will change when we call from the database#####
    path = 'C:\Users\court\Desktop\BioMetrix\PreProcessing-master\PreProcessing\app\test\data\anatomicalCalibration\Good.csv'
#    data = su.Analytics(path, 0, 0, 100)
##    body = TransformData(data.hipdataset)