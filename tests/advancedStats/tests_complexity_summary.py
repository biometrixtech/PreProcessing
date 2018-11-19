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
    assert (len(session_list) > 0)


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


def test_get_movement_asymmetries():

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
            'adduc_motion_covered_hip': [f.adduc_motion_covered_hip],
            'flex_ROM_hip': [f.flex_ROM_hip],
            'flex_motion_covered_hip': [f.flex_motion_covered_hip]
        }, index=[f.stance])
        df = df.append(ab)

    df.to_csv('~/decay/kruskal_' + athlete + '_' + date + 'v6.csv', sep=',', index_label='Stance',
                               columns=[
                                   'complexity_level', 'grf_level', 'cma_level', 'adduc_ROM', 'adduc_motion_covered',
                                   'flex_ROM', 'flex_motion_covered', 'adduc_ROM_hip',
                                   'adduc_motion_covered_hip', 'flex_ROM_hip', 'flex_motion_covered_hip'])



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
            # lots to add here!!!
        }, index=[f.stance])
        df = df.append(ab)

    df.to_csv('~/decay/complexity_' + athlete + '_' + date + 'v6.csv', sep=',', index_label='Stance',
                        columns=[
                            'complexity_level',
                            'grf_level',
                            'cma_level',
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
                            'ground_contact_time_left',
                            'ground_contact_time_right',
                            'total_ground_contact_time',
                        ])


def test_session_asymmetries():

    athlete = "Maggie"
    date = "2018-04-24"

    mc_sl_list, mc_dl_list = advancedStats.logic.complexity_matrix_logic.get_complexity_matrices(athlete, date)

    proc = AsymmetryProcessor(athlete, date, "", mc_sl_list, mc_dl_list)

    session_asymmmetry = proc.get_session_asymmetry()

    df = pandas.DataFrame()

