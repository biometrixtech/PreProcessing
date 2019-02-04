from pymongo import ASCENDING
import logging

from ..job import Job
from config import get_mongo_collection

_logger = logging.getLogger()


class AdvancedstatsJob(Job):

    def _run(self):
        user_id = self.datastore.get_metadatum('user_id')
        event_date = self.datastore.get_metadatum('event_date')
        unit_blocks = get_unit_blocks(user_id, event_date)

        # Write out active blocks
        from .summary_analysis_job import SummaryAnalysisJob
        SummaryAnalysisJob(self.datastore, unit_blocks).run()

        from .training_volume_job import TrainingVolumeJob
        TrainingVolumeJob(self.datastore, unit_blocks).run()

        from .complexity_matrix_job import ComplexityMatrixJob
        ComplexityMatrixJob(self.datastore, unit_blocks).run()


def get_unit_blocks(user, date):
    """
    Load the unit blocks records from MongoDB
    :param user:
    :param date:
    :return:
    """
    collection = get_mongo_collection('ACTIVEBLOCKS')

    # unit_blocks = list(col.find({'userId': {'$eq': user},'eventDate':date},{'unitBlocks':1,'_id':0}))
    unit_blocks = list(collection.find(
        {'userId': {'$eq': user}, 'eventDate': date},
        {'unitBlocks': 1, '_id': 1, 'timeStart': 1, 'timeEnd': 1}).sort('unitBlocks.timeStart', direction=ASCENDING)
    )
    return unit_blocks
