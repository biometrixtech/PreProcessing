from datetime import datetime
import pandas as pd

from ._unit_block_job import UnitBlockJob
from utils import parse_datetime


class SummaryAnalysisJob(UnitBlockJob):

    def _run(self):
        data = self._query_mongo_ab()

        self.datastore.put_data(self.name, data)
        self.datastore.copy_to_s3(self.name, "advanced-stats", '_'.join([self.event_date, self.user_id]) + "/ab.csv")

    def _query_mongo_ab(self):
        block_count = 0
        event_date = None
        current_session_start_time = datetime.now()

        data = pd.DataFrame()

        for block in self._unit_blocks:

            block_start_time = parse_datetime(block.get('timeStart'))
            block_end_time = parse_datetime(block.get('timeEnd'))
            if event_date != block.get('eventDate'):
                # Starting a new date, reset the block count
                block_count = 0
                current_session_start_time = parse_datetime(block.get('timeStart'))
            else:
                block_count += 1

            cumulative_start_time = (block_start_time - current_session_start_time).seconds
            cumulative_end_time = (block_end_time - current_session_start_time).seconds

            obj_id = str(block.get('_id'))
            event_date = block.get('eventDate')

            contact_duration_lf = block.get('contactDurationLF')
            contact_duration_rf = block.get('contactDurationRF')
            peak_grf_lf = block.get('peakGrfLF')
            peak_grf_rf = block.get('peakGrfRF')

            if contact_duration_lf is not None and contact_duration_rf is not None:
                contact_duration_perc_diff_lf_rf = abs(contact_duration_lf-contact_duration_rf) / max(contact_duration_lf, contact_duration_rf)
            else:
                contact_duration_perc_diff_lf_rf = None

            if peak_grf_lf is not None and peak_grf_rf is not None:
                peak_grf_perc_diff_lf_rf = abs(peak_grf_lf-peak_grf_rf) / max(peak_grf_lf, peak_grf_rf)
            else:
                peak_grf_perc_diff_lf_rf = None

            data = data.append(pd.DataFrame(
                {
                    'userId': [self.user_id],
                    'eventDate': [event_date],
                    'activeBlock': [obj_id],
                    'abNum': [block_count],
                    'timeStart': [(block_start_time.time().strftime("%H:%M:%S"))],
                    'timeEnd': [(block_end_time.time().strftime("%H:%M:%S"))],
                    'cumulative_end_time': [cumulative_end_time],
                    'cumulative_start_time': [cumulative_start_time],
                    'duration': [block.get('duration')],
                    'totalAccelAvg': [block.get('totalAccelAvg')],
                    'contactDurationLF': [contact_duration_lf],
                    'contactDurationRF': [contact_duration_rf],
                    'contactDurationPercDiffLFRF': [contact_duration_perc_diff_lf_rf],
                    'peakGrfLF': [peak_grf_lf],
                    'peakGrfRF': [peak_grf_rf],
                    'peakGRFPercDiffLFRF': [peak_grf_perc_diff_lf_rf],
                    'percOptimal': [block.get('percOptimal')],
                    'totalGRF': [block.get('totalGRF')],
                    'totalGRFAvg': [block.get('totalGRFAvg')],
                    #'optimalGRF': [block.get('optimalGRF')],
                    #'irregularGRF': [block.get('irregularGRF')],
                    'LFgRF': [block.get('LFgRF')],
                    'RFgRF': [block.get('RFgRF')],
                    'leftGRF': [block.get('leftGRF')],
                    'rightGRF': [block.get('rightGRF')],
                    'singleLegGRF': [block.get('singleLegGRF')],
                    'percLeftGRF': [block.get('percLeftGRF')],
                    'percRightGRF': [block.get('percRightGRF')],
                    'percLRGRFDiff': [block.get('percLRGRFDiff')],
                    'totalAccel': [block.get('totalAccel')]
                    #'irregularAccel': [block.get('irregularAccel')]
                }))

            return data
