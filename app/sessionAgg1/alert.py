import boto3
import json
import logging
import os


logger = logging.getLogger()


class Alert(object):

    def __init__(self, user_id, team_id, training_group_ids, event_date, session_type, category, subcategory, granularity, value):
        self.user_id = user_id
        self.team_id = team_id
        self.training_group_ids = training_group_ids
        self.event_date = event_date
        self.session_type = int(session_type)
        self.category = int(category)
        self.subcategory = int(subcategory)
        self.granularity = granularity
        self.value = float(value)

    def json_serialise(self):
        ret = {
            'userId': self.user_id,
            'teamId': self.team_id,
            'trainingGroupIds': self.training_group_ids,
            'eventDate': self.event_date,
            'sessionType': self.session_type,
            'category': self.category,
            'subcategory': self.subcategory,
            'granularity': self.granularity,
            'value': str(self.value),
        }

        return ret

    @property
    def training_group_id(self):
        return self.training_group_ids[0] if len(self.training_group_ids) else None

    def publish(self):
        sns_client = boto3.client('sns')
        sns_topic = 'arn:aws:sns:{}:887689817172:alerts-{}-trigger'.format(
            os.environ['AWS_DEFAULT_REGION'],
            os.environ['ENVIRONMENT']
        )
        payload = {'alert': self.json_serialise(), 'session_id': os.environ['SESSION_ID']}
        print(payload)
#        response = sns_client.publish(TopicArn=sns_topic, Message=json.dumps(payload))
#        logger.info("SNS Message ID: {}".format(response.get('MessageId', None)))
