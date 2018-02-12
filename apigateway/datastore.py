from session import Session
from abc import abstractmethod, ABCMeta
from aws_xray_sdk.core import xray_recorder
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
from datetime import datetime
import boto3
import os


class Datastore(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self, event_date, status=None, user_id=None, team_id=None, training_group_id=None):
        pass

    @abstractmethod
    def put(self, alerts):
        pass


class DynamodbDatastore(Datastore):
    @xray_recorder.capture('datastore.DynamodbDatastore.get')
    def get(self, event_date, status=None, user_id=None, team_id=None, training_group_id=None):
        if isinstance(event_date, tuple):
            kcx = Key('eventDate').between(event_date[0], event_date[1])
        else:
            kcx = Key('eventDate').eq(event_date)

        if user_id is not None:
            kcx = kcx & Key('userId').eq(user_id)
            index_name = 'userId-eventDate'
        elif team_id is not None:
            kcx = kcx & Key('teamId').eq(team_id)
            index_name = 'teamId-eventDate'
        elif training_group_id is not None:
            kcx = kcx & Key('trainingGroupId').eq(training_group_id)
            index_name = 'trainingGroupId-eventDate'
        else:
            raise Exception('One of user_id, team_id, training_group_id must be specified')

        if status is not None:
            fx = Attr('sessionStatus').eq(status)
        else:
            fx = Attr('sessionStatus').exists()

        return self._query_dynamodb(index_name, key_condition_expression=kcx, filter_expression=fx)

    def put(self, alerts):
        if not isinstance(alerts, list):
            alerts = [alerts]
        for alert in alerts:
            self._put_dynamodb(alert)

    def _query_dynamodb(self, index_name, key_condition_expression, filter_expression=None, exclusive_start_key=None):
        ret = self._get_dynamodb_resource().query(
            IndexName=index_name if index_name else None,
            Select='ALL_ATTRIBUTES',
            Limit=10000,
            ConsistentRead=False,
            ReturnConsumedCapacity='INDEXES',
            KeyConditionExpression=key_condition_expression,
            FilterExpression=filter_expression,
            # ExclusiveStartKey=exclusive_start_key,
        )

        # TODO make use of the metrics in ret['Count'] vs ret['ScannedCount'], and ret['ConsumedCapacity']

        if 'LastEvaluatedKey' in ret:
            # There are more records to be scanned
            # TODO
            raise Exception('Not supported')
            # items = ret['Items'] + self._query_dynamodb(index_name, key_condition_expression, filter_expression, ret['LastEvaluatedKey'])
        else:
            # No more items
            items = ret['Items']

        return [self.item_from_dynamodb(item) for item in items]

    def _put_dynamodb(self, alert):
        item = self.item_to_dynamodb(alert)
        response = self._get_dynamodb_resource().put_item(
            Item=item,
            ReturnConsumedCapacity='INDEXES',
            ReturnItemCollectionMetrics='SIZE',
            ConditionExpression=Attr('id').not_exists(),
        )

        # TODO make use of the metrics in response['ConsumedCapacity']

    @staticmethod
    @abstractmethod
    def item_to_dynamodb(item):
        pass

    @staticmethod
    @abstractmethod
    def item_from_dynamodb(item):
        pass

    def _get_dynamodb_resource(self):
        # TODO maybe cache this if performance impact is noticeable
        return boto3.resource('dynamodb').Table(str(self._dynamodb_table_name))

    @property
    @abstractmethod
    def _dynamodb_table_name(self):
        pass


class SessionDatastore(DynamodbDatastore):
    @staticmethod
    def item_to_dynamodb(session):
        item = {
            'id': session.session_id,
            'userId': session.user_id,
            'teamId': session.team_id,
            'trainingGroupIds': session.training_group_ids,
            'eventDate': session.event_date,
            'sessionStatus': session.session_status,
            'createdDate': session.created_date,
            'updatedDate': datetime.now().isoformat()[:-6] + 'Z',
            'version': session.version,
            's3Files': session.s3_files,
        }

        return item

    @staticmethod
    def item_from_dynamodb(item):
        return Session(
            session_id=item['id'],
            user_id=item.get('userId', None),
            team_id=item.get('teamId', None),
            training_group_ids=item.get('trainingGroupId', None),
            event_date=item.get('eventDate', None),
            session_status=item.get('sessionStatus', None),
            created_date=item.get('createdDate', None),
            updated_date=item.get('updatedDate', None),
            version=item.get('version', None),
            s3_files=item.get('s3Files', None),
        )

    @property
    def _dynamodb_table_name(self):
        return 'preprocessing-{}-ingest-sessions'.format(os.environ['ENVIRONMENT'])
