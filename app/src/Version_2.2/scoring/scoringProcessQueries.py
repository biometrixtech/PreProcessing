# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 10:21:31 2016

@author: Gautam
Lists all the postgres queries needed for sessionProcess
"""

quer_create = "CREATE TEMP TABLE temp_mov AS SELECT * FROM movement LIMIT 0"

quer_delete = "delete from movement where session_event_id = (%s)"

# Query to copy data over from temp table to movement table
quer_update = """UPDATE movement
    set mech_stress = temp_mov.mech_stress,
        total_accel = temp_mov.total_accel,
        contra_hip_drop_lf = temp_mov.contra_hip_drop_lf,
        contra_hip_drop_rf = temp_mov.contra_hip_drop_rf,
        ankle_rot_lf = temp_mov.ankle_rot_lf,
        ankle_rot_rf = temp_mov.ankle_rot_rf,
        foot_position_lf = temp_mov.foot_position_lf,
        foot_position_rf = temp_mov.foot_position_rf,
        land_pattern_lf = temp_mov.land_pattern_lf,
        land_pattern_rf = temp_mov.land_pattern_rf,
        land_time = temp_mov.land_time,
        control = temp_mov.control,
        hip_control = temp_mov.hip_control,
        ankle_control = temp_mov.ankle_control,
        control_lf = temp_mov.control_lf,
        control_rf = temp_mov.control_rf,
        consistency = temp_mov.consistency,
        hip_consistency = temp_mov.hip_consistency,
        ankle_consistency = temp_mov.ankle_consistency,
        consistency_lf = temp_mov.consistency_lf,
        consistency_rf = temp_mov.consistency_rf,
        symmetry = temp_mov.symmetry,
        hip_symmetry = temp_mov.hip_symmetry,
        ankle_symmetry = temp_mov.ankle_symmetry,
        destr_multiplier = temp_mov.destr_multiplier,
        dest_mech_stress = temp_mov.dest_mech_stress,
        const_mech_stress = temp_mov.const_mech_stress,
        session_duration = temp_mov.session_duration,
        session_mech_stress_elapsed = temp_mov.session_mech_stress_elapsed
    from temp_mov
    where movement.user_id = temp_mov.user_id and
          movement.session_event_id = temp_mov.session_event_id and
          movement.obs_index = temp_mov.obs_index"""

# finally drop the temp table
quer_drop = "DROP TABLE temp_mov"


# read the team_id to create alternate flow for research vs regular users
quer_read_team_id = """select t.id from teams t, users u where t.id = u.team_id
        and u.id =(select user_id from session_events where sensor_data_filename = (%s))"""

# Update session_events to indicate successful completion of processing
quer_update_session_events = """update session_events
                                set session_success=True,
                                updated_at = now()
                                where id = (%s)"""
