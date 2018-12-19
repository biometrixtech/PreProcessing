import pandas
import advancedStats.logic.asymmetry_logic
from advancedStats.logic.training_volume_logic import TrainingVolumeProcessor
import app.advancedStats.summary_analysis as calc
from app.advancedStats.models.variable import CategorizationVariable


def test_get_unit_blocks():

    collection = ""
    athlete = ""
    date = ""
    output_path = ""

    calc.query_mongo_ub(collection, athlete, date, output_path)


def test_get_active_blocks():
    collection = ""
    athlete = "Maggie"
    date = "2018-04-24"
    output_path = "~/decay/"

    calc.query_mongo_ab(athlete, date, output_path)


def test_get_intensity_matrix():

    athlete = "Maggie"
    date = "2018-04-24"
    processor = TrainingVolumeProcessor()
    td = processor.get_session_training_volume_data(athlete, date)

    training_data = pandas.DataFrame({
        'accumulated_grf': [td.accumulated_grf],
        'cma': [td.cma],
        'active_time': [td.active_time],
        'gct_left': [td.ground_contact_time_left],
        'gct_right': [td.ground_contact_time_right],
        'avg_peak_grf_left': [td.average_peak_vertical_grf_lf],
        'avg_peak_grf_right': [td.average_peak_vertical_grf_rf],
        'avg_grf': [td.average_total_GRF],
        'agg_peak_accel': [td.average_peak_acceleration],

    }, index=["Summary"])

    training_data.to_csv('~/decay/session_workload_summary' + athlete + '_' + date + '.csv', sep=',',
                           index_label='Level')

def test_get_intensity_bands():

    athlete = "Maggie"
    date = "2018-04-24"
    processor = TrainingVolumeProcessor()
    td = processor.get_session_training_volume_data(athlete, date)

    intensity_df = pandas.DataFrame()

    intensity_df = intensity_df.append(convert_intensity_band_to_csv(td.intensity_bands.low))
    intensity_df = intensity_df.append(convert_intensity_band_to_csv(td.intensity_bands.moderate))
    intensity_df = intensity_df.append(convert_intensity_band_to_csv(td.intensity_bands.high))
    intensity_df = intensity_df.append(convert_intensity_band_to_csv(td.intensity_bands.total))

    intensity_df.to_csv('~/decay/session_intensity_bands' + athlete + '_' + date + '.csv', sep=',',
                           index_label='Level', columns = [
                                # 'complexity_level',
                                'seconds',
                                'seconds_percentage',
                                'cma',
                                'cma_percentage',
                                'accumulated_grf',
                                'accumulated_grf_percentage',
                                'left_cumulative_average_peak_vGRF',
                                'right_cumulative_average_peak_vGRF',
                                'left_cumulative_average_GRF',
                                'right_cumulative_average_GRF',
                                'left_cumulative_average_accel',
                                'right_cumulative_average_accel',
                                'left_gct',
                                'right_gct',
                                'left_gct_percentage',
                                'right_gct_percentage',

    ]
                        )

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

'''Legacy
def test_get_variable_matrix():

    athlete = "Maggie"
    date = "2018-04-24"
    var_list = []
    var_list.append(CategorizationVariable("peak_grf_perc_diff_lf", 0, 5, 5, 10, 10, 100, False))
    var_list.append(CategorizationVariable("peak_grf_perc_diff_rf", 0, 5, 5, 10, 10, 100, False))
    var_list.append(CategorizationVariable("gct_perc_diff_lf", 0, 5, 5, 10, 10, 100, False))
    var_list.append(CategorizationVariable("gct_perc_diff_rf", 0, 5, 5, 10, 10, 100, False))
    var_list.append(CategorizationVariable("peak_grf_gct_left_over", 0, 2.5, 2.5, 5, 5, 100, False))
    var_list.append(CategorizationVariable("peak_grf_gct_left_under", 0, 2.5, 2.5, 5, 5, 10, False))
    var_list.append(CategorizationVariable("peak_grf_gct_right_over", 0, 2.5, 2.5, 5, 5, 100, False))
    var_list.append(CategorizationVariable("peak_grf_gct_right_under", 0, 2.5, 2.5, 5, 5, 10, False))
    #var_list.append(CategorizationVariable("hip_control", 85, 100, 70, 85, 0, 70, True))
    #var_list.append(CategorizationVariable("control_lf", 85, 100, 70, 85, 0, 70, True))
    #var_list.append(CategorizationVariable("control_rf", 85, 100, 70, 85, 0, 70, True))
    #var_list.append(CategorizationVariable("symmetry", 85, 100, 70, 85, 0, 70, True))
    #var_list.append(CategorizationVariable("hip_symmetry", 85, 100, 70, 85, 0, 70, True))
    #var_list.append(CategorizationVariable("ankle_symmetry", 85, 100, 70, 85, 0, 70, True))

    variable_matrix = advancedStats.logic.asymmetry_logic.create_variable_matrix(athlete, date, var_list)

    variable_matrix.to_csv('~/decay/var_matrix_' + athlete + '_' + date + 'v6.csv', sep=',',
                           index_label='variable')


def test_get_percentage_matrix():

    athlete = "Maggie"
    date = "2018-04-24"
    var_list = []
    var_list.append(CategorizationVariable("peak_grf_perc_diff_lf", 0, 5, 5, 10, 10, 100, False))
    var_list.append(CategorizationVariable("peak_grf_perc_diff_rf", 0, 5, 5, 10, 10, 100, False))
    var_list.append(CategorizationVariable("gct_perc_diff_lf", 0, 5, 5, 10, 10, 100, False))
    var_list.append(CategorizationVariable("gct_perc_diff_rf", 0, 5, 5, 10, 10, 100, False))
    var_list.append(CategorizationVariable("peak_grf_gct_left_over", 0, 2.5, 2.5, 5, 5, 100, False))
    var_list.append(CategorizationVariable("peak_grf_gct_left_under", 0, 2.5, 2.5, 5, 5, 10, False))
    var_list.append(CategorizationVariable("peak_grf_gct_right_over", 0, 2.5, 2.5, 5, 5, 100, False))
    var_list.append(CategorizationVariable("peak_grf_gct_right_under", 0, 2.5, 2.5, 5, 5, 10, False))
    var_list.append(CategorizationVariable("hip_control", 85, 100, 70, 85, 0, 70, True))
    var_list.append(CategorizationVariable("control_lf", 85, 100, 70, 85, 0, 70, True))
    var_list.append(CategorizationVariable("control_rf", 85, 100, 70, 85, 0, 70, True))
    var_list.append(CategorizationVariable("symmetry", 85, 100, 70, 85, 0, 70, True))
    var_list.append(CategorizationVariable("hip_symmetry", 85, 100, 70, 85, 0, 70, True))
    var_list.append(CategorizationVariable("ankle_symmetry", 85, 100, 70, 85, 0, 70, True))

    percentage_matrix = calc.create_percentage_matrix(athlete, date, var_list)

    percentage_matrix.to_csv('~/decay/perc_matrix_' + athlete + '_' + date + 'v6.csv', sep=',', index_label='variable') '''