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
        ], 'mongo')
import pandas

from tests.app.writemongo.datastore import MockDatastore
from jobs.advancedstats import get_unit_blocks
from jobs.advancedstats.summary_analysis_job import SummaryAnalysisJob
from jobs.advancedstats.training_volume_job import TrainingVolumeJob


# noinspection PyProtectedMember
def test_get_active_blocks():
    athlete = "Maggie"
    date = "2018-04-24"
    unit_blocks = get_unit_blocks(athlete, date)
    ds = MockDatastore(athlete, date, None)
    active_blocks = SummaryAnalysisJob(ds, unit_blocks)._query_mongo_ab()

    assert len(active_blocks) > 0


# noinspection PyProtectedMember
def test_get_intensity_matrix():
    athlete = "Maggie"
    date = "2018-04-24"
    unit_blocks = get_unit_blocks(athlete, date)
    ds = MockDatastore(athlete, date, None)
    td = TrainingVolumeJob(ds, unit_blocks)._calculate_training_volume()

    # optional output to csv
    # training_data = pandas.DataFrame({
    #     'accumulated_grf': [td.accumulated_grf],
    #     'cma': [td.cma],
    #     'active_time': [td.active_time],
    #     'gct_left': [td.ground_contact_time_left],
    #     'gct_right': [td.ground_contact_time_right],
    #     'avg_peak_grf_left': [td.average_peak_vertical_grf_lf],
    #     'avg_peak_grf_right': [td.average_peak_vertical_grf_rf],
    #     'avg_grf': [td.average_total_GRF],
    #     'agg_peak_accel': [td.average_peak_acceleration],
    #
    # }, index=["Summary"])
    #
    # training_data.to_csv('~/decay/session_workload_summary' + athlete + '_' + date + '.csv', sep=',', index_label='Level')

    assert td.accumulated_grf > 0
    assert td.active_time > 0
    assert td.average_peak_vertical_grf_lf > 0
    assert td.cma > 0
    assert td.grf_bands.total.cma_percentage == 100.0
    assert td.intensity_bands.total.cma_percentage == 100.0
    assert td.left_right_bands.total.cma_percentage == 100.0
    assert td.stance_bands.total.cma_percentage == 100.0


# noinspection PyProtectedMember
def test_get_intensity_bands():
    athlete = "Maggie"
    date = "2018-04-24"
    unit_blocks = get_unit_blocks(athlete, date)
    ds = MockDatastore(athlete, date, None)
    td = TrainingVolumeJob(ds, unit_blocks)._calculate_training_volume()

    # optional output to csv
    # intensity_df = pandas.DataFrame()
    #
    # intensity_df = intensity_df.append(convert_intensity_band_to_csv(td.intensity_bands.low))
    # intensity_df = intensity_df.append(convert_intensity_band_to_csv(td.intensity_bands.moderate))
    # intensity_df = intensity_df.append(convert_intensity_band_to_csv(td.intensity_bands.high))
    # intensity_df = intensity_df.append(convert_intensity_band_to_csv(td.intensity_bands.total))
    #
    # columns = [
    #     # 'complexity_level',
    #     'seconds',
    #     'seconds_percentage',
    #     'cma',
    #     'cma_percentage',
    #     'accumulated_grf',
    #     'accumulated_grf_percentage',
    #     'left_cumulative_average_peak_vGRF',
    #     'right_cumulative_average_peak_vGRF',
    #     'left_cumulative_average_GRF',
    #     'right_cumulative_average_GRF',
    #     'left_cumulative_average_accel',
    #     'right_cumulative_average_accel',
    #     'left_gct',
    #     'right_gct',
    #     'left_gct_percentage',
    #     'right_gct_percentage',
    #
    # ]
    # intensity_df.to_csv(
    #     '~/decay/session_intensity_bands' + athlete + '_' + date + '.csv',
    #     sep=',',
    #     index_label='Level',
    #     columns=columns)

    assert td.accumulated_grf > 0
    assert td.active_time > 0
    assert td.average_peak_vertical_grf_lf > 0
    assert td.cma > 0
    assert td.grf_bands.total.cma_percentage == 100.0
    assert td.intensity_bands.total.cma_percentage == 100.0
    assert td.left_right_bands.total.cma_percentage == 100.0
    assert td.stance_bands.total.cma_percentage == 100.0


def convert_intensity_band_to_csv(t):
        ab = pandas.DataFrame({
            'seconds': [t.seconds],
            'seconds_percentage': [t.seconds_percentage],
            'cma': [t.cma],
            'cma_percentage': [t.cma_percentage],
            'accumulated_grf': [t.accumulated_grf],
            'accumulated_grf_percentage': [t.accumulated_grf_percentage],
            'left_cumulative_average_peak_vGRF': [t.left.cumulative_average_peak_vGRF],
            'right_cumulative_average_peak_vGRF': [t.right.cumulative_average_peak_vGRF],
            'left_cumulative_average_GRF': [t.left.cumulative_average_GRF],
            'right_cumulative_average_GRF': [t.right.cumulative_average_GRF],
            'left_cumulative_average_accel': [t.left.cumulative_average_accel],
            'right_cumulative_average_accel': [t.right.cumulative_average_accel],
            'left_gct': [t.left.gct],
            'right_gct': [t.right.gct],
            'left_gct_percentage': [t.left.gct_percentage],
            'right_gct_percentage': [t.right.gct_percentage],
        }, index=[t.descriptor])

        return ab
