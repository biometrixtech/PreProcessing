from datastore import Datastore


class MockDatastore(Datastore):
    def __init__(self, session_id, event_date, user_id):
        try:
            super().__init__(session_id)
        except NotADirectoryError:
            pass  # Exception caused by nonexistent /net/efs/preprocessing directory
        self._metadata = {'event_date': event_date, 'user_id': user_id}
        self.side_loaded_data = None

    def get_metadatum(self, datum, default=NotImplemented):
        if datum in self._metadata:
            return self._metadata[datum]
        raise NotImplementedError

    def get_data(self, source_job, columns=None):
        return self.side_loaded_data

    def put_data(self, source_job, data, columns=None, chunk_size=0, is_binary=False):
        self.side_loaded_data = data

    def put_metadata(self, data):
        for key, value in data.items():
            self._metadata[key] = value
