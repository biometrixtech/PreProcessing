import pandas

import advancedStats.logic.fatigue_logic
import app.advancedStats.complexity_symmetry as calc
from app.advancedStats.models.complexity_matrix import ComplexityMatrix
from app.advancedStats.models.fatigue import SessionFatigue


def test_get_cma_time_summaries():

    athlete = "Maggie"
    date = "2018-04-24"

    mc_sl_list, mc_dl_list = calc.get_complexity_matrices(athlete, date)
    fatigue_events = advancedStats.logic.fatigue_logic.get_fatigue_events(mc_sl_list, mc_dl_list)
    session_fatigue = SessionFatigue(athlete, date, "", fatigue_events)
    cma_time_list = session_fatigue.cma_time_block_summary()
    assert(len(cma_time_list) >0)


def test_get_grf_time_summaries():

    athlete = "Maggie"
    date = "2018-04-24"

    mc_sl_list, mc_dl_list = calc.get_complexity_matrices(athlete, date)
    fatigue_events = advancedStats.logic.fatigue_logic.get_fatigue_events(mc_sl_list, mc_dl_list)
    session_fatigue = SessionFatigue(athlete, date, "", fatigue_events)
    grf_time_list = session_fatigue.grf_time_block_summary()
    assert(len(grf_time_list) >0)


def test_get_cma_grf_summaries():
    athlete = "Maggie"
    date = "2018-04-24"

    mc_sl_list, mc_dl_list = calc.get_complexity_matrices(athlete, date)
    fatigue_events = advancedStats.logic.fatigue_logic.get_fatigue_events(mc_sl_list, mc_dl_list)
    session_fatigue = SessionFatigue(athlete, date, "", fatigue_events)
    cma_grf_list = session_fatigue.cma_grf_summary()
    assert (len(cma_grf_list) > 0)


def test_get_cma_summaries():
    athlete = "Maggie"
    date = "2018-04-24"

    mc_sl_list, mc_dl_list = calc.get_complexity_matrices(athlete, date)
    fatigue_events = advancedStats.logic.fatigue_logic.get_fatigue_events(mc_sl_list, mc_dl_list)
    session_fatigue = SessionFatigue(athlete, date, "", fatigue_events)
    cma_list = session_fatigue.cma_summary()
    assert (len(cma_list) > 0)


def test_get_time_summaries():
    athlete = "Maggie"
    date = "2018-04-24"

    mc_sl_list, mc_dl_list = calc.get_complexity_matrices(athlete, date)
    fatigue_events = advancedStats.logic.fatigue_logic.get_fatigue_events(mc_sl_list, mc_dl_list)
    session_fatigue = SessionFatigue(athlete, date, "", fatigue_events)
    time_list = session_fatigue.grf_summary()
    assert (len(time_list) > 0)


def test_get_session_summaries():
    athlete = "Maggie"
    date = "2018-04-24"

    mc_sl_list, mc_dl_list = calc.get_complexity_matrices(athlete, date)
    fatigue_events = advancedStats.logic.fatigue_logic.get_fatigue_events(mc_sl_list, mc_dl_list)
    session_fatigue = SessionFatigue(athlete, date, "", fatigue_events)

    session_list = session_fatigue.session_summary()
    assert (len(session_list) > 0)


def test_get_decay_dataframe():

    athlete = "Maggie"
    date = "2018-04-24"

    mc_sl_list, mc_dl_list = calc.get_complexity_matrices(athlete, date)
    fatigue_events = advancedStats.logic.fatigue_logic.get_fatigue_events(mc_sl_list, mc_dl_list)

    decay_frame = pandas.DataFrame()

    for f in fatigue_events:
        ab = pandas.DataFrame({
            'active_block': [f.active_block_id],
            'grf_level': [f.grf_level],
            'cma_level': [f.cma_level],
            'complexity_level': [f.complexity_level],
            'attribute_name': [f.attribute_name],
            'label': [f.attribute_label],
            'orientation': [f.orientation],
            'cumulative_end_time': [f.cumulative_end_time],
            'z_score': [f.z_score],
            'raw_value': [f.raw_value]
        }, index=[f.stance])
        decay_frame = decay_frame.append(ab)

    decay_frame.to_csv('~/decay/outliers_' + athlete + '_' + date + 'v6.csv', sep=',', index_label='Stance',
                       columns=[
                           'active_block', 'complexity_level', 'grf_level', 'cma_level','attribute_name', 'label',
                           'orientation', 'cumulative_end_time', 'z_score', 'raw_value'])

    # decay_frame.to_csv('C:\\UNC\\v6\\decay_'+athlete+'_'+date+'v6.csv',sep=',',index_label='Stance',columns=[
    #    'complexity_level','row_name','column_name',
    #    'adduc_ROM_LF',
    #    'adduc_ROM_RF',
    #    'adduc_pronation_LF',
    #    'adduc_pronation_RF',
    #    'adduc_supination_LF',
    #    'adduc_supination_RF',
    #    'flex_ROM_LF',
    #    'flex_ROM_RF',
    #    'dorsiflexion_LF',
    #    'dorsiflexion_RF',
    #    'plantarflexion_LF',
    #    'plantarflexion_RF',
    #    'adduc_ROM_hip_LF',
    #    'adduc_ROM_hip_RF',
    #    'adduc_positive_hip_LF',
    #    'adduc_positive_hip_RF',
    #    'adduc_negative_hip_LF',
    #    'adduc_negative_hip_RF',
    #    'flex_ROM_hip_LF',
    #    'flex_ROM_hip_RF',
    #    'flex_positive_hip_LF',
    #    'flex_positive_hip_RF',
    #    'flex_negative_hip_LF',
    #    'flex_negative_hip_RF'])


def test_get_kruskal_dataframe():

    athlete = "Maggie"
    date = "2018-04-24"

    mc_sl_list, mc_dl_list = calc.get_complexity_matrices(athlete, date)
    kruskal_calcs_frame = calc.get_kruskal_data_frame(mc_sl_list, mc_dl_list)

    kruskal_calcs_frame.to_csv('~/decay/kruskal_' + athlete + '_' + date + 'v6.csv', sep=',', index_label='Stance',
                               columns=[
                                   'complexity_level', 'row_name', 'column_name', 'adduc_ROM', 'adduc_motion_covered',
                                   'flex_ROM', 'flex_motion_covered', 'adduc_ROM_hip',
                                   'adduc_motion_covered_hip', 'flex_ROM_hip', 'flex_motion_covered_hip'])


def test_get_asymmetry_dataframe():

    athlete = "Maggie"
    date = "2018-04-24"

    mc_sl_list, mc_dl_list = calc.get_complexity_matrices(athlete, date)
    asymmetry_data_frame = calc.get_asymmetry_data_frame(mc_sl_list, mc_dl_list, "total_grf")

    asymmetry_data_frame.to_csv('~/decay/complexity_' + athlete + '_' + date + 'v6.csv', sep=',', index_label='Stance',
                        columns=[
                            'complexity_level',
                            'row_name',
                            'column_name',
                            'left_steps',
                            'right_steps',
                            'total_steps',
                            'left_avg_accum_grf_sec',
                            'right_avg_accum_grf_sec',
                            'grf_training_asymmetry',
                            'grf_kinematic_asymmetry',
                            'grf_total_asymmetry',
                            'grf_total_sum',
                            'grf_asym_percent',
                            'left_duration',
                            'right_duration',
                            'total_duration',
                            'left_adduc_ROM_mean',
                            'left_adduc_ROM_stddev',
                            'right_adduc_ROM_mean',
                            'right_adduc_ROM_stddev',
                            'left_adduc_motion_covered_mean',
                            'left_adduc_motion_covered_stddev',
                            'right_adduc_motion_covered_mean',
                            'right_adduc_motion_covered_stddev',
                            'left_flex_ROM_mean',
                            'left_flex_ROM_stddev',
                            'right_flex_ROM_mean',
                            'right_flex_ROM_stddev',
                            'left_flex_motion_covered_mean',
                            'left_flex_motion_covered_stddev',
                            'right_flex_motion_covered_mean',
                            'right_flex_motion_covered_stddev',
                            'left_adduc_ROM_hip_mean',
                            'left_adduc_ROM_hip_stddev',
                            'right_adduc_ROM_hip_mean',
                            'right_adduc_ROM_hip_stddev',
                            'left_adduc_motion_covered_hip_mean',
                            'left_adduc_motion_covered_hip_stddev',
                            'right_adduc_motion_covered_hip_mean',
                            'right_adduc_motion_covered_hip_stddev',
                            'left_flex_ROM_hip_mean',
                            'left_flex_ROM_hip_stddev',
                            'right_flex_ROM_hip_mean',
                            'right_flex_ROM_hip_stddev',
                            'left_flex_motion_covered_hip_mean',
                            'left_flex_motion_covered_hip_stddev',
                            'right_flex_motion_covered_hip_mean',
                            'right_flex_motion_covered_hip_stddev',
                            'left_adduc_ROM_time_corr',
                            'right_adduc_ROM_time_corr',
                            'left_adduc_motion_covered_time_corr',
                            'right_adduc_motion_covered_time_corr'

                        ])

def test_get_fatigue_dataframe():

    # THIS IS NOT NEEDED!!!!

    athlete = "Maggie"
    date = "2018-04-24"

    mc_sl_list, mc_dl_list = calc.get_complexity_matrices(athlete, date)
    fatigue_data_frame = calc.get_fatigue_data_frame(mc_sl_list, mc_dl_list, "total_grf")

    fatigue_data_frame.to_csv('~decay/fatigue_' + athlete + '_' + date + 'v6.csv', sep=',', index_label='Stance',
                         columns=[
                             'complexity_level',
                             'fatigue_level',
                             'left_steps',
                             'right_steps',
                             'total_steps',
                             'left_avg_accum_grf_sec',
                             'right_avg_accum_grf_sec',
                             'grf_training_asymmetry',
                             'grf_kinematic_asymmetry',
                             'grf_total_asymmetry',
                             'grf_total_sum',
                             'grf_asym_percent',
                             'left_duration',
                             'right_duration',
                             'total_duration',
                             'left_adduc_ROM_mean',
                             'left_adduc_ROM_stddev',
                             'right_adduc_ROM_mean',
                             'right_adduc_ROM_stddev',
                             'left_adduc_motion_covered_mean',
                             'left_adduc_motion_covered_stddev',
                             'right_adduc_motion_covered_mean',
                             'right_adduc_motion_covered_stddev',
                             'left_flex_ROM_mean',
                             'left_flex_ROM_stddev',
                             'right_flex_ROM_mean',
                             'right_flex_ROM_stddev',
                             'left_flex_motion_covered_mean',
                             'left_flex_motion_covered_stddev',
                             'right_flex_motion_covered_mean',
                             'right_flex_motion_covered_stddev',
                             'left_adduc_ROM_hip_mean',
                             'left_adduc_ROM_hip_stddev',
                             'right_adduc_ROM_hip_mean',
                             'right_adduc_ROM_hip_stddev',
                             'left_adduc_motion_covered_hip_mean',
                             'left_adduc_motion_covered_hip_stddev',
                             'right_adduc_motion_covered_hip_mean',
                             'right_adduc_motion_covered_hip_stddev',
                             'left_flex_ROM_hip_mean',
                             'left_flex_ROM_hip_stddev',
                             'right_flex_ROM_hip_mean',
                             'right_flex_ROM_hip_stddev',
                             'left_flex_motion_covered_hip_mean',
                             'left_flex_motion_covered_hip_stddev',
                             'right_flex_motion_covered_hip_mean',
                             'right_flex_motion_covered_hip_stddev',
                             'left_adduc_ROM_time_corr',
                             'right_adduc_ROM_time_corr',
                             'left_adduc_motion_covered_time_corr',
                             'right_adduc_motion_covered_time_corr'

                         ])


def test_get_matrix_dataframe():

    athlete = "Maggie"
    date = "2018-04-24"

    dl_comp_matrix = ComplexityMatrix("Double Leg")
    sl_comp_matrix = ComplexityMatrix("Single Leg")

    matrix_frame = calc.get_matrix_data_frame(sl_comp_matrix, dl_comp_matrix, "total_grf")

    matrix_frame.to_csv('~/decay/asym_' + athlete + '_' + date + 'v6.csv', sep=',', index_label='Stance', columns=[
        'complexity_level',
        'row',
        'column',
        'left_steps',
        'right_steps',
        'total_steps',
        'left_avg_accum_grf_sec',
        'right_avg_accum_grf_sec',
        'grf_training_asymmetry',
        'grf_kinematic_asymmetry',
        'grf_total_asymmetry',
        'grf_total_sum',
        'grf_asym_percent',
        'left_duration',
        'right_duration',
        'total_duration',
        'left_adduc_ROM_mean',
        'left_adduc_ROM_stddev',
        'right_adduc_ROM_mean',
        'right_adduc_ROM_stddev',
        'left_adduc_motion_covered_mean',
        'left_adduc_motion_covered_stddev',
        'right_adduc_motion_covered_mean',
        'right_adduc_motion_covered_stddev',
        'left_flex_ROM_mean',
        'left_flex_ROM_stddev',
        'right_flex_ROM_mean',
        'right_flex_ROM_stddev',
        'left_flex_motion_covered_mean',
        'left_flex_motion_covered_stddev',
        'right_flex_motion_covered_mean',
        'right_flex_motion_covered_stddev',
        'left_adduc_ROM_hip_mean',
        'left_adduc_ROM_hip_stddev',
        'right_adduc_ROM_hip_mean',
        'right_adduc_ROM_hip_stddev',
        'left_adduc_motion_covered_hip_mean',
        'left_adduc_motion_covered_hip_stddev',
        'right_adduc_motion_covered_hip_mean',
        'right_adduc_motion_covered_hip_stddev',
        'left_flex_ROM_hip_mean',
        'left_flex_ROM_hip_stddev',
        'right_flex_ROM_hip_mean',
        'right_flex_ROM_hip_stddev',
        'left_flex_motion_covered_hip_mean',
        'left_flex_motion_covered_hip_stddev',
        'right_flex_motion_covered_hip_mean',
        'right_flex_motion_covered_hip_stddev',
        'left_adduc_ROM_time_corr',
        'right_adduc_ROM_time_corr',
        'left_adduc_motion_covered_time_corr',
        'right_adduc_motion_covered_time_corr'

    ])

