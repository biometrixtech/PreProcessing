from datetime import datetime
from advancedStats.models.unit_block import UnitBlock
from advancedStats.models.step import Step
from advancedStats.summary_analysis import get_unit_blocks
from advancedStats.models.training_volume_metrics import LeftRightBands, LowModHighBands, SessionTrainingVolume, StanceBands


def create_intensity_matrix(user, date):
    mongo_unit_blocks = get_unit_blocks(user, date)
    session_volume = SessionTrainingVolume()
    intensity_bands = LowModHighBands()
    grf_bands = LowModHighBands()
    stance_bands = StanceBands()
    left_right_bands = LeftRightBands()

    accumulated_grf_LF = 0
    accumulated_grf_RF = 0

    session_position = 0

    if len(mongo_unit_blocks) > 0:

        for ub in mongo_unit_blocks:
            if len(ub) > 0:
                active_block = str(ub.get('_id'))
                unit_bock_count = len(ub.get('unitBlocks'))

                for n in range(0, unit_bock_count):
                    ub_data = ub.get('unitBlocks')[n]
                    ub_rec = UnitBlock(ub_data)
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

                    # intensity bands

                    intensity_bands.total_seconds += ub_rec.duration
                    intensity_bands.total_accumulated_grf += ub_rec.accumulated_grf
                    intensity_bands.total_cma += ub_rec.total_accel
                    intensity_bands.total_accumulated_peak_vGRF += ub_rec.peak_grf_lf + ub_rec.peak_grf_rf
                    intensity_bands.total_gct += ub_rec.contact_duration_lf + ub_rec.contact_duration_rf

                    if ub_rec.total_accel_avg < 45:
                        intensity_bands.low_seconds += (time_end_object - time_start_object).seconds
                        intensity_bands.low_accumulated_grf += ub_rec.accumulated_grf
                        intensity_bands.low_cma += ub_rec.total_accel
                        intensity_bands.low_accumulated_peak_vGRF += ub_rec.peak_grf_lf + ub_rec.peak_grf_rf
                        intensity_bands.low_gct += ub_rec.contact_duration_lf + ub_rec.contact_duration_rf
                    elif ub_rec.total_accel_avg >= 45 and ub_rec.total_accel_avg < 105:
                        intensity_bands.moderate_seconds += (time_end_object - time_start_object).seconds
                        intensity_bands.moderate_accumulated_grf += ub_rec.accumulated_grf
                        intensity_bands.moderate_cma += ub_rec.total_accel
                        intensity_bands.moderate_accumulated_peak_vGRF += ub_rec.peak_grf_lf + ub_rec.peak_grf_rf
                        intensity_bands.moderate_gct += ub_rec.contact_duration_lf + ub_rec.contact_duration_rf
                    else:
                        intensity_bands.high_seconds += (time_end_object - time_start_object).seconds
                        intensity_bands.high_accumulated_grf += ub_rec.accumulated_grf
                        intensity_bands.high_cma += ub_rec.total_accel
                        intensity_bands.high_accumulated_peak_vGRF += ub_rec.peak_grf_lf + ub_rec.peak_grf_rf
                        intensity_bands.high_gct += ub_rec.contact_duration_lf + ub_rec.contact_duration_rf

                    # grf bands

                    grf_bands.total_seconds += ub_rec.duration
                    grf_bands.total_accumulated_grf += ub_rec.accumulated_grf
                    grf_bands.total_cma += ub_rec.total_accel
                    grf_bands.total_accumulated_peak_vGRF += ub_rec.peak_grf_lf + ub_rec.peak_grf_rf
                    grf_bands.total_gct += ub_rec.contact_duration_lf + ub_rec.contact_duration_rf

                    stance_bands.total_seconds += ub_rec.duration
                    stance_bands.total_accumulated_grf += ub_rec.accumulated_grf
                    stance_bands.total_cma += ub_rec.total_accel
                    stance_bands.total_accumulated_peak_vGRF += ub_rec.peak_grf_lf + ub_rec.peak_grf_rf
                    stance_bands.total_gct += ub_rec.contact_duration_lf + ub_rec.contact_duration_rf

                    left_right_bands.total_seconds += ub_rec.duration
                    left_right_bands.total_accumulated_grf += ub_rec.accumulated_grf
                    left_right_bands.total_cma += ub_rec.total_accel
                    left_right_bands.total_accumulated_peak_vGRF += ub_rec.peak_grf_lf + ub_rec.peak_grf_rf
                    left_right_bands.total_gct += ub_rec.contact_duration_lf + ub_rec.contact_duration_rf

                    lf_steps = ub_data.get('stepsLF')
                    for lf_step in lf_steps:
                        left_step = Step(lf_step, accumulated_grf_LF, 'Left', active_block, n, session_position,
                                         session_time_start_object)

                        accumulated_grf_LF += left_step.total_grf

                        if left_step.peak_grf < 2:
                            grf_bands.low_seconds += 0
                            grf_bands.low_accumulated_grf += accumulated_grf_LF
                            grf_bands.low_cma += left_step.total_accel
                            grf_bands.low_accumulated_peak_vGRF += left_step.peak_grf
                            grf_bands.low_gct += left_step.contact_duration
                        elif 2 > left_step.peak_grf <= 3:
                            grf_bands.moderate_seconds += 0
                            grf_bands.moderate_accumulated_grf += accumulated_grf_LF
                            grf_bands.moderate_cma += left_step.total_accel
                            grf_bands.moderate_accumulated_peak_vGRF += left_step.peak_grf
                            grf_bands.moderate_gct += left_step.contact_duration
                        else:
                            grf_bands.high_seconds += 0
                            grf_bands.high_accumulated_grf += accumulated_grf_LF
                            grf_bands.high_cma += left_step.total_accel
                            grf_bands.high_accumulated_peak_vGRF += left_step.peak_grf
                            grf_bands.high_gct += left_step.contact_duration

                        if left_step.stance_calc == 4: # double
                            stance_bands.double_seconds += 0
                            stance_bands.double_accumulated_grf += accumulated_grf_LF
                            stance_bands.double_cma += left_step.total_accel
                            stance_bands.double_accumulated_peak_vGRF += left_step.peak_grf
                            stance_bands.double_gct += left_step.contact_duration
                        elif left_step.stance_calc == 2: # single
                            stance_bands.single_seconds += 0
                            stance_bands.single_accumulated_grf += accumulated_grf_LF
                            stance_bands.single_cma += left_step.total_accel
                            stance_bands.single_accumulated_peak_vGRF += left_step.peak_grf
                            stance_bands.single_gct += left_step.contact_duration

                        left_right_bands.left_seconds += 0
                        left_right_bands.left_accumulated_grf += accumulated_grf_LF
                        left_right_bands.left_cma += left_step.total_accel
                        left_right_bands.left_accumulated_peak_vGRF += left_step.peak_grf
                        left_right_bands.left_gct += left_step.contact_duration

                    rf_steps = ub_data.get('stepsRF')
                    for rf_step in rf_steps:
                        right_step = Step(rf_step, accumulated_grf_RF, 'Right', active_block, n, session_position,
                                          session_time_start_object)

                        accumulated_grf_RF += right_step.total_grf

                        if right_step.peak_grf < 2:
                            grf_bands.low_seconds += 0
                            grf_bands.low_accumulated_grf += accumulated_grf_RF
                            grf_bands.low_cma += right_step.total_accel
                            grf_bands.low_accumulated_peak_vGRF += right_step.peak_grf
                            grf_bands.low_gct += right_step.contact_duration
                        elif 2 > right_step.peak_grf <= 3:
                            grf_bands.moderate_seconds += 0
                            grf_bands.moderate_accumulated_grf += accumulated_grf_RF
                            grf_bands.moderate_cma += right_step.total_accel
                            grf_bands.moderate_accumulated_peak_vGRF += right_step.peak_grf
                            grf_bands.moderate_gct += right_step.contact_duration
                        else:
                            grf_bands.high_seconds += 0
                            grf_bands.high_accumulated_grf += accumulated_grf_RF
                            grf_bands.high_cma += right_step.total_accel
                            grf_bands.high_accumulated_peak_vGRF += right_step.peak_grf
                            grf_bands.high_gct += right_step.contact_duration

                        if right_step.stance_calc == 4: # double
                            stance_bands.double_seconds += 0
                            stance_bands.double_accumulated_grf += accumulated_grf_RF
                            stance_bands.double_cma += right_step.total_accel
                            stance_bands.double_accumulated_peak_vGRF += right_step.peak_grf
                            stance_bands.double_gct += right_step.contact_duration
                        elif right_step.stance_calc == 2: # single
                            stance_bands.single_seconds += 0
                            stance_bands.single_accumulated_grf += accumulated_grf_RF
                            stance_bands.single_cma += right_step.total_accel
                            stance_bands.single_accumulated_peak_vGRF += right_step.peak_grf
                            stance_bands.single_gct += right_step.contact_duration

                        left_right_bands.right_seconds += 0
                        left_right_bands.right_accumulated_grf += accumulated_grf_RF
                        left_right_bands.right_cma += right_step.total_accel
                        left_right_bands.right_accumulated_peak_vGRF += right_step.peak_grf
                        left_right_bands.right_gct += right_step.contact_duration
                    session_position = session_position + 1


        intensity_bands.low_seconds_percentage += (intensity_bands.low_seconds / intensity_bands.total_seconds) * 100
        intensity_bands.moderate_seconds_percentage += (intensity_bands.moderate_seconds / intensity_bands.total_seconds) * 100
        intensity_bands.high_seconds_percentage += (intensity_bands.high_seconds / intensity_bands.total_seconds) * 100

        intensity_bands.low_accumulated_grf_percentage += (intensity_bands.low_accumulated_grf / intensity_bands.total_accumulated_grf) * 100
        intensity_bands.moderate_accumulated_grf_percentage += (intensity_bands.moderate_accumulated_grf / intensity_bands.total_accumulated_grf) * 100
        intensity_bands.high_accumulated_grf_percentage += (intensity_bands.high_accumulated_grf / intensity_bands.total_accumulated_grf) * 100

        intensity_bands.low_cma_percentage += (intensity_bands.low_cma / intensity_bands.total_cma) * 100
        intensity_bands.moderate_cma_percentage += (intensity_bands.moderate_cma / intensity_bands.total_cma) * 100
        intensity_bands.high_cma_percentage += (intensity_bands.high_cma / intensity_bands.total_cma) * 100

        intensity_bands.low_accumulated_peak_vGRF_percentage += (intensity_bands.low_accumulated_peak_vGRF / intensity_bands.total_accumulated_peak_vGRF) * 100
        intensity_bands.moderate_accumulated_peak_vGRF_percentage += (intensity_bands.moderate_accumulated_peak_vGRF / intensity_bands.total_accumulated_peak_vGRF) * 100
        intensity_bands.high_accumulated_peak_vGRF_percentage += (intensity_bands.high_accumulated_peak_vGRF / intensity_bands.total_accumulated_peak_vGRF) * 100

        intensity_bands.low_gct_percentage += (intensity_bands.low_gct / intensity_bands.total_gct) * 100
        intensity_bands.moderate_gct_percentage += (intensity_bands.moderate_gct / intensity_bands.total_gct) * 100
        intensity_bands.high_gct_percentage += (intensity_bands.high_gct / intensity_bands.total_gct) * 100

        grf_bands.low_seconds_percentage += (grf_bands.low_seconds / grf_bands.total_seconds) * 100
        grf_bands.moderate_seconds_percentage += ( grf_bands.moderate_seconds / grf_bands.total_seconds) * 100
        grf_bands.high_seconds_percentage += (grf_bands.high_seconds / grf_bands.total_seconds) * 100

        grf_bands.low_accumulated_grf_percentage += (grf_bands.low_accumulated_grf / grf_bands.total_accumulated_grf) * 100
        grf_bands.moderate_accumulated_grf_percentage += (grf_bands.moderate_accumulated_grf / grf_bands.total_accumulated_grf) * 100
        grf_bands.high_accumulated_grf_percentage += (grf_bands.high_accumulated_grf / grf_bands.total_accumulated_grf) * 100

        grf_bands.low_cma_percentage += (grf_bands.low_cma / grf_bands.total_cma) * 100
        grf_bands.moderate_cma_percentage += (grf_bands.moderate_cma / grf_bands.total_cma) * 100
        grf_bands.high_cma_percentage += (grf_bands.high_cma / grf_bands.total_cma) * 100

        grf_bands.low_accumulated_peak_vGRF_percentage += (grf_bands.low_accumulated_peak_vGRF / grf_bands.total_accumulated_peak_vGRF) * 100
        grf_bands.moderate_accumulated_peak_vGRF_percentage += (grf_bands.moderate_accumulated_peak_vGRF / grf_bands.total_accumulated_peak_vGRF) * 100
        grf_bands.high_accumulated_peak_vGRF_percentage += (grf_bands.high_accumulated_peak_vGRF / grf_bands.total_accumulated_peak_vGRF) * 100

        grf_bands.low_gct_percentage += (grf_bands.low_gct / grf_bands.total_gct) * 100
        grf_bands.moderate_gct_percentage += (grf_bands.moderate_gct / grf_bands.total_gct) * 100
        grf_bands.high_gct_percentage += (grf_bands.high_gct / grf_bands.total_gct) * 100

        stance_bands.single_seconds_percentage += (stance_bands.single_seconds / stance_bands.total_seconds) * 100
        stance_bands.double_seconds_percentage += (stance_bands.double_seconds / stance_bands.total_seconds) * 100

        stance_bands.single_accumulated_grf_percentage += (stance_bands.single_accumulated_grf / stance_bands.total_accumulated_grf) * 100
        stance_bands.double_accumulated_grf_percentage += (stance_bands.double_accumulated_grf / stance_bands.total_accumulated_grf) * 100

        stance_bands.single_cma_percentage += (stance_bands.single_cma / stance_bands.total_cma) * 100
        stance_bands.double_cma_percentage += (stance_bands.double_cma / stance_bands.total_cma) * 100

        stance_bands.single_accumulated_peak_vGRF_percentage += (stance_bands.single_accumulated_peak_vGRF / stance_bands.total_accumulated_peak_vGRF) * 100
        stance_bands.double_accumulated_peak_vGRF_percentage += (stance_bands.double_accumulated_peak_vGRF / stance_bands.total_accumulated_peak_vGRF) * 100

        stance_bands.single_gct_percentage += (stance_bands.single_gct / stance_bands.total_gct) * 100
        stance_bands.double_gct_percentage += (stance_bands.double_gct / stance_bands.total_gct) * 100

        left_right_bands.left_seconds_percentage += (left_right_bands.left_seconds / left_right_bands.total_seconds) * 100
        left_right_bands.right_seconds_percentage += (left_right_bands.right_seconds / left_right_bands.total_seconds) * 100

        left_right_bands.left_accumulated_grf_percentage += (left_right_bands.left_accumulated_grf / left_right_bands.total_accumulated_grf) * 100
        left_right_bands.right_accumulated_grf_percentage += (left_right_bands.right_accumulated_grf / left_right_bands.total_accumulated_grf) * 100

        left_right_bands.left_cma_percentage += (left_right_bands.left_cma / left_right_bands.total_cma) * 100
        left_right_bands.right_cma_percentage += (left_right_bands.right_cma / left_right_bands.total_cma) * 100

        left_right_bands.left_accumulated_peak_vGRF_percentage += (left_right_bands.left_accumulated_peak_vGRF / left_right_bands.total_accumulated_peak_vGRF) * 100
        left_right_bands.right_accumulated_peak_vGRF_percentage += (left_right_bands.right_accumulated_peak_vGRF / left_right_bands.total_accumulated_peak_vGRF) * 100

        left_right_bands.left_gct_percentage += (left_right_bands.left_gct / left_right_bands.total_gct) * 100
        left_right_bands.right_gct_percentage += (left_right_bands.right_gct / left_right_bands.total_gct) * 100

        session_volume.intensity_bands = intensity_bands
        session_volume.grf_bands = grf_bands
        session_volume.stance_bands = stance_bands
        session_volume.left_right_bands = left_right_bands

    return session_volume
