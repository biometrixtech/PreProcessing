from datetime import datetime
from advancedStats.models.unit_block import UnitBlock
from advancedStats.models.step import Step
from advancedStats.summary_analysis import get_unit_blocks
from advancedStats.models.training_volume_metrics import LeftRightBands, LowModHighBands, SessionTrainingVolume, StanceBands


def get_session_training_volume_data(user, date):
    mongo_unit_blocks = get_unit_blocks(user, date)
    session_volume = SessionTrainingVolume()
    intensity_bands = LowModHighBands()
    grf_bands = LowModHighBands()
    stance_bands = StanceBands()
    left_right_bands = LeftRightBands()

    session_position = 0

    right_peak_grf_present = 0
    left_peak_grf_present = 0

    left_step_peak_grf_present = 0
    right_step_peak_grf_present = 0

    accumulated_grf = 0

    accumulated_grf_LF = 0
    accumulated_grf_RF = 0

    right_step_peak_grf_low_present = 0
    right_step_peak_grf_mod_present = 0
    right_step_peak_grf_high_present = 0
    left_step_peak_grf_low_present = 0
    left_step_peak_grf_mod_present = 0
    left_step_peak_grf_high_present = 0

    right_step_peak_int_low_present = 0
    right_step_peak_int_mod_present = 0
    right_step_peak_int_high_present = 0
    left_step_peak_int_low_present = 0
    left_step_peak_int_mod_present = 0
    left_step_peak_int_high_present = 0

    left_stance_single_present = 0
    left_stance_double_present = 0
    right_stance_single_present = 0
    right_stance_double_present = 0

    if len(mongo_unit_blocks) > 0:

        for ub in mongo_unit_blocks:
            if len(ub) > 0:
                active_block = str(ub.get('_id'))
                unit_bock_count = len(ub.get('unitBlocks'))

                for n in range(0, unit_bock_count):
                    ub_data = ub.get('unitBlocks')[n]
                    ub_rec = UnitBlock(ub_data, accumulated_grf)
                    time_start = ub.get('unitBlocks')[n].get('timeStart')
                    time_end = ub.get('unitBlocks')[n].get('timeEnd')
                    session_time_start = mongo_unit_blocks[0].get('timeStart')

                    try:
                        session_time_start_object = datetime.strptime(session_time_start, '%Y-%m-%d %H:%M:%S.%f')
                    except ValueError:
                        session_time_start_object = datetime.strptime(session_time_start, '%Y-%m-%d %H:%M:%S')

                    try:
                        time_start_object = datetime.strptime(time_start, '%Y-%m-%d %H:%M:%S.%f')
                    except ValueError:
                        time_start_object = datetime.strptime(time_start, '%Y-%m-%d %H:%M:%S')
                    try:
                        time_end_object = datetime.strptime(time_end, '%Y-%m-%d %H:%M:%S.%f')
                    except ValueError:
                        time_end_object = datetime.strptime(time_end, '%Y-%m-%d %H:%M:%S')

                    if ub_rec.peak_grf_lf is not None:
                        left_peak_grf_present += 1
                    if ub_rec.peak_grf_rf is not None:
                        right_peak_grf_present += 1
                    # intensity bands

                    accumulated_grf += ub_rec.total_grf

                    session_volume.accumulated_grf += ub_rec.total_grf
                    session_volume.active_time += ub_rec.duration
                    session_volume.cma += ub_rec.total_accel
                    session_volume.average_peak_acceleration += ub_rec.total_accel_avg
                    session_volume.average_total_GRF += ub_rec.total_grf_avg

                    if ub_rec.peak_grf_lf is not None:
                        session_volume.average_peak_vertical_grf_lf += ub_rec.peak_grf_lf
                    if ub_rec.peak_grf_rf is not None:
                        session_volume.average_peak_vertical_grf_rf += ub_rec.peak_grf_rf

                    lf_steps = ub_data.get('stepsLF')
                    rf_steps = ub_data.get('stepsRF')

                    intensity_bands.total_seconds += ub_rec.duration
                    intensity_bands.total_accumulated_grf += ub_rec.total_grf
                    intensity_bands.total_cma += ub_rec.total_accel
                    if ub_rec.peak_grf_lf is not None:
                        intensity_bands.total_average_peak_vGRF_lf += ub_rec.peak_grf_lf
                    if ub_rec.peak_grf_rf is not None:
                        intensity_bands.total_average_peak_vGRF_rf += ub_rec.peak_grf_rf

                    if ub_rec.total_accel_avg < 45:
                        intensity_bands.low_seconds += (time_end_object - time_start_object).seconds
                        intensity_bands.low_accumulated_grf += ub_rec.total_grf
                        intensity_bands.low_cma += ub_rec.total_accel
                        if ub_rec.peak_grf_lf is not None:
                            intensity_bands.low_average_peak_vGRF_lf += ub_rec.peak_grf_lf
                            left_step_peak_int_low_present += 1
                        if ub_rec.peak_grf_rf is not None:
                            intensity_bands.low_average_peak_vGRF_rf += ub_rec.peak_grf_rf
                            right_step_peak_int_low_present += 1
                        intensity_bands.low_gct_left += get_gct_from_steps(lf_steps, accumulated_grf_LF, "Left",
                                                                           active_block, n, session_position,
                                                                           session_time_start_object)
                        intensity_bands.low_gct_right += get_gct_from_steps(rf_steps, accumulated_grf_LF, "Right",
                                                                            active_block, n, session_position,
                                                                            session_time_start_object)

                    elif ub_rec.total_accel_avg >= 45 and ub_rec.total_accel_avg < 105:
                        intensity_bands.moderate_seconds += (time_end_object - time_start_object).seconds
                        intensity_bands.moderate_accumulated_grf += ub_rec.total_grf
                        intensity_bands.moderate_cma += ub_rec.total_accel
                        if ub_rec.peak_grf_lf is not None:
                            intensity_bands.moderate_average_peak_vGRF_lf += ub_rec.peak_grf_lf
                            left_step_peak_int_mod_present += 1
                        if ub_rec.peak_grf_rf is not None:
                            intensity_bands.moderate_average_peak_vGRF_rf += ub_rec.peak_grf_rf
                            right_step_peak_int_mod_present += 1
                        intensity_bands.moderate_gct_left += get_gct_from_steps(lf_steps, accumulated_grf_LF, "Left",
                                                                           active_block, n, session_position,
                                                                           session_time_start_object)
                        intensity_bands.moderate_gct_right += get_gct_from_steps(rf_steps, accumulated_grf_LF, "Right",
                                                                            active_block, n, session_position,
                                                                            session_time_start_object)

                    else:
                        intensity_bands.high_seconds += (time_end_object - time_start_object).seconds
                        intensity_bands.high_accumulated_grf += ub_rec.total_grf
                        intensity_bands.high_cma += ub_rec.total_accel
                        if ub_rec.peak_grf_lf is not None:
                            intensity_bands.high_average_peak_vGRF_lf += ub_rec.peak_grf_lf
                            left_step_peak_int_high_present += 1
                        if ub_rec.peak_grf_rf is not None:
                            intensity_bands.high_average_peak_vGRF_rf += ub_rec.peak_grf_rf
                            right_step_peak_int_high_present += 1
                        intensity_bands.high_gct_left += get_gct_from_steps(lf_steps, accumulated_grf_LF, "Left",
                                                                           active_block, n, session_position,
                                                                           session_time_start_object)
                        intensity_bands.high_gct_right += get_gct_from_steps(rf_steps, accumulated_grf_LF, "Right",
                                                                            active_block, n, session_position,
                                                                            session_time_start_object)

                    # grf bands

                    grf_bands.total_seconds += ub_rec.duration
                    grf_bands.total_accumulated_grf += ub_rec.total_grf
                    grf_bands.total_cma += ub_rec.total_accel
                    if ub_rec.peak_grf_lf is not None:
                        grf_bands.total_average_peak_vGRF_lf += ub_rec.peak_grf_lf
                    if ub_rec.peak_grf_rf is not None:
                        grf_bands.total_average_peak_vGRF_rf += ub_rec.peak_grf_rf

                    stance_bands.total_seconds += ub_rec.duration
                    stance_bands.total_accumulated_grf += ub_rec.total_grf
                    stance_bands.total_cma += ub_rec.total_accel

                    left_right_bands.total_seconds += ub_rec.duration
                    left_right_bands.total_accumulated_grf += ub_rec.total_grf
                    left_right_bands.total_cma += ub_rec.total_accel
                    if ub_rec.peak_grf_lf is not None:
                        left_right_bands.left_average_peak_vGRF += ub_rec.peak_grf_lf
                    if ub_rec.peak_grf_rf is not None:
                        left_right_bands.right_average_peak_vGRF += ub_rec.peak_grf_rf

                    for lf_step in lf_steps:
                        left_step = Step(lf_step, accumulated_grf_LF, 'Left', active_block, n, session_position,
                                         session_time_start_object)

                        accumulated_grf_LF += left_step.total_grf

                        if left_step.peak_grf < 2:
                            grf_bands.low_seconds += 0
                            grf_bands.low_accumulated_grf += left_step.total_grf
                            grf_bands.low_cma += left_step.total_accel
                            if left_step.peak_grf is not None:
                                grf_bands.low_average_peak_vGRF_lf += left_step.peak_grf
                                left_step_peak_grf_low_present += 1
                            grf_bands.low_gct_left += left_step.contact_duration
                        elif 2 < left_step.peak_grf <= 3:
                            grf_bands.moderate_seconds += 0
                            grf_bands.moderate_accumulated_grf += left_step.total_grf
                            grf_bands.moderate_cma += left_step.total_accel
                            if left_step.peak_grf is not None:
                                grf_bands.moderate_average_peak_vGRF_lf += left_step.peak_grf
                                left_step_peak_grf_mod_present += 1
                            grf_bands.moderate_gct_left += left_step.contact_duration
                        else:
                            grf_bands.high_seconds += 0
                            grf_bands.high_accumulated_grf += left_step.total_grf
                            grf_bands.high_cma += left_step.total_accel
                            if left_step.peak_grf is not None:
                                grf_bands.high_average_peak_vGRF_lf += left_step.peak_grf
                                left_step_peak_grf_high_present += 1
                            grf_bands.high_gct_left += left_step.contact_duration

                        if left_step.stance_calc == 4: # double
                            stance_bands.double_seconds += 0
                            stance_bands.double_accumulated_grf += left_step.total_grf
                            stance_bands.double_cma += left_step.total_accel
                            if left_step.peak_grf is not None:
                                stance_bands.double_average_peak_vGRF_lf += left_step.peak_grf
                                left_stance_double_present += 1
                            stance_bands.double_gct_left += left_step.contact_duration
                        elif left_step.stance_calc == 2: # single
                            stance_bands.single_seconds += 0
                            stance_bands.single_accumulated_grf += left_step.total_grf
                            stance_bands.single_cma += left_step.total_accel
                            if left_step.peak_grf is not None:
                                stance_bands.single_average_peak_vGRF_lf += left_step.peak_grf
                                left_stance_single_present += 1
                            stance_bands.single_gct_left += left_step.contact_duration

                        left_right_bands.left_seconds += 0
                        left_right_bands.left_accumulated_grf += left_step.total_grf
                        left_right_bands.left_cma += left_step.total_accel
                        if left_step.peak_grf is not None:
                            left_right_bands.left_average_peak_vGRF += left_step.peak_grf
                            left_peak_grf_present += 1
                        left_right_bands.left_gct += left_step.contact_duration

                        session_volume.ground_contact_time_left += left_step.contact_duration
                        intensity_bands.gct_total_left += left_step.contact_duration
                        grf_bands.gct_total_left += left_step.contact_duration
                        stance_bands.gct_total_left += left_step.contact_duration

                    for rf_step in rf_steps:
                        right_step = Step(rf_step, accumulated_grf_RF, 'Right', active_block, n, session_position,
                                          session_time_start_object)

                        accumulated_grf_RF += right_step.total_grf

                        if right_step.peak_grf < 2:
                            grf_bands.low_seconds += 0
                            grf_bands.low_accumulated_grf += right_step.total_grf
                            grf_bands.low_cma += right_step.total_accel
                            if right_step.peak_grf is not None:
                                grf_bands.low_average_peak_vGRF_rf += right_step.peak_grf
                                right_step_peak_grf_low_present += 1
                            grf_bands.low_gct_right += right_step.contact_duration
                        elif 2 < right_step.peak_grf <= 3:
                            grf_bands.moderate_seconds += 0
                            grf_bands.moderate_accumulated_grf += right_step.total_grf
                            grf_bands.moderate_cma += right_step.total_accel
                            if right_step.peak_grf is not None:
                                grf_bands.moderate_average_peak_vGRF_rf += right_step.peak_grf
                                right_step_peak_grf_mod_present += 1
                            grf_bands.moderate_gct_right += right_step.contact_duration
                        else:
                            grf_bands.high_seconds += 0
                            grf_bands.high_accumulated_grf += right_step.total_grf
                            grf_bands.high_cma += right_step.total_accel
                            if right_step.peak_grf is not None:
                                grf_bands.high_average_peak_vGRF_rf += right_step.peak_grf
                                right_step_peak_grf_high_present += 1
                            grf_bands.high_gct_right += right_step.contact_duration

                        if right_step.stance_calc == 4: # double
                            stance_bands.double_seconds += 0
                            stance_bands.double_accumulated_grf += right_step.total_grf
                            stance_bands.double_cma += right_step.total_accel
                            if right_step.peak_grf is not None:
                                stance_bands.double_average_peak_vGRF_rf += right_step.peak_grf
                                right_stance_double_present += 1
                            stance_bands.double_gct_right += right_step.contact_duration
                        elif right_step.stance_calc == 2: # single
                            stance_bands.single_seconds += 0
                            stance_bands.single_accumulated_grf += right_step.total_grf
                            stance_bands.single_cma += right_step.total_accel
                            if right_step.peak_grf is not None:
                                stance_bands.single_average_peak_vGRF_rf += right_step.peak_grf
                                right_stance_single_present += 1
                            stance_bands.single_gct_right += right_step.contact_duration

                        left_right_bands.right_seconds += 0
                        left_right_bands.right_accumulated_grf += right_step.total_grf
                        left_right_bands.right_cma += right_step.total_accel
                        if right_step.peak_grf is not None:
                            left_right_bands.right_average_peak_vGRF += right_step.peak_grf
                            right_peak_grf_present += 1
                        left_right_bands.right_gct += right_step.contact_duration

                        session_volume.ground_contact_time_right += right_step.contact_duration
                        intensity_bands.gct_total_right += right_step.contact_duration
                        grf_bands.gct_total_right += right_step.contact_duration
                        stance_bands.gct_total_right += right_step.contact_duration

                    session_position = session_position + 1

        session_volume.ground_contact_time_right = session_volume.ground_contact_time_right / 1000
        session_volume.ground_contact_time_left = session_volume.ground_contact_time_left / 1000
        # intensity_bands.gct_total_right = intensity_bands.gct_total_right / 1000
        # intensity_bands.gct_total_left = intensity_bands.gct_total_left / 1000
        # grf_bands.gct_total_right = grf_bands.gct_total_right / 1000
        # grf_bands.gct_total_left = grf_bands.gct_total_left / 1000
        # stance_bands.gct_total_right = stance_bands.gct_total_right / 1000
        # stance_bands.gct_total_left = stance_bands.gct_total_left / 1000

        if session_position > 0:

            session_volume.average_peak_vertical_grf_lf = (session_volume.average_peak_vertical_grf_lf /
                                                           float(session_position + 1))
            session_volume.average_peak_vertical_grf_rf = (session_volume.average_peak_vertical_grf_rf /
                                                           float(session_position + 1))

            session_volume.average_total_GRF = (session_volume.average_total_GRF /
                                                           float(session_position + 1))
            session_volume.average_peak_acceleration = (session_volume.average_peak_acceleration /
                                                           float(session_position + 1))

            grf_bands.total_average_peak_vGRF_lf = (grf_bands.total_average_peak_vGRF_lf /
                                                           float(session_position + 1))
            grf_bands.total_average_peak_vGRF_rf = (grf_bands.total_average_peak_vGRF_rf /
                                                           float(session_position + 1))

            intensity_bands.total_average_peak_vGRF_lf = (intensity_bands.total_average_peak_vGRF_lf /
                                                           float(session_position + 1))
            intensity_bands.total_average_peak_vGRF_rf = (intensity_bands.total_average_peak_vGRF_rf /
                                                           float(session_position + 1))

        if left_step_peak_int_high_present > 0:

            intensity_bands.high_average_peak_vGRF_lf = (intensity_bands.high_average_peak_vGRF_lf /
                                                         float(left_step_peak_int_high_present))
        if left_step_peak_int_mod_present > 0:
            intensity_bands.moderate_average_peak_vGRF_lf = (intensity_bands.moderate_average_peak_vGRF_lf /
                                                             float(left_step_peak_int_mod_present))
        if left_step_peak_int_low_present > 0:
            intensity_bands.low_average_peak_vGRF_lf = (intensity_bands.low_average_peak_vGRF_lf /
                                                         float(left_step_peak_int_low_present))

        if right_step_peak_int_high_present > 0:

            intensity_bands.high_average_peak_vGRF_rf = (intensity_bands.high_average_peak_vGRF_rf /
                                                         float(right_step_peak_int_high_present))
        if right_step_peak_int_mod_present > 0:
            intensity_bands.moderate_average_peak_vGRF_rf = (intensity_bands.moderate_average_peak_vGRF_rf /
                                                         float(right_step_peak_int_mod_present))
        if right_step_peak_int_low_present > 0:
            intensity_bands.low_average_peak_vGRF_rf = (intensity_bands.low_average_peak_vGRF_rf /
                                                         float(right_step_peak_int_low_present))

        if left_step_peak_grf_high_present > 0:

            grf_bands.high_average_peak_vGRF_lf = (grf_bands.high_average_peak_vGRF_lf /
                                                         float(left_step_peak_grf_high_present))

        if right_step_peak_grf_high_present > 0:

            grf_bands.high_average_peak_vGRF_rf = (grf_bands.high_average_peak_vGRF_rf /
                                                         float(right_step_peak_grf_high_present))

        if left_step_peak_grf_mod_present > 0:

            grf_bands.moderate_average_peak_vGRF_lf = (grf_bands.moderate_average_peak_vGRF_lf /
                                                             float(left_step_peak_grf_mod_present))

        if right_step_peak_grf_mod_present > 0:

            grf_bands.moderate_average_peak_vGRF_rf = (grf_bands.moderate_average_peak_vGRF_rf /
                                                             float(right_step_peak_grf_mod_present))

        if left_step_peak_grf_low_present > 0:
            grf_bands.low_average_peak_vGRF_lf = (grf_bands.low_average_peak_vGRF_lf /
                                                        float(left_step_peak_grf_low_present))

        if right_step_peak_grf_low_present > 0:
            grf_bands.low_average_peak_vGRF_rf = (grf_bands.low_average_peak_vGRF_rf /
                                                        float(right_step_peak_grf_low_present))

        if left_stance_single_present > 0:
            stance_bands.single_average_peak_vGRF_lf = (stance_bands.single_average_peak_vGRF_lf /
                                                        float(left_stance_single_present))

        if left_stance_double_present > 0:
            stance_bands.double_average_peak_vGRF_lf = (stance_bands.double_average_peak_vGRF_lf /
                                                        float(left_stance_double_present))

        if right_stance_single_present > 0:
            stance_bands.single_average_peak_vGRF_rf = (stance_bands.single_average_peak_vGRF_rf /
                                                        float(right_stance_single_present))

        if right_stance_double_present > 0:
            stance_bands.double_average_peak_vGRF_rf = (stance_bands.double_average_peak_vGRF_rf /
                                                        float(right_stance_double_present))

        if left_peak_grf_present > 0:
            left_right_bands.left_average_peak_vGRF = (left_right_bands.left_average_peak_vGRF /
                                                        float(left_peak_grf_present))

        if right_peak_grf_present > 0:
            left_right_bands.right_average_peak_vGRF = (left_right_bands.right_average_peak_vGRF /
                                                        float(right_peak_grf_present))

        if intensity_bands.total_seconds > 0:
            intensity_bands.low_seconds_percentage += (intensity_bands.low_seconds / intensity_bands.total_seconds) * 100
            intensity_bands.moderate_seconds_percentage += (intensity_bands.moderate_seconds / intensity_bands.total_seconds) * 100
            intensity_bands.high_seconds_percentage += (intensity_bands.high_seconds / intensity_bands.total_seconds) * 100

        if intensity_bands.total_accumulated_grf > 0:
            intensity_bands.low_accumulated_grf_percentage += (intensity_bands.low_accumulated_grf / intensity_bands.total_accumulated_grf) * 100
            intensity_bands.moderate_accumulated_grf_percentage += (intensity_bands.moderate_accumulated_grf / intensity_bands.total_accumulated_grf) * 100
            intensity_bands.high_accumulated_grf_percentage += (intensity_bands.high_accumulated_grf / intensity_bands.total_accumulated_grf) * 100

        if intensity_bands.total_cma > 0:
            intensity_bands.low_cma_percentage += (intensity_bands.low_cma / intensity_bands.total_cma) * 100
            intensity_bands.moderate_cma_percentage += (intensity_bands.moderate_cma / intensity_bands.total_cma) * 100
            intensity_bands.high_cma_percentage += (intensity_bands.high_cma / intensity_bands.total_cma) * 100

        if intensity_bands.gct_total_left > 0:
            intensity_bands.low_gct_left_percentage += (intensity_bands.low_gct_left / intensity_bands.gct_total_left) * 100
            intensity_bands.moderate_gct_left_percentage += (intensity_bands.moderate_gct_left / intensity_bands.gct_total_left) * 100
            intensity_bands.high_gct_left_percentage += (intensity_bands.high_gct_left / intensity_bands.gct_total_left) * 100

        if intensity_bands.gct_total_right > 0:
            intensity_bands.low_gct_right_percentage += (intensity_bands.low_gct_right / intensity_bands.gct_total_right) * 100
            intensity_bands.moderate_gct_right_percentage += (intensity_bands.moderate_gct_right / intensity_bands.gct_total_right) * 100
            intensity_bands.high_gct_right_percentage += (intensity_bands.high_gct_right / intensity_bands.gct_total_right) * 100

        if grf_bands.total_seconds > 0:
            grf_bands.low_seconds_percentage += (grf_bands.low_seconds / grf_bands.total_seconds) * 100
            grf_bands.moderate_seconds_percentage += ( grf_bands.moderate_seconds / grf_bands.total_seconds) * 100
            grf_bands.high_seconds_percentage += (grf_bands.high_seconds / grf_bands.total_seconds) * 100

        if grf_bands.total_accumulated_grf > 0:
            grf_bands.low_accumulated_grf_percentage += (grf_bands.low_accumulated_grf / grf_bands.total_accumulated_grf) * 100
            grf_bands.moderate_accumulated_grf_percentage += (grf_bands.moderate_accumulated_grf / grf_bands.total_accumulated_grf) * 100
            grf_bands.high_accumulated_grf_percentage += (grf_bands.high_accumulated_grf / grf_bands.total_accumulated_grf) * 100

        if grf_bands.total_cma > 0:
            grf_bands.low_cma_percentage += (grf_bands.low_cma / grf_bands.total_cma) * 100
            grf_bands.moderate_cma_percentage += (grf_bands.moderate_cma / grf_bands.total_cma) * 100
            grf_bands.high_cma_percentage += (grf_bands.high_cma / grf_bands.total_cma) * 100

        if grf_bands.gct_total_left > 0:
            grf_bands.low_gct_left_percentage += (grf_bands.low_gct_left / grf_bands.gct_total_left) * 100
            grf_bands.moderate_gct_left_percentage += (grf_bands.moderate_gct_left / grf_bands.gct_total_left) * 100
            grf_bands.high_gct_left_percentage += (grf_bands.high_gct_left / grf_bands.gct_total_left) * 100

        if grf_bands.gct_total_right > 0:
            grf_bands.low_gct_right_percentage += (grf_bands.low_gct_right / grf_bands.gct_total_right) * 100
            grf_bands.moderate_gct_right_percentage += (grf_bands.moderate_gct_right / grf_bands.gct_total_right) * 100
            grf_bands.high_gct_right_percentage += (grf_bands.high_gct_right / grf_bands.gct_total_right) * 100

        if stance_bands.total_seconds > 0:
            stance_bands.single_seconds_percentage += (stance_bands.single_seconds / stance_bands.total_seconds) * 100
            stance_bands.double_seconds_percentage += (stance_bands.double_seconds / stance_bands.total_seconds) * 100

        if stance_bands.total_accumulated_grf > 0:
            stance_bands.single_accumulated_grf_percentage += (stance_bands.single_accumulated_grf / stance_bands.total_accumulated_grf) * 100
            stance_bands.double_accumulated_grf_percentage += (stance_bands.double_accumulated_grf / stance_bands.total_accumulated_grf) * 100

        if stance_bands.total_cma > 0:
            stance_bands.single_cma_percentage += (stance_bands.single_cma / stance_bands.total_cma) * 100
            stance_bands.double_cma_percentage += (stance_bands.double_cma / stance_bands.total_cma) * 100

        if stance_bands.gct_total_left > 0:
            stance_bands.single_gct_left_percentage += (stance_bands.single_gct_left / stance_bands.gct_total_left) * 100
            stance_bands.double_gct_left_percentage += (stance_bands.double_gct_left / stance_bands.gct_total_left) * 100

        if stance_bands.gct_total_right > 0:
            stance_bands.single_gct_right_percentage += (stance_bands.single_gct_right / stance_bands.gct_total_right) * 100
            stance_bands.double_gct_right_percentage += (stance_bands.double_gct_right / stance_bands.gct_total_right) * 100

        if left_right_bands.total_seconds > 0:
            left_right_bands.left_seconds_percentage += (left_right_bands.left_seconds / left_right_bands.total_seconds) * 100
            left_right_bands.right_seconds_percentage += (left_right_bands.right_seconds / left_right_bands.total_seconds) * 100

        if left_right_bands.total_accumulated_grf > 0:
            left_right_bands.left_accumulated_grf_percentage += (left_right_bands.left_accumulated_grf / left_right_bands.total_accumulated_grf) * 100
            left_right_bands.right_accumulated_grf_percentage += (left_right_bands.right_accumulated_grf / left_right_bands.total_accumulated_grf) * 100

        if left_right_bands.total_cma > 0:
            left_right_bands.left_cma_percentage += (left_right_bands.left_cma / left_right_bands.total_cma) * 100
            left_right_bands.right_cma_percentage += (left_right_bands.right_cma / left_right_bands.total_cma) * 100

        session_volume.intensity_bands = intensity_bands
        session_volume.grf_bands = grf_bands
        session_volume.stance_bands = stance_bands
        session_volume.left_right_bands = left_right_bands

    return session_volume


def get_gct_from_steps(step_list, accumulated_grf_LF, orientation, active_block, n, session_position, session_time_start_object):

    gct = 0

    for step in step_list:
        new_step = Step(step, accumulated_grf_LF, orientation, active_block, n, session_position, session_time_start_object)
        gct += new_step.contact_duration

    return gct
