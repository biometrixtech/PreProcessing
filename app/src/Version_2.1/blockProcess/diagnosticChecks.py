# -*- coding: utf-8 -*-
"""
Created on Tue Nov 15 15:05:52 2016

@author: court
"""
import numpy as np

class DiagnosticChecks(object):
    
    """
    Check that attributes of object meet certain criteria before being written
    to the database. Commented code included for checks for attributes not yet
    created.
    
    Arg:
        object - self.data object
        
    Returns:
        object with boolean attributes checking for NaNs in each row, checking
        that binaries are only assignned values 0 or 1, and that booleans are
        boolean type.

    Note: True indicates that all is as expected. False indicates a possible
    deviation from the expected.

    """
            
    def __init__(self):
        
        # Check for NaNs in columns to be saved in movement table
            # (will need to comment appropriately for implementation
            # in training event execution)
        self.no_nans_corrupt_type = not any(np.isnan(self.corrupt_type))
        self.no_nans_missing_type = not any(np.isnan(self.missing_type))
        self.no_nans_obs_index = not any(np.isnan(self.obs_index))
        self.no_nans_obs_master_index = not any(np.isnan(
            self.obs_master_index))
        self.no_nans_time_stamp = not any(np.isnan(self.time_stamp))
        self.no_nans_epoch_time = not any(np.isnan(self.epoch_time))
        self.no_nans_ms_elapsed = not any(np.isnan(self.ms_elapsed))
        self.no_nans_phase_lf = not any(np.isnan(self.phase_lf))
        self.no_nans_phase_rf = not any(np.isnan(self.phase_rf))
        self.no_nans_mech_stress = not any(np.isnan(self.mech_stress))
#        self.no_nans_mech_stress_lf = not any(np.isnan(self.mech_stress_lf))
#        self.no_nans_mech_stress_rf = not any(np.isnan(self.mech_stress_rf))
        self.no_nans_const_mech_stress = not any(np.isnan(
            self.const_mech_stress))
        self.no_nans_dest_mech_stress = not any(np.isnan(
            self.dest_mech_stress))
#        self.no_nans_rate_force_absorption_lf = not any(np.isnan(
#            self.rate_force_absorption_lf))
#        self.no_nans_rate_force_absorption_rf = not any(np.isnan(
#            self.rate_force_absorption_rf))
#        self.no_nans_rate_force_production_lf = not any(np.isnan(
#            self.rate_force_production_lf))
#        self.no_nans_rate_force_production_rf = not any(np.isnan(
#            self.rate_force_production_rf))
        self.no_nans_total_accel = not any(np.isnan(self.total_accel))
        self.no_nans_block_duration = not any(np.isnan(self.block_duration))
        self.no_nans_session_duration = not any(np.isnan(
            self.session_duration))
        self.no_nans_block_mech_stress_elapsed = not any(np.isnan(
            self.block_mech_stress_elapsed))
        self.no_nans_session_mech_stress_elapsed = not any(np.isnan(
            self.session_mech_stress_elapsed))
#        self.no_nans_destr_multiplier = not any(np.isnan(
#            self.destr_multiplier))
        self.no_nans_symmetry = not any(np.isnan(self.symmetry))
#        self.no_nans_knee_symmetry = not any(np.isnan(self.knee_symmetry))
        self.no_nans_hip_symmetry = not any(np.isnan(self.hip_symmetry))
        self.no_nans_ankle_symmetry = not any(np.isnan(self.ankle_symmetry))
        self.no_nans_consistency = not any(np.isnan(self.consistency))
        self.no_nans_hip_consistency = not any(np.isnan(self.hip_consistency))
#        self.no_nans_knee_consistency = not any(np.isnan(
#            self.knee_consistency))
#        self.no_nans_consistency_lk = not any(np.isnan(self.consistency_lk))
#        self.no_nans_consistency_rk = not any(np.isnan(self.consistency_rk))
        self.no_nans_ankle_consistency = not any(np.isnan(
            self.ankle_consistency))
        self.no_nans_consistency_lf = not any(np.isnan(self.consistency_lf))
        self.no_nans_consistency_rf = not any(np.isnan(self.consistency_rf))
#        self.no_nans_perc_mech_stress_lf = not any(np.isnan(
#            self.perc_mech_stress_lf))
        self.no_nans_contra_hip_drop_lf = not any(np.isnan(
            self.contra_hip_drop_lf))
        self.no_nans_contra_hip_drop_rf = not any(np.isnan(
            self.contra_hip_drop_rf))
#        self.no_nans_hip_rot = not any(np.isnan(self.hip_rot))
#        self.no_nans_pelvic_tilt = not any(np.isnan(self.pelvic_tilt))
        self.no_nans_ankle_rot_lf = not any(np.isnan(self.ankle_rot_lf))
        self.no_nans_ankle_rot_rf = not any(np.isnan(self.ankle_rot_rf))
#        self.no_nans_foot_position_lf = not any(np.isnan(
#            self.foot_position_lf))
#        self.no_nans_foot_position_rf = not any(np.isnan(
#            self.foot_position_rf))
#        self.no_nans_dorsi_flexion_lf = not any(np.isnan(
#            self.dorsi_flexion_lf))
#        self.no_nans_dorsi_flexion_rf = not any(np.isnan(
#            self.dorsi_flexion_rf))
        self.no_nans_land_pattern_lf = not any(np.isnan(self.land_pattern_lf))
        self.no_nans_land_pattern_rf = not any(np.isnan(self.land_pattern_rf))
        self.no_nans_land_time = not any(np.isnan(self.land_time))
#        self.no_nans_knee_valgus_lf = not any(np.isnan(self.knee_valgus_lf))
#        self.no_nans_knee_valgus_rf = not any(np.isnan(self.knee_valgus_rf))
#        self.no_nans_knee_disp_lf = not any(np.isnan(self.knee_disp_lf))
#        self.no_nans_knee_disp_rf = not any(np.isnan(self.knee_disp_rf))
#        self.no_nans_single_leg_random = not any(np.isnan(
#            self.single_leg_random))
#        self.no_nans_single_leg_alternating = not any(np.isnan(
#            self.single_leg_alternating))
        self.no_nans_single_leg_stationary = not any(np.isnan(
            self.single_leg_stationary))
        self.no_nans_single_leg_dynamic = not any(np.isnan(
            self.single_leg_dynamic))
        self.no_nans_double_leg = not any(np.isnan(self.double_leg))
        self.no_nans_feet_eliminated = not any(np.isnan(self.feet_eliminated))
#        self.no_nans_sidelying_left = not any(np.isnan(self.sidelying_left))
#        self.no_nans_sidelying_right = not any(np.isnan(self.sidelying_right))
#        self.no_nans_supine = not any(np.isnan(self.supine))
#        self.no_nans_prone = not any(np.isnan(self.prone))
        self.no_nans_rot = not any(np.isnan(self.rot))
        self.no_nans_lat = not any(np.isnan(self.lat))
        self.no_nans_vert = not any(np.isnan(self.vert))
        self.no_nans_horz = not any(np.isnan(self.horz))
        self.no_nans_rot_binary = not any(np.isnan(self.rot_binary))
        self.no_nans_lat_binary = not any(np.isnan(self.lat_binary))
        self.no_nans_vert_binary = not any(np.isnan(self.vert_binary))
        self.no_nans_horz_binary = not any(np.isnan(self.horz_binary))
        self.no_nans_stationary_binary = not any(np.isnan(
            self.stationary_binary))
#        self.no_nans_hip_dom = not any(np.isnan(self.hip_dom))
#        self.no_nans_knee_dom = not any(np.isnan(self.knee_dom))
        self.no_nans_LaX = not any(np.isnan(self.LaX))
        self.no_nans_LaY = not any(np.isnan(self.LaY))
        self.no_nans_LaZ = not any(np.isnan(self.LaZ))
        self.no_nans_LeX = not any(np.isnan(self.LeX))
        self.no_nans_LeY = not any(np.isnan(self.LeY))
        self.no_nans_LeZ = not any(np.isnan(self.LeZ))
        self.no_nans_LqW = not any(np.isnan(self.LqW))
        self.no_nans_LqX = not any(np.isnan(self.LqX))
        self.no_nans_LqY = not any(np.isnan(self.LqY))
        self.no_nans_LqZ = not any(np.isnan(self.LqZ))
        self.no_nans_HaX = not any(np.isnan(self.HaX))
        self.no_nans_HaY = not any(np.isnan(self.HaY))
        self.no_nans_HaZ = not any(np.isnan(self.HaZ))
        self.no_nans_HeX = not any(np.isnan(self.HeX))
        self.no_nans_HeY = not any(np.isnan(self.HeY))
        self.no_nans_HeZ = not any(np.isnan(self.HeZ))
        self.no_nans_HqW = not any(np.isnan(self.HqW))
        self.no_nans_HqX = not any(np.isnan(self.HqX))
        self.no_nans_HqY = not any(np.isnan(self.HqY))
        self.no_nans_HqZ = not any(np.isnan(self.HqZ))
        self.no_nans_RaX = not any(np.isnan(self.RaX))
        self.no_nans_RaY = not any(np.isnan(self.RaY))
        self.no_nans_RaZ = not any(np.isnan(self.RaZ))
        self.no_nans_ReX = not any(np.isnan(self.ReX))
        self.no_nans_ReY = not any(np.isnan(self.ReY))
        self.no_nans_ReZ = not any(np.isnan(self.ReZ))
        self.no_nans_RqW = not any(np.isnan(self.RqW))
        self.no_nans_RqX = not any(np.isnan(self.RqX))
        self.no_nans_RqY = not any(np.isnan(self.RqY))
        self.no_nans_RqZ = not any(np.isnan(self.RqZ))

        # check length of timestamp
        time_stamp_len = np.zeros(len(self.time_stamp))
        for i in range(len(self.time_stamp)):
            if len(str(self.time_stamp[i])) != 15: # 13 digits plus 2 brackets
                time_stamp_len[i] = 1
            else:
                pass
        if sum(time_stamp_len) != 0:
            self.time_stamp_len = False
        else:
            self.time_stamp_len = True
            
        # check for duplicate timestamps
        unique_times = np.unique(self.time_stamp)
        self.unique_time_stamps = len(self.time_stamp) == len(unique_times)

        # check for strictly increasing timestamps
        self.increasing_time = np.all(np.diff(
            self.time_stamp.reshape(-1,)) > 0)

        # check that defined binaries are actually binaries
        self.rot_bin_is_bin = all(np.in1d(self.rot_binary.reshape(-1,),
                                          [0, 1]) == True)
        self.lat_bin_is_bin = all(np.in1d(self.lat_binary.reshape(-1,),
                                          [0, 1]) == True)
        self.vert_bin_is_bin = all(np.in1d(self.vert_binary.reshape(-1,),
                                           [0, 1]) == True)
        self.horz_bin_is_bin = all(np.in1d(self.horz_binary.reshape(-1,),
                                           [0, 1]) == True)

        # check if phase values are integers [0,6)
        self.phase_lf_enum = all(np.in1d(self.phase_lf.reshape(-1,),
                                         [0, 1, 2, 3, 4, 5]) == True)
        self.phase_rf_enum = all(np.in1d(self.phase_rf.reshape(-1,),
                                         [0, 1, 2, 3, 4, 5]) == True)

        # check if all euler angles are in reasonable ranges for relevant phase
        # Isolate angles to be used in CMES

        # angles relevant for pronation
        left_pron_angs = np.in1d(self.LeX, [0, 1, 4])*self.LeX
        self.safe_left_pron_angs = ((-np.pi/2 < left_pron_angs)
            & (left_pron_angs < np.pi/2)).sum() == len(np.nonzero(
            np.in1d(self.LeX, [0, 1, 4])))
        right_pron_angs = np.in1d(self.ReX, [0, 2, 5])*self.ReX
        self.safe_right_pron_angs = ((-np.pi/2 < right_pron_angs)
            & (right_pron_angs < np.pi/2)).sum() == len(np.nonzero(
            np.in1d(self.ReX, [0, 2, 5])))

#        # angles relevant for foot position
#        left_foot_pos_angs = np.in1d(self.LeY, [1,4])*self.LeY
#        self.safe_left_foot_pos_angs = ((-np.pi/2 < left_foot_pos_angs)
#            & (left_foot_pos_angs < np.pi/2)).sum() == len(np.nonzero(
#            np.in1d(self.LeY, [1,4])))
#        right_foot_pos_angs = np.in1d(self.ReY, [2,5])*self.ReY
#        self.safe_right_foot_pos_angs = ((-np.pi/2 < right_foot_pos_angs)
#            & (right_foot_pos_angs < np.pi/2)).sum() == len(np.nonzero(
#            np.in1d(self.ReY, [2,5])))

        # angles relevant for contralateral hip drop
        left_hip_drop_angs = np.in1d(self.HeX, [1, 4])*self.HeX
        self.safe_left_hip_drop_angs = ((-np.pi/2 < left_hip_drop_angs)
            & (left_hip_drop_angs < np.pi/2)).sum() == len(np.nonzero(
            np.in1d(self.HeX, [1, 4])))
        right_hip_drop_angs = np.in1d(self.HeX, [2, 5])*self.HeX
        self.safe_right_hip_drop_angs = ((-np.pi/2 < right_hip_drop_angs)
            & (right_hip_drop_angs < np.pi/2)).sum() == len(np.nonzero(
            np.in1d(self.HeX, [2, 5])))

#        # angles relevant for lateral hip rotation
#        lat_hip_rot_angs = np.in1d(self.HeZ, [0,1,2,4,5])*self.HeZ
#        self.safe_lat_hip_rot_angs = ((-np.pi/2 < lat_hip_rot_angs)
#            & (lat_hip_rot_angs < np.pi/2)).sum() == len(np.nonzero(
#            np.in1d(self.HeZ, [0,1,2,4,5])))

        # FOR USE IN TRAINING EXECUTION
#        # check if defined boolean values are truly booleans
#        self.horz_exer_is_bool = all(isinstance(x, bool) for x in
#            self.horizontal_exerc.tolist())
#        self.lat_exer_is_bool = all(isinstance(x, bool) for x in
#            self.lateral_exerc.tolist())
#        self.vert_exer_is_bool = all(isinstance(x, bool) for x in
#            self.vertical_exerc.tolist())
#        self.rot_exer_is_bool = all(isinstance(x, bool) for x in
#            self.rotational_exerc.tolist())
#        self.stat_exer_is_bool = all(isinstance(x, bool) for x in
#            self.stationary_exerc.tolist())
#        self.dbllg_exer_is_bool = all(isinstance(x, bool) for x in
#            self.double_leg_exerc.tolist())
#        self.sngllg_exer_is_bool = all(isinstance(x, bool) for x in
#            self.single_leg_exerc.tolist())
#        self.feet_elim_exer_is_bool = all(isinstance(x, bool) for x in
#            self.feet_eliminated_exerc.tolist())