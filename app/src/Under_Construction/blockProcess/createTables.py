# -*- coding: utf-8 -*-
"""
Created on Thu Oct 20 17:32:47 2016

@author: Gautam
"""
import numpy as np

def create_movement_data(N, data):
    
    """Create a structured array to store movement data
    Args:
        N: number or rows expected
        data: data object with all the required values
    Returns:
        movement_data: empty movement data table    
    """
    
    # define attributes to be stored
    movement_data  = np.recarray((N,),
                             dtype = [('team_id','S64'),
                                      ('user_id','S64'),
                                        ('team_regimen_id','S64'),
                                        ('block_id','S64'),
                                        ('block_event_id','S64'),
                                        ('training_session_log_id','S64'),
                                        ('session_event_id','S64'),
                                        ('session_type','int'),
                                        ('exercise_id','S64'),
                                        ('obs_index','int'),
                                        ('obs_master_index','int'),
                                        ('time_stamp','S64'),
                                        ('epoch_time','int64'),
                                        ('ms_elapsed', 'int'),
                                        ('phase_l', 'int'),
                                        ('phase_r', 'int'),
                                        ('activity_id', 'int'),
                                        ('mech_stress','float'),
                                        ('const_mech_stress','float'),
                                        ('dest_mech_stress','float'),
                                        ('total_accel','float'),
                                        ('block_duration','float'),
                                        ('session_duration','float'),
                                        ('block_mech_stress_elapsed','float'),
                                        ('session_mech_stress_elapsed','float'),
                                        ('destr_multiplier','float'),
                                        ('symmetry','float'),
                                        ('hip_symmetry','float'),
                                        ('ankle_symmetry','float'),
                                        ('consistency','float'),
                                        ('hip_consistency','float'),
                                        ('ankle_consistency','float'),
                                        ('l_consistency','float'),
                                        ('r_consistency','float'),
                                        ('control','float'),
                                        ('hip_control','float'),
                                        ('ankle_control','float'),
                                        ('l_control','float'),
                                        ('r_control','float'),
                                        ('hip_drop_l','float'),
                                        ('hip_drop_r','float'),
                                        ('hip_rot','float'),
                                        ('ankle_rot_l','float'),
                                        ('ankle_rot_r','float'),
                                        ('land_pattern_l','float'),
                                        ('land_pattern_r','float'),
                                        ('land_time','float'),
                                        ('single_leg_stat','int'),
                                        ('single_leg_dyn','int'),
                                        ('double_leg','int'),
                                        ('feet_eliminated','int'),
                                        ('rot','float'),
                                        ('lat','float'),
                                        ('vert','float'),
                                        ('horz','float'),
                                        ('rot_binary','int'),
                                        ('lat_binary','int'),
                                        ('vert_binary','int'),
                                        ('horz_binary','int'),
                                        ('stationary_binary','int'),
                                        ('LaX','float'),
                                        ('LaY','float'),
                                        ('LaZ','float'),
                                        ('LeX','float'),
                                        ('LeY','float'),
                                        ('LeZ','float'),
                                        ('LqW','float'),
                                        ('LqX','float'),
                                        ('LqY','float'),
                                        ('LqZ','float'),
                                        ('HaX','float'),
                                        ('HaY','float'),
                                        ('HaZ','float'),
                                        ('HeX','float'),
                                        ('HeY','float'),
                                        ('HeZ','float'),
                                        ('HqW','float'),
                                        ('HqX','float'),
                                        ('HqY','float'),
                                        ('HqZ','float'),
                                        ('RaX','float'),
                                        ('RaY','float'),
                                        ('RaZ','float'),
                                        ('ReX','float'),
                                        ('ReY','float'),
                                        ('ReZ','float'),
                                        ('RqW','float'),
                                        ('RqX','float'),
                                        ('RqY','float'),
                                        ('RqZ','float')])
    
    # fill table with values from dataObject
    movement_data.team_id = data.team_id.reshape(-1,)
    movement_data.user_id = data.user_id.reshape(-1,)
    movement_data.team_regimen_id = data.team_regimen_id.reshape(-1,)
    movement_data.block_id = data.block_id.reshape(-1,)
    movement_data.block_event_id = data.block_event_id.reshape(-1,)
    movement_data.training_session_log_id = data.training_session_log_id.reshape(-1,)
    movement_data.session_event_id = data.session_event_id.reshape(-1,)
    movement_data.session_type = data.session_type.reshape(-1,)
    movement_data.exercise_id = data.exercise_id.reshape(-1,)
    movement_data.obs_index  = data.obs_index.reshape(-1,)
    movement_data.obs_master_index  = data.obs_master_index.reshape(-1,)
    movement_data.time_stamp = data.time_stamp.reshape(-1,) #timestamp without time zone,
    movement_data.epoch_time = data.epoch_time.reshape(-1,) #bigint,
    movement_data.ms_elapsed = data.ms_elapsed.reshape(-1,) #bigint,
    
    movement_data.phase_l = data.phase_l.reshape(-1,) #double precision,
    movement_data.phase_r = data.phase_r.reshape(-1,) #double precision,
    movement_data.activity_id = data.activity_id.reshape(-1,) #integer,
    movement_data.mech_stress = data.mech_stress.reshape(-1,) #double precision,
    movement_data.const_mech_stress = data.const_mech_stress.reshape(-1,) #double precision,
    movement_data.dest_mech_stress = data.dest_mech_stress.reshape(-1,) #double precision,
    #movement_data.rate_force_absorp_l = data. #double precision,
    #movement_data.rate_force_absorp_r = data. #double precision,
    movement_data.total_accel = data.total_accel.reshape(-1,) #double,
    movement_data.block_duration = data.block_duration.reshape(-1,) # double,
    movement_data.session_duration = data.session_duration.reshape(-1,) # double,
    movement_data.block_mech_stress_elapsed = data.block_mech_stress_elapsed.reshape(-1,) # double,
    movement_data.session_mech_stress_elapsed = data.session_mech_stress_elapsed.reshape(-1,) # double,
    movement_data.destr_multiplier = data.destr_multiplier.reshape(-1,) # double precision,
    movement_data.symmetry  = data.symmetry.reshape(-1,) # double precision,
    movement_data.hip_symmetry = data.hip_symmetry.reshape(-1,) # double precision,
    movement_data.ankle_symmetry = data.ankle_symmetry.reshape(-1,) # double precision,
    movement_data.consistency = data.consistency.reshape(-1,) # double precision,
    movement_data.hip_consistency = data.hip_consistency.reshape(-1,) # double precision,
    movement_data.ankle_consistency = data.ankle_consistency.reshape(-1,) # double precision,
    movement_data.l_consistency = data.l_consistency.reshape(-1,) # double precision,
    movement_data.r_consistency = data.r_consistency.reshape(-1,) # double precision,
    movement_data.control = data.control.reshape(-1,) # double precision,
    movement_data.hip_control = data.hip_control.reshape(-1,) # double precision,
    movement_data.ankle_control = data.ankle_control.reshape(-1,) # double precision,
    movement_data.l_control = data.l_control.reshape(-1,) # double precision,
    movement_data.r_control = data.r_control.reshape(-1,) # double precision,
    #movement_data.perc_mech_stress_l = data. # double precision,
    movement_data.hip_drop_l = data.hip_drop_l.reshape(-1,) # double precision,
    movement_data.hip_drop_r = data.hip_drop_r.reshape(-1,) # double precision,
    movement_data.hip_rot = data.hip_rot.reshape(-1,) # double precision,
    #movement_data.hip_dom = data. # integer,
    #movement_data.knee_dom = data. # integer,
    movement_data.ankle_rot_l = data.ankle_rot_l.reshape(-1,) # double precision,
    movement_data.ankle_rot_r = data.ankle_rot_r.reshape(-1,) # double precision,
    #movement_data.foot_position_l = data. # double precision,
    #movement_data.foot_position_r = data. # double precision,
    movement_data.land_pattern_l = data.land_pattern_l.reshape(-1,) # double precision,
    movement_data.land_pattern_r = data.land_pattern_r.reshape(-1,) # double precision,
    movement_data.land_time = data.land_time.reshape(-1,) # double precision,
    movement_data.single_leg_stat = data.single_leg_stat.reshape(-1,) #boolean
    movement_data.single_leg_dyn = data.single_leg_dyn.reshape(-1,) #boolean
    #movement_data.single_leg_alt = data. # integer,
    #movement_data.single_leg_rand = data. # integer,
    movement_data.double_leg = data.double_leg.reshape(-1,) # integer,
    movement_data.feet_eliminated = data.feet_eliminated.reshape(-1,) #integer,
    movement_data.rot = data.rot.reshape(-1,) # double precision,
    movement_data.lat = data.lat.reshape(-1,) # double precision,
    movement_data.vert = data.vert.reshape(-1,) # double precision,
    movement_data.horz = data.horz.reshape(-1,) # double precision,
    movement_data.rot_binary = data.rot_binary.reshape(-1,) # integer,
    movement_data.lat_binary = data.lat_binary.reshape(-1,) # integer,
    movement_data.vert_binary = data.vert_binary.reshape(-1,) # integer,
    movement_data.horz_binary = data.horz_binary.reshape(-1,) # integer,
    movement_data.LaX = data.LaX.reshape(-1,) # float
    movement_data.LaY = data.LaY.reshape(-1,) # float
    movement_data.LaZ = data.LaZ.reshape(-1,) # float
    movement_data.LeX = data.LeX.reshape(-1,) # float
    movement_data.LeY = data.LeY.reshape(-1,) # float
    movement_data.LeZ = data.LeZ.reshape(-1,) # float
    movement_data.LqW = data.LqW.reshape(-1,) # float
    movement_data.LqX = data.LqX.reshape(-1,) # float
    movement_data.LqY = data.LqY.reshape(-1,) # float
    movement_data.LqZ = data.LqZ.reshape(-1,) # float
    movement_data.HaX = data.HaX.reshape(-1,) # float
    movement_data.HaY = data.HaY.reshape(-1,) # float
    movement_data.HaZ = data.HaZ.reshape(-1,) # float
    movement_data.HeX = data.HeX.reshape(-1,) # float
    movement_data.HeY = data.HeY.reshape(-1,) # float
    movement_data.HeZ = data.HeZ.reshape(-1,) # float
    movement_data.HqW = data.HqW.reshape(-1,) # float
    movement_data.HqX = data.HqX.reshape(-1,) # float
    movement_data.HqY = data.HqY.reshape(-1,) # float
    movement_data.HqZ = data.HqZ.reshape(-1,) # float
    movement_data.RaX = data.RaX.reshape(-1,) # float
    movement_data.RaY = data.RaY.reshape(-1,) # float
    movement_data.RaZ = data.RaZ.reshape(-1,) # float
    movement_data.ReX = data.ReX.reshape(-1,) # float
    movement_data.ReY = data.ReY.reshape(-1,) # float
    movement_data.ReZ = data.ReZ.reshape(-1,) # float
    movement_data.RqW = data.RqW.reshape(-1,) # float
    movement_data.RqX = data.RqX.reshape(-1,) # float
    movement_data.RqY = data.RqY.reshape(-1,) # float
    movement_data.RqZ = data.RqZ.reshape(-1,) # float

    return movement_data
   
        
def create_sensor_data(N, data):
    
    """Create a structured array to store raw data
    Args:
        N: number or rows expected
        data: data object with the required data (before subsetting for activity id)
    Returns:
        sensor_data: empty raw sensor data table    
    """
    
    # Define attributes to be stored
    sensor_data  = np.recarray((N,),
                             dtype = [('team_id','S64'),
                                      ('user_id','S64'),
                                        ('team_regimen_id','S64'),
                                        ('block_id','S64'),
                                        ('block_event_id','S64'),
                                        ('training_session_log_id','S64'),
                                        ('session_event_id','S64'),
                                        ('session_type','int'),
                                        ('obs_index','int64'),
                                        ('obs_master_index','int64'),
                                        ('time_stamp','S64'),
                                        ('epoch_time','int64'),
                                        ('ms_elapsed', 'int'),
                                        ('phase_l', 'int'),
                                        ('phase_r', 'int'),
                                        ('activity_id', 'int'),
                                        ('LaX','float'),
                                        ('LaY','float'),
                                        ('LaZ','float'),
                                        ('LqW','float'),
                                        ('LqX','float'),
                                        ('LqY','float'),
                                        ('LqZ','float'),
                                        ('HaX','float'),
                                        ('HaY','float'),
                                        ('HaZ','float'),
                                        ('HqW','float'),
                                        ('HqX','float'),
                                        ('HqY','float'),
                                        ('HqZ','float'),
                                        ('RaX','float'),
                                        ('RaY','float'),
                                        ('RaZ','float'),
                                        ('RqW','float'),
                                        ('RqX','float'),
                                        ('RqY','float'),
                                        ('RqZ','float'),
                                        ('raw_LaX','float'),
                                        ('raw_LaY','float'),
                                        ('raw_LaZ','float'),
                                        ('raw_LqX','float'),
                                        ('raw_LqY','float'),
                                        ('raw_LqZ','float'),
                                        ('raw_HaX','float'),
                                        ('raw_HaY','float'),
                                        ('raw_HaZ','float'),
                                        ('raw_HqX','float'),
                                        ('raw_HqY','float'),
                                        ('raw_HqZ','float'),
                                        ('raw_RaX','float'),
                                        ('raw_RaY','float'),
                                        ('raw_RaZ','float'),
                                        ('raw_RqX','float'),
                                        ('raw_RqY','float'),
                                        ('raw_RqZ','float')])
                                        
    # fill table with values from dataObject
    sensor_data.team_id = data.team_id.reshape(-1,)
    sensor_data.user_id = data.user_id.reshape(-1,)
    sensor_data.team_regimen_id = data.team_regimen_id.reshape(-1,)
    sensor_data.block_id = data.block_id.reshape(-1,)
    sensor_data.block_event_id = data.block_event_id.reshape(-1,)
    sensor_data.training_session_log_id = data.training_session_log_id.reshape(-1,)
    sensor_data.session_event_id = data.session_event_id.reshape(-1,)
    sensor_data.session_type = data.session_type.reshape(-1,)
    sensor_data.exercise_id = data.exercise_id.reshape(-1,)
    sensor_data.obs_master_index  = data.obs_master_index.reshape(-1,)
    sensor_data.time_stamp = data.time_stamp.reshape(-1,)
    sensor_data.epoch_time = data.epoch_time.reshape(-1,)
    sensor_data.ms_elapsed = data.ms_elapsed.reshape(-1,)
    sensor_data.phase_l = data.phase_l.reshape(-1,)
    sensor_data.phase_r = data.phase_r.reshape(-1,)
    sensor_data.activity_id = data.activity_id.reshape(-1,)
    sensor_data.ms_elapsed = data.ms_elapsed.reshape(-1,)
    
    sensor_data.LaX = data.LaX.reshape(-1,) # float
    sensor_data.LaY = data.LaY.reshape(-1,) # float
    sensor_data.LaZ = data.LaZ.reshape(-1,) # float
    sensor_data.LqW = data.LqW.reshape(-1,) # float
    sensor_data.LqX = data.LqX.reshape(-1,) # float
    sensor_data.LqY = data.LqY.reshape(-1,) # float
    sensor_data.LqZ = data.LqZ.reshape(-1,) # float
    sensor_data.HaX = data.HaX.reshape(-1,) # float
    sensor_data.HaY = data.HaY.reshape(-1,) # float
    sensor_data.HaZ = data.HaZ.reshape(-1,) # float
    sensor_data.HqW = data.HqW.reshape(-1,) # float
    sensor_data.HqX = data.HqX.reshape(-1,) # float
    sensor_data.HqY = data.HqY.reshape(-1,) # float
    sensor_data.HqZ = data.HqZ.reshape(-1,) # float
    sensor_data.RaX = data.RaX.reshape(-1,) # float
    sensor_data.RaY = data.RaY.reshape(-1,) # float
    sensor_data.RaZ = data.RaZ.reshape(-1,) # float
    sensor_data.RqW = data.RqW.reshape(-1,) # float
    sensor_data.RqX = data.RqX.reshape(-1,) # float
    sensor_data.RqY = data.RqY.reshape(-1,) # float
    sensor_data.RqZ = data.RqZ.reshape(-1,) # float
    
    sensor_data.raw_LaX = data.raw_LaX.reshape(-1,) # float
    sensor_data.raw_LaY = data.raw_LaY.reshape(-1,) # float
    sensor_data.raw_LaZ = data.raw_LaZ.reshape(-1,) # float
    sensor_data.raw_LqX = data.raw_LqX.reshape(-1,) # float
    sensor_data.raw_LqY = data.raw_LqY.reshape(-1,) # float
    sensor_data.raw_LqZ = data.raw_LqZ.reshape(-1,) # float
    sensor_data.raw_HaX = data.raw_HaX.reshape(-1,) # float
    sensor_data.raw_HaY = data.raw_HaY.reshape(-1,) # float
    sensor_data.raw_HaZ = data.raw_HaZ.reshape(-1,) # float
    sensor_data.raw_HqX = data.raw_HqX.reshape(-1,) # float
    sensor_data.raw_HqY = data.raw_HqY.reshape(-1,) # float
    sensor_data.raw_HqZ = data.raw_HqZ.reshape(-1,) # float
    sensor_data.raw_RaX = data.raw_RaX.reshape(-1,) # float
    sensor_data.raw_RaY = data.raw_RaY.reshape(-1,) # float
    sensor_data.raw_RaZ = data.raw_RaZ.reshape(-1,) # float
    sensor_data.raw_RqX = data.raw_RqX.reshape(-1,) # float
    sensor_data.raw_RqY = data.raw_RqY.reshape(-1,) # float
    sensor_data.raw_RqZ = data.raw_RqZ.reshape(-1,) # float
                                        
    return sensor_data


def create_training_data(N, data):
    
    """Create a structured array to store training data
    Args:
        N: number or rows expected
        data: data object with all the required values
    Returns:
        training_data: empty training data table    
    """
    
    # define attributes to be stored
    training_data  = np.recarray((N,),
                             dtype = [  ('epoch_time','int64'),
                                        ('corrupt_magn','int'),
                                        ('missing_type','int'),
                                        ('exercise_id','S64'),
                                        ('failure_type','int'),
                                        ('total_accel','float'),
                                        ('rot','float'),
                                        ('lat','float'),
                                        ('vert','float'),
                                        ('horz','float'),
                                        ('rot_binary','int'),
                                        ('lat_binary','int'),
                                        ('vert_binary','int'),
                                        ('horz_binary','int'),
                                        ('stationary_binary','int'),
                                        ('single_leg','int'),
                                        ('double_leg','int'),
                                        ('feet_eliminated','int'),
                                        ('LaX','float'),
                                        ('LaY','float'),
                                        ('LaZ','float'),
                                        ('LeX','float'),
                                        ('LeY','float'),
                                        ('LeZ','float'),
                                        ('LqW','float'),
                                        ('LqX','float'),
                                        ('LqY','float'),
                                        ('LqZ','float'),
                                        ('HaX','float'),
                                        ('HaY','float'),
                                        ('HaZ','float'),
                                        ('HeX','float'),
                                        ('HeY','float'),
                                        ('HeZ','float'),
                                        ('HqW','float'),
                                        ('HqX','float'),
                                        ('HqY','float'),
                                        ('HqZ','float'),
                                        ('RaX','float'),
                                        ('RaY','float'),
                                        ('RaZ','float'),
                                        ('ReX','float'),
                                        ('ReY','float'),
                                        ('ReZ','float'),
                                        ('RqW','float'),
                                        ('RqX','float'),
                                        ('RqY','float'),
                                        ('RqZ','float')])
    
    # fill table with values from dataObject
    training_data.epoch_time = data.epoch_time.reshape(-1,)
    training_data.corrupt_magn = data.corrupt_magn.reshape(-1,)
    training_data.missing_type = data.missing_type.reshape(-1,)                                    
    training_data.exercise_id = data.exercise_id.reshape(-1,)
#    training_data.failure_type = data.failure_type.reshape(-1,) #bigint,
    training_data.total_accel = data.total_accel.reshape(-1,) # double precision
    training_data.rot = data.rot.reshape(-1,) # double precision,
    training_data.lat = data.lat.reshape(-1,) # double precision,
    training_data.vert = data.vert.reshape(-1,) # double precision,
    training_data.horz = data.horz.reshape(-1,) # double precision,
    training_data.rot_binary = data.rot_binary.reshape(-1,) # integer,
    training_data.lat_binary = data.lat_binary.reshape(-1,) # integer,
    training_data.vert_binary = data.vert_binary.reshape(-1,) # integer,
    training_data.horz_binary = data.horz_binary.reshape(-1,) # integer,
    training_data.stationary_binary = data.stationary_binary.reshape(-1,) # integer,
    training_data.single_leg = data.single_leg.reshape(-1,) # integer,
    training_data.double_leg = data.double_leg.reshape(-1,) # integer,
    training_data.feet_eliminated = data.feet_eliminated.reshape(-1,) #integer,
    training_data.LaX = data.LaX.reshape(-1,) # float
    training_data.LaY = data.LaY.reshape(-1,) # float
    training_data.LaZ = data.LaZ.reshape(-1,) # float
    training_data.LeX = data.LeX.reshape(-1,) # float
    training_data.LeY = data.LeY.reshape(-1,) # float
    training_data.LeZ = data.LeZ.reshape(-1,) # float
    training_data.LqW = data.LqW.reshape(-1,) # float
    training_data.LqX = data.LqX.reshape(-1,) # float
    training_data.LqY = data.LqY.reshape(-1,) # float
    training_data.LqZ = data.LqZ.reshape(-1,) # float
    training_data.HaX = data.HaX.reshape(-1,) # float
    training_data.HaY = data.HaY.reshape(-1,) # float
    training_data.HaZ = data.HaZ.reshape(-1,) # float
    training_data.HeX = data.HeX.reshape(-1,) # float
    training_data.HeY = data.HeY.reshape(-1,) # float
    training_data.HeZ = data.HeZ.reshape(-1,) # float
    training_data.HqW = data.HqW.reshape(-1,) # float
    training_data.HqX = data.HqX.reshape(-1,) # float
    training_data.HqY = data.HqY.reshape(-1,) # float
    training_data.HqZ = data.HqZ.reshape(-1,) # float
    training_data.RaX = data.RaX.reshape(-1,) # float
    training_data.RaY = data.RaY.reshape(-1,) # float
    training_data.RaZ = data.RaZ.reshape(-1,) # float
    training_data.ReX = data.ReX.reshape(-1,) # float
    training_data.ReY = data.ReY.reshape(-1,) # float
    training_data.ReZ = data.ReZ.reshape(-1,) # float
    training_data.RqW = data.RqW.reshape(-1,) # float
    training_data.RqX = data.RqX.reshape(-1,) # float
    training_data.RqY = data.RqY.reshape(-1,) # float
    training_data.RqZ = data.RqZ.reshape(-1,) # float
    
    return training_data