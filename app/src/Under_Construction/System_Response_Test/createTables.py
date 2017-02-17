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
        movement_data: Movement table filled with correct entries.
                columns currently not calculated are assigned nan and returned
                as such
    """
    
    # define attributes to be stored
    movement_data = np.recarray((N,),
                                dtype=[
#                                ('team_id', 'S64'),
#                                       ('user_id', 'S64'),
#                                       ('team_regimen_id', 'S64'),
#                                       ('block_id', 'S64'),
#                                       ('block_event_id', 'S64'),
#                                       ('training_session_log_id', 'S64'),
#                                       ('session_event_id', 'S64'),
#                                       ('session_type', 'int'),
#                                       ('exercise_id', 'S64'),
                                       ('corrupt_type', 'int'),
                                       ('missing_type', 'int'),
#                                       ('exercise_weight', 'float'),
#                                       ('unknown1', 'float'),
#                                       ('unknown2', 'float'),
#                                       ('obs_index', 'int'),
#                                       ('obs_master_index', 'int'),
                                       ('time_stamp', 'S64'),
                                       ('epoch_time', 'int64'),
                                       ('ms_elapsed', 'int'),
                                       ('phase_lf', 'int'),
                                       ('phase_rf', 'int'),
#                                       ('activity_id', 'int'),
#                                       ('mech_stress', 'float'),
#                                       ('mech_stress_lf', 'float'),
#                                       ('mech_stress_rf', 'float'),
#                                       ('const_mech_stress', 'float'),
#                                       ('dest_mech_stress', 'float'),
#                                       ('rate_force_absorption_lf', 'float'),
#                                       ('rate_force_absorption_rf', 'float'),
#                                       ('rate_force_production_lf', 'float'),
#                                       ('rate_force_production_rf', 'float'),
                                       ('total_accel', 'float'),
#                                       ('unknown3', 'float'),
#                                       ('unknown4', 'float'),
#                                       ('unknown0', 'float'),
#                                       ('block_duration', 'float'),
#                                       ('session_duration', 'float'),
#                                       ('block_mech_stress_elapsed', 'float'),
#                                       ('session_mech_stress_elapsed', 'float'),
#                                       ('destr_multiplier', 'float'),
#                                       ('symmetry', 'float'),
#                                       ('knee_symmetry', 'float'),
#                                       ('hip_symmetry', 'float'),
#                                       ('ankle_symmetry', 'float'),
#                                       ('consistency', 'float'),
#                                       ('hip_consistency', 'float'),
#                                       ('knee_consistency', 'float'),
#                                       ('consistency_lk', 'float'),
#                                       ('consistency_rk', 'float'),
#                                       ('ankle_consistency', 'float'),
#                                       ('consistency_lf', 'float'),
#                                       ('consistency_rf', 'float'),
#                                       ('control', 'float'),
#                                       ('hip_control', 'float'),
#                                       ('ankle_control', 'float'),
#                                       ('control_lf', 'float'),
#                                       ('control_rf', 'float'),
#                                       ('unknown5', 'float'),
#                                       ('unknown6', 'float'),
#                                       ('unknown7', 'float'),
#                                       ('unknown8', 'float'),
#                                       ('unknown9', 'float'),
#                                       ('perc_mech_stress_lf', 'float'),
                                       ('contra_hip_drop_lf', 'float'),
                                       ('contra_hip_drop_rf', 'float'),
#                                       ('hip_rot', 'float'),
#                                       ('pelvic_tilt', 'float'),
                                       ('ankle_rot_lf', 'float'),
                                       ('ankle_rot_rf', 'float'),
                                       ('foot_position_lf', 'float'),
                                       ('foot_position_rf', 'float'),
                                       ('dorsi_flexion_lf', 'float'),
                                       ('dorsi_flexion_rf', 'float'),
                                       ('land_pattern_lf', 'float'),
                                       ('land_pattern_rf', 'float'),
#                                       ('land_time', 'float'),
#                                       ('knee_valgus_lf', 'float'),
#                                       ('knee_valgus_rf', 'float'),
#                                       ('knee_disp_lk', 'float'),
#                                       ('knee_disp_rk', 'float'),
#                                       ('single_leg_random', 'int'),
#                                       ('single_leg_alternating', 'int'),
                                       ('single_leg_stationary', 'int'),
                                       ('single_leg_dynamic', 'int'),
                                       ('double_leg', 'int'),
                                       ('feet_eliminated', 'int'),
#                                       ('sidelying_left', 'int'),
#                                       ('sidelying_right', 'int'),
#                                       ('supine', 'int'),
#                                       ('prone', 'int'),
                                       ('rot', 'float'),
                                       ('lat', 'float'),
                                       ('vert', 'float'),
                                       ('horz', 'float'),
                                       ('rot_binary', 'int'),
                                       ('lat_binary', 'int'),
                                       ('vert_binary', 'int'),
                                       ('horz_binary', 'int'),
                                       ('stationary_binary', 'int'),
#                                       ('hip_dom', 'int'),
#                                       ('knee_dom', 'int'),
#                                       ('unknown10', 'float'),
#                                       ('unknown11', 'float'),
                                       ('LaX', 'float'),
                                       ('LaY', 'float'),
                                       ('LaZ', 'float'),
                                       ('LeX', 'float'),
                                       ('LeY', 'float'),
                                       ('LeZ', 'float'),
                                       ('LqW', 'float'),
                                       ('LqX', 'float'),
                                       ('LqY', 'float'),
                                       ('LqZ', 'float'),
                                       ('HaX', 'float'),
                                       ('HaY', 'float'),
                                       ('HaZ', 'float'),
                                       ('HeX', 'float'),
                                       ('HeY', 'float'),
                                       ('HeZ', 'float'),
                                       ('HqW', 'float'),
                                       ('HqX', 'float'),
                                       ('HqY', 'float'),
                                       ('HqZ', 'float'),
                                       ('RaX', 'float'),
                                       ('RaY', 'float'),
                                       ('RaZ', 'float'),
                                       ('ReX', 'float'),
                                       ('ReY', 'float'),
                                       ('ReZ', 'float'),
                                       ('RqW', 'float'),
                                       ('RqX', 'float'),
                                       ('RqY', 'float'),
                                       ('RqZ', 'float'),
                                       ('LaX_neutral', 'float'),
                                       ('LaY_neutral', 'float'),
                                       ('LaZ_neutral', 'float'),
                                       ('LeX_neutral', 'float'),
                                       ('LeY_neutral', 'float'),
                                       ('LeZ_neutral', 'float'),
                                       ('LqW_neutral', 'float'),
                                       ('LqX_neutral', 'float'),
                                       ('LqY_neutral', 'float'),
                                       ('LqZ_neutral', 'float'),
                                       ('HaX_neutral', 'float'),
                                       ('HaY_neutral', 'float'),
                                       ('HaZ_neutral', 'float'),
                                       ('HeX_neutral', 'float'),
                                       ('HeY_neutral', 'float'),
                                       ('HeZ_neutral', 'float'),
                                       ('HqW_neutral', 'float'),
                                       ('HqX_neutral', 'float'),
                                       ('HqY_neutral', 'float'),
                                       ('HqZ_neutral', 'float'),
                                       ('RaX_neutral', 'float'),
                                       ('RaY_neutral', 'float'),
                                       ('RaZ_neutral', 'float'),
                                       ('ReX_neutral', 'float'),
                                       ('ReY_neutral', 'float'),
                                       ('ReZ_neutral', 'float'),
                                       ('RqW_neutral', 'float'),
                                       ('RqX_neutral', 'float'),
                                       ('RqY_neutral', 'float'),
                                       ('RqZ_neutral', 'float')])
    
    # fill table with values from dataObject
#    movement_data.team_id = data.team_id.reshape(-1,)
#    movement_data.user_id = data.user_id.reshape(-1,)
#    movement_data.team_regimen_id = data.team_regimen_id.reshape(-1,)
#    movement_data.block_id = data.block_id.reshape(-1,)
#    movement_data.block_event_id = data.block_event_id.reshape(-1,)
#    movement_data.training_session_log_id = data.training_session_log_id.reshape(-1,)
#    movement_data.session_event_id = data.session_event_id.reshape(-1,)
#    movement_data.session_type = data.session_type.reshape(-1,)
#    movement_data.exercise_id = data.exercise_id.reshape(-1,)
    movement_data.corrupt_type = data.corrupt_type.reshape(-1,)
    movement_data.missing_type = data.missing_type.reshape(-1,)
    
#    movement_data.exercise_weight = data.exercise_weight.reshape(-1,)
#    movement_data.unknown1 = data.unknown1.reshape(-1,)
#    movement_data.unknown2 = data.unknown2.reshape(-1,)
#    movement_data.exercise_weight = np.zeros(N)*np.nan
#    movement_data.unknown1 = np.zeros(N)*np.nan
#    movement_data.unknown2 = np.zeros(N)*np.nan
#    movement_data.unknown0 = np.zeros(N)*np.nan
       
#    movement_data.obs_index = data.obs_index.reshape(-1,)
#    movement_data.obs_master_index = data.obs_master_index.reshape(-1,)
    movement_data.time_stamp = data.time_stamp.reshape(-1,) #timestamp without time zone,
    movement_data.epoch_time = data.epoch_time.reshape(-1,) #bigint,
    movement_data.ms_elapsed = data.ms_elapsed.reshape(-1,) #bigint,
    movement_data.phase_lf = data.phase_lf.reshape(-1,) #double precision,
    movement_data.phase_rf = data.phase_rf.reshape(-1,) #double precision,
#    movement_data.activity_id = data.activity_id.reshape(-1,) #integer,
#    movement_data.mech_stress = data.mech_stress.reshape(-1,) #double precision,
    
#    movement_data.mech_stress_lf = data.mech_stress_lf.reshape(-1,) #double precision,
#    movement_data.mech_stress_rf = data.mech_stress_rf.reshape(-1,) #double precision,
#    movement_data.mech_stress_lf = np.zeros(N)*np.nan #double precision,
#    movement_data.mech_stress_rf = np.zeros(N)*np.nan #double precision,
#    
#    movement_data.const_mech_stress = data.const_mech_stress.reshape(-1,)
#    movement_data.dest_mech_stress = data.dest_mech_stress.reshape(-1,)
    
#    movement_data.rate_force_absorption_lf = data.rate_force_absorption_lf.reshape(-1,)
#    movement_data.rate_force_absorption_rf = data.rate_force_absorption_rf.reshape(-1,)
#    movement_data.rate_force_production_lf = data.rate_force_production_lf.reshape(-1,)
#    movement_data.rate_force_production_rf = data.rate_force_production_rf.reshape(-1,)
#    movement_data.rate_force_absorption_lf = np.zeros(N)*np.nan
#    movement_data.rate_force_absorption_rf = np.zeros(N)*np.nan
#    movement_data.rate_force_production_lf = np.zeros(N)*np.nan
#    movement_data.rate_force_production_rf = np.zeros(N)*np.nan
#    
    movement_data.total_accel = data.total_accel.reshape(-1,) #double,
    
#    movement_data.unknown3 = data.unknown3.reshape(-1,)
#    movement_data.unknown4 = data.unknown4.reshape(-1,)
#    movement_data.unknown3 = np.zeros(N)*np.nan #double precision,
#    movement_data.unknown4 = np.zeros(N)*np.nan #double precision,
    
#    movement_data.block_duration = data.block_duration.reshape(-1,) # double,
#    movement_data.session_duration = data.session_duration.reshape(-1,) # double,
#    movement_data.block_mech_stress_elapsed = data.block_mech_stress_elapsed.reshape(-1,)
#    movement_data.session_mech_stress_elapsed = data.session_mech_stress_elapsed.reshape(-1,)
#    movement_data.destr_multiplier = data.destr_multiplier.reshape(-1,) # double precision,
#    movement_data.symmetry = data.symmetry.reshape(-1,) # double precision,
#    movement_data.hip_symmetry = data.hip_symmetry.reshape(-1,) # double precision,

#    movement_data.knee_symmetry = data.knee_symmetry.reshape(-1,) # double precision,
#    movement_data.knee_symmetry = np.zeros(N)*np.nan # double precision,
    
#    movement_data.ankle_symmetry = data.ankle_symmetry.reshape(-1,) # double precision,
#    movement_data.consistency = data.consistency.reshape(-1,) # double precision,
#    movement_data.hip_consistency = data.hip_consistency.reshape(-1,) # double precision,
    
#    movement_data.knee_consistency = data.knee_consistency.reshape(-1,) # double precision,
#    movement_data.consistency_lk = data.consistency_lk.reshape(-1,) # double precision,
#    movement_data.consistency_rk = data.consistency_rk.reshape(-1,) # double precision,
#    movement_data.knee_consistency = np.zeros(N)*np.nan # double precision,
#    movement_data.consistency_lk = np.zeros(N)*np.nan # double precision,
#    movement_data.consistency_rk = np.zeros(N)*np.nan # double precision,
    
#    movement_data.ankle_consistency = data.ankle_consistency.reshape(-1,) # double precision,
#    movement_data.consistency_lf = data.consistency_lf.reshape(-1,) # double precision,
#    movement_data.consistency_rf = data.consistency_rf.reshape(-1,) # double precision,
#    movement_data.control = data.control.reshape(-1,) # double precision,
#    movement_data.hip_control = data.hip_control.reshape(-1,) # double precision,
#    movement_data.ankle_control = data.ankle_control.reshape(-1,) # double precision,
#    movement_data.control_lf = data.control_lf.reshape(-1,) # double precision,
#    movement_data.control_rf = data.control_rf.reshape(-1,) # double precision,

#    movement_data.unknown5 = data.unknown5.reshape(-1,)
#    movement_data.unknown6 = data.unknown6.reshape(-1,)
#    movement_data.unknown7 = data.unknown7.reshape(-1,)
#    movement_data.unknown8 = data.unknown8.reshape(-1,)
#    movement_data.unknown9 = data.unknown9.reshape(-1,)
#    movement_data.perc_mech_stress_lf = data.perc_mech_stress_lf(-1,) # double precision,
#    movement_data.unknown5 = np.zeros(N)*np.nan
#    movement_data.unknown6 = np.zeros(N)*np.nan
#    movement_data.unknown7 = np.zeros(N)*np.nan
#    movement_data.unknown8 = np.zeros(N)*np.nan
#    movement_data.unknown9 = np.zeros(N)*np.nan
#    movement_data.perc_mech_stress_lf = np.zeros(N)*np.nan # double precision,

    movement_data.contra_hip_drop_lf = data.contra_hip_drop_lf.reshape(-1,) # double precision,
    movement_data.contra_hip_drop_rf = data.contra_hip_drop_rf.reshape(-1,) # double precision,
    movement_data.hip_rot = data.hip_rot.reshape(-1,) # double precision,
    
#    movement_data.pelvic_tilt = data.pelvic_tilt.reshape(-1,) #double precision
#    movement_data.pelvic_tilt = np.zeros(N)*np.nan #double precision

    movement_data.ankle_rot_lf = data.ankle_rot_lf.reshape(-1,) # double precision,
    movement_data.ankle_rot_rf = data.ankle_rot_rf.reshape(-1,) # double precision,

#    movement_data.foot_position_lf = data.foot_position_lf.reshpae(-1,) # double precision,
#    movement_data.foot_position_rf = data.foot_position_rf.reshape(-1,) # double precision,
#    movement_data.dorsi_flexion_lf = data.dorsi_flexion_lf.reshape(-1,) # double precision,
#    movement_data.dorsi_flexion_rf = data.dorsi_flexion_rf.reshape(-1,) # double precision,
    movement_data.foot_position_lf = np.zeros(N)*np.nan # double precision,
    movement_data.foot_position_rf = np.zeros(N)*np.nan # double precision,
#    movement_data.dorsi_flexion_lf = np.zeros(N)*np.nan # double precision,
#    movement_data.dorsi_flexion_rf = np.zeros(N)*np.nan # double precision,

    movement_data.land_pattern_lf = data.land_pattern_lf.reshape(-1,) # double precision,
    movement_data.land_pattern_rf = data.land_pattern_rf.reshape(-1,) # double precision,
#    movement_data.land_time = data.land_time.reshape(-1,) # double precision,

#    movement_data.knee_valgus_lf = data.knee_valgus_lf.reshape(-1,) # double precision,
#    movement_data.knee_valgus_rf = data.knee_valgus_rf.reshape(-1,) # double precision,
#    movement_data.knee_disp_lk = data.knee_disp_lk.reshape(-1,) # double precision,
#    movement_data.knee_disp_rk = data.knee_disp_rk.reshape(-1,) # double precision,
#    movement_data.single_leg_random = data.single_leg_random.reshape(-1,) #boolean
#    movement_data.single_leg_alternating = data.single_leg_alternating.reshape(-1,) #boolean
#    movement_data.knee_valgus_lf = np.zeros(N)*np.nan # double precision,
#    movement_data.knee_valgus_rf = np.zeros(N)*np.nan # double precision,
#    movement_data.knee_disp_lk = np.zeros(N)*np.nan # double precision,
#    movement_data.knee_disp_rk = np.zeros(N)*np.nan # double precision,
#    movement_data.single_leg_random = np.zeros(N)*np.nan #boolean
#    movement_data.single_leg_alternating = np.zeros(N)*np.nan #boolean

    movement_data.single_leg_stationary = data.single_leg_stationary.reshape(-1,) #boolean
    movement_data.single_leg_dynamic = data.single_leg_dynamic.reshape(-1,) #boolean
    movement_data.double_leg = data.double_leg.reshape(-1,) # integer,
    movement_data.feet_eliminated = data.feet_eliminated.reshape(-1,) #integer,

#    movement_data.sidelying_left = data.sidelying_left.reshape(-1,) #integer,
#    movement_data.sidelying_right = data.sidelying_right.reshape(-1,) #integer,
#    movement_data.supine = data.supine.reshape(-1,) #integer,
#    movement_data.prone = data.prone.reshape(-1,) #integer,
#    movement_data.sidelying_left = np.zeros(N)*np.nan #integer,
#    movement_data.sidelying_right = np.zeros(N)*np.nan #integer,
#    movement_data.supine = np.zeros(N)*np.nan #integer,
#    movement_data.prone = np.zeros(N)*np.nan #integer,
    
    movement_data.rot = data.rot.reshape(-1,) # double precision,
    movement_data.lat = data.lat.reshape(-1,) # double precision,
    movement_data.vert = data.vert.reshape(-1,) # double precision,
    movement_data.horz = data.horz.reshape(-1,) # double precision,
    movement_data.rot_binary = data.rot_binary.reshape(-1,) # integer,
    movement_data.lat_binary = data.lat_binary.reshape(-1,) # integer,
    movement_data.vert_binary = data.vert_binary.reshape(-1,) # integer,
    movement_data.horz_binary = data.horz_binary.reshape(-1,) # integer,
    movement_data.stationary_binary = data.stationary_binary.reshape(-1,)

#    movement_data.hip_dom = data.hip_dom.reshape(-1,) # integer,
#    movement_data.knee_dom = data.knee_dom.reshape(-1,) # integer,
#    movement_data.unknown10 = data.unknown10.reshape(-1,) # integer,
#    movement_data.unknown11 = data.unknown11.reshape(-1,) # integer,
#    movement_data.hip_dom = np.zeros(N)*np.nan # integer,
#    movement_data.knee_dom = np.zeros(N)*np.nan # integer,
#    movement_data.unknown10 = np.zeros(N)*np.nan # integer,
#    movement_data.unknown11 = np.zeros(N)*np.nan # integer,

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
    
    
    
    movement_data.LqW_neutral = data.LqW_neutral.reshape(-1,) # float
    movement_data.LqX_neutral = data.LqX_neutral.reshape(-1,) # float
    movement_data.LqY_neutral = data.LqY_neutral.reshape(-1,) # float
    movement_data.LqZ_neutral = data.LqZ_neutral.reshape(-1,) # float
    
    movement_data.HqW_neutral = data.HqW_neutral.reshape(-1,) # float
    movement_data.HqX_neutral = data.HqX_neutral.reshape(-1,) # float
    movement_data.HqY_neutral = data.HqY_neutral.reshape(-1,) # float
    movement_data.HqZ_neutral = data.HqZ_neutral.reshape(-1,) # float
    
    movement_data.RqW_neutral = data.RqW_neutral.reshape(-1,) # float
    movement_data.RqX_neutral = data.RqX_neutral.reshape(-1,) # float
    movement_data.RqY_neutral = data.RqY_neutral.reshape(-1,) # float
    movement_data.RqZ_neutral = data.RqZ_neutral.reshape(-1,) # float

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
    sensor_data = np.recarray((N,),
                              dtype=[('team_id', 'S64'),
                                     ('user_id', 'S64'),
                                     ('team_regimen_id', 'S64'),
                                     ('block_id', 'S64'),
                                     ('block_event_id', 'S64'),
                                     ('training_session_log_id', 'S64'),
                                     ('session_event_id', 'S64'),
                                     ('session_type', 'int'),
                                     ('obs_index', 'int64'),
                                     ('obs_master_index', 'int64'),
                                     ('time_stamp', 'S64'),
                                     ('epoch_time', 'int64'),
                                     ('ms_elapsed', 'int'),
                                     ('phase_lf', 'int'),
                                     ('phase_rf', 'int'),
                                     ('activity_id', 'int'),
                                     ('LaX', 'float'),
                                     ('LaY', 'float'),
                                     ('LaZ', 'float'),
                                     ('LqW', 'float'),
                                     ('LqX', 'float'),
                                     ('LqY', 'float'),
                                     ('LqZ', 'float'),
                                     ('HaX', 'float'),
                                     ('HaY', 'float'),
                                     ('HaZ', 'float'),
                                     ('HqW', 'float'),
                                     ('HqX', 'float'),
                                     ('HqY', 'float'),
                                     ('HqZ', 'float'),
                                     ('RaX', 'float'),
                                     ('RaY', 'float'),
                                     ('RaZ', 'float'),
                                     ('RqW', 'float'),
                                     ('RqX', 'float'),
                                     ('RqY', 'float'),
                                     ('RqZ', 'float'),
                                     ('raw_LaX', 'float'),
                                     ('raw_LaY', 'float'),
                                     ('raw_LaZ', 'float'),
                                     ('raw_LqX', 'float'),
                                     ('raw_LqY', 'float'),
                                     ('raw_LqZ', 'float'),
                                     ('raw_HaX', 'float'),
                                     ('raw_HaY', 'float'),
                                     ('raw_HaZ', 'float'),
                                     ('raw_HqX', 'float'),
                                     ('raw_HqY', 'float'),
                                     ('raw_HqZ', 'float'),
                                     ('raw_RaX', 'float'),
                                     ('raw_RaY', 'float'),
                                     ('raw_RaZ', 'float'),
                                     ('raw_RqX', 'float'),
                                     ('raw_RqY', 'float'),
                                     ('raw_RqZ', 'float')])
                                        
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
    sensor_data.obs_master_index = data.obs_master_index.reshape(-1,)
    sensor_data.time_stamp = data.time_stamp.reshape(-1,)
    sensor_data.epoch_time = data.epoch_time.reshape(-1,)
    sensor_data.ms_elapsed = data.ms_elapsed.reshape(-1,)
    sensor_data.phase_lf = data.phase_lf.reshape(-1,)
    sensor_data.phase_rf = data.phase_rf.reshape(-1,)
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
    training_data = np.recarray((N,),
                                dtype=[('epoch_time', 'int64'),
                                       ('corrupt_magn', 'int'),
                                       ('missing_type', 'int'),
                                       ('exercise_id', 'S64'),
                                       ('failure_type', 'int'),
                                       ('total_accel', 'float'),
                                       ('rot', 'float'),
                                       ('lat', 'float'),
                                       ('vert', 'float'),
                                       ('horz', 'float'),
                                       ('rot_binary', 'int'),
                                       ('lat_binary', 'int'),
                                       ('vert_binary', 'int'),
                                       ('horz_binary', 'int'),
                                       ('stationary_binary', 'int'),
                                       ('single_leg', 'int'),
                                       ('double_leg', 'int'),
                                       ('feet_eliminated', 'int'),
                                       ('LaX', 'float'),
                                       ('LaY', 'float'),
                                       ('LaZ', 'float'),
                                       ('LeX', 'float'),
                                       ('LeY', 'float'),
                                       ('LeZ', 'float'),
                                       ('LqW', 'float'),
                                       ('LqX', 'float'),
                                       ('LqY', 'float'),
                                       ('LqZ', 'float'),
                                       ('HaX', 'float'),
                                       ('HaY', 'float'),
                                       ('HaZ', 'float'),
                                       ('HeX', 'float'),
                                       ('HeY', 'float'),
                                       ('HeZ', 'float'),
                                       ('HqW', 'float'),
                                       ('HqX', 'float'),
                                       ('HqY', 'float'),
                                       ('HqZ', 'float'),
                                       ('RaX', 'float'),
                                       ('RaY', 'float'),
                                       ('RaZ', 'float'),
                                       ('ReX', 'float'),
                                       ('ReY', 'float'),
                                       ('ReZ', 'float'),
                                       ('RqW', 'float'),
                                       ('RqX', 'float'),
                                       ('RqY', 'float'),
                                       ('RqZ', 'float')])

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