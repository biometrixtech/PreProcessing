from pymongo import MongoClient
import os


def get_mongo_config(instance):
    keys = ['host', 'replicaset', 'user', 'password', 'database', 'collection']
    config = {k.lower(): os.environ.get('MONGO_{}_{}'.format(k.upper(), instance.upper()), None) for k in keys}
    return config


def get_mongo_database(instance):
    config = get_mongo_config(instance)
    mongo_client = MongoClient(
        config['host'],
        replicaset=config['replicaset'] if config['replicaset'] != '---' else None,
        ssl=True,
    )
    database = mongo_client[config['database']]
    database.authenticate(config['user'], config['password'], mechanism='SCRAM-SHA-1', source='admin')

    return database


def get_mongo_collection(instance, collection_override=None):
    config = get_mongo_config(instance)
    database = get_mongo_database(instance)
    return database[collection_override if collection_override is not None else config['collection']]
