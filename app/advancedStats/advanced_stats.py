from __future__ import print_function

from config import get_mongo_collection
import complexity_symmetry
import summary_analysis

def script_handler(input_data):
    print("Running Advanced aggregations")

    try:
        mongo_collection_blocks = get_mongo_collection('ACTIVEBLOCKS')

        user_id = input_data.get('UserId', None)
        event_date = input_data.get('EventDate')

    except Exception as e:
        print(e)
        print('Process did not complete successfully! See error below!')
        raise
