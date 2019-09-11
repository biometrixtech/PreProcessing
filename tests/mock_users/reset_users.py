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
            'MONGO_COLLECTION_ASYMMETRYRESERVE',
            'MONGO_COLLECTION_SESSIONASYMMETRYRESERVE',
        ], 'mongo')
from config import get_mongo_collection


def clear_user(user_id, suffix='Test'):
    asymmetry = get_mongo_collection('asymmetry')
    asymmetry_reserve = get_mongo_collection('asymmetryreserve')
    session_asymmetry_reserve = get_mongo_collection('sessionasymmetryreserve')

    asymmetry.delete_many({"user_id": user_id})
    asymmetry_reserve.delete_many({"user_id": user_id})
    session_asymmetry_reserve.delete_many({"user_id": user_id})