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

"""
#############################################INPUT/OUTPUT#############################################################   
Inputs: filepath to anatomical calibration dataset, sampling rate
Outputs: object holding attributes for anatomical corrections on each sensor
Datasets: Return errors indicated by filename, Good file returns: self.yaw_alignh_q = [[ 0.79647758, 0, 0, 0.60466807]]
self.pitch_alignl_q = [[0.98168758, 0, -0.19049804, 0]]
######################################################################################################################
"""

class RunAnatomical(object):
    def __init__(self, path, hz):
        data = su.SensCal(path, hz)
        lfoot = data.lfdataset
        hips = data.hipdataset
        rfoot = data.rfdataset
        
        self.status = ac.test_errors(hips, rfoot, lfoot, data.hz) #test for convergence of quaternions    
        if self.status == 'success':
            #find anatomically neutral orientation for each sensor and decide if any movement errors    
            lfoot.s_q, lfoot.orient, self.status = ac.init_orientation(lfoot, .03)
            hips.s_q, hips.orient, self.status = ac.init_orientation(hips, .6)
            rfoot.s_q, rfoot.orient, self.status = ac.init_orientation(rfoot, .03)
            
            #make sure sensors are right side up and foot sensors are pointing opposite directions
            self.status = ac.status_checks(hips, lfoot, rfoot)
            if self.status == 'success':
                bodyframe = np.zeros((1,4))
                for i in range(len(data.timestamp)):
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
                hfx_q, self.status = ac.hip_orientation_fix(hglob, prep.Calc_Euler(hips.s_q)[2], hz) #find degree offset of hip sensor from forward
                if self.status == 'success':
                    self.status = ac.hipCenter(hfx_q) #check to see if hip sensor is way off center 
                    if self.status == 'success':
                        fixed_h = prep.QuatProd(prep.QuatConj(hfx_q), hips.s_q)  #correct heading of hip sensor
                        
                        forward = prep.Calc_Euler(hips.s_q)[2]-prep.Calc_Euler(hfx_q)[2] #find forward heading
                        #make sure right foot is sensor pointing closer to forward
                        self.status = ac.feetCheck(prep.Calc_Euler(rfoot.s_q)[2], prep.Calc_Euler(lfoot.s_q)[2], forward)
                        if self.status == 'success':
                            #make sure foot sensors angles the right way
                            if prep.Calc_Euler(rfoot.s_q)[1] < .1:
                                self.status = 'failure11'
                            if self.status == 'success':
                                if prep.Calc_Euler(lfoot.s_q)[1] > -.1:
                                    self.status = 'failure12'
                                if self.status == 'success':
                                    #find pitch offset of anatomically neutral position of each sensor
                                    self.pitch_alignl_q = ac.pitch_offset(lfoot.s_q)
                                    self.pitch_alignr_q = ac.pitch_offset(rfoot.s_q)
                                    self.pitch_alignh_q = ac.pitch_offset(hips.s_q)
                                    
                                    #find feet offset to true forward attributes
                                    self.yaw_alignl_q = ac.orient_feet(lfoot.s_q, fixed_h)
                                    self.yaw_alignr_q = ac.orient_feet(rfoot.s_q, fixed_h)
                                    self.yaw_alignh_q = hfx_q