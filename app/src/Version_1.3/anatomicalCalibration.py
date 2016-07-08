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

class MovementError(Exception):
    pass

class DataCollectionError(Exception):
    pass

class BowSpeedError(Exception):
    pass

def direct(x,y):
    #choose correct direction for prediction vector
    if abs(x) > abs(y):
        return np.sign(x)
    if abs(y) > abs(x):
        return -np.sign(y)

def eul2dcm(eul):
    #set euler angles
    x = eul[0]
    y = eul[1]
    z = eul[2]
    
    #calc euler angles with sin and cosin
    cx = np.cos(x)
    sx = np.sin(x)
    cy = np.cos(y)
    sy = np.sin(y)
    cz = np.cos(z)
    sz = np.sin(z)
    
    #make into rotation matrices
    rx = np.matrix([[1,0,0],[0,cx,-sx],[0,sx,cx]])
    ry = np.matrix([[cy,0,sy],[0,1,0],[-sy,0,cy]])
    rz = np.matrix([[cz,-sz,0],[sz,cz,0],[0,0,1]])
    
    #multiply rotation matrices together to get complete rotation matrix
    R = rz.dot(ry.dot(rx))
    return R

def dcm2q(dcm):
    T = dcm[0,0] + dcm[1,1] + dcm[2,2]
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
    
def hip_orientation_fix(hips, ref, hz):
    gyr_x = hips['gyrX'].values
    gyr_y = hips['gyrY'].values
    eul = hips['EulerZ'].values
    
    expect = []
    length = []
    for i in range(len(gyr_x)):
        actual = np.array([gyr_x[i], gyr_y[i]]) #create actual vector
        posneg = direct(gyr_x[i], gyr_y[i]) #choose direction of prediction vector
        mag = posneg*np.sqrt(actual.dot(actual.transpose())) #find magnitude of prediction vector (with direction)
        length.append(mag) #append mag
        diff = ref - eul[i] #find yaw rotation away from neutral reference
        R = np.array([[np.cos(diff), -np.sin(diff)],[np.sin(diff), np.cos(diff)]]) #create rotation matrix
        naive = np.array([mag,0]) #create naive prediction vector
        expect.append(R.dot(naive)) #create actual prediction vector and append to list of pred vectors
    
    theta = []
    ang_indic = []
    for i in range(len(gyr_x)):
        if abs(length[i]) > 10: #only care about vectors greater than 10 magnitude
            exp = expect[i] #get predicted vector
            actual = np.array([gyr_x[i], gyr_y[i]]) #get actual vector
            sign = np.sign(exp[1]*exp[0]) #determine sign of theta
            angle = np.arccos((exp.dot(actual))/(np.linalg.norm(exp)*np.linalg.norm(actual))) #find mag of theta
            theta.append(sign*angle) #combine to get theta for data point
        #keep track of which points are classified as moving and which weren't
        if abs(length[i]) > 10:
            ang_indic.append(20)
        else:
            ang_indic.append(0)
    #throw error if bow happened too fast
    if ang_indic.count(20) < hz*1.5:
        print('Bow too fast, please try again')
        raise BowSpeedError
    #throw error if bow seems to have been cut off at end
    if ang_indic[-int(hz*.1):].count(20) > 1:
        print('Bow too slow, please try again')
        raise BowSpeedError
    #take avg of theta list to get final theta vector       
    fin_theta = np.mean(theta)
    
    #create hip fix quaternion
    w = np.cos(fin_theta/2)
    if fin_theta < 0:
        z = -np.sqrt(1-w**2) #compute 4th term of offset quaternion
    else:
        z = np.sqrt(1-w**2)
    yaw_fix = np.matrix([w, 0, 0, z])
    return yaw_fix

def init_orientation(data, err_tol):
    roll_val = []
    ptch_val = []
    yaw_val = []
    indic = []
    for i in range(len(data)):
        #consider points that can be classified as not moving
        if np.sqrt(data.ix[i,'gyrX_raw']**2 + data.ix[i,'gyrY_raw']**2 + data.ix[i,'gyrZ_raw']**2) < 10:
            q = np.matrix([data.ix[i,'qW_raw'], data.ix[i,'qX_raw'], data.ix[i,'qY_raw'], data.ix[i,'qZ_raw']]) #get quaternion 
            eul = prep.Calc_Euler(q) #calculate euler angle
            #append euler angles to respective lists
            roll_val.append(eul[0])
            ptch_val.append(eul[1])
            yaw_val.append(eul[2])
        else:
            #keep track of how many points involved movement
            indic.append(0)
    #if movement time exceeds expected amount ask to stop moving
    if len(indic) > err_tol*len(data):
        print('Do not move during calibration')
        raise MovementError
    else:
        #create list of euler angle averages
        eul_avg = [np.mean(roll_val),np.mean(ptch_val),np.mean(yaw_val)]
        R = eul2dcm(eul_avg) #create rotation matrix from euler angles
        q = dcm2q(R) #create quaternion from rotation matrix
        return q

def orient_feet(foot, hip):
    #calc euler angles of neutral quaternions
    eul_ft = prep.Calc_Euler(foot)
    eul_hp = prep.Calc_Euler(hip)
    #find diff between foot and hip heading
    diff = eul_ft[2]-eul_hp[2]
    
    #convert diff in heading to quaternion for each foot
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

def test_errors(hdata, rdata, ldata, hz):
    thresh = .3
    #calculate euler angles of t=0 data point
    hq0 = np.matrix([hdata.ix[0,'qW_raw'], hdata.ix[0,'qX_raw'], hdata.ix[0,'qY_raw'], hdata.ix[0,'qZ_raw']])
    rq0 = np.matrix([rdata.ix[0,'qW_raw'], rdata.ix[0,'qX_raw'], rdata.ix[0,'qY_raw'], rdata.ix[0,'qZ_raw']])
    lq0 = np.matrix([ldata.ix[0,'qW_raw'], ldata.ix[0,'qX_raw'], ldata.ix[0,'qY_raw'], ldata.ix[0,'qZ_raw']])
    thetah = prep.Calc_Euler(hq0)
    thetar = prep.Calc_Euler(rq0)
    thetal = prep.Calc_Euler(lq0)
    
    #test for quaternion convergence
    for i in range(1,hz):
        #calc euler angles for each sensor at time=i
        hq = np.matrix([hdata.ix[i,'qW_raw'], hdata.ix[i,'qX_raw'], hdata.ix[i,'qY_raw'], hdata.ix[i,'qZ_raw']])
        rq = np.matrix([rdata.ix[i,'qW_raw'], rdata.ix[i,'qX_raw'], rdata.ix[i,'qY_raw'], rdata.ix[i,'qZ_raw']])
        lq = np.matrix([ldata.ix[i,'qW_raw'], ldata.ix[i,'qX_raw'], ldata.ix[i,'qY_raw'], ldata.ix[i,'qZ_raw']])
        hang = prep.Calc_Euler(hq)
        rang = prep.Calc_Euler(rq)
        lang = prep.Calc_Euler(lq)
        #if diff between t=0 and t=i euler angle is greater than .2 declare a convergence issue
        if abs(hang[0] - thetah[0]) > thresh or abs(hang[1]-thetah[1]) > thresh or abs(hang[2]-thetah[2]) > thresh:
            print("hip", i)
            print('Technical error, please try again')
            raise DataCollectionError
        elif abs(rang[0] - thetar[0]) > thresh or abs(rang[1]-thetar[1]) > thresh or abs(rang[2]-thetar[2]) > thresh:
            print("right", i)
            print('Technical error, please try again')
            raise DataCollectionError
        elif abs(lang[0] - thetal[0]) > thresh or abs(lang[1]-thetal[1]) > thresh or abs(lang[2]-thetal[2]) > thresh:
            print("left", i)
            print('Technical error, please try again')
            raise DataCollectionError
        else:
            pass

if __name__ == "__main__":    
    hroot = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\Alignment test\\bow8.csv'
    rroot = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\Alignment test\\rbow13.csv'
    lroot = 'C:\\Users\\Brian\\Documents\\Biometrix\\Data\\Collected Data\\Alignment test\\lbow13.csv'
    
    hz = 100
    hdata = pd.read_csv(hroot)
    rdata = pd.read_csv(rroot)
    ldata = pd.read_csv(lroot)
    #create vector that represents 90 degree heading rotation
    xy_switch = np.matrix([1,0,0,-1])/np.linalg.norm([1,0,0,-1]) 
    
    test_errors(hdata, rdata, ldata, hz) #test for convergence of quaternions    
    
    #find anatomically neutral orientation for each sensor and decide if any movement errors    
    h_q = init_orientation(hdata, .60)
    r_q = init_orientation(rdata, .03)
    l_q = init_orientation(ldata, .03)
    
    bodyframe = []
    for i in range(len(hdata)):
        gyro = np.matrix([0, hdata.ix[i,'gyrX_raw'], hdata.ix[i,'gyrY_raw'], hdata.ix[i,'gyrZ_raw']]) #get gyr quaternion
        q = np.matrix([hdata.ix[i,'qW_raw'], hdata.ix[i,'qX_raw'], hdata.ix[i,'qY_raw'], hdata.ix[i,'qZ_raw']]) #get orientation quaternion
        yaw_fix = prep.yaw_offset(q) #uses yaw offset function above to compute yaw offset quaternion
        yfix_c = prep.QuatConj(yaw_fix) #offset the yaw at every point
        qf = prep.QuatProd(yfix_c, q) #create new orient quat with yaw offset
        yaw = prep.Calc_Euler(q)[2] #calculate yaw of original orientation quaternion to track heading
        bodyframe.append(np.append(prep.rotate_quatdata(gyro,qf),yaw))
    
    hglob = pd.DataFrame(bodyframe, columns=["gyrX", "gyrY", "gyrZ", "EulerZ"]) #create dataframe of corrected gyro, and heading data
    hfx_q = hip_orientation_fix(hglob, prep.Calc_Euler(h_q)[2], hz) #find degree offset of hip sensor from forward
    fixed_h = prep.QuatProd(prep.QuatConj(xy_switch), prep.QuatProd(prep.QuatConj(hfx_q), h_q)) #correct heading of hip sensor
    
    #find pitch offset of anatomically neutral position of each sensor
    pitch_alignl_q = pitch_offset(l_q)
    pitch_alignr_q = pitch_offset(r_q)
    pitch_alignh_q = pitch_offset(h_q)
    
    #find feet offset to true forward
    yaw_alignl_q = orient_feet(l_q, fixed_h)
    yaw_alignr_q = orient_feet(r_q, fixed_h)
    yaw_alignh_q = prep.QuatProd(xy_switch, hfx_q)
    
    #combine true forward offset and pitch offset 
    alignl_q = prep.QuatProd(pitch_alignl_q, yaw_alignl_q)
    alignr_q = prep.QuatProd(pitch_alignr_q, yaw_alignr_q)
    alignh_q = prep.QuatProd(xy_switch, prep.QuatProd(pitch_alignh_q, hfx_q))
    
    #create neutral quaternions for CME comparison
    neutral_lq = prep.QuatProd(yaw_alignl_q, prep.QuatProd(prep.QuatConj(pitch_alignl_q),prep.QuatProd(prep.QuatConj(prep.yaw_offset(l_q)), l_q)))
    neutral_rq = prep.QuatProd(yaw_alignr_q, prep.QuatProd(prep.QuatConj(pitch_alignr_q),prep.QuatProd(prep.QuatConj(prep.yaw_offset(r_q)), r_q)))
    neutral_hq = prep.QuatProd(hfx_q, prep.QuatProd(prep.QuatConj(pitch_alignh_q),prep.QuatProd(prep.QuatConj(prep.yaw_offset(h_q)), h_q)))
    print('Success!')
        