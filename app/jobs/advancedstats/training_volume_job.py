import pandas as pd


from ._unit_block_job import UnitBlockJob
from utils import parse_datetime
from models.session_training_volume import SessionTrainingVolume
from models.step import Step
from models.unit_block import UnitBlock


class TrainingVolumeJob(UnitBlockJob):

    def _run(self):
        session_training_volume_data = self._calculate_training_volume()

        self.write_session_workload_summary(session_training_volume_data)
        self.write_intensity_bands(session_training_volume_data)

    def write_session_workload_summary(self, session_training_volume_data):
        training_data = pd.DataFrame({
            'accumulated_grf': [session_training_volume_data.accumulated_grf],
            'cma': [session_training_volume_data.cma],
            'active_time': [session_training_volume_data.active_time],
            'gct_left': [session_training_volume_data.ground_contact_time_left],
            'gct_right': [session_training_volume_data.ground_contact_time_right],
            'avg_peak_grf_left': [session_training_volume_data.average_peak_vertical_grf_lf],
            'avg_peak_grf_right': [session_training_volume_data.average_peak_vertical_grf_rf],
            'avg_grf': [session_training_volume_data.average_total_GRF],
            'agg_peak_accel': [session_training_volume_data.average_peak_acceleration],

        }, index=["Summary"])

        self.datastore.put_data('sessionworkloadsummary', training_data)
        self.datastore.copy_to_s3('sessionworkloadsummary', "advanced-stats", '_'.join([self.event_date, self.user_id]) + "/session_workload_summary.csv")

    def write_intensity_bands(self, session_training_volume_data):
        intensity_df = pd.DataFrame()
        intensity_df = intensity_df.append(_convert_intensity_band_to_csv(session_training_volume_data.intensity_bands.low))
        intensity_df = intensity_df.append(_convert_intensity_band_to_csv(session_training_volume_data.intensity_bands.moderate))
        intensity_df = intensity_df.append(_convert_intensity_band_to_csv(session_training_volume_data.intensity_bands.high))
        intensity_df = intensity_df.append(_convert_intensity_band_to_csv(session_training_volume_data.intensity_bands.total))
        columns = [
            'seconds',
            'seconds_percentage',
            'cma',
            'cma_percentage',
            'accumulated_grf',
            'accumulated_grf_percentage',
            'left_cumulative_average_peak_vGRF',
            'right_cumulative_average_peak_vGRF',
            'left_cumulative_average_GRF',
            'right_cumulative_average_GRF',
            'left_cumulative_average_accel',
            'right_cumulative_average_accel',
            'left_gct',
            'right_gct',
            'left_gct_percentage',
            'right_gct_percentage', ]

        self.datastore.put_data('sessionintensitybands', intensity_df, columns=columns)
        self.datastore.copy_to_s3('sessionintensitybands', "advanced-stats", '_'.join([self.event_date, self.user_id]) + "/session_intensity_bands.csv")

    def _calculate_training_volume(self):
        session_volume = SessionTrainingVolume()

        session_position = 0

        right_peak_grf_present = 0
        left_peak_grf_present = 0

        accumulated_grf = 0

        accumulated_grf_lf = 0
        accumulated_grf_rf = 0

        for ub in self._unit_blocks:
            if len(ub) > 0:
                active_block = str(ub.get('_id'))
                unit_bock_count = len(ub.get('unitBlocks'))

                for n in range(0, unit_bock_count):
                    ub_data = ub.get('unitBlocks')[n]
                    ub_rec = UnitBlock(ub_data, accumulated_grf)
                    time_start = parse_datetime(ub.get('unitBlocks')[n].get('timeStart'))
                    time_end = parse_datetime(ub.get('unitBlocks')[n].get('timeEnd'))
                    session_time_start = parse_datetime(self._unit_blocks[0].get('timeStart'))

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

                    session_volume.intensity_bands.total.seconds += ub_rec.duration
                    session_volume.intensity_bands.total.accumulated_grf += ub_rec.total_grf
                    session_volume.intensity_bands.total.cma += ub_rec.total_accel
                    session_volume.intensity_bands.total.left.average_peak_vGRF.add_value(ub_rec.peak_grf_lf, 1)
                    session_volume.intensity_bands.total.right.average_peak_vGRF.add_value(ub_rec.peak_grf_rf, 1)

                    if ub_rec.total_accel_avg < 45:
                        session_volume.intensity_bands.low = self.calc_intensity_band(
                            session_volume.intensity_bands.low, time_end,
                            time_start, ub_rec, lf_steps, rf_steps,
                            accumulated_grf_lf, accumulated_grf_rf,
                            active_block, n, session_position,
                            session_time_start
                        )

                    elif 45 <= ub_rec.total_accel_avg < 105:
                        session_volume.intensity_bands.moderate = self.calc_intensity_band(
                            session_volume.intensity_bands.moderate, time_end,
                            time_start, ub_rec, lf_steps,
                            rf_steps,
                            accumulated_grf_lf, accumulated_grf_rf,
                            active_block, n, session_position,
                            session_time_start
                        )

                    else:
                        session_volume.intensity_bands.high = self.calc_intensity_band(
                            session_volume.intensity_bands.high,
                            time_end,
                            time_start, ub_rec, lf_steps,
                            rf_steps,
                            accumulated_grf_lf, accumulated_grf_rf,
                            active_block, n, session_position,
                            session_time_start
                        )

                    # grf bands

                    session_volume.grf_bands.total.seconds += ub_rec.duration
                    session_volume.grf_bands.total.accumulated_grf += ub_rec.total_grf
                    session_volume.grf_bands.total.cma += ub_rec.total_accel
                    session_volume.grf_bands.total.left.average_peak_vGRF.add_value(ub_rec.peak_grf_lf, 1)
                    session_volume.grf_bands.total.right.average_peak_vGRF.add_value(ub_rec.peak_grf_rf, 1)

                    session_volume.stance_bands.total.seconds += ub_rec.duration
                    session_volume.stance_bands.total.accumulated_grf += ub_rec.total_grf
                    session_volume.stance_bands.total.cma += ub_rec.total_accel

                    session_volume.left_right_bands.total.seconds += ub_rec.duration
                    session_volume.left_right_bands.total.accumulated_grf += ub_rec.total_grf
                    session_volume.left_right_bands.total.cma += ub_rec.total_accel

                    for lf_step in lf_steps:
                        left_step = Step(lf_step, accumulated_grf_lf, 'Left', active_block, n, session_position,
                                         session_time_start)

                        accumulated_grf_lf += left_step.total_grf

                        if left_step.peak_grf < 2:
                            session_volume.grf_bands.low = self.calc_left_grf_band(session_volume.grf_bands.low, left_step)
                        elif 2 < left_step.peak_grf <= 3:
                            session_volume.grf_bands.moderate = self.calc_left_grf_band(session_volume.grf_bands.moderate, left_step)
                        else:
                            session_volume.grf_bands.high = self.calc_left_grf_band(session_volume.grf_bands.high, left_step)

                        if left_step.stance_calc == 4:  # double
                            session_volume.stance_bands.double = self.calc_left_stance(session_volume.stance_bands.double, left_step)
                        elif left_step.stance_calc == 2:  # single
                            session_volume.stance_bands.single = self.calc_left_stance(session_volume.stance_bands.single, left_step)

                        session_volume.left_right_bands.left.seconds += 0
                        session_volume.left_right_bands.left.accumulated_grf += left_step.total_grf
                        session_volume.left_right_bands.left.cma += left_step.total_accel
                        session_volume.left_right_bands.left.average_peak_vGRF.add_value(left_step.peak_grf, 1)
                        session_volume.left_right_bands.left.gct += left_step.contact_duration

                        session_volume.ground_contact_time_left += left_step.contact_duration
                        session_volume.intensity_bands.total.left.gct += left_step.contact_duration
                        session_volume.grf_bands.total.left.gct += left_step.contact_duration
                        session_volume.stance_bands.total.left.gct += left_step.contact_duration

                    for rf_step in rf_steps:
                        right_step = Step(rf_step, accumulated_grf_rf, 'Right', active_block, n, session_position,
                                          session_time_start)

                        accumulated_grf_rf += right_step.total_grf

                        if right_step.peak_grf < 2:
                            session_volume.grf_bands.low = self.calc_right_grf_band(session_volume.grf_bands.low, right_step)
                        elif 2 < right_step.peak_grf <= 3:
                            session_volume.grf_bands.moderate = self.calc_right_grf_band(session_volume.grf_bands.moderate, right_step)
                        else:
                            session_volume.grf_bands.high = self.calc_right_grf_band(session_volume.grf_bands.high, right_step)

                        if right_step.stance_calc == 4:  # double
                            session_volume.stance_bands.double = self.calc_right_stance(session_volume.stance_bands.double, right_step)
                        elif right_step.stance_calc == 2:  # single
                            session_volume.stance_bands.single = self.calc_right_stance(session_volume.stance_bands.single, right_step)

                        session_volume.left_right_bands.right.seconds += 0
                        session_volume.left_right_bands.right.accumulated_grf += right_step.total_grf
                        session_volume.left_right_bands.right.cma += right_step.total_accel
                        session_volume.left_right_bands.right.average_peak_vGRF.add_value(right_step.peak_grf, 1)
                        session_volume.left_right_bands.right.gct += right_step.contact_duration

                        session_volume.ground_contact_time_right += right_step.contact_duration
                        session_volume.intensity_bands.total.right.gct += right_step.contact_duration
                        session_volume.grf_bands.total.right.gct += right_step.contact_duration
                        session_volume.stance_bands.total.right.gct += right_step.contact_duration

                    session_position = session_position + 1

            session_volume.ground_contact_time_right = session_volume.ground_contact_time_right / 1000
            session_volume.ground_contact_time_left = session_volume.ground_contact_time_left / 1000

            if session_position > 0:

                session_volume.average_peak_vertical_grf_lf = (session_volume.average_peak_vertical_grf_lf / float(session_position + 1))
                session_volume.average_peak_vertical_grf_rf = (session_volume.average_peak_vertical_grf_rf / float(session_position + 1))

                session_volume.average_total_GRF = (session_volume.average_total_GRF / float(session_position + 1))
                session_volume.average_peak_acceleration = (session_volume.average_peak_acceleration / float(session_position + 1))

            session_volume.intensity_bands.update_band_calculations()
            session_volume.grf_bands.update_band_calculations()
            session_volume.stance_bands.update_band_calculations()
            session_volume.left_right_bands.update_band_calculations()

        return session_volume

    @staticmethod
    def calc_left_stance(stance_band, left_step):

        stance_band.seconds += 0
        stance_band.accumulated_grf += left_step.total_grf
        stance_band.cma += left_step.total_accel
        stance_band.left.average_peak_vGRF.add_value(left_step.peak_grf, 1)
        stance_band.left.gct += left_step.contact_duration

        return stance_band

    @staticmethod
    def calc_right_stance(stance_band, right_step):
        stance_band.seconds += 0
        stance_band.accumulated_grf += right_step.total_grf
        stance_band.cma += right_step.total_accel
        stance_band.right.average_peak_vGRF.add_value(right_step.peak_grf, 1)
        stance_band.right.gct += right_step.contact_duration

        return stance_band

    @staticmethod
    def calc_left_grf_band(grf_band, left_step):
        grf_band.seconds += 0
        grf_band.accumulated_grf += left_step.total_grf
        grf_band.cma += left_step.total_accel
        grf_band.left.average_peak_vGRF.add_value(left_step.peak_grf, 1)
        grf_band.left.gct += left_step.contact_duration
        grf_band.left.average_accel.add_value(left_step.total_accel_avg, 1)
        grf_band.left.average_GRF.add_value(left_step.total_grf_avg, 1)

        return grf_band

    @staticmethod
    def calc_right_grf_band(grf_band, right_step):
        grf_band.seconds += 0
        grf_band.accumulated_grf += right_step.total_grf
        grf_band.cma += right_step.total_accel
        grf_band.right.average_peak_vGRF.add_value(right_step.peak_grf, 1)
        grf_band.right.gct += right_step.contact_duration
        grf_band.right.average_accel.add_value(right_step.total_accel_avg, 1)
        grf_band.right.average_GRF.add_value(right_step.total_grf_avg, 1)

        return grf_band

    def calc_intensity_band(self, intensity_reporting_band, time_end_object, time_start_object, ub_rec,
                            lf_steps, rf_steps, accumulated_grf_lf, accumulated_grf_rf, active_block, n,
                            session_position, session_time_start_object):
        intensity_reporting_band.seconds += (time_end_object - time_start_object).seconds
        intensity_reporting_band.accumulated_grf += ub_rec.total_grf
        intensity_reporting_band.cma += ub_rec.total_accel
        intensity_reporting_band.left.average_peak_vGRF.add_value(ub_rec.peak_grf_lf, 1)
        intensity_reporting_band.right.average_peak_vGRF.add_value(ub_rec.peak_grf_rf, 1)

        intensity_reporting_band.left.gct += self.get_gct_from_steps(lf_steps, accumulated_grf_lf, "Left",
                                                                     active_block, n, session_position,
                                                                     session_time_start_object)
        intensity_reporting_band.right.gct += self.get_gct_from_steps(rf_steps, accumulated_grf_rf, "Right",
                                                                      active_block, n, session_position,
                                                                      session_time_start_object)
        intensity_reporting_band.left.average_accel.add_value(self.get_avg_from_steps(lf_steps, "total_accel_avg",
                                                                                      accumulated_grf_lf, "Left",
                                                                                      active_block, n, session_position,
                                                                                      session_time_start_object), 1)
        intensity_reporting_band.right.average_accel.add_value(self.get_avg_from_steps(rf_steps, "total_accel_avg",
                                                                                       accumulated_grf_rf, "Right",
                                                                                       active_block, n, session_position,
                                                                                       session_time_start_object), 1)
        intensity_reporting_band.left.average_GRF.add_value(self.get_avg_from_steps(lf_steps, "total_grf_avg", accumulated_grf_lf,
                                                                                    "Left",
                                                                                    active_block, n, session_position,
                                                                                    session_time_start_object), 1)
        intensity_reporting_band.right.average_GRF.add_value(self.get_avg_from_steps(rf_steps, "total_grf_avg", accumulated_grf_rf,
                                                                                     "Right",
                                                                                     active_block, n, session_position,
                                                                                     session_time_start_object), 1)

        return intensity_reporting_band

    @staticmethod
    def get_gct_from_steps(step_list, accumulated_grf, orientation, active_block, n, session_position, session_time_start_object):

        gct = 0

        for step in step_list:
            new_step = Step(step, accumulated_grf, orientation, active_block, n, session_position, session_time_start_object)
            gct += new_step.contact_duration

        return gct

    @staticmethod
    def get_avg_from_steps(step_list, attribute_name, accumulated_grf, orientation, active_block, n, session_position, session_time_start_object):

        val = 0
        cnt = 0

        for step in step_list:
            new_step = Step(step, accumulated_grf, orientation, active_block, n, session_position, session_time_start_object)
            val += getattr(new_step, attribute_name)
            cnt += 1

        if cnt > 0:
            avg = val/float(cnt)
        else:
            avg = 0

        return avg


def _convert_intensity_band_to_csv(t):
    ab = pd.DataFrame({
        'seconds': [t.seconds],
        'seconds_percentage': [t.seconds_percentage],
        'cma': [t.cma],
        'cma_percentage': [t.cma_percentage],
        'accumulated_grf': [t.accumulated_grf],
        'accumulated_grf_percentage': [t.accumulated_grf_percentage],
        'left_cumulative_average_peak_vGRF': [t.left.cumulative_average_peak_vGRF],
        'right_cumulative_average_peak_vGRF': [t.right.cumulative_average_peak_vGRF],
        'left_cumulative_average_GRF': [t.left.cumulative_average_GRF],
        'right_cumulative_average_GRF': [t.right.cumulative_average_GRF],
        'left_cumulative_average_accel': [t.left.cumulative_average_accel],
        'right_cumulative_average_accel': [t.right.cumulative_average_accel],
        'left_gct': [t.left.gct],
        'right_gct': [t.right.gct],
        'left_gct_percentage': [t.left.gct_percentage],
        'right_gct_percentage': [t.right.gct_percentage],
    }, index=[t.descriptor])

    return ab
