from serialisable import Serialisable
from decimal import Decimal


class Session(Serialisable):

    def __init__(self, *,
                 session_id,
                 user_id,
                 team_id,
                 training_group_ids,
                 event_date,
                 session_status,
                 created_date,
                 updated_date,
                 version,
                 s3_files
                 ):
        self.session_id = session_id
        self.user_id = user_id
        self.team_id = team_id
        self.training_group_ids = training_group_ids
        self.event_date = event_date
        self.session_status = session_status
        self.created_date = created_date
        self.updated_date = updated_date
        self.version = version
        self.s3_files = s3_files

    def json_serialise(self):
        ret = {
            'id': self.session_id,
            'user_id': self.user_id,
            'team_id': self.team_id,
            'training_group_ids': self.training_group_ids,
            'event_date': self.event_date,
            'session_status': self.session_status,
            'created_date': self.created_date,
            'updated_date': self.updated_date,
            # 'version': self.version,
            # 's3_files': self.s3_files,
        }
        return ret
