# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 11:33:52 2016

@author: Gautam
"""
quer_read_mass = """select weight from users where id=%s"""

quer_create = "CREATE TEMP TABLE temp_mov AS SELECT * FROM movement LIMIT 0"

# Query to copy data over from temp table to movement table
quer_update = """UPDATE movement
    set phase_lf = temp_mov.phase_lf,
        phase_rf = temp_mov.phase_rf,
        activity_id = temp_mov.activity_id,
        lf_impact_phase = temp_mov.lf_impact_phase,
        rf_impact_phase = temp_mov.rf_impact_phase,
        rate_force_absorption_lf = temp_mov.rate_force_absorption_lf,
        rate_force_absorption_rf = temp_mov.rate_force_absorption_rf,
        single_leg_stationary = temp_mov.single_leg_stationary,
        single_leg_dynamic = temp_mov.single_leg_dynamic,
        double_leg = temp_mov.double_leg,
        feet_eliminated = temp_mov.feet_eliminated,
        rot = temp_mov.rot,
        lat = temp_mov.lat,
        vert = temp_mov.vert,
        horz = temp_mov.horz,
        rot_binary = temp_mov.rot_binary,
        lat_binary = temp_mov.lat_binary,
        vert_binary = temp_mov.vert_binary,
        horz_binary = temp_mov.horz_binary,
        stationary_binary = temp_mov.stationary_binary
    from temp_mov
    where movement.user_id = temp_mov.user_id and
          movement.session_event_id = temp_mov.session_event_id and
          movement.obs_index = temp_mov.obs_index"""

# finally drop the temp table
quer_drop = "DROP TABLE temp_mov"