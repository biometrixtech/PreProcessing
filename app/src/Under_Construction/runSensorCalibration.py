# -*- coding: utf-8 -*-
"""
Created on Mon Aug 22 18:29:05 2016

@author: Brian
"""

import setUp as su
import matplotlib.pyplot as plt
import anatomicalCalibration as ac
import coordinateFrameTransformation as prep
import dataObject as do
import numpy as np


def ident_hip(data1, data2, data3):
    std1 = [np.std(data1), np.std(data2), np.std(data3)]

    max_val = max(std1)
    max_idx = std1.index(max_val)
    return max_idx

def ident_feet(foot1, foot2, forward):
    f1_h = prep.Calc_Euler(foot1)[2]
    f2_h = prep.Calc_Euler(foot2)[2]
    diff = [abs(f1_h-forward), abs(f2_h-forward)]

    min_val = min(diff)
    min_idx = diff.index(min_val)
    return min_idx
    
def status_checks(hips, foot1, foot2):
    #make sure sensors are oriented right
    if hips.orient < 700 or foot1.orient < 0 or foot2.orient < 0:
        status = "failure4"
        return status
    else:
        status = ''
    
    f1_h = prep.Calc_Euler(foot1.s_q)[2]
    f2_h = prep.Calc_Euler(foot2.s_q)[2]
    if abs(f1_h-f2_h) < .5:
        status = "failure1"
        return status                 
        
class runSensorCalibration(object):
    def __init__(self, path, hz):
        #data = su.SensPlace(path, hz)
        data = su.SensCal(path, hz)
        sens1 = data.lfdataset
        sens2 = data.hipdataset
        sens3 = data.rfdataset
        self.status = ''
        
        self.status = ac.test_errors(sens1, sens2, sens3, data.hz) #test for convergence of quaternions    
        
        #order is important!
        hip_id = ident_hip(sens1.gX, sens2.gX, sens3.gX)
        self.sensorPlacement = [0, data.prefix[hip_id], 0]
        
        if hip_id == 0:
            hips = sens1
            foot1 = sens2
            foot2 = sens3
            ft_rel = {0:1, 1:2}
        elif hip_id == 1:
            hips = sens2
            foot1 = sens1
            foot2 = sens3
            ft_rel = {0:0, 1:2}
        elif hip_id == 2:
            hips = sens3
            foot1 = sens1
            foot2 = sens2
            ft_rel = {0:0, 1:1}
        
        #find anatomically neutral orientation for each sensor and decide if any movement errors
        foot1.s_q, foot1.orient = ac.init_orientation(foot1, .03)
        hips.s_q, hips.orient = ac.init_orientation(hips, .6)
        foot2.s_q, foot2.orient = ac.init_orientation(foot2, .03)     
        print(prep.Calc_Euler(foot1.s_q), prep.Calc_Euler(hips.s_q), prep.Calc_Euler(foot2.s_q))
        
        self.status = status_checks(hips, foot1, foot2)
        print(self.status)
        
        bodyframe = np.zeros((1,4))
        for i in range(len(hips.gX)):
            gyro = np.matrix([0, hips.gX[i], hips.gY[i], hips.gZ[i]]) #get gyr quaternion
            q = np.matrix([hips.qW[i], hips.qX[i], hips.qY[i], hips.qZ[i]]) #get orientation quaternion
            yaw_fix = prep.yaw_offset(q) #uses yaw offset function above to compute yaw offset quaternion
            yfix_c = prep.QuatConj(yaw_fix) #offset the yaw at every point
            qf = prep.QuatProd(yfix_c, q) #create new orient quat with yaw offset
            yaw = prep.Calc_Euler(q)[2] #calculate yaw of original orientation quaternion to track heading
            obody = np.append(prep.rotate_quatdata(gyro,qf),yaw)

            bodyframe = np.vstack([bodyframe, obody])
            if i == 0:
                bodyframe = np.delete(bodyframe, 0, axis=0)
                
        hglob = do.AnatomicalFrame(bodyframe)
        hfx_q = ac.hip_orientation_fix(hglob, prep.Calc_Euler(hips.s_q)[2], hz) #find degree offset of hip sensor from forward
        self.status = ac.hipCenter(hfx_q)
        fixed_h = prep.QuatProd(prep.QuatConj(hfx_q), hips.s_q)        
        
        forward = prep.Calc_Euler(hips.s_q)[2]-prep.Calc_Euler(hfx_q)[2]
        rft_id = ident_feet(foot1.s_q, foot2.s_q, forward)
        self.sensorPlacement[2] = data.prefix[ft_rel[rft_id]]
        self.sensorPlacement[0] = [x for x in data.prefix if x not in self.sensorPlacement][0]
        
        if rft_id == 0:
            rfoot = foot1
            lfoot = foot2
        else:
            rfoot = foot2
            lfoot = foot1
        
        if prep.Calc_Euler(rfoot.s_q)[1] < 0:
            self.status = "failure2"
        if prep.Calc_Euler(lfoot.s_q)[1] > 0:
            self.status = "failure3"
            
        #find pitch offset of anatomically neutral position of each sensor
        self.pitch_alignl_q = ac.pitch_offset(lfoot.s_q)
        self.pitch_alignr_q = ac.pitch_offset(rfoot.s_q)
        self.pitch_alignh_q = ac.pitch_offset(hips.s_q)
        
        #find feet offset to true forward attributes
        self.yaw_alignl_q = ac.orient_feet(lfoot.s_q, fixed_h)
        self.yaw_alignr_q = ac.orient_feet(rfoot.s_q, fixed_h)
        self.yaw_alignh_q = hfx_q
        
        print(prep.Calc_Euler(self.yaw_alignl_q), prep.Calc_Euler(self.yaw_alignr_q), prep.Calc_Euler(self.yaw_alignh_q))
        print(prep.Calc_Euler(self.pitch_alignl_q), prep.Calc_Euler(self.pitch_alignr_q), prep.Calc_Euler(self.pitch_alignh_q))
        print(self.sensorPlacement, self.status)
        
        
        
        
        
        
        
        