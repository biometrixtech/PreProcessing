from collections import OrderedDict


class PlansFactory(object):
    def __init__(self, plans_api_version, environment, user_id, event_date, session_id, seconds_duration, asymmetry_events, end_date=None):
        self.plans_api_version = plans_api_version
        self.environment = environment
        self.user_id = user_id
        self.event_date = event_date
        self.end_date = end_date
        self.session_id = session_id
        self.seconds_duration = seconds_duration
        self.asymmetry_events = asymmetry_events
        self.latest_plans_version = "4_5"

    def get_plans(self):
        if self.plans_api_version == "4_4":
            return Plans_4_4(self.environment, self.user_id, self.event_date, self.session_id, self.seconds_duration,
                             self.asymmetry_events)
        elif self.plans_api_version == "4_5":
            return Plans_4_5(self.environment, self.user_id, self.event_date,self.session_id, self.seconds_duration,
                             self.asymmetry_events, end_date=self.end_date)
        else:
            return Plans_4_3(self.environment, self.user_id, self.event_date, self.session_id, self.seconds_duration,
                             self.asymmetry_events)


class PlansBase(object):
    def __init__(self, environment, user_id, event_date, session_id, seconds_duration, asymmetry_events):
        self.environment = environment
        self.user_id = user_id
        self.event_date = event_date
        self.session_id = session_id
        self.seconds_duration = seconds_duration
        self.asymmetry_events = asymmetry_events

    def get_mongo_asymmetry_record(self, movement_events):
        pass


class Plans_4_4(PlansBase):
    def __init__(self, environment, user_id, event_date, session_id, seconds_duration, asymmetry_events):
        super().__init__(environment, user_id, event_date, session_id, seconds_duration, asymmetry_events)
        self.endpoint = f'https://apis.{self.environment}.fathomai.com/plans/4_4/session/{user_id}/three_sensor_data'
        self.body = {
                'event_date': event_date,
                "session_id": session_id,
                "seconds_duration": seconds_duration,
                "asymmetry": {
                    "left_apt": asymmetry_events.anterior_pelvic_tilt_summary.left,
                    "right_apt": asymmetry_events.anterior_pelvic_tilt_summary.right,
                    "asymmetric_events": asymmetry_events.anterior_pelvic_tilt_summary.asymmetric_events,
                    "symmetric_events": asymmetry_events.anterior_pelvic_tilt_summary.symmetric_events,
                }
            }

    def get_mongo_asymmetry_record(self, movement_events):

        user_id = self.user_id

        record_out = OrderedDict()
        record_out['user_id'] = user_id
        record_out['event_date'] = self.event_date

        record_out['session_id'] = self.session_id
        record_out['left_apt'] = self.asymmetry_events.anterior_pelvic_tilt_summary.left
        record_out['right_apt'] = self.asymmetry_events.anterior_pelvic_tilt_summary.right

        record_out['symmetric_events'] = self.asymmetry_events.anterior_pelvic_tilt_summary.symmetric_events
        record_out['asymmetric_events'] = self.asymmetry_events.anterior_pelvic_tilt_summary.asymmetric_events
        record_out['percent_events_asymmetric'] = self.asymmetry_events.anterior_pelvic_tilt_summary.percent_events_asymmetric
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
    def __init__(self, environment, user_id, event_date, session_id, seconds_duration, asymmetry_events):
        super().__init__(environment, user_id, event_date, session_id, seconds_duration, asymmetry_events)
        self.endpoint = f'https://apis.{self.environment}.fathomai.com/plans/4_3/session/three_sensor_data'
        self.body['user_id'] = user_id


class Plans_4_5(PlansBase):
    def __init__(self, environment, user_id, event_date, session_id, seconds_duration, asymmetry_events, end_date):
        super().__init__(environment, user_id, event_date, session_id, seconds_duration, asymmetry_events)
        self.endpoint = f'https://apis.{self.environment}.fathomai.com/plans/4_5/session/{user_id}/three_sensor_data'
        self.body = {
                    'event_date': event_date,
                    "session_id": session_id,
                    "seconds_duration": seconds_duration,
                    "end_date": end_date,
                    "asymmetry": {
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
                            }
                        }
                    }

    def get_mongo_asymmetry_record(self, movement_events):

        record_out = OrderedDict()
        record_out['user_id'] = self.user_id
        record_out['event_date'] = self.event_date
        record_out['seconds_duration'] = self.seconds_duration
        record_out['session_id'] = self.session_id

        # sym_count = [m for m in movement_events if not m.significant and (m.left_median > 0 or m.right_median > 0)]
        # asym_count = [m for m in movement_events if m.significant and (m.left_median > 0 or m.right_median > 0)]

        anterior_pelivic_tilt = OrderedDict()
        anterior_pelivic_tilt['left'] = self.asymmetry_events.anterior_pelvic_tilt_summary.left
        anterior_pelivic_tilt['right'] = self.asymmetry_events.anterior_pelvic_tilt_summary.right
        anterior_pelivic_tilt['symmetric_events'] = self.asymmetry_events.anterior_pelvic_tilt_summary.symmetric_events
        anterior_pelivic_tilt['asymmetric_events'] = self.asymmetry_events.anterior_pelvic_tilt_summary.asymmetric_events
        anterior_pelivic_tilt[
            'percent_events_asymmetric'] = self.asymmetry_events.anterior_pelvic_tilt_summary.percent_events_asymmetric

        record_out['apt'] = anterior_pelivic_tilt

        ankle_pitch = OrderedDict()
        ankle_pitch['left'] = self.asymmetry_events.ankle_pitch_summary.left
        ankle_pitch['right'] = self.asymmetry_events.ankle_pitch_summary.right
        ankle_pitch['symmetric_events'] = self.asymmetry_events.ankle_pitch_summary.symmetric_events
        ankle_pitch['asymmetric_events'] = self.asymmetry_events.ankle_pitch_summary.asymmetric_events
        ankle_pitch['percent_events_asymmetric'] = self.asymmetry_events.ankle_pitch_summary.percent_events_asymmetric

        record_out['ankle_pitch'] = ankle_pitch

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

            record_asymmetries.append(event_record)

        record_out['time_blocks'] = record_asymmetries

        return record_out
