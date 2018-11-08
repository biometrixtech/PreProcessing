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
    athlete = ""
    date = ""
    output_path = ""

    calc.query_mongo_ab(collection, athlete, date, output_path)


def test_get_intensity_matrix():

    athlete = "Maggie"
    date = "2018-04-24"

    intensity_matrix = calc.create_intensity_matrix(athlete, date)

    intensity_matrix.to_csv('~/decay/intensity_matrix_' + athlete + '_' + date + 'v6.csv', sep=',',
                           index_label='variable')


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
    var_list.append(CategorizationVariable("hip_control", 85, 100, 70, 85, 0, 70, True))
    var_list.append(CategorizationVariable("control_lf", 85, 100, 70, 85, 0, 70, True))
    var_list.append(CategorizationVariable("control_rf", 85, 100, 70, 85, 0, 70, True))
    var_list.append(CategorizationVariable("symmetry", 85, 100, 70, 85, 0, 70, True))
    var_list.append(CategorizationVariable("hip_symmetry", 85, 100, 70, 85, 0, 70, True))
    var_list.append(CategorizationVariable("ankle_symmetry", 85, 100, 70, 85, 0, 70, True))

    variable_matrix = calc.create_variable_matrix(athlete, date, var_list)

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

    percentage_matrix.to_csv('~/decay/perc_matrix_' + athlete + '_' + date + 'v6.csv', sep=',',
                             index_label='variable')