from abc import abstractmethod, ABCMeta
from aws_xray_sdk.core import xray_recorder
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from decimal import Decimal
from datetime import datetime
import boto3
import os

from exceptions import DuplicateEntityException
from models.session import Session


class Datastore(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self, event_date, status=None, user_id=None, team_id=None, training_group_id=None):
        pass

    @abstractmethod
    def put(self, alerts):
        pass


class DynamodbDatastore(Datastore):

    def put(self, items, allow_patch=False):
        if not isinstance(items, list):
            items = [items]
        try:
            for item in items:
                self._put_dynamodb(item, allow_patch)
        except ClientError as e:
            if 'ConditionalCheckFailed' in str(e) and not allow_patch:
                raise DuplicateEntityException
            raise e

    def _query_dynamodb(self, index_name, key_condition_expression, filter_expression=None, exclusive_start_key=None):
        # This nasty splatting is required because boto3 chokes on trying to set things like IndexName to None if you
        # don't want an index, you have to not pass the parameter at all
        ret = self._get_dynamodb_resource().query(**{k: v for k, v in {
            'IndexName': index_name if index_name else None,
            'Select': 'ALL_ATTRIBUTES',
            'Limit': 10000,
            'ConsistentRead': False,
            'ReturnConsumedCapacity': 'INDEXES',
            'KeyConditionExpression': key_condition_expression,
            'FilterExpression': filter_expression,
            'ExclusiveStartKey': exclusive_start_key,
        }.items() if v is not None})

        # TODO make use of the metrics in ret['Count'] vs ret['ScannedCount'], and ret['ConsumedCapacity']

        if 'LastEvaluatedKey' in ret:
            # There are more records to be scanned
            items = ret['Items'] + self._query_dynamodb(index_name, key_condition_expression, filter_expression, ret['LastEvaluatedKey'])
        else:
            # No more items
            items = ret['Items']

        return [self.item_from_dynamodb(item) for item in items]

    def _put_dynamodb(self, item, allow_patch=False):
        item = self.item_to_dynamodb(item)
        cx = Attr('id').not_exists() | Attr('id').exists() if allow_patch else Attr('id').not_exists()
        response = self._get_dynamodb_resource().put_item(
            Item=item,
            ReturnConsumedCapacity='INDEXES',
            ReturnItemCollectionMetrics='SIZE',
            ConditionExpression=cx,
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

    @xray_recorder.capture('datastore.DynamodbDatastore.get')
    def get(self, *, session_id=None, event_date=None, status=None, user_id=None, team_id=None, training_group_id=None):
        if session_id is not None:
            kcx = Key('id').eq(session_id)
            fx = Attr('session_status').exists()
            index_name = None

        else:
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

    @staticmethod
    def item_to_dynamodb(session):
        item = {
            'id': session.get_id(),
            'user_id': session.user_id,
            'user_mass': Decimal(session.user_mass),
            'team_id': session.team_id,
            'training_group_ids': session.training_group_ids,
            'event_date': session.event_date,
            'session_status': session.session_status,
            'created_date': session.created_date,
            'updated_date': datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            'version': session.version,
            's3_files': session.s3_files,
        }

        return {k: v for k, v in item.items() if v}

    @staticmethod
    def item_from_dynamodb(item):
        session = Session(
            session_id=item['id'],
            event_date=item.get('event_date', item.get('eventDate', None)),
            created_date=item.get('created_date', item.get('createdDate', None)),
            updated_date=item.get('updated_date', item.get('updatedDate', None)),
            session_status=item.get('session_status', item.get('sessionStatus', None)),
            version=item.get('version', None),
            s3_files=item.get('s3_files', item.get('s3Files', None)),
        )
        session.user_id = item.get('user_id', item.get('userId', None))
        session.user_mass = item.get('user_mass', item.get('userMass', None))
        session.team_id = item.get('team_id', item.get('teamId', None))
        session.training_group_ids = item.get('training_group_ids', item.get('trainingGroupId', None))
        return session

    @property
    def _dynamodb_table_name(self):
        return 'preprocessing-{}-ingest-sessions'.format(os.environ['ENVIRONMENT'])
