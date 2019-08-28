from aws_xray_sdk.core import xray_recorder
xray_recorder.configure(sampling=False)
xray_recorder.begin_segment(name="test")
from config import load_parameters
load_parameters([
            'MONGO_HOST',
            'MONGO_USER',
            'MONGO_PASSWORD',
            'MONGO_DATABASE',
            'MONGO_REPLICASET',
            'MONGO_COLLECTION_ACTIVEBLOCKS',
            'MONGO_COLLECTION_ASYMMETRY',
        ], 'mongo')
from config import get_mongo_collection


def clear_user(user_id, suffix='Test'):
    asymmetry = get_mongo_collection('asymmetry')

    asymmetry.delete_many({"user_id": user_id})