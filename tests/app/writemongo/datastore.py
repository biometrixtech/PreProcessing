from datastore import Datastore


class MockDatastore(Datastore):
    def __init__(self, session_id, event_date, user_id):
        try:
            super().__init__(session_id)
        except NotADirectoryError:
            pass  # Exception caused by nonexistent /net/efs/preprocessing directory
        self._metadata = {'event_date': event_date, 'user_id': user_id}

    def get_metadatum(self, datum, default=NotImplemented):
        if datum in self._metadata:
            return self._metadata[datum]
        raise NotImplementedError
