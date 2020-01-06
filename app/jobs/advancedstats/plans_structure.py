from collections import OrderedDict
from models.movement_pattern import MovementPatternType


class PlansFactory(object):
    def __init__(self, plans_api_version, environment, user_id, event_date, session_id, seconds_duration, end_date=None):
        self.plans_api_version = plans_api_version
        self.environment = environment
        self.user_id = user_id
        self.event_date = event_date
        self.end_date = end_date
        self.session_id = session_id
        self.seconds_duration = seconds_duration
        self.latest_plans_version = "4_7"

    def get_plans(self):
        if self.plans_api_version == "4_4":
            return Plans_4_4(self.environment, self.user_id, self.event_date, self.session_id, self.seconds_duration)
        elif self.plans_api_version == "4_5":
            return Plans_4_5(self.environment, self.user_id, self.event_date,self.session_id, self.seconds_duration,
                             end_date=self.end_date)
        elif self.plans_api_version == "4_6":
            return Plans_4_6(self.environment, self.user_id, self.event_date, self.session_id, self.seconds_duration,
                             end_date=self.end_date)
        elif self.plans_api_version == "4_7":
            return Plans_4_7(self.environment, self.user_id, self.event_date, self.session_id, self.seconds_duration,
                             end_date=self.end_date)
        else:
            return Plans_4_3(self.environment, self.user_id, self.event_date, self.session_id, self.seconds_duration)


class PlansBase(object):
    def __init__(self, environment, user_id, event_date, session_id, seconds_duration):
        self.environment = environment
        self.user_id = user_id
        self.event_date = event_date
        self.session_id = session_id
        self.seconds_duration = seconds_duration

    def get_mongo_asymmetry_record(self, asymmetry_events, movement_events):
        pass

    def get_mongo_movement_pattern_record(self, movement_patterns):

        record_out = OrderedDict()
        record_out['user_id'] = self.user_id
        record_out['event_date'] = self.event_date
        record_out['seconds_duration'] = self.seconds_duration
        record_out['session_id'] = self.session_id

        apt_stats_list = []
        hip_drop_apt_stats_list = []
        hip_drop_pva_stats_list = []
        knee_valgus_hip_drop_stats_list = []
        knee_valgus_pva_stats_list = []
        knee_valgus_apt_stats_list = []
        hip_rotation_ankle_pitch_stats_list = []
        hip_rotation_apt_stats_list = []

        if movement_patterns is not None:
            apt_stats_list = self.get_mongo_record_for_stats_collection(movement_patterns.apt_ankle_pitch_stats)
            hip_drop_apt_stats_list = self.get_mongo_record_for_stats_collection(movement_patterns.hip_drop_apt_stats)
            hip_drop_pva_stats_list = self.get_mongo_record_for_stats_collection(movement_patterns.hip_drop_pva_stats)
            knee_valgus_hip_drop_stats_list = self.get_mongo_record_for_stats_collection(movement_patterns.knee_valgus_hip_drop_stats)
            knee_valgus_pva_stats_list = self.get_mongo_record_for_stats_collection(movement_patterns.knee_valgus_pva_stats)
            knee_valgus_apt_stats_list = self.get_mongo_record_for_stats_collection(movement_patterns.knee_valgus_apt_stats)
            hip_rotation_ankle_pitch_stats_list = self.get_mongo_record_for_stats_collection(
                movement_patterns.hip_rotation_ankle_pitch_stats)
            hip_rotation_apt_stats_list = self.get_mongo_record_for_stats_collection(
                movement_patterns.hip_rotation_apt_stats)

        record_out["apt_ankle_pitch_stats"] = apt_stats_list
        record_out["hip_drop_apt_stats"] = hip_drop_apt_stats_list
        record_out["hip_drop_pva_stats"] = hip_drop_pva_stats_list
        record_out["knee_valgus_hip_drop_stats"] = knee_valgus_hip_drop_stats_list
        record_out["knee_valgus_pva_stats"] = knee_valgus_pva_stats_list
        record_out["knee_valgus_apt_stats"] = knee_valgus_apt_stats_list
        record_out["hip_rotation_ankle_pitch_stats"] = hip_rotation_ankle_pitch_stats_list
        record_out["hip_rotation_apt_stats"] = hip_rotation_apt_stats_list

        return record_out

    def get_mongo_record_for_stats_collection(self, movement_patterns_collection):

        stats_list = []

        for movement_pattern_stats in movement_patterns_collection:
            apt_stats = OrderedDict()
            apt_stats["side"] = movement_pattern_stats.side
            apt_stats["cadence"] = movement_pattern_stats.cadence
            apt_stats["elasticity"] = movement_pattern_stats.elasticity
            apt_stats["elasticity_t"] = movement_pattern_stats.elasticity_t
            apt_stats["elasticity_se"] = movement_pattern_stats.elasticity_se
            apt_stats["obs"] = movement_pattern_stats.obs
            apt_stats["adf"] = movement_pattern_stats.adf
            apt_stats["adf_critical"] = movement_pattern_stats.adf_critical

            stats_list.append(apt_stats)

        return stats_list


class Plans_4_4(PlansBase):
    def __init__(self, environment, user_id, event_date, session_id, seconds_duration):
        super().__init__(environment, user_id, event_date, session_id, seconds_duration)
        self.endpoint = f'https://apis.{self.environment}.fathomai.com/plans/4_4/session/{user_id}/three_sensor_data'

    def get_body(self, asymmetry_events, movement_patterns):

        return {
                'event_date': self.event_date,
                "session_id": self.session_id,
                "seconds_duration": self.seconds_duration,
                "asymmetry": {
                    "left_apt": asymmetry_events.anterior_pelvic_tilt_summary.left,
                    "right_apt": asymmetry_events.anterior_pelvic_tilt_summary.right,
                    "asymmetric_events": asymmetry_events.anterior_pelvic_tilt_summary.asymmetric_events,
                    "symmetric_events": asymmetry_events.anterior_pelvic_tilt_summary.symmetric_events,
                }
            }

    def get_mongo_asymmetry_record(self, asymmetry_events, movement_events):

        user_id = self.user_id

        record_out = OrderedDict()
        record_out['user_id'] = user_id
        record_out['event_date'] = self.event_date

        record_out['session_id'] = self.session_id
        record_out['left_apt'] = asymmetry_events.anterior_pelvic_tilt_summary.left
        record_out['right_apt'] = asymmetry_events.anterior_pelvic_tilt_summary.right

        record_out['symmetric_events'] = asymmetry_events.anterior_pelvic_tilt_summary.symmetric_events
        record_out['asymmetric_events'] = asymmetry_events.anterior_pelvic_tilt_summary.asymmetric_events
        record_out['percent_events_asymmetric'] = asymmetry_events.anterior_pelvic_tilt_summary.percent_events_asymmetric
        record_out['seconds_duration'] = self.seconds_duration

        record_asymmetries = []

        for m in movement_events:
            event_record = OrderedDict()
            event_record['time_block'] = m.time_block
            event_record['start_time'] = m.start_time
            event_record['end_time'] = m.end_time
            event_record['left'] = m.anterior_pelvic_tilt.left
            event_record['right'] = m.anterior_pelvic_tilt.right
            event_record['significant'] = m.anterior_pelvic_tilt.significant

            record_asymmetries.append(event_record)

        record_out['time_blocks'] = record_asymmetries

        return record_out


class Plans_4_3(Plans_4_4):
    def __init__(self, environment, user_id, event_date, session_id, seconds_duration):
        super().__init__(environment, user_id, event_date, session_id, seconds_duration)
        self.endpoint = f'https://apis.{self.environment}.fathomai.com/plans/4_3/session/three_sensor_data'

    def get_body(self, asymmetry_events, movement_patterns):
        body = super().get_body(asymmetry_events, movement_patterns)

        body['user_id'] = self.user_id

        return body


class Plans_4_5(PlansBase):
    def __init__(self, environment, user_id, event_date, session_id, seconds_duration, end_date):
        super().__init__(environment, user_id, event_date, session_id, seconds_duration)
        self.endpoint = f'https://apis.{self.environment}.fathomai.com/plans/4_5/session/{user_id}/three_sensor_data'
        self.end_date = end_date

    def get_body(self, asymmetry_events, movement_patterns):

            body = OrderedDict()
            body["event_date"] = self.event_date
            body["session_id"] = self.session_id
            body["seconds_duration"] = self.seconds_duration
            body["end_date"] = self.end_date

            if asymmetry_events is not None:
                body['asymmetry'] = {
                                "apt":{
                                    "left": asymmetry_events.anterior_pelvic_tilt_summary.left,
                                    "right": asymmetry_events.anterior_pelvic_tilt_summary.right,
                                    "asymmetric_events": asymmetry_events.anterior_pelvic_tilt_summary.asymmetric_events,
                                    "symmetric_events": asymmetry_events.anterior_pelvic_tilt_summary.symmetric_events,
                                    "percent_events_asymmetric": asymmetry_events.anterior_pelvic_tilt_summary.percent_events_asymmetric
                                    },
                                "ankle_pitch": {
                                    "left": asymmetry_events.ankle_pitch_summary.left,
                                    "right": asymmetry_events.ankle_pitch_summary.right,
                                    "asymmetric_events": asymmetry_events.ankle_pitch_summary.asymmetric_events,
                                    "symmetric_events": asymmetry_events.ankle_pitch_summary.symmetric_events,
                                    "percent_events_asymmetric": asymmetry_events.ankle_pitch_summary.percent_events_asymmetric
                                    },
                                "hip_drop": {
                                    "left": asymmetry_events.hip_drop_summary.left,
                                    "right": asymmetry_events.hip_drop_summary.right,
                                    "asymmetric_events": asymmetry_events.hip_drop_summary.asymmetric_events,
                                    "symmetric_events": asymmetry_events.hip_drop_summary.symmetric_events,
                                    "percent_events_asymmetric": asymmetry_events.hip_drop_summary.percent_events_asymmetric
                                    }
                                }
            return body

    def get_mongo_asymmetry_record(self, asymmetry_events, movement_events):

        record_out = OrderedDict()
        record_out['user_id'] = self.user_id
        record_out['event_date'] = self.event_date
        record_out['seconds_duration'] = self.seconds_duration
        record_out['session_id'] = self.session_id

        # sym_count = [m for m in movement_events if not m.significant and (m.left_median > 0 or m.right_median > 0)]
        # asym_count = [m for m in movement_events if m.significant and (m.left_median > 0 or m.right_median > 0)]

        anterior_pelivic_tilt = OrderedDict()
        anterior_pelivic_tilt['left'] = asymmetry_events.anterior_pelvic_tilt_summary.left
        anterior_pelivic_tilt['right'] = asymmetry_events.anterior_pelvic_tilt_summary.right
        anterior_pelivic_tilt['symmetric_events'] = asymmetry_events.anterior_pelvic_tilt_summary.symmetric_events
        anterior_pelivic_tilt['asymmetric_events'] = asymmetry_events.anterior_pelvic_tilt_summary.asymmetric_events
        anterior_pelivic_tilt[
            'percent_events_asymmetric'] = asymmetry_events.anterior_pelvic_tilt_summary.percent_events_asymmetric

        record_out['apt'] = anterior_pelivic_tilt

        ankle_pitch = OrderedDict()
        ankle_pitch['left'] = asymmetry_events.ankle_pitch_summary.left
        ankle_pitch['right'] = asymmetry_events.ankle_pitch_summary.right
        ankle_pitch['symmetric_events'] = asymmetry_events.ankle_pitch_summary.symmetric_events
        ankle_pitch['asymmetric_events'] = asymmetry_events.ankle_pitch_summary.asymmetric_events
        ankle_pitch['percent_events_asymmetric'] = asymmetry_events.ankle_pitch_summary.percent_events_asymmetric

        record_out['ankle_pitch'] = ankle_pitch

        hip_drop = OrderedDict()
        hip_drop['left'] = asymmetry_events.hip_drop_summary.left
        hip_drop['right'] = asymmetry_events.hip_drop_summary.right
        hip_drop['symmetric_events'] = asymmetry_events.hip_drop_summary.symmetric_events
        hip_drop['asymmetric_events'] = asymmetry_events.hip_drop_summary.asymmetric_events
        hip_drop['percent_events_asymmetric'] = asymmetry_events.hip_drop_summary.percent_events_asymmetric

        record_out['hip_drop'] = hip_drop

        record_asymmetries = []

        for m in movement_events:
            event_record = OrderedDict()
            event_record['time_block'] = m.time_block
            event_record['start_time'] = m.start_time
            event_record['end_time'] = m.end_time

            apt_time_block = OrderedDict()
            apt_time_block['left'] = m.anterior_pelvic_tilt.left
            apt_time_block['right'] = m.anterior_pelvic_tilt.right
            apt_time_block['significant'] = m.anterior_pelvic_tilt.significant

            event_record['apt'] = apt_time_block

            ankle_pitch_time_block = OrderedDict()
            ankle_pitch_time_block['left'] = m.ankle_pitch.left
            ankle_pitch_time_block['right'] = m.ankle_pitch.right
            ankle_pitch_time_block['significant'] = m.ankle_pitch.significant

            event_record['ankle_pitch'] = ankle_pitch_time_block

            hip_drop_time_block = OrderedDict()
            hip_drop_time_block['left'] = m.hip_drop.left
            hip_drop_time_block['right'] = m.hip_drop.right
            hip_drop_time_block['significant'] = m.hip_drop.significant

            event_record['hip_drop'] = hip_drop_time_block

            record_asymmetries.append(event_record)

        record_out['time_blocks'] = record_asymmetries

        return record_out


class Plans_4_6(PlansBase):
    def __init__(self, environment, user_id, event_date, session_id, seconds_duration, end_date):
        super().__init__(environment, user_id, event_date, session_id, seconds_duration)
        self.endpoint = f'https://apis.{self.environment}.fathomai.com/plans/4_6/session/{user_id}/three_sensor_data'
        self.end_date = end_date

    def get_body(self, asymmetry_events, movement_patterns):

        body = OrderedDict()
        body["event_date"] = self.event_date
        body["session_id"] = self.session_id
        body["seconds_duration"] = self.seconds_duration
        body["end_date"] = self.end_date

        if asymmetry_events is not None:
            body['asymmetry'] = {
                "apt": {
                    "left": asymmetry_events.anterior_pelvic_tilt_summary.left,
                    "right": asymmetry_events.anterior_pelvic_tilt_summary.right,
                    "asymmetric_events": asymmetry_events.anterior_pelvic_tilt_summary.asymmetric_events,
                    "symmetric_events": asymmetry_events.anterior_pelvic_tilt_summary.symmetric_events,
                    "percent_events_asymmetric": asymmetry_events.anterior_pelvic_tilt_summary.percent_events_asymmetric
                },
                "ankle_pitch": {
                    "left": asymmetry_events.ankle_pitch_summary.left,
                    "right": asymmetry_events.ankle_pitch_summary.right,
                    "asymmetric_events": asymmetry_events.ankle_pitch_summary.asymmetric_events,
                    "symmetric_events": asymmetry_events.ankle_pitch_summary.symmetric_events,
                    "percent_events_asymmetric": asymmetry_events.ankle_pitch_summary.percent_events_asymmetric
                },
                "hip_drop": {
                    "left": asymmetry_events.hip_drop_summary.left,
                    "right": asymmetry_events.hip_drop_summary.right,
                    "asymmetric_events": asymmetry_events.hip_drop_summary.asymmetric_events,
                    "symmetric_events": asymmetry_events.hip_drop_summary.symmetric_events,
                    "percent_events_asymmetric": asymmetry_events.hip_drop_summary.percent_events_asymmetric
                },
            }
        if movement_patterns is not None:
            body['movement_patterns'] = {
                "apt_ankle_pitch": {
                    "left": {
                        "elasticity": movement_patterns.get_elasticity(1, MovementPatternType.apt_ankle_pitch),
                        "y_adf": movement_patterns.get_adf(1, MovementPatternType.apt_ankle_pitch)
                    },
                    "right": {
                        "elasticity": movement_patterns.get_elasticity(2, MovementPatternType.apt_ankle_pitch),
                        "y_adf": movement_patterns.get_adf(2, MovementPatternType.apt_ankle_pitch)
                    }
                },
                "hip_drop_apt": {
                    "left": {
                        "elasticity": movement_patterns.get_elasticity(1, MovementPatternType.hip_drop_apt),
                        "y_adf": movement_patterns.get_adf(1, MovementPatternType.hip_drop_apt)
                    },
                    "right": {
                        "elasticity": movement_patterns.get_elasticity(2, MovementPatternType.hip_drop_apt),
                        "y_adf": movement_patterns.get_adf(2, MovementPatternType.hip_drop_apt)
                    }
                },
                "hip_drop_pva": {
                    "left": {
                        "elasticity": movement_patterns.get_elasticity(1, MovementPatternType.hip_drop_pva),
                        "y_adf": movement_patterns.get_adf(1, MovementPatternType.hip_drop_pva)
                    },
                    "right": {
                        "elasticity": movement_patterns.get_elasticity(2, MovementPatternType.hip_drop_pva),
                        "y_adf": movement_patterns.get_adf(2, MovementPatternType.hip_drop_pva)
                    }
                },
                "knee_valgus_hip_drop": {
                    "left": {
                        "elasticity": movement_patterns.get_elasticity(1, MovementPatternType.knee_valgus_hip_drop),
                        "y_adf": movement_patterns.get_adf(1, MovementPatternType.knee_valgus_hip_drop)
                    },
                    "right": {
                        "elasticity": movement_patterns.get_elasticity(2, MovementPatternType.knee_valgus_hip_drop),
                        "y_adf": movement_patterns.get_adf(2, MovementPatternType.knee_valgus_hip_drop)
                    }
                },
                "knee_valgus_pva": {
                    "left": {
                        "elasticity": movement_patterns.get_elasticity(1, MovementPatternType.knee_valgus_pva),
                        "y_adf": movement_patterns.get_adf(1, MovementPatternType.knee_valgus_pva)
                    },
                    "right": {
                        "elasticity": movement_patterns.get_elasticity(2, MovementPatternType.knee_valgus_pva),
                        "y_adf": movement_patterns.get_adf(2, MovementPatternType.knee_valgus_pva)
                    }
                },
                "knee_valgus_apt": {
                    "left": {
                        "elasticity": movement_patterns.get_elasticity(1, MovementPatternType.knee_valgus_apt),
                        "y_adf": movement_patterns.get_adf(1, MovementPatternType.knee_valgus_apt)
                    },
                    "right": {
                        "elasticity": movement_patterns.get_elasticity(2, MovementPatternType.knee_valgus_apt),
                        "y_adf": movement_patterns.get_adf(2, MovementPatternType.knee_valgus_apt)
                    }
                },
            }
        return body

    def get_mongo_asymmetry_record(self, asymmetry_events, movement_events):

        record_out = OrderedDict()
        record_out['user_id'] = self.user_id
        record_out['event_date'] = self.event_date
        record_out['seconds_duration'] = self.seconds_duration
        record_out['session_id'] = self.session_id

        # sym_count = [m for m in movement_events if not m.significant and (m.left_median > 0 or m.right_median > 0)]
        # asym_count = [m for m in movement_events if m.significant and (m.left_median > 0 or m.right_median > 0)]

        anterior_pelivic_tilt = OrderedDict()
        anterior_pelivic_tilt['left'] = asymmetry_events.anterior_pelvic_tilt_summary.left
        anterior_pelivic_tilt['right'] = asymmetry_events.anterior_pelvic_tilt_summary.right
        anterior_pelivic_tilt['symmetric_events'] = asymmetry_events.anterior_pelvic_tilt_summary.symmetric_events
        anterior_pelivic_tilt['asymmetric_events'] = asymmetry_events.anterior_pelvic_tilt_summary.asymmetric_events
        anterior_pelivic_tilt[
            'percent_events_asymmetric'] = asymmetry_events.anterior_pelvic_tilt_summary.percent_events_asymmetric

        record_out['apt'] = anterior_pelivic_tilt

        ankle_pitch = OrderedDict()
        ankle_pitch['left'] = asymmetry_events.ankle_pitch_summary.left
        ankle_pitch['right'] = asymmetry_events.ankle_pitch_summary.right
        ankle_pitch['symmetric_events'] = asymmetry_events.ankle_pitch_summary.symmetric_events
        ankle_pitch['asymmetric_events'] = asymmetry_events.ankle_pitch_summary.asymmetric_events
        ankle_pitch['percent_events_asymmetric'] = asymmetry_events.ankle_pitch_summary.percent_events_asymmetric

        record_out['ankle_pitch'] = ankle_pitch

        hip_drop = OrderedDict()
        hip_drop['left'] = asymmetry_events.hip_drop_summary.left
        hip_drop['right'] = asymmetry_events.hip_drop_summary.right
        hip_drop['symmetric_events'] = asymmetry_events.hip_drop_summary.symmetric_events
        hip_drop['asymmetric_events'] = asymmetry_events.hip_drop_summary.asymmetric_events
        hip_drop['percent_events_asymmetric'] = asymmetry_events.hip_drop_summary.percent_events_asymmetric

        record_out['hip_drop'] = hip_drop

        knee_valgus = OrderedDict()
        knee_valgus['left'] = asymmetry_events.knee_valgus_summary.left
        knee_valgus['right'] = asymmetry_events.knee_valgus_summary.right
        knee_valgus['symmetric_events'] = asymmetry_events.knee_valgus_summary.symmetric_events
        knee_valgus['asymmetric_events'] = asymmetry_events.knee_valgus_summary.asymmetric_events
        knee_valgus['percent_events_asymmetric'] = asymmetry_events.knee_valgus_summary.percent_events_asymmetric

        record_out['knee_valgus'] = knee_valgus

        hip_rotation = OrderedDict()
        hip_rotation['left'] = asymmetry_events.hip_rotation_summary.left
        hip_rotation['right'] = asymmetry_events.hip_rotation_summary.right
        hip_rotation['symmetric_events'] = asymmetry_events.hip_rotation_summary.symmetric_events
        hip_rotation['asymmetric_events'] = asymmetry_events.hip_rotation_summary.asymmetric_events
        hip_rotation['percent_events_asymmetric'] = asymmetry_events.hip_rotation_summary.percent_events_asymmetric

        record_out['hip_rotation'] = hip_rotation

        record_asymmetries = []

        for m in movement_events:
            event_record = OrderedDict()
            event_record['time_block'] = m.time_block
            event_record['start_time'] = m.start_time
            event_record['end_time'] = m.end_time

            apt_time_block = OrderedDict()
            apt_time_block['left'] = m.anterior_pelvic_tilt.left
            apt_time_block['right'] = m.anterior_pelvic_tilt.right
            apt_time_block['significant'] = m.anterior_pelvic_tilt.significant

            event_record['apt'] = apt_time_block

            ankle_pitch_time_block = OrderedDict()
            ankle_pitch_time_block['left'] = m.ankle_pitch.left
            ankle_pitch_time_block['right'] = m.ankle_pitch.right
            ankle_pitch_time_block['significant'] = m.ankle_pitch.significant

            event_record['ankle_pitch'] = ankle_pitch_time_block

            hip_drop_time_block = OrderedDict()
            hip_drop_time_block['left'] = m.hip_drop.left
            hip_drop_time_block['right'] = m.hip_drop.right
            hip_drop_time_block['significant'] = m.hip_drop.significant

            event_record['hip_drop'] = hip_drop_time_block

            knee_valgus_time_block = OrderedDict()
            knee_valgus_time_block['left'] = m.knee_valgus.left
            knee_valgus_time_block['right'] = m.knee_valgus.right
            knee_valgus_time_block['significant'] = m.knee_valgus.significant

            event_record['knee_valgus'] = knee_valgus_time_block

            hip_rotation_time_block = OrderedDict()
            hip_rotation_time_block['left'] = m.hip_rotation.left
            hip_rotation_time_block['right'] = m.hip_rotation.right
            hip_rotation_time_block['significant'] = m.hip_rotation.significant

            event_record['hip_rotation'] = hip_rotation_time_block

            record_asymmetries.append(event_record)

        record_out['time_blocks'] = record_asymmetries

        return record_out


class Plans_4_7(PlansBase):
    def __init__(self, environment, user_id, event_date, session_id, seconds_duration, end_date):
        super().__init__(environment, user_id, event_date, session_id, seconds_duration)
        self.endpoint = f'https://apis.{self.environment}.fathomai.com/plans/4_7/session/{user_id}/three_sensor_data'
        self.end_date = end_date

    def get_body(self, asymmetry_events, movement_patterns):

        body = OrderedDict()
        body["event_date"] = self.event_date
        body["session_id"] = self.session_id
        body["seconds_duration"] = self.seconds_duration
        body["end_date"] = self.end_date

        if asymmetry_events is not None:
            body['asymmetry'] = {
                "apt": {
                    "left": asymmetry_events.anterior_pelvic_tilt_summary.left,
                    "right": asymmetry_events.anterior_pelvic_tilt_summary.right,
                    "asymmetric_events": asymmetry_events.anterior_pelvic_tilt_summary.asymmetric_events,
                    "symmetric_events": asymmetry_events.anterior_pelvic_tilt_summary.symmetric_events,
                    "percent_events_asymmetric": asymmetry_events.anterior_pelvic_tilt_summary.percent_events_asymmetric
                },
                "ankle_pitch": {
                    "left": asymmetry_events.ankle_pitch_summary.left,
                    "right": asymmetry_events.ankle_pitch_summary.right,
                    "asymmetric_events": asymmetry_events.ankle_pitch_summary.asymmetric_events,
                    "symmetric_events": asymmetry_events.ankle_pitch_summary.symmetric_events,
                    "percent_events_asymmetric": asymmetry_events.ankle_pitch_summary.percent_events_asymmetric
                },
                "hip_drop": {
                    "left": asymmetry_events.hip_drop_summary.left,
                    "right": asymmetry_events.hip_drop_summary.right,
                    "asymmetric_events": asymmetry_events.hip_drop_summary.asymmetric_events,
                    "symmetric_events": asymmetry_events.hip_drop_summary.symmetric_events,
                    "percent_events_asymmetric": asymmetry_events.hip_drop_summary.percent_events_asymmetric
                },
                "knee_valgus": {
                    "left": asymmetry_events.knee_valgus_summary.left,
                    "right": asymmetry_events.knee_valgus_summary.right,
                    "asymmetric_events": asymmetry_events.knee_valgus_summary.asymmetric_events,
                    "symmetric_events": asymmetry_events.knee_valgus_summary.symmetric_events,
                    "percent_events_asymmetric": asymmetry_events.knee_valgus_summary.percent_events_asymmetric
                },
                "hip_rotation": {
                    "left": asymmetry_events.hip_rotation_summary.left,
                    "right": asymmetry_events.hip_rotation_summary.right,
                    "asymmetric_events": asymmetry_events.hip_rotation_summary.asymmetric_events,
                    "symmetric_events": asymmetry_events.hip_rotation_summary.symmetric_events,
                    "percent_events_asymmetric": asymmetry_events.hip_rotation_summary.percent_events_asymmetric
                }
            }
        if movement_patterns is not None:
            body['movement_patterns'] = {
                "apt_ankle_pitch": {
                    "left": {
                        "elasticity": movement_patterns.get_elasticity(1, MovementPatternType.apt_ankle_pitch),
                        "y_adf": movement_patterns.get_adf(1, MovementPatternType.apt_ankle_pitch)
                    },
                    "right": {
                        "elasticity": movement_patterns.get_elasticity(2, MovementPatternType.apt_ankle_pitch),
                        "y_adf": movement_patterns.get_adf(2, MovementPatternType.apt_ankle_pitch)
                    }
                },
                "hip_drop_apt": {
                    "left": {
                        "elasticity": movement_patterns.get_elasticity(1, MovementPatternType.hip_drop_apt),
                        "y_adf": movement_patterns.get_adf(1, MovementPatternType.hip_drop_apt)
                    },
                    "right": {
                        "elasticity": movement_patterns.get_elasticity(2, MovementPatternType.hip_drop_apt),
                        "y_adf": movement_patterns.get_adf(2, MovementPatternType.hip_drop_apt)
                    }
                },
                "hip_drop_pva": {
                    "left": {
                        "elasticity": movement_patterns.get_elasticity(1, MovementPatternType.hip_drop_pva),
                        "y_adf": movement_patterns.get_adf(1, MovementPatternType.hip_drop_pva)
                    },
                    "right": {
                        "elasticity": movement_patterns.get_elasticity(2, MovementPatternType.hip_drop_pva),
                        "y_adf": movement_patterns.get_adf(2, MovementPatternType.hip_drop_pva)
                    }
                },
                "knee_valgus_hip_drop": {
                    "left": {
                        "elasticity": movement_patterns.get_elasticity(1, MovementPatternType.knee_valgus_hip_drop),
                        "y_adf": movement_patterns.get_adf(1, MovementPatternType.knee_valgus_hip_drop)
                    },
                    "right": {
                        "elasticity": movement_patterns.get_elasticity(2, MovementPatternType.knee_valgus_hip_drop),
                        "y_adf": movement_patterns.get_adf(2, MovementPatternType.knee_valgus_hip_drop)
                    }
                },
                "knee_valgus_pva": {
                    "left": {
                        "elasticity": movement_patterns.get_elasticity(1, MovementPatternType.knee_valgus_pva),
                        "y_adf": movement_patterns.get_adf(1, MovementPatternType.knee_valgus_pva)
                    },
                    "right": {
                        "elasticity": movement_patterns.get_elasticity(2, MovementPatternType.knee_valgus_pva),
                        "y_adf": movement_patterns.get_adf(2, MovementPatternType.knee_valgus_pva)
                    }
                },
                "knee_valgus_apt": {
                    "left": {
                        "elasticity": movement_patterns.get_elasticity(1, MovementPatternType.knee_valgus_apt),
                        "y_adf": movement_patterns.get_adf(1, MovementPatternType.knee_valgus_apt)
                    },
                    "right": {
                        "elasticity": movement_patterns.get_elasticity(2, MovementPatternType.knee_valgus_apt),
                        "y_adf": movement_patterns.get_adf(2, MovementPatternType.knee_valgus_apt)
                    }
                },
                "hip_rotation_ankle_pitch": {
                    "left": {
                        "elasticity": movement_patterns.get_elasticity(1, MovementPatternType.hip_rotation_ankle_pitch),
                        "y_adf": movement_patterns.get_adf(1, MovementPatternType.hip_rotation_ankle_pitch)
                    },
                    "right": {
                        "elasticity": movement_patterns.get_elasticity(2, MovementPatternType.hip_rotation_ankle_pitch),
                        "y_adf": movement_patterns.get_adf(2, MovementPatternType.hip_rotation_ankle_pitch)
                    }
                },
                "hip_rotation_apt": {
                    "left": {
                        "elasticity": movement_patterns.get_elasticity(1, MovementPatternType.hip_rotation_apt),
                        "y_adf": movement_patterns.get_adf(1, MovementPatternType.hip_rotation_apt)
                    },
                    "right": {
                        "elasticity": movement_patterns.get_elasticity(2, MovementPatternType.hip_rotation_apt),
                        "y_adf": movement_patterns.get_adf(2, MovementPatternType.hip_rotation_apt)
                    }
                },
            }
        return body

    def get_mongo_asymmetry_record(self, asymmetry_events, movement_events):

        record_out = OrderedDict()
        record_out['user_id'] = self.user_id
        record_out['event_date'] = self.event_date
        record_out['seconds_duration'] = self.seconds_duration
        record_out['session_id'] = self.session_id

        # sym_count = [m for m in movement_events if not m.significant and (m.left_median > 0 or m.right_median > 0)]
        # asym_count = [m for m in movement_events if m.significant and (m.left_median > 0 or m.right_median > 0)]

        anterior_pelivic_tilt = OrderedDict()
        anterior_pelivic_tilt['left'] = asymmetry_events.anterior_pelvic_tilt_summary.left
        anterior_pelivic_tilt['right'] = asymmetry_events.anterior_pelvic_tilt_summary.right
        anterior_pelivic_tilt['symmetric_events'] = asymmetry_events.anterior_pelvic_tilt_summary.symmetric_events
        anterior_pelivic_tilt['asymmetric_events'] = asymmetry_events.anterior_pelvic_tilt_summary.asymmetric_events
        anterior_pelivic_tilt[
            'percent_events_asymmetric'] = asymmetry_events.anterior_pelvic_tilt_summary.percent_events_asymmetric

        record_out['apt'] = anterior_pelivic_tilt

        ankle_pitch = OrderedDict()
        ankle_pitch['left'] = asymmetry_events.ankle_pitch_summary.left
        ankle_pitch['right'] = asymmetry_events.ankle_pitch_summary.right
        ankle_pitch['symmetric_events'] = asymmetry_events.ankle_pitch_summary.symmetric_events
        ankle_pitch['asymmetric_events'] = asymmetry_events.ankle_pitch_summary.asymmetric_events
        ankle_pitch['percent_events_asymmetric'] = asymmetry_events.ankle_pitch_summary.percent_events_asymmetric

        record_out['ankle_pitch'] = ankle_pitch

        hip_drop = OrderedDict()
        hip_drop['left'] = asymmetry_events.hip_drop_summary.left
        hip_drop['right'] = asymmetry_events.hip_drop_summary.right
        hip_drop['symmetric_events'] = asymmetry_events.hip_drop_summary.symmetric_events
        hip_drop['asymmetric_events'] = asymmetry_events.hip_drop_summary.asymmetric_events
        hip_drop['percent_events_asymmetric'] = asymmetry_events.hip_drop_summary.percent_events_asymmetric

        record_out['hip_drop'] = hip_drop

        knee_valgus = OrderedDict()
        knee_valgus['left'] = asymmetry_events.knee_valgus_summary.left
        knee_valgus['right'] = asymmetry_events.knee_valgus_summary.right
        knee_valgus['symmetric_events'] = asymmetry_events.knee_valgus_summary.symmetric_events
        knee_valgus['asymmetric_events'] = asymmetry_events.knee_valgus_summary.asymmetric_events
        knee_valgus['percent_events_asymmetric'] = asymmetry_events.knee_valgus_summary.percent_events_asymmetric

        record_out['knee_valgus'] = knee_valgus

        hip_rotation = OrderedDict()
        hip_rotation['left'] = asymmetry_events.hip_rotation_summary.left
        hip_rotation['right'] = asymmetry_events.hip_rotation_summary.right
        hip_rotation['symmetric_events'] = asymmetry_events.hip_rotation_summary.symmetric_events
        hip_rotation['asymmetric_events'] = asymmetry_events.hip_rotation_summary.asymmetric_events
        hip_rotation['percent_events_asymmetric'] = asymmetry_events.hip_rotation_summary.percent_events_asymmetric

        record_out['hip_rotation'] = hip_rotation

        record_asymmetries = []

        for m in movement_events:
            event_record = OrderedDict()
            event_record['time_block'] = m.time_block
            event_record['start_time'] = m.start_time
            event_record['end_time'] = m.end_time

            apt_time_block = OrderedDict()
            apt_time_block['left'] = m.anterior_pelvic_tilt.left
            apt_time_block['right'] = m.anterior_pelvic_tilt.right
            apt_time_block['significant'] = m.anterior_pelvic_tilt.significant

            event_record['apt'] = apt_time_block

            ankle_pitch_time_block = OrderedDict()
            ankle_pitch_time_block['left'] = m.ankle_pitch.left
            ankle_pitch_time_block['right'] = m.ankle_pitch.right
            ankle_pitch_time_block['significant'] = m.ankle_pitch.significant

            event_record['ankle_pitch'] = ankle_pitch_time_block

            hip_drop_time_block = OrderedDict()
            hip_drop_time_block['left'] = m.hip_drop.left
            hip_drop_time_block['right'] = m.hip_drop.right
            hip_drop_time_block['significant'] = m.hip_drop.significant

            event_record['hip_drop'] = hip_drop_time_block

            knee_valgus_time_block = OrderedDict()
            knee_valgus_time_block['left'] = m.knee_valgus.left
            knee_valgus_time_block['right'] = m.knee_valgus.right
            knee_valgus_time_block['significant'] = m.knee_valgus.significant

            event_record['knee_valgus'] = knee_valgus_time_block

            hip_rotation_time_block = OrderedDict()
            hip_rotation_time_block['left'] = m.hip_rotation.left
            hip_rotation_time_block['right'] = m.hip_rotation.right
            hip_rotation_time_block['significant'] = m.hip_rotation.significant

            event_record['hip_rotation'] = hip_rotation_time_block

            record_asymmetries.append(event_record)

        record_out['time_blocks'] = record_asymmetries

        return record_out
