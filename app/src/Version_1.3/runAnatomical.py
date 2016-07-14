# -*- coding: utf-8 -*-
"""
Created on Wed Jul 13 20:45:20 2016

@author: Brian
"""

import setUp as su
import anatomicalCalibration as ac
import coordinateFrameTransformation as prep
import dataObject as do
import numpy as np

class RunAnatomical(object):
    def __init__(self, path, hz):
        data = su.Anatomical(path, hz)
        
        #create vector that represents 90 degree heading rotation
        xy_switch = np.matrix([1,0,0,-1])/np.linalg.norm([1,0,0,-1]) 
        
        ac.test_errors(data.hipdataset, data.rfdataset, data.lfdataset, data.hz) #test for convergence of quaternions    
        
        #find anatomically neutral orientation for each sensor and decide if any movement errors    
        h_q = ac.init_orientation(data.hipdataset, .60)
        r_q = ac.init_orientation(data.rfdataset, .03)
        l_q = ac.init_orientation(data.lfdataset, .03)
        
        bodyframe = np.zeros((1,4))
        for i in range(len(data.hipdataset.gX)):
            gyro = np.matrix([0, data.hipdataset.gX[i], data.hipdataset.gY[i], data.hipdataset.gZ[i]]) #get gyr quaternion
            q = np.matrix([data.hipdataset.qW[i], data.hipdataset.qX[i], data.hipdataset.qY[i], data.hipdataset.qZ[i]]) #get orientation quaternion
            yaw_fix = prep.yaw_offset(q) #uses yaw offset function above to compute yaw offset quaternion
            yfix_c = prep.QuatConj(yaw_fix) #offset the yaw at every point
            qf = prep.QuatProd(yfix_c, q) #create new orient quat with yaw offset
            yaw = prep.Calc_Euler(q)[2] #calculate yaw of original orientation quaternion to track heading
            obody = np.append(prep.rotate_quatdata(gyro,qf),yaw)

            bodyframe = np.vstack([bodyframe, obody])
            if i == 0:
                bodyframe = np.delete(bodyframe, 0, axis=0)
        
        hglob = do.AnatomicalFrame(bodyframe)
        hfx_q = ac.hip_orientation_fix(hglob, prep.Calc_Euler(h_q)[2], hz) #find degree offset of hip sensor from forward
        fixed_h = prep.QuatProd(prep.QuatConj(xy_switch), prep.QuatProd(prep.QuatConj(hfx_q), h_q)) #correct heading of hip sensor
        
        #find pitch offset of anatomically neutral position of each sensor
        pitch_alignl_q = ac.pitch_offset(l_q)
        pitch_alignr_q = ac.pitch_offset(r_q)
        pitch_alignh_q = ac.pitch_offset(h_q)
        
        #find feet offset to true forward
        self.yaw_alignl_q = ac.orient_feet(l_q, fixed_h)
        self.yaw_alignr_q = ac.orient_feet(r_q, fixed_h)
        self.yaw_alignh_q = prep.QuatProd(xy_switch, hfx_q)
        
        #combine true forward offset and pitch offset 
        self.alignl_q = prep.QuatProd(self.yaw_alignl_q, pitch_alignl_q)
        self.alignr_q = prep.QuatProd(self.yaw_alignr_q, pitch_alignr_q)
        self.alignh_q = prep.QuatProd(self.yaw_alignh_q, pitch_alignh_q)
        
        #create neutral quaternions for CME comparison
        self.neutral_lq = prep.QuatProd(self.yaw_alignl_q, prep.QuatProd(prep.QuatConj(pitch_alignl_q),prep.QuatProd(prep.QuatConj(prep.yaw_offset(l_q)), l_q)))
        self.neutral_rq = prep.QuatProd(self.yaw_alignr_q, prep.QuatProd(prep.QuatConj(pitch_alignr_q),prep.QuatProd(prep.QuatConj(prep.yaw_offset(r_q)), r_q)))
        self.neutral_hq = prep.QuatProd(hfx_q, prep.QuatProd(prep.QuatConj(pitch_alignh_q),prep.QuatProd(prep.QuatConj(prep.yaw_offset(h_q)), h_q)))