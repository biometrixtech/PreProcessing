# -*- coding: utf-8 -*-
"""
Created on Thu Jan 05 11:23:59 2017

@author: Gautam
"""

columns_calib = ['index', 'corrupt_magn', 'missing_type',
                 'epoch_time_lf', 'corrupt_magn_lf',
                 'LaX', 'LaY', 'LaZ', 'LqX', 'LqY', 'LqZ',
                 'epoch_time_h', 'corrupt_magn_h',
                 'HaX', 'HaY', 'HaZ', 'HqX', 'HqY', 'HqZ',
                 'epoch_time_rf', 'corrupt_magn_rf',
                 'RaX', 'RaY', 'RaZ', 'RqX', 'RqY', 'RqZ']

columns_session = ['epoch_time', 'corrupt_magn',
                   'epoch_time_lf', 'corrupt_magn_lf', 'missing_type_lf',
                   'LaX', 'LaY', 'LaZ', 'LqX', 'LqY', 'LqZ',
                   'epoch_time_h', 'corrupt_magn_h', 'missing_type_h',
                   'HaX', 'HaY', 'HaZ', 'HqX', 'HqY', 'HqZ',
                   'epoch_time_rf', 'corrupt_magn_rf', 'missing_type_rf',
                   'RaX', 'RaY', 'RaZ', 'RqX', 'RqY', 'RqZ']

column_session1_out = ['team_id', 'user_id', 'team_regimen_id',
                       'training_session_log_id', 'session_event_id',
                       'session_type', 'corrupt_type', 'missing_type_lf',
                       'missing_type_h', 'missing_type_rf', 'exercise_weight',
                       'obs_index', 'obs_master_index',
                       'time_stamp', 'epoch_time', 'ms_elapsed',
                       'LaX', 'LaY', 'LaZ', 'LeX', 'LeY', 'LeZ', 'LqW', 'LqX', 'LqY', 'LqZ',
                       'HaX', 'HaY', 'HaZ', 'HeX', 'HeY', 'HeZ', 'HqW', 'HqX', 'HqY', 'HqZ',
                       'RaX', 'RaY', 'RaZ', 'ReX', 'ReY', 'ReZ', 'RqW', 'RqX', 'RqY', 'RqZ',
                       'LqW_n', 'LqX_n', 'LqY_n', 'LqZ_n',
                       'HqW_n', 'HqX_n', 'HqY_n', 'HqZ_n',
                       'RqW_n', 'RqX_n', 'RqY_n', 'RqZ_n']

column_session1_to_DB = ['team_id', 'user_id', 'team_regimen_id',
                         'training_session_log_id', 'session_event_id',
                         'session_type', 'corrupt_type', 'missing_type_lf',
                         'missing_type_h', 'missing_type_rf', 'exercise_weight',
                         'obs_index', 'obs_master_index',
                         'time_stamp', 'epoch_time', 'ms_elapsed',
                         'phase_lf', 'phase_rf', 'activity_id',
                         'LaX', 'LaY', 'LaZ', 'LeX', 'LeY', 'LeZ', 'LqW', 'LqX', 'LqY', 'LqZ',
                         'HaX', 'HaY', 'HaZ', 'HeX', 'HeY', 'HeZ', 'HqW', 'HqX', 'HqY', 'HqZ',
                         'RaX', 'RaY', 'RaZ', 'ReX', 'ReY', 'ReZ', 'RqW', 'RqX', 'RqY', 'RqZ']

column_session1_to_s3 = ['team_id', 'user_id', 'session_event_id',
                         'session_type', 'exercise_weight',
                         'obs_index', 'obs_master_index', 'ms_elapsed',
                         'LaX', 'LaY', 'LaZ', 'LeX', 'LeY', 'LeZ', 'LqW', 'LqX', 'LqY', 'LqZ',
                         'HaX', 'HaY', 'HaZ', 'HeX', 'HeY', 'HeZ', 'HqW', 'HqX', 'HqY', 'HqZ',
                         'RaX', 'RaY', 'RaZ', 'ReX', 'ReY', 'ReZ', 'RqW', 'RqX', 'RqY', 'RqZ',
                         'LqW_n', 'LqX_n', 'LqY_n', 'LqZ_n',
                         'HqW_n', 'HqX_n', 'HqY_n', 'HqZ_n',
                         'RqW_n', 'RqX_n', 'RqY_n', 'RqZ_n']

column_session2_out = ['team_id', 'user_id', 'session_event_id',
                       'session_type', 'obs_index', 'obs_master_index','ms_elapsed',
                       'phase_lf', 'phase_rf', 'activity_id',
                       'mech_stress', 'total_accel',
                       'rate_force_absorption_lf', 'rate_force_absorption_rf',
                       'contra_hip_drop_lf', 'contra_hip_drop_rf',
                       'ankle_rot_lf', 'ankle_rot_rf',
                       'foot_position_lf', 'foot_position_rf',
                       'land_pattern_lf', 'land_pattern_rf', 'land_time',
                       'single_leg_stationary', 'single_leg_dynamic', 'double_leg', 'feet_eliminated',
                       'rot', 'lat', 'vert', 'horz', 'rot_binary', 'lat_binary','vert_binary', 'horz_binary', 'stationary_binary',
                       'LeX','HeX','ReX']

column_session2_to_DB = ['user_id', 'session_event_id', 'obs_index', 'obs_master_index',
                       'phase_lf', 'phase_rf', 'activity_id',
                         'rate_force_absorption_lf', 'rate_force_absorption_rf',
                         'single_leg_stationary', 'single_leg_dynamic', 'double_leg', 'feet_eliminated',
                         'rot', 'lat', 'vert', 'horz', 'rot_binary', 'lat_binary','vert_binary', 'horz_binary', 'stationary_binary']

column_session2_to_s3 = ['team_id', 'user_id', 'session_event_id',
                         'session_type', 'obs_index', 'obs_master_index',
                         'ms_elapsed',
                         'phase_lf', 'phase_rf',
                         'mech_stress', 'total_accel',
                         'contra_hip_drop_lf', 'contra_hip_drop_rf',
                         'ankle_rot_lf', 'ankle_rot_rf',
                         'foot_position_lf', 'foot_position_rf',
                         'land_pattern_lf', 'land_pattern_rf', 'land_time','LeX','HeX','ReX']

column_scoring_out = ['user_id', 'session_event_id', 'obs_index', 'obs_master_index',
                      'mech_stress', 'total_accel',
                      'contra_hip_drop_lf', 'contra_hip_drop_rf',
                      'ankle_rot_lf', 'ankle_rot_rf',
                      'foot_position_lf', 'foot_position_rf',
                      'land_pattern_lf', 'land_pattern_rf', 'land_time',
                      'const_mech_stress', 'dest_mech_stress',
                      'session_duration','session_mech_stress_elapsed',
                      'destr_multiplier',
                      'symmetry','hip_symmetry', 'ankle_symmetry',
                      'consistency', 'hip_consistency', 'ankle_consistency', 'consistency_lf', 'consistency_rf',
                      'control', 'hip_control', 'ankle_control', 'control_lf', 'control_rf']