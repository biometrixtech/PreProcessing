# -*- coding: utf-8 -*-
"""
Created on Tue Jun 28 16:51:34 2016

@author: Brian
"""
import pandas as pd
import numpy as np
import coordinateFrameTransformation as prep

"""
#############################################INPUT/OUTPUT####################################################   
Inputs: raw gyro and quaternions for all three sensors collected during Anatomical Alignment method

Outputs: alignl_q, alignr_q, alignh_q ---> for sensor-body frame alignment; yaw_alignl_q, yaw_alignr_q, hfx_q
---> for adjusted inertial frame; neutral_lq, neutral_rq, neutral_hq ---> anatomic neutral for comparing 
against body frame alignment in CMEs, yaw is relative to hip sensor
#############################################################################################################
"""

def eul2dcm(eul):
    x = eul[0]
    y = eul[1]
    z = eul[2]
    
    cx = np.cos(x)
    sx = np.sin(x)
    cy = np.cos(y)
    sy = np.sin(y)
    cz = np.cos(z)
    sz = np.sin(z)
    
    #define matrices
    rx = np.matrix([[1,0,0],[0,cx,-sx],[0,sx,cx]])
    ry = np.matrix([[cy,0,sy],[0,1,0],[-sy,0,cy]])
    rz = np.matrix([[cz,-sz,0],[sz,cz,0],[0,0,1]])
    
    #create rotation matrix
    R = rz.dot(ry.dot(rx))
    return R

def dcm2q(dcm):
    #calculate trace
    T = dcm[0,0] + dcm[1,1] + dcm[2,2]
    #calculate quaternions
    if T > 10**-8:
        qw = 0.5*np.sqrt(1+T)
        qx = (dcm[2,1]-dcm[1,2])/(4*qw)
        qy = (dcm[0,2]-dcm[2,0])/(4*qw)
        qz = (dcm[1,0]-dcm[0,1])/(4*qw)
    elif (dcm[0,0] > dcm[1,1]) & (dcm[0,0] > dcm[2,2]):
        S = np.sqrt(1 + dcm[0,0] - dcm[1,1] - dcm[2,2])*2
        qw = (dcm[2,1]-dcm[1,2])/S
        qx = 0.25*S
        qy = (dcm[0,1]+dcm[1,0])/S
        qz = (dcm[0,2]+dcm[2,0])/S
    elif (dcm[1,1]>dcm[2,2]):
        S = np.sqrt(1 + dcm[1,1] - dcm[0,0] - dcm[2,2])*2
        qw = (dcm[0,2]-dcm[2,0])/S
        qx = (dcm[0,1]+dcm[1,0])/S
        qy = 0.25*S
        qz = (dcm[1,2]+dcm[2,1])/S
    else:
        S = np.sqrt(1 + dcm[2,2] - dcm[0,0] - dcm[1,1])*2
        qw = (dcm[1,0]-dcm[0,1])/S
        qx = (dcm[0,2]+dcm[2,0])/S
        qy = (dcm[1,2]+dcm[2,1])/S
        qz = 0.25*S   
    q = np.matrix([qw, qx, qy, qz])
    return q
    
def hip_orientation_fix(hips):
    #create series of gyro x and y data
    gyr_x = hips['gyrX'].values
    gyr_y = hips['gyrY'].values
    
    #create series of magnitude
    mag = np.sign(gyr_y+gyr_x)*(np.sqrt((gyr_x**2) + (gyr_y**2)))
    
    #find array of possible rotation angles for every time point
    theta = []
    for i in range(len(gyr_x)):
        #filter out times with no movement
        if abs(gyr_x[i]-gyr_y[i]) > 10:
            norm = np.array([mag[i], 0]) #expected vector
            actual = np.array([gyr_x[i], gyr_y[i]]) #actual vector
            sign = np.sign(mag[i]*gyr_y[i]) #determine sign of theta
            angle = np.arccos((norm.dot(actual))/(mag[i]**2)) #determine angle of theta
            theta.append(sign*angle)
    fin_theta = np.mean(theta) #take mean of theta array
    
    #create quaternion representing theta
    w = np.cos(fin_theta/2)
    if fin_theta < 0:
        z = -np.sqrt(1-w**2) #compute 4th term of offset quaternion
    else:
        z = np.sqrt(1-w**2)
    yaw_fix = np.matrix([w, 0, 0, z])
    return yaw_fix

def init_orientation(data):
    roll_val = []
    ptch_val = []
    yaw_val = []
    #calculate roll, pitch, yaw for each sensor and time point 
    for i in range(len(data)):
        q = np.matrix([data.ix[i,'qW_raw'], data.ix[i,'qX_raw'], data.ix[i,'qY_raw'], data.ix[i,'qZ_raw']]) 
        eul = prep.Calc_Euler(q)
        roll_val.append(eul[0])
        ptch_val.append(eul[1])
        yaw_val.append(eul[2])
    #take average of lists to find euler angle
    eul_avg = [np.mean(roll_val),np.mean(ptch_val),np.mean(yaw_val)]
    #convert to matrix
    R = eul2dcm(eul_avg)
    #convert to quaternion
    q = dcm2q(R)
    return q

def orient_feet(foot, hip):
    eul_ft = prep.Calc_Euler(foot)
    eul_hp = prep.Calc_Euler(hip)
    #find yaw difference between foot and corrected hip
    diff = eul_ft[2]-eul_hp[2]
    
    #create quaternion representing diff
    w = np.cos(diff/2)
    if diff < 0:
        z = -np.sqrt(1-w**2) #compute 4th term of offset quaternion
    else:
        z = np.sqrt(1-w**2)
    yaw_fix = np.matrix([w, 0, 0, z])
    return yaw_fix

def pitch_offset(q):
    f_dcm = prep.q2dcm(q) #call q2dcm to convert quaternion to rotation matrix
    ptch = np.arcsin(-f_dcm[2,0]) #calculate pitch of transformation using rotation matrix
    q0 = np.cos(ptch/2) #compute first term of offset quaternion
    if ptch < 0:
        q2 = -np.sqrt(1-q0**2) #compute 3rd term of offset quaternion
    else:
        q2 = np.sqrt(1-q0**2)
    yaw_fix = np.matrix([q0, 0, q2, 0]) #build pitch offset quaternion
    return yaw_fix

if __name__ == "__main__":    
    hroot = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\Alignment test\\bow13.csv'
    rroot = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\Alignment test\\rbow13.csv'
    lroot = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\Alignment test\\lbow13.csv'
    
    hdata = pd.read_csv(hroot)
    rdata = pd.read_csv(rroot)
    ldata = pd.read_csv(lroot)
    xy_switch = np.matrix([1,0,0,1])/np.linalg.norm([1,0,0,1]) #quaternion used to rotate xy plane 90 degrees    
    
    #find initial orientation
    h_q = init_orientation(hdata)
    r_q = init_orientation(rdata)
    l_q = init_orientation(ldata)
    
    #put hip data into adjusted inertial frame (with x-axis aligned with sensor not body part)
    bodyframe = []
    for i in range(len(hdata)):
        gyro = np.matrix([0, hdata.ix[i,'gyrX_raw'], hdata.ix[i,'gyrY_raw'], hdata.ix[i,'gyrZ_raw']])
        q = np.matrix([hdata.ix[i,'qW_raw'], hdata.ix[i,'qX_raw'], hdata.ix[i,'qY_raw'], hdata.ix[i,'qZ_raw']])
        yaw_fix = prep.yaw_offset(q) #uses yaw offset function above to compute yaw offset quaternion
        yfix_c = prep.QuatConj(yaw_fix)
        qf = prep.QuatProd(yfix_c, q)
        bodyframe.append(prep.rotate_quatdata(gyro,qf))
    
    hglob = pd.DataFrame(bodyframe, columns=["gyrX", "gyrY", "gyrZ"]) #df of corrected hip data
    hfx_q = hip_orientation_fix(hglob) #determine xy hip orientation
    fixed_h = prep.QuatProd(xy_switch, prep.QuatProd(hfx_q, h_q)) #align hip x-axis with true forward
    pitch_alignl_q = pitch_offset(l_q) #find pitch offset for left foot
    pitch_alignr_q = pitch_offset(r_q) #find pitch offset for left foot
    pitch_alignh_q = pitch_offset(h_q) #find pitch offset for left foot
    yaw_alignl_q = orient_feet(l_q, fixed_h) #find true forward for left foot
    yaw_alignr_q = orient_feet(r_q, fixed_h) #find true forward for right foot
    alignl_q = prep.QuatProd(pitch_alignl_q, yaw_alignl_q) #align true forward and adjust for pitch
    alignr_q = prep.QuatProd(pitch_alignr_q, yaw_alignr_q) #align true forward and adjust for pitch
    alignh_q = prep.QuatProd(pitch_alignh_q, hfx_q) #align true forward and adjust for pitch
    
    #calculate quaternions that represent anatomically "neutral" position
    neutral_lq = prep.QuatProd(yaw_alignl_q, prep.QuatProd(prep.QuatConj(pitch_alignl_q),prep.QuatProd(prep.QuatConj(prep.yaw_offset(l_q)), l_q)))
    neutral_rq = prep.QuatProd(yaw_alignr_q, prep.QuatProd(prep.QuatConj(pitch_alignr_q),prep.QuatProd(prep.QuatConj(prep.yaw_offset(r_q)), r_q)))
    neutral_hq = prep.QuatProd(hfx_q, prep.QuatProd(prep.QuatConj(pitch_alignh_q),prep.QuatProd(prep.QuatConj(prep.yaw_offset(h_q)), h_q)))
    
    
    