from aws_xray_sdk.core import xray_recorder
from pymongo import MongoClient
import os
import json
import boto3
from botocore.exceptions import ClientError


client = boto3.client('secretsmanager')


@xray_recorder.capture('app.config.get_mongo_config')
def get_mongo_config():
    keys = ['host', 'replicaset', 'user', 'password', 'database']
    config = {k.lower(): os.environ.get('MONGO_{}'.format(k.upper()), None) for k in keys}
    return config


@xray_recorder.capture('app.config.get_mongo_database')
def get_mongo_database():
    config = get_mongo_config()
    mongo_client = MongoClient(
        config['host'],
        replicaset=config['replicaset'] if config['replicaset'] != '---' else None,
        ssl=True,
        serverSelectionTimeoutMS=10000,
    )
    database = mongo_client[config['database']]
    database.authenticate(config['user'], config['password'], mechanism='SCRAM-SHA-1', source='admin')

    return database


@xray_recorder.capture('app.config.get_mongo_collection')
def get_mongo_collection(collection, collection_override=None):
    database = get_mongo_database()
    mongo_collection = os.environ['MONGO_COLLECTION_' + collection.upper()]
    return database[collection_override if collection_override is not None else mongo_collection]


@xray_recorder.capture('app.config.get_secret')
def get_secret(secret_name):
    try:
        secret_name = '/'.join(['preprocessing', os.environ['ENVIRONMENT'], secret_name])
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise Exception('SecretsManagerError', json.dumps(e.response), 500)
    else:
        if 'SecretString' in get_secret_value_response:
            return json.loads(get_secret_value_response['SecretString'])
        else:
            return get_secret_value_response['SecretBinary']


@xray_recorder.capture('app.config.load_parameters')
def load_parameters(keys, secret_name):
    keys_to_load = [key for key in keys if key.upper() not in os.environ]
    if len(keys_to_load) > 0:
        print('Retrieving configuration for [{}] from SecretsManager'.format(", ".join(keys_to_load)))
        params = get_secret(secret_name)
        # Export to environment
        for k in keys_to_load:
            os.environ[k.upper()] = params[k.lower()]
            print("Got value for {} from SecretsManager".format(k))
