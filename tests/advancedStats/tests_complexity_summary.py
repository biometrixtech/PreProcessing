import pandas

import advancedStats.logic.complexity_matrix_logic
from advancedStats.logic.fatigue_logic import FatigueProcessor
from advancedStats.logic.asymmetry_logic import AsymmetryProcessor
# import app.advancedStats.complexity_symmetry as calc
# from app.advancedStats.models.complexity_matrix import ComplexityMatrix
from app.advancedStats.models.fatigue import SessionFatigue


def test_get_cma_time_summaries():

    athlete = "Maggie"
    date = "2018-04-24"
    processor = FatigueProcessor()

    mc_sl_list, mc_dl_list = advancedStats.logic.complexity_matrix_logic.get_complexity_matrices(athlete, date)
    fatigue_events = processor.get_fatigue_events(mc_sl_list, mc_dl_list)
    session_fatigue = SessionFatigue(athlete, date, "", fatigue_events)
    cma_time_list = session_fatigue.cma_time_block_summary()
    assert(len(cma_time_list) >0)


def test_get_grf_time_summaries():

    athlete = "Maggie"
    date = "2018-04-24"
    processor = FatigueProcessor()
    mc_sl_list, mc_dl_list = advancedStats.logic.complexity_matrix_logic.get_complexity_matrices(athlete, date)
    fatigue_events = processor.get_fatigue_events(mc_sl_list, mc_dl_list)
    session_fatigue = SessionFatigue(athlete, date, "", fatigue_events)
    grf_time_list = session_fatigue.grf_time_block_summary()
    assert(len(grf_time_list) >0)


def test_get_cma_grf_summaries():
    athlete = "Maggie"
    date = "2018-04-24"
    processor = FatigueProcessor()
    mc_sl_list, mc_dl_list = advancedStats.logic.complexity_matrix_logic.get_complexity_matrices(athlete, date)
    fatigue_events = processor.get_fatigue_events(mc_sl_list, mc_dl_list)
    session_fatigue = SessionFatigue(athlete, date, "", fatigue_events)
    cma_grf_list = session_fatigue.cma_grf_summary()
    assert (len(cma_grf_list) > 0)


def test_get_cma_grf_crosstab():
    athlete = "Maggie"
    date = "2018-04-24"
    processor = FatigueProcessor()
    mc_sl_list, mc_dl_list = advancedStats.logic.complexity_matrix_logic.get_complexity_matrices(athlete, date)
    fatigue_events = processor.get_fatigue_events(mc_sl_list, mc_dl_list)
    session_fatigue = SessionFatigue(athlete, date, "", fatigue_events)
    cma_grf_list = session_fatigue.cma_grf_crosstab()

    fatigue_frame = pandas.DataFrame()

    for f in cma_grf_list:
        ab = pandas.DataFrame({
            #'stance': [f.stance],
            'grf_level': [f.grf_level],
            'cma_level': [f.cma_level],
            'adduc_hip_neg_left_dec': [f.adduc_neg_hip_left_dec],
            'adduc_hip_neg_right_dec': [f.adduc_neg_hip_right_dec],
            'adduc_hip_neg_left_inc': [f.adduc_neg_hip_left_inc],
            'adduc_hip_neg_right_inc': [f.adduc_neg_hip_right_inc],
            'adduc_hip_pos_left_dec': [f.adduc_pos_hip_left_dec],
            'adduc_hip_pos_right_dec': [f.adduc_pos_hip_right_dec],
            'adduc_hip_pos_left_inc': [f.adduc_pos_hip_left_inc],
            'adduc_hip_pos_right_inc': [f.adduc_pos_hip_right_inc],

            'flex_hip_neg_left_dec': [f.flex_neg_hip_left_dec],
            'flex_hip_neg_right_dec': [f.flex_neg_hip_right_dec],
            'flex_hip_neg_left_inc': [f.flex_neg_hip_left_inc],
            'flex_hip_neg_right_inc': [f.flex_neg_hip_right_inc],
            'flex_hip_pos_left_dec': [f.flex_pos_hip_left_dec],
            'flex_hip_pos_right_dec': [f.flex_pos_hip_right_dec],
            'flex_hip_pos_left_inc': [f.flex_pos_hip_left_inc],
            'flex_hip_pos_right_inc': [f.flex_pos_hip_right_inc],

            'adduc_rom_hip_left_dec': [f.adduc_rom_hip_left_dec],
            'adduc_rom_hip_right_dec': [f.adduc_rom_hip_right_dec],
            'adduc_rom_hip_left_inc': [f.adduc_rom_hip_left_inc],
            'adduc_rom_hip_right_inc': [f.adduc_rom_hip_right_inc],
            'flex_rom_hip_left_dec': [f.flex_rom_hip_left_dec],
            'flex_rom_hip_right_dec': [f.flex_rom_hip_right_dec],
            'flex_rom_hip_left_inc': [f.flex_rom_hip_left_inc],
            'flex_rom_hip_right_inc': [f.flex_rom_hip_right_inc],

        }, index=[f.stance])
        fatigue_frame = fatigue_frame.append(ab)

    fatigue_frame.to_csv('~/decay/fatigue_xtab_' + athlete + '_' + date + 'v6.csv', sep=',', index_label='Stance',
                       columns=[
                                'grf_level',
                                'cma_level',
                                'adduc_hip_neg_left_dec',
                                'adduc_hip_neg_right_dec',
                                'adduc_hip_neg_left_inc',
                                'adduc_hip_neg_right_inc',
                                'adduc_hip_pos_left_dec',
                                'adduc_hip_pos_right_dec',
                                'adduc_hip_pos_left_inc',
                                'adduc_hip_pos_right_inc',
                                'flex_hip_neg_left_dec',
                                'flex_hip_neg_right_dec',
                                'flex_hip_neg_left_inc',

                                'flex_hip_neg_right_inc',
                                'flex_hip_pos_left_dec',
                                'flex_hip_pos_right_dec',

                                'flex_hip_pos_left_inc',
                                'flex_hip_pos_right_inc',

                                'adduc_rom_hip_left_dec',
                                'adduc_rom_hip_right_dec',
                                'adduc_rom_hip_left_inc',

                                'adduc_rom_hip_right_inc',
                                'flex_rom_hip_left_dec',
                                'flex_rom_hip_right_dec',
                                'flex_rom_hip_left_inc',
                                'flex_rom_hip_right_inc'
                       ])

    assert (len(cma_grf_list) > 0)


def test_get_active_block_crosstab():
    athlete = "Maggie"
    date = "2018-04-24"
    processor = FatigueProcessor()
    mc_sl_list, mc_dl_list = advancedStats.logic.complexity_matrix_logic.get_complexity_matrices(athlete, date)
    fatigue_events = processor.get_fatigue_events(mc_sl_list, mc_dl_list)
    session_fatigue = SessionFatigue(athlete, date, "", fatigue_events)
    cma_grf_list = session_fatigue.active_block_crosstab()

    fatigue_frame = pandas.DataFrame()

    for f in cma_grf_list:
        ab = pandas.DataFrame({
            # 'stance': [f.stance],
            'cumulative_end_time': [f.cumulative_end_time],
            'time_block': [f.time_block],
            'adduc_hip_neg_left_dec': [f.adduc_neg_hip_left_dec],
            'adduc_hip_neg_right_dec': [f.adduc_neg_hip_right_dec],
            'adduc_hip_neg_left_inc': [f.adduc_neg_hip_left_inc],
            'adduc_hip_neg_right_inc': [f.adduc_neg_hip_right_inc],
            'adduc_hip_pos_left_dec': [f.adduc_pos_hip_left_dec],
            'adduc_hip_pos_right_dec': [f.adduc_pos_hip_right_dec],
            'adduc_hip_pos_left_inc': [f.adduc_pos_hip_left_inc],
            'adduc_hip_pos_right_inc': [f.adduc_pos_hip_right_inc],

            'flex_hip_neg_left_dec': [f.flex_neg_hip_left_dec],
            'flex_hip_neg_right_dec': [f.flex_neg_hip_right_dec],
            'flex_hip_neg_left_inc': [f.flex_neg_hip_left_inc],
            'flex_hip_neg_right_inc': [f.flex_neg_hip_right_inc],
            'flex_hip_pos_left_dec': [f.flex_pos_hip_left_dec],
            'flex_hip_pos_right_dec': [f.flex_pos_hip_right_dec],
            'flex_hip_pos_left_inc': [f.flex_pos_hip_left_inc],
            'flex_hip_pos_right_inc': [f.flex_pos_hip_right_inc],

            'adduc_rom_hip_left_dec': [f.adduc_rom_hip_left_dec],
            'adduc_rom_hip_right_dec': [f.adduc_rom_hip_right_dec],
            'adduc_rom_hip_left_inc': [f.adduc_rom_hip_left_inc],
            'adduc_rom_hip_right_inc': [f.adduc_rom_hip_right_inc],
            'flex_rom_hip_left_dec': [f.flex_rom_hip_left_dec],
            'flex_rom_hip_right_dec': [f.flex_rom_hip_right_dec],
            'flex_rom_hip_left_inc': [f.flex_rom_hip_left_inc],
            'flex_rom_hip_right_inc': [f.flex_rom_hip_right_inc],

        }, index=[f.active_block])
        fatigue_frame = fatigue_frame.append(ab)

    fatigue_frame.to_csv('~/decay/fatigue_ab_xtab_' + athlete + '_' + date + 'v6.csv', sep=',', index_label='Active Block',
                         columns=[
                             'cumulative_end_time',
                             'time_block',
                             'adduc_hip_neg_left_dec',
                             'adduc_hip_neg_right_dec',
                             'adduc_hip_neg_left_inc',
                             'adduc_hip_neg_right_inc',
                             'adduc_hip_pos_left_dec',
                             'adduc_hip_pos_right_dec',
                             'adduc_hip_pos_left_inc',
                             'adduc_hip_pos_right_inc',
                             'flex_hip_neg_left_dec',
                             'flex_hip_neg_right_dec',
                             'flex_hip_neg_left_inc',

                             'flex_hip_neg_right_inc',
                             'flex_hip_pos_left_dec',
                             'flex_hip_pos_right_dec',

                             'flex_hip_pos_left_inc',
                             'flex_hip_pos_right_inc',

                             'adduc_rom_hip_left_dec',
                             'adduc_rom_hip_right_dec',
                             'adduc_rom_hip_left_inc',

                             'adduc_rom_hip_right_inc',
                             'flex_rom_hip_left_dec',
                             'flex_rom_hip_right_dec',
                             'flex_rom_hip_left_inc',
                             'flex_rom_hip_right_inc'
                         ])

    assert (len(cma_grf_list) > 0)


def test_get_cma_summaries():
    athlete = "Maggie"
    date = "2018-04-24"
    processor = FatigueProcessor()
    mc_sl_list, mc_dl_list = advancedStats.logic.complexity_matrix_logic.get_complexity_matrices(athlete, date)
    fatigue_events = processor.get_fatigue_events(mc_sl_list, mc_dl_list)
    session_fatigue = SessionFatigue(athlete, date, "", fatigue_events)
    cma_list = session_fatigue.cma_summary()
    assert (len(cma_list) > 0)


def test_get_time_summaries():
    athlete = "Maggie"
    date = "2018-04-24"
    processor = FatigueProcessor()
    mc_sl_list, mc_dl_list = advancedStats.logic.complexity_matrix_logic.get_complexity_matrices(athlete, date)
    fatigue_events = processor.get_fatigue_events(mc_sl_list, mc_dl_list)
    session_fatigue = SessionFatigue(athlete, date, "", fatigue_events)
    time_list = session_fatigue.grf_summary()
    assert (len(time_list) > 0)


def test_get_session_summaries():
    athlete = "Maggie"
    date = "2018-04-24"
    processor = FatigueProcessor()
    mc_sl_list, mc_dl_list = advancedStats.logic.complexity_matrix_logic.get_complexity_matrices(athlete, date)
    fatigue_events = processor.get_fatigue_events(mc_sl_list, mc_dl_list)
    session_fatigue = SessionFatigue(athlete, date, "", fatigue_events)

    session_list = session_fatigue.session_summary()
    decay_frame = pandas.DataFrame()

    for f in session_list:
        ab = pandas.DataFrame({
            'attribute_name': [f.attribute_name],
            'attribute_label': [f.attribute_label],
            'orientation': [f.orientation],
            'count': [f.count],
        }, index=[f.stance])
        decay_frame = decay_frame.append(ab)

    decay_frame.to_csv('~/decay/fatigue_session_summary_' + athlete + '_' + date + 'v7.csv', sep=',', index_label='Stance',
                       columns=[
                           'attribute_name', 'attribute_label', 'orientation', 'count'])


def test_get_decay_dataframe():

    athlete = "Maggie"
    date = "2018-04-24"
    processor = FatigueProcessor()
    mc_sl_list, mc_dl_list = advancedStats.logic.complexity_matrix_logic.get_complexity_matrices(athlete, date)
    fatigue_events = processor.get_fatigue_events(mc_sl_list, mc_dl_list)

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


def test_get_movement_asymmetries_kruskal():

    athlete = "Maggie"
    date = "2018-04-24"

    mc_sl_list, mc_dl_list = advancedStats.logic.complexity_matrix_logic.get_complexity_matrices(athlete, date)

    proc = AsymmetryProcessor(athlete, date, "", mc_sl_list, mc_dl_list)

    asymmetry_events = proc.get_movement_asymmetries()

    df = pandas.DataFrame()

    for f in asymmetry_events:
        ab = pandas.DataFrame({
            'complexity_level': [f.complexity_level],
            'grf_level': [f.grf_level],
            'cma_level': [f.cma_level],
            'adduc_ROM': [f.adduc_ROM],
            'adduc_motion_covered': [f.adduc_motion_covered],
            'flex_ROM': [f.flex_ROM],
            'flex_motion_covered': [f.flex_motion_covered],
            'adduc_ROM_hip': [f.adduc_ROM_hip],
            'adduc_motion_covered_total_hip': [f.adduc_motion_covered_hip],
            'flex_ROM_hip': [f.flex_ROM_hip],
            'flex_motion_covered_total_hip': [f.flex_motion_covered_hip]
        }, index=[f.stance])
        df = df.append(ab)

    df.to_csv('~/decay/kruskal_' + athlete + '_' + date + 'v6.csv', sep=',', index_label='Stance',
                               columns=[
                                   'complexity_level', 'grf_level', 'cma_level', 'adduc_ROM', 'adduc_motion_covered',
                                   'flex_ROM', 'flex_motion_covered', 'adduc_ROM_hip',
                                   'adduc_motion_covered_total_hip', 'flex_ROM_hip', 'flex_motion_covered_total_hip'])



def test_get_loading_asymmetries():

    athlete = "Maggie"
    date = "2018-04-24"

    mc_sl_list, mc_dl_list = advancedStats.logic.complexity_matrix_logic.get_complexity_matrices(athlete, date)

    proc = AsymmetryProcessor(athlete, date, "", mc_sl_list, mc_dl_list)

    asymmetry_events = proc.get_loading_asymmetries()

    df = pandas.DataFrame()

    for f in asymmetry_events:
        ab = pandas.DataFrame({
            'complexity_level': [f.complexity_level],
            'grf_level': [f.grf_level],
            'cma_level': [f.cma_level],
            'acc_grf_left': [f.total_left_sum],
            'acc_grf_right': [f.total_right_sum],
            'acc_grf_perc_asymm': [f.total_percent_asymmetry],
            'gc_event_left': [ f.left_step_count],
            'gc_event_right': [f.right_step_count],
            'gc_event_perc_asymm': [f.step_count_percent_asymmetry],
            'gct_left': [f.ground_contact_time_left],
            'gct_right': [f.ground_contact_time_right],
            'gct_perc_asymm': [f.ground_contact_time_percent_asymmetry],
            'rate_of_acc_grf_left': [f.left_avg_accumulated_grf_sec],
            'rate_of_acc_grf_right': [f.right_avg_accumulated_grf_sec],
            'rate_of_acc_grf_perc_asymm': [f.accumulated_grf_sec_percent_asymmetry]
        }, index=[f.stance])
        df = df.append(ab)

    df.to_csv('~/decay/loading_asymmetry_' + athlete + '_' + date + 'v7.csv', sep=',', index_label='Stance',
                        columns=[
                            'complexity_level',
                            'grf_level',
                            'cma_level',
                            'acc_grf_left',
                            'acc_grf_right',
                            'acc_grf_perc_asymm',
                            'gc_event_left',
                            'gc_event_right',
                            'gc_event_perc_asymm',
                            'gct_left',
                            'gct_right',
                            'gct_perc_asymm',
                            'rate_of_acc_grf_left',
                            'rate_of_acc_grf_right',
                            'rate_of_acc_grf_perc_asymm',
                        ])


def test_loading_asymmetry_summaries():

    athlete = "Maggie"
    date = "2018-04-24"

    mc_sl_list, mc_dl_list = advancedStats.logic.complexity_matrix_logic.get_complexity_matrices(athlete, date)

    proc = AsymmetryProcessor(athlete, date, "", mc_sl_list, mc_dl_list)

    session_asymmmetry = proc.get_session_asymmetry()

    df = pandas.DataFrame()
    for var, f in session_asymmmetry.loading_asymmetry_summaries.items():
        ab = pandas.DataFrame({
            'red:grf': [f.red_grf],
            'red:grf_percent': [f.red_grf_percent],
            'red:cma': [f.red_cma],
            'red:cma_percent': [f.red_cma_percent],
            'red:time': [f.red_time],
            'red:time_percent': [f.red_time_percent],
            'yellow:grf': [f.yellow_grf],
            'yellow:grf_percent': [f.yellow_grf_percent],
            'yellow:cma': [f.yellow_cma],
            'yellow:cma_percent': [f.yellow_cma_percent],
            'yellow:time': [f.yellow_time],
            'yellow:time_percent': [f.yellow_time_percent],
            'green:grf': [f.green_grf],
            'green:grf_percent': [f.green_grf_percent],
            'green:cma': [f.green_cma],
            'green:cma_percent': [f.green_cma_percent],
            'green:time': [f.green_time],
            'green:time_percent': [f.green_time_percent],
            'total_grf': [f.total_grf],
            'total_cma': [f.total_cma],
            'total_time': [f.total_time],
            'total_session_time': [f.total_session_time],
            # lots to add here!!!
        }, index=[f.variable_name])
        df = df.append(ab)

    df.to_csv('~/decay/rel_magnitude_asymmetry_' + athlete + '_' + date + 'v7.csv', sep=',', index_label='Variable',
              columns=[
                        'red:grf',
                        'red:grf_percent',
                        'red:cma',
                        'red:cma_percent',
                        'red:time',
                        'red:time_percent',
                        'yellow:grf',
                        'yellow:grf_percent',
                        'yellow:cma',
                        'yellow:cma_percent',
                        'yellow:time',
                        'yellow:time_percent',
                        'green:grf',
                        'green:grf_percent',
                        'green:cma',
                        'green:cma_percent',
                        'green:time',
                        'green:time_percent',
                        'total_grf',
                        'total_cma',
                        'total_time',
                        'total_session_time',
              ])


def test_get_movement_asymmetries():

    athlete = "Maggie"
    date = "2018-04-24"

    mc_sl_list, mc_dl_list = advancedStats.logic.complexity_matrix_logic.get_complexity_matrices(athlete, date)

    proc = AsymmetryProcessor(athlete, date, "", mc_sl_list, mc_dl_list)

    asymmetry_events = proc.get_movement_asymmetries()

    df = pandas.DataFrame()

    for f in asymmetry_events:
        ab = pandas.DataFrame({
            #'complexity_level': [f.complexity_level],
            'grf_level': [f.grf_level],
            'cma_level': [f.cma_level],
            'adduc_rom_hip': [f.adduc_rom_hip],
            'adduc_motion_covered_total_hip': [f.adduc_motion_covered_hip],
            'flex_rom_hip': [f.flex_rom_hip],
            'flex_motion_covered_total_hip': [f.flex_motion_covered_hip]
            # lots to add here!!!
        }, index=[f.stance])
        df = df.append(ab)

    df.to_csv('~/decay/movement_asymmetries_' + athlete + '_' + date + 'v7.csv', sep=',', index_label='Stance',
                        columns=[
                            #'complexity_level',
                            'grf_level',
                            'cma_level',

                            'adduc_rom_hip',
                            'adduc_motion_covered_total_hip',
                            'flex_rom_hip',
                            'flex_motion_covered_total_hip',
                        ])

def test_get_loading_and_movement_asymmetries():

    athlete = "Maggie"
    date = "2018-04-24"

    mc_sl_list, mc_dl_list = advancedStats.logic.complexity_matrix_logic.get_complexity_matrices(athlete, date)

    proc = AsymmetryProcessor(athlete, date, "", mc_sl_list, mc_dl_list)

    movement_events = proc.get_movement_asymmetries()
    loading_events = proc.get_loading_asymmetries()

    df = pandas.DataFrame()

    for d in movement_events:
        for f in loading_events:
            if d.cma_level == f.cma_level and d.grf_level == f.grf_level and d.stance == f.stance:

                ab = pandas.DataFrame({
                    #'complexity_level': [f.complexity_level],
                    'grf_level': [f.grf_level],
                    'cma_level': [f.cma_level],
                    'acc_grf_left': [f.total_left_sum],
                    'acc_grf_right': [f.total_right_sum],
                    'acc_grf_perc_asymm': [f.total_percent_asymmetry],
                    'gc_event_left': [f.left_step_count],
                    'gc_event_right': [f.right_step_count],
                    'gc_event_perc_asymm': [f.step_count_percent_asymmetry],
                    'gct_left': [f.ground_contact_time_left],
                    'gct_right': [f.ground_contact_time_right],
                    'gct_perc_asymm': [f.ground_contact_time_percent_asymmetry],
                    'rate_of_acc_grf_left': [f.left_avg_accumulated_grf_sec],
                    'rate_of_acc_grf_right': [f.right_avg_accumulated_grf_sec],
                    'rate_of_acc_grf_perc_asymm': [f.accumulated_grf_sec_percent_asymmetry],
                    'adduc_rom_hip': [d.adduc_rom_hip_flag()],
                    'adduc_motion_covered_total_hip': [d.adduc_motion_covered_tot_hip_flag()],
                    'adduc_motion_covered_pos_hip': [d.adduc_motion_covered_pos_hip_flag()],
                    'adduc_motion_covered_neg_hip': [d.adduc_motion_covered_neg_hip_flag()],
                    'flex_rom_hip': [d.flex_rom_hip_flag()],
                    'flex_motion_covered_total_hip': [d.adduc_motion_covered_tot_hip_flag()],
                    'flex_motion_covered_pos_hip': [d.adduc_motion_covered_pos_hip_flag()],
                    'flex_motion_covered_neg_hip': [d.adduc_motion_covered_neg_hip_flag()],
                }, index=[f.stance])
                df = df.append(ab)

    df.to_csv('~/decay/loading_movement_asymm_' + athlete + '_' + date + 'v7.csv', sep=',', index_label='Stance',
                        columns=[
                            #'complexity_level',
                            'grf_level',
                            'cma_level',
                            'adduc_rom_hip',
                            'adduc_motion_covered_total_hip',
                            'adduc_motion_covered_pos_hip',
                            'adduc_motion_covered_neg_hip',
                            'flex_rom_hip',
                            'flex_motion_covered_total_hip',
                            'flex_motion_covered_pos_hip',
                            'flex_motion_covered_neg_hip',
                            'acc_grf_left',
                            'acc_grf_right',
                            'acc_grf_perc_asymm',
                            'gc_event_left',
                            'gc_event_right',
                            'gc_event_perc_asymm',
                            'gct_left',
                            'gct_right',
                            'gct_perc_asymm',
                            'rate_of_acc_grf_left',
                            'rate_of_acc_grf_right',
                            'rate_of_acc_grf_perc_asymm',
                        ])




def test_session_asymmetries():

    athlete = "Maggie"
    date = "2018-04-24"

    mc_sl_list, mc_dl_list = advancedStats.logic.complexity_matrix_logic.get_complexity_matrices(athlete, date)

    proc = AsymmetryProcessor(athlete, date, "", mc_sl_list, mc_dl_list)

    session_asymmmetry = proc.get_session_asymmetry()

    df = pandas.DataFrame()

