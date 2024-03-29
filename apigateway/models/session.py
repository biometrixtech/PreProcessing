import boto3
import uuid

from fathomapi.api.config import Config
from fathomapi.models.dynamodb_entity import DynamodbEntity


class Session(DynamodbEntity):
    _dynamodb_table_name = 'preprocessing-{}-ingest-sessions'.format(Config.get('ENVIRONMENT'))

    def __init__(self, session_id):
        super().__init__({'id': session_id})

    @staticmethod
    def generate_uuid(body):
        unique_key = 'http://session.fathomai.com/{}_{}_{}_{}'.format(
            body.get('accessory_id'),
            ','.join(sorted(body.get('sensor_ids', []))),
            body.get('user_id'),
            body.get('event_date'),
        )
        return str(uuid.uuid5(uuid.NAMESPACE_URL, unique_key))
