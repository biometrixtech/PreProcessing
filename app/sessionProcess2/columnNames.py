# -*- coding: utf-8 -*-
"""
Created on Thu Jan 05 11:23:59 2017

@author: Gautam
"""
incoming_from_accessory = ['epoch_time', 'corrupt', 
                           'magn_lf', 'corrupt_lf', 
                           'LaX', 'LaY', 'LaZ', 'LqX', 'LqY', 'LqZ', 'LqW', 
                           'magn_h', 'corrupt_h', 
                           'HaX', 'HaY', 'HaZ', 'HqX', 'HqY', 'HqZ', 'HqW', 
                           'magn_rf', 'corrupt_rf', 
                           'RaX', 'RaY', 'RaZ', 'RqX', 'RqY', 'RqZ', 'RqW'] 

column_session2_out = ['obs_index', 'time_stamp', 'epoch_time', 'ms_elapsed',
                       'loading_lf', 'loading_rf',
                       'phase_lf',  'phase_rf', 'impact_phase_lf', 'impact_phase_rf',
                       'grf', 'grf_lf', 'grf_rf', 'grf_bal_phase',
                       'contra_hip_drop_lf', 'contra_hip_drop_rf',
                       'ankle_rot_lf', 'ankle_rot_rf',
                       'foot_position_lf', 'foot_position_rf',
                       'land_pattern_lf', 'land_pattern_rf', 'land_time',
                       'rate_force_absorption_lf', 'rate_force_absorption_rf',
                       'rate_force_production_lf', 'rate_force_production_rf', 'total_accel',
                       'stance', 'plane', 'rot', 'lat', 'vert', 'horz',
                       'LeX', 'LeY', 'HeX', 'HeY', 'ReX', 'ReY',
                       'corrupt_lf', 'corrupt_h', 'corrupt_rf',
                       'adduc_motion_covered_lf', 'adduc_range_of_motion_lf',
                       'flex_motion_covered_lf', 'flex_range_of_motion_lf',
                       'contact_duration_lf',
                       'adduc_motion_covered_h', 'adduc_range_of_motion_h',
                       'flex_motion_covered_h', 'flex_range_of_motion_h',
                       'contact_duration_h',
                       'adduc_motion_covered_rf',
                       'adduc_range_of_motion_rf', 'flex_motion_covered_rf',
                       'flex_range_of_motion_rf', 'contact_duration_rf']

column_scoring_out = ['obs_index','time_stamp', 'epoch_time', 'ms_elapsed', 'session_duration',
                      'loading_lf', 'loading_rf', 
                      'phase_lf', 'phase_rf','impact_phase_lf', 'impact_phase_rf', 
                      'grf','grf_lf','grf_rf','const_grf','dest_grf','destr_multiplier',
                      'session_grf_elapsed',
                      'symmetry','symmetry_l','symmetry_r',
                      'hip_symmetry','hip_symmetry_l','hip_symmetry_r',
                      'ankle_symmetry','ankle_symmetry_l','ankle_symmetry_r', 
                      'consistency','hip_consistency','ankle_consistency',
                      'consistency_lf','consistency_rf', 
                      'control','hip_control','ankle_control','control_lf','control_rf', 
                      'contra_hip_drop_lf','contra_hip_drop_rf',
                      'ankle_rot_lf','ankle_rot_rf','foot_position_lf','foot_position_rf', 
                      'land_pattern_lf','land_pattern_rf','land_time', 
                      'rate_force_absorption_lf','rate_force_absorption_rf',
                      'rate_force_production_lf','rate_force_production_rf','total_accel', 
                      'stance','plane','rot','lat','vert','horz']
