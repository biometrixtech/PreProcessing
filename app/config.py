from pymongo import MongoClient
import os


def get_mongo_config(instance):
    keys = ['host', 'replicaset', 'user', 'password']
    config = {k.lower(): os.environ['MONGO_{}_{}'.format(k.upper(), instance.upper())] for k in keys}
    return config


def get_mongo_database(instance):
    config = get_mongo_config(instance)
    mongo_client = MongoClient(
        config['host'],
        authSource='admin',
        mechanism='SCRAM-SHA-1',
        password=config['password'],
        replicaset=config['replicaset'] if config['replicaset'] != '---' else None,
        ssl=True,
        username=config['user'],
    )

    return mongo_client[config['database']]


def get_mongo_collection(instance, collection_override=None):
    config = get_mongo_config(instance)
    database = get_mongo_database(instance)
    return database[collection_override if collection_override is not None else config['collection']]
