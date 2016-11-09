# -*- coding: utf-8 -*-
"""
Created on Thu Oct 13 08:13:38 2016

@author: court
"""

import numpy as np

""""
Calculate Movement Attributes and Performance Variables.
    Performance Variables:
        total acceleration
    Movement Attributes:
        [plane]
            -horizontal
            -lateral
            -vertical
            -rotational
            -stationary
        [stance]
            -feet eliminated
            -double leg
            -single leg
                -stationary
                -dynamic
                
"""

def total_accel(hip_acc_aif):
    
    """
    Take magnitude of acceleration at each point in time.
    
    Arg:
        hip_acc_aif: hip acceleration in the adjusted inertial frame 
        (post-coordinate frame transform) for all times in recording
    Return:
        Column of the magnitude of total acceleration for each point in time
    
    """
    
    accel_mag=np.empty((len(hip_acc_aif),1))
    accel_mag = np.sqrt(hip_acc_aif[:,0]**2+hip_acc_aif[:,1]**2 \
                        +hip_acc_aif[:,2]**2)
    
#     # instantaneous calculation
#    for i in range(len(hip_acc_aif)):
#        AccelMag[i]=np.sqrt(hip_acc_aif[i][0]**2+hip_acc_aif[i][1]**2 \
#                            +hip_acc_aif[i][2]**2)

    return accel_mag 
    
def plane_analysis(hip_acc,hip_eul,hz):
    
    """
    Define planes in which movement is occurring at a point in time.
    
    Args:
        hip_acc: hip acceleration data after coordinate frame transformation
        hip_eul: hip orientation data after coordinate frame transformation
        hz: sampling frequency
        
    Returns:
        instantaneous values and characterizing binary values for planes of
        motion:
            lat,
            vert,
            horz,
            rot,
            lat_binary,
            vert_binary,
            horz_binary,
            rot_binary,
            stationary_binary,
            accel_mag
    
    """
    
    # create storage for variables
    lat=np.empty((len(hip_acc),1))
    vert=np.empty((len(hip_acc),1))
    horz=np.empty((len(hip_acc),1))
    _ang_vel=np.zeros_like(hip_eul)
    _ang_acc=np.zeros_like(hip_eul)
    _rot_mag=np.zeros((len(hip_eul),1))
    rot=np.empty((len(hip_eul),1))
    lat_binary=np.zeros((len(hip_acc),1))
    vert_binary=np.zeros((len(hip_acc),1))
    horz_binary=np.zeros((len(hip_acc),1))
    rot_binary=np.zeros((len(hip_acc),1))
    stationary_binary=np.zeros((len(hip_acc),1))
    
    # define 'radius' of body to relate angular acceleration to linear accel
    RADIUS=0.1524 # 6 inches conv. to meters
    
    # find magnitude of linear acceleration
    accel_mag = total_accel(hip_acc)
    
    # calculate angular velocity
    for i in range(1,len(hip_eul)):

        _ang_vel[i]=(np.array(hip_eul[i].tolist())-\
                    np.array(hip_eul[i-1].tolist()))*hz
        
    # calculate angular acceleration    
    for i in range(2,len(_ang_vel)):

        _ang_acc[i]=(np.array(_ang_vel[i].tolist())-\
                    np.array(_ang_vel[i-1].tolist()))*hz

        # calculate magnitude of angular acceleration
        _rot_mag[i]=np.sqrt(_ang_acc[i][0]**2+_ang_acc[i][1]**2+_ang_acc[i][2]**2)
 
    for i in range(len(hip_acc)):  
        
        # relate angular acceleration to tangential linear acceleration
        rot[i]=RADIUS/_rot_mag[i]
        if _rot_mag[i]==0:
            
            rot[i]=0.0
            
        else:
            pass
            
        # Characterize proportion of motion of each type
        lat[i]=np.absolute(hip_acc[i][1])/accel_mag[i]
        vert[i]=np.absolute(hip_acc[i][2])/accel_mag[i]
        horz[i]=np.absolute(hip_acc[i][0])/accel_mag[i]     
        
        # give binaries value according to instantaneous percentages of each
            # plane of motion
        if accel_mag[i]<0.75:
            stationary_binary[i]=1
        else:
            stationary_binary[i]=0
              
            if lat[i] > 0.15: 
                lat_binary[i]=1
            else:
                pass
            
            if vert[i] > 0.15:
                vert_binary[i]=1
            else:
                pass
            
            if horz[i] > 0.15:
                horz_binary[i]=1
            else:
                pass
            
            if rot[i] > 0.2:
                rot_binary[i]=1
            else:
                pass
    
    return lat,vert,horz,rot,lat_binary,vert_binary,horz_binary,rot_binary,\
            stationary_binary,accel_mag.reshape(-1,1)
    
    
def standing_or_not(hip_eul,hz):
    
    """
    
    Determine when the subject is standing or not.
    
    Args: 
        hip_eul: body frame euler angle position data at hip
        hz: sampling frequency
        
    Returns:
        2 binary lists characterizing position:
            standing
            not_standing
    
    """
    
    # create storage for variables
    standing=np.zeros((len(hip_eul),1))
    
    # define minimum window to be characterized as standing
    _standing_win=int(0.5*hz)
                        
    for i in range(_standing_win,len(hip_eul)):
        
        _stand_sum=0
        
        # use _stand_sum as counter to see where in past window of time subject 
            # has been vertical
        for k in range(_standing_win):
            
            if np.absolute(hip_eul[i-k][1])<np.pi/4:
                _stand_sum=_stand_sum+1
               
                # subject has been vertical for duration of window, assume 
                   # standing at that time
                if _stand_sum==_standing_win:
                    standing[i]=1
                    
                    # assume that they have been standing for entire duration 
                        # of window
                    for m in range(k):
                        standing[i-m]=1
                       
                else:
                    pass
                        
            else:
                pass
    
    # define not_standing as the points in time where subject is not standing
    not_standing=[1]*len(standing)
    not_standing=np.asarray(not_standing).reshape((len(standing),1))
    not_standing=not_standing-standing
            
    return standing,not_standing
    
    
def double_or_single_leg(lf_phase,rf_phase,standing,hz): 
    
    """
    Determine when the subject is standing on a single leg vs. both legs.
    Heavily dependent on phase data.
    
    Args:
        lf_phase: left foot phase
        rf_phase: right foot phase
        standing: string of binaries where 1 indicates standing position, 0
            indicates not standing position
        hz: sampling frequency
    
    Returns:
        double_leg: string of binaries where 1 indicates standing on both legs,
            0 indicates other position
        single_leg: string of binaries where 1 indicates standing on one leg,
            0 indicates other position
        feet_eliminated: string of binaries where 1 indicates no feet on ground,
            0 indicates some contact with ground
    
    """
    
    # reshape inputs from flats to multidimensional arrays
    lf_phase = lf_phase.reshape(-1,)
    rf_phase = rf_phase.reshape(-1,)
    standing = standing.reshape(-1,)
    
    # isolate only phases for acceleration measured standing, adjusting s.t. 
        # 0=not standing, 1=lf + rf ground, 2=lf ground, 3=rf ground, 
        # 4=lf + rf air, 5 = lf impact, 6 = rf impact
    _lf_phase_iso_stand=(lf_phase+1)*standing
    _lf_phase_iso_stand=_lf_phase_iso_stand.astype(int)
    _rf_phase_iso_stand=(rf_phase+1)*standing
    _rf_phase_iso_stand=_rf_phase_iso_stand.astype(int)
    
    # create storage for variables
    double_leg=np.zeros((len(lf_phase),1))
    single_leg=np.zeros((len(lf_phase),1))
    feet_eliminated=np.zeros((len(lf_phase),1))
    
    # define window to be classified as particular stance
    _double_win=int(hz)
                        
    for i in range(_double_win,len(standing)):
        _doub_sum=0
        
        # use _stand_sum as counter to see where in past window of time subject has been standing on 2 legs
        for k in range(_double_win):
            
            if _lf_phase_iso_stand[i-k].item()==1 and _rf_phase_iso_stand[i-k].item()==1:
                _doub_sum=_doub_sum+1
               
                # subject has been double leg standing for duration of window, assume standing at that time
                if _doub_sum==_double_win:
                    double_leg[i]=1
                    
                    # assume that they have been double leg standing for entire duration of window
                    for m in range(k):
                        double_leg[i-m]=1
                       
                else:
                    pass
            
            # subject not double leg standing but has at least 1 foot on ground, so single leg standing
            elif (_lf_phase_iso_stand[i-k].item() in [2,3,5,6] or _rf_phase_iso_stand[i-k].item() in [2,3,5,6]): 
                single_leg[i]=1
                
            else:
                feet_eliminated[i]=1
         
    return double_leg,single_leg,feet_eliminated
    
    
def stationary_or_dynamic(lf_phase,rf_phase,single_leg,hz):
    
    """
    Determine when the subject is stationary or dynamic while standing on
    one leg.
    Heavily dependent on phase data.
    
    Args:
        lf_phase: left foot phase
        rf_phase: right foot phase
        single_leg: string of binaries where 1 indicates standing on a single
            leg, 0 indicates not standing position
        hz: sampling frequency
    
    Returns:
        stationary: string of binaries where 1 indicates stationary stance on 
            one leg, 0 indicates other position
        dynamic: string of binaries where 1 indicates dynamic stance on one
            leg, 0 indicates other position
    
    """
    
    # reshape inputs from flats to multidimensional arrays
    lf_phase = lf_phase.reshape(-1,)
    rf_phase = rf_phase.reshape(-1,)
    single_leg = single_leg.reshape(-1,)
    
    # isolate only phases for single leg standing, adjusting s.t. 
        # 0=not standing, 1=lf + rf ground, 2=lf ground, 3=rf ground, 
        # 4=lf + rf air, 5 = lf impact, 6 = rf impact
    _lf_phase_iso_sing=(lf_phase+1)*single_leg
    _lf_phase_iso_sing=_lf_phase_iso_sing.astype(int)
    _rf_phase_iso_sing=(rf_phase+1)*single_leg
    _rf_phase_iso_sing=_rf_phase_iso_sing.astype(int)
    
    # create storage for variables
    stationary=np.zeros((len(lf_phase),1))
    
    # define minimum window for "standing still"
    _stationary_win=int(hz)
     
    # determine what part of time spend on one leg is stationary standing
    for i in range(_stationary_win,len(lf_phase)):
        _stat_sum=0
        
        # use _stand_sum as counter to see where in past window of time subject
            # has been on one leg
        for k in range(_stationary_win):
            
            # left leg analysis
            if _lf_phase_iso_sing[i-k].item()==2:
                _stat_sum=_stat_sum+1
                
                # subject has been on one leg for duration of window, assume 
                    # standing at that time
                if _stat_sum==_stationary_win:
                    stationary[i]=1
                    
                    # assume that they have been standing for entire duration 
                        # of window
                    for m in range(k):
                        stationary[i-m]=1
                        
                else:
                    pass
            
            # right leg analysis
            elif _rf_phase_iso_sing[i-k].item()==3:
                _stat_sum=_stat_sum+1
                
                # subject has been on one leg for duration of window, assume 
                    # standing at that time
                if _stat_sum==_stationary_win:
                    stationary[i]=1
                    
                    # assume that they have been standing for entire duration 
                        # of window
                    for m in range(k):
                        stationary[i-m]=1
                        
                else:
                    pass
                
            else:
                pass
                             
    # define dynamic as one leg standing that is not stationary
    dynamic = np.ones(len(single_leg))
    dynamic=(dynamic-stationary.reshape((-1,)))*single_leg

    return stationary,dynamic.reshape(-1,1) # singleLegStat and singleLegDyn