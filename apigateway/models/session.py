from serialisable import Serialisable
import uuid


class Session(Serialisable):

    def __init__(self, *,
                 event_date,
                 session_status,
                 created_date,
                 updated_date,
                 session_id=None,
                 version='2.3',
                 s3_files=None
                 ):
        self.session_id = session_id
        self.event_date = event_date
        self.session_status = session_status
        self.created_date = created_date
        self.updated_date = updated_date
        self.version = version
        self.s3_files = s3_files

        self.user_id = None
        self.user_mass = None
        self.team_id = None
        self.training_group_ids = set()

    def get_id(self):
        return self.session_id or self._generate_uuid()

    def _generate_uuid(self):
        unique_key = 'http://session.fathomai.com/{}_{}_{}_{}'.format(
            self.user_id,
            self.event_date,
        )
        return str(uuid.uuid5(uuid.NAMESPACE_URL, unique_key))

    def json_serialise(self):
        ret = {
            'id': self.get_id(),
            'user_id': self.user_id,
            'user_mass': self.user_mass,
            'team_id': self.team_id,
            'training_group_ids': self.training_group_ids,
            'event_date': self.event_date,
            'session_status': self.session_status,
            'created_date': self.created_date,
            'updated_date': self.updated_date,
        }
        return ret
