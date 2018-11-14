import pandas
from datetime import datetime
from models.step import Step
from models.fatigue import FatigueEvent
from models.complexity_matrix import ComplexityMatrix
from pymongo import ASCENDING
from config import load_parameters, get_mongo_collection


def get_unit_blocks(user, date):

    load_parameters([
        'MONGO_HOST',
        'MONGO_USER',
        'MONGO_PASSWORD',
        'MONGO_DATABASE',
        'MONGO_REPLICASET',
        'MONGO_COLLECTION_ACTIVEBLOCKS',
    ], 'mongo')

    col = get_mongo_collection('ACTIVEBLOCKS')

    # unit_blocks = list(col.find({'userId': {'$eq': user},'eventDate':date},{'unitBlocks':1,'_id':0}))
    unit_blocks = list(col.find({'userId': {'$eq': user}, 'eventDate': date},
                                {'unitBlocks': 1, '_id': 1, 'timeStart': 1, 'timeEnd': 1}).sort('unitBlocks.timeStart',
                                                                                                direction=ASCENDING))
    return unit_blocks


def get_complexity_matrices(athlete, date):
    mongo_unit_blocks = get_unit_blocks(athlete, date)
    dl_comp_matrix = ComplexityMatrix("Double Leg")
    sl_comp_matrix = ComplexityMatrix("Single Leg")

    accumulated_grf_LF = 0
    accumulated_grf_RF = 0
    cnt = 1
    session_position = 0
    sessionTimeStart = mongo_unit_blocks[0].get('timeStart')

    try:
        sessionTimeStart_object = datetime.strptime(sessionTimeStart, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        sessionTimeStart_object = datetime.strptime(sessionTimeStart, '%Y-%m-%d %H:%M:%S')

    active_block_count = 0
    previous_active_block = ""

    for ub in mongo_unit_blocks:

        if len(ub) > 0:
            active_block = str(ub.get('_id'))
            if previous_active_block != active_block:
                active_block_count += 1
            else:
                previous_active_block = active_block
            unit_bock_count = len(ub.get('unitBlocks'))
            for n in range(0, unit_bock_count):
                ubData = ub.get('unitBlocks')[n]

                lf_steps = ubData.get('stepsLF')
                for lf_step in lf_steps:
                    left_step = Step(lf_step, accumulated_grf_LF, 'Left', active_block, n, session_position,
                                     sessionTimeStart_object)
                    left_step.active_block_number = active_block_count
                    accumulated_grf_LF += left_step.total_grf
                    if (left_step.stance_calc == 4):
                        dl_comp_matrix.add_step(left_step)
                    elif (left_step.stance_calc == 2):
                        sl_comp_matrix.add_step(left_step)

                rf_steps = ubData.get('stepsRF')
                for rf_step in rf_steps:
                    right_step = Step(rf_step, accumulated_grf_RF, 'Right', active_block, n, session_position,
                                      sessionTimeStart_object)
                    right_step.active_block_number = active_block_count
                    accumulated_grf_RF += right_step.total_grf
                    if (right_step.stance_calc == 4):
                        dl_comp_matrix.add_step(right_step)
                    elif (right_step.stance_calc == 2):
                        sl_comp_matrix.add_step(right_step)
                session_position = session_position + 1

    mc_sl_list = {}
    mc_sl_list.update(sl_comp_matrix.cells)

    mc_dl_list = {}
    mc_dl_list.update(dl_comp_matrix.cells)

    return mc_sl_list, mc_dl_list


def get_matrix_data_frame(sl_comp_matrix, dl_comp_matrix, variable_name):

    matrix_frame = pandas.DataFrame()

    for sl_cell_key, sl_cell in sl_comp_matrix.cells.items():
       asym = sl_cell.get_asymmetry(variable_name)
       summary = sl_cell.get_summary()
       desc_stats = sl_cell.get_descriptive_stats()
       asym_perc = None
       if(asym.total_sum>0):
           asym_perc = (asym.total_asymmetry/asym.total_sum)*100
       
       ab = pandas.DataFrame(
            {
                'complexity_level':[sl_cell.complexity_level],
                'row':[sl_cell.row_name],
                'column':[sl_cell.column_name],
                'total_duration':[summary.total_duration],
                'left_duration':[summary.left_duration],
                'right_duration':[summary.right_duration],
                'total_steps':[summary.total_steps],
                'left_steps':[summary.left_step_count],
                'right_steps':[summary.right_step_count],
                'left_avg_accum_grf_sec':[summary.left_avg_accumulated_grf_sec],
                'right_avg_accum_grf_sec':[summary.right_avg_accumulated_grf_sec],
                'grf_training_asymmetry':[asym.training_asymmetry],
                'grf_kinematic_asymmetry':[asym.kinematic_asymmetry],
                'grf_total_asymmetry':[asym.total_asymmetry],
                'grf_total_sum':[asym.total_sum],
                'grf_asym_percent':[asym_perc],
                'left_adduc_ROM_mean' :[desc_stats.left_adduc_ROM_mean],
                'left_adduc_ROM_stddev':[desc_stats.left_adduc_ROM_stddev],
                'right_adduc_ROM_mean':[desc_stats.right_adduc_ROM_mean],
                'right_adduc_ROM_stddev':[desc_stats.right_adduc_ROM_stddev],
                'left_adduc_motion_covered_mean':[desc_stats.left_adduc_motion_covered_mean],
                'left_adduc_motion_covered_stddev':[desc_stats.left_adduc_motion_covered_stddev],
                'right_adduc_motion_covered_mean':[desc_stats.right_adduc_motion_covered_mean],
                'right_adduc_motion_covered_stddev':[desc_stats.right_adduc_motion_covered_stddev],
                'left_flex_ROM_mean':[desc_stats.left_flex_ROM_mean],
                'left_flex_ROM_stddev':[desc_stats.left_flex_ROM_stddev],
                'right_flex_ROM_mean':[desc_stats.right_flex_ROM_mean],
                'right_flex_ROM_stddev':[desc_stats.right_flex_ROM_stddev],
                'left_flex_motion_covered_mean':[desc_stats.left_flex_motion_covered_mean],
                'left_flex_motion_covered_stddev':[desc_stats.left_flex_motion_covered_stddev],
                'right_flex_motion_covered_mean':[desc_stats.right_flex_motion_covered_mean],
                'right_flex_motion_covered_stddev':[desc_stats.right_flex_motion_covered_stddev],
                'left_adduc_ROM_hip_mean':[desc_stats.left_adduc_ROM_hip_mean],
                'left_adduc_ROM_hip_stddev':[desc_stats.left_adduc_ROM_hip_stddev],
                'right_adduc_ROM_hip_mean':[desc_stats.right_adduc_ROM_hip_mean],
                'right_adduc_ROM_hip_stddev':[desc_stats.right_adduc_ROM_hip_stddev],
                'left_adduc_motion_covered_hip_mean':[desc_stats.left_adduc_motion_covered_hip_mean],
                'left_adduc_motion_covered_hip_stddev':[desc_stats.left_adduc_motion_covered_hip_stddev],
                'right_adduc_motion_covered_hip_mean':[desc_stats.right_adduc_motion_covered_hip_mean],
                'right_adduc_motion_covered_hip_stddev':[desc_stats.right_adduc_motion_covered_hip_stddev],
                'left_flex_ROM_hip_mean':[desc_stats.left_flex_ROM_hip_mean],
                'left_flex_ROM_hip_stddev':[desc_stats.left_flex_ROM_hip_stddev],
                'right_flex_ROM_hip_mean':[desc_stats.right_flex_ROM_hip_mean],
                'right_flex_ROM_hip_stddev':[desc_stats.right_flex_ROM_hip_stddev],
                'left_flex_motion_covered_hip_mean':[desc_stats.left_flex_motion_covered_hip_mean],
                'left_flex_motion_covered_hip_stddev':[desc_stats.left_flex_motion_covered_hip_stddev],
                'right_flex_motion_covered_hip_mean':[desc_stats.right_flex_motion_covered_hip_mean],
                'right_flex_motion_covered_hip_stddev':[desc_stats.right_flex_motion_covered_hip_stddev],
                'left_adduc_ROM_time_corr':[desc_stats.left_adduc_ROM_time_corr],
                'right_adduc_ROM_time_corr':[desc_stats.right_adduc_ROM_time_corr],
                'left_adduc_motion_covered_time_corr':[desc_stats.left_adduc_motion_covered_time_corr],
                'right_adduc_motion_covered_time_corr':[desc_stats.right_adduc_motion_covered_time_corr]
            },index=["Single Leg"])
       matrix_frame = matrix_frame.append(ab)

    for dl_cell_key, dl_cell in dl_comp_matrix.cells.items():
       asym = dl_cell.get_asymmetry(variable_name)
       summary = dl_cell.get_summary()
       desc_stats = dl_cell.get_descriptive_stats()
       asym_perc = None
       if(asym.total_sum>0):
           asym_perc = (asym.total_asymmetry/asym.total_sum)*100
       ab = pandas.DataFrame(
            {
                'complexity_level':[dl_cell.complexity_level],
                'row':[dl_cell.row_name],
                'column':[dl_cell.column_name],
                'total_duration':[summary.total_duration],
                'left_duration':[summary.left_duration],
                'right_duration':[summary.right_duration],
                'total_steps':[summary.total_steps],
                'left_steps':[summary.left_step_count],
                'right_steps':[summary.right_step_count],
                'left_avg_accum_grf_sec':[summary.left_avg_accumulated_grf_sec],
                'right_avg_accum_grf_sec':[summary.right_avg_accumulated_grf_sec],
                'grf_training_asymmetry':[asym.training_asymmetry],
                'grf_kinematic_asymmetry':[asym.kinematic_asymmetry],
                'grf_total_asymmetry':[asym.total_asymmetry],
                'grf_total_sum':[asym.total_sum],
                'grf_asym_percent':[asym_perc],
                'left_adduc_ROM_mean' :[desc_stats.left_adduc_ROM_mean],
                'left_adduc_ROM_stddev':[desc_stats.left_adduc_ROM_stddev],
                'right_adduc_ROM_mean':[desc_stats.right_adduc_ROM_mean],
                'right_adduc_ROM_stddev':[desc_stats.right_adduc_ROM_stddev],
                'left_adduc_motion_covered_mean':[desc_stats.left_adduc_motion_covered_mean],
                'left_adduc_motion_covered_stddev':[desc_stats.left_adduc_motion_covered_stddev],
                'right_adduc_motion_covered_mean':[desc_stats.right_adduc_motion_covered_mean],
                'right_adduc_motion_covered_stddev':[desc_stats.right_adduc_motion_covered_stddev],
                'left_flex_ROM_mean':[desc_stats.left_flex_ROM_mean],
                'left_flex_ROM_stddev':[desc_stats.left_flex_ROM_stddev],
                'right_flex_ROM_mean':[desc_stats.right_flex_ROM_mean],
                'right_flex_ROM_stddev':[desc_stats.right_flex_ROM_stddev],
                'left_flex_motion_covered_mean':[desc_stats.left_flex_motion_covered_mean],
                'left_flex_motion_covered_stddev':[desc_stats.left_flex_motion_covered_stddev],
                'right_flex_motion_covered_mean':[desc_stats.right_flex_motion_covered_mean],
                'right_flex_motion_covered_stddev':[desc_stats.right_flex_motion_covered_stddev],
                'left_adduc_ROM_hip_mean':[desc_stats.left_adduc_ROM_hip_mean],
                'left_adduc_ROM_hip_stddev':[desc_stats.left_adduc_ROM_hip_stddev],
                'right_adduc_ROM_hip_mean':[desc_stats.right_adduc_ROM_hip_mean],
                'right_adduc_ROM_hip_stddev':[desc_stats.right_adduc_ROM_hip_stddev],
                'left_adduc_motion_covered_hip_mean':[desc_stats.left_adduc_motion_covered_hip_mean],
                'left_adduc_motion_covered_hip_stddev':[desc_stats.left_adduc_motion_covered_hip_stddev],
                'right_adduc_motion_covered_hip_mean':[desc_stats.right_adduc_motion_covered_hip_mean],
                'right_adduc_motion_covered_hip_stddev':[desc_stats.right_adduc_motion_covered_hip_stddev],
                'left_flex_ROM_hip_mean':[desc_stats.left_flex_ROM_hip_mean],
                'left_flex_ROM_hip_stddev':[desc_stats.left_flex_ROM_hip_stddev],
                'right_flex_ROM_hip_mean':[desc_stats.right_flex_ROM_hip_mean],
                'right_flex_ROM_hip_stddev':[desc_stats.right_flex_ROM_hip_stddev],
                'left_flex_motion_covered_hip_mean':[desc_stats.left_flex_motion_covered_hip_mean],
                'left_flex_motion_covered_hip_stddev':[desc_stats.left_flex_motion_covered_hip_stddev],
                'right_flex_motion_covered_hip_mean':[desc_stats.right_flex_motion_covered_hip_mean],
                'right_flex_motion_covered_hip_stddev':[desc_stats.right_flex_motion_covered_hip_stddev],
                'left_adduc_ROM_time_corr':[desc_stats.left_adduc_ROM_time_corr],
                'right_adduc_ROM_time_corr':[desc_stats.right_adduc_ROM_time_corr],
                'left_adduc_motion_covered_time_corr':[desc_stats.left_adduc_motion_covered_time_corr],
                'right_adduc_motion_covered_time_corr':[desc_stats.right_adduc_motion_covered_time_corr]
                
            },index=["Double Leg"])
       matrix_frame = matrix_frame.append(ab)


def get_fatigue_data_frame(mc_sl_list, mc_dl_list, variable_name):

    fatigue_frame = pandas.DataFrame()

    sl_fatigue_list = []
    for mc_sl in mc_sl_list.items():
        mc_sl.calc_fatigue()
        for fat_key, fat_val in mc_sl.fatigue_cells.items():
            sl_fatigue_list.append(fat_val)

    dl_fatigue_list = []
    for mc_dl in mc_dl_list.items():
        mc_dl.calc_fatigue()
        for fat_key, fat_val in mc_dl.fatigue_cells.items():
            dl_fatigue_list.append(fat_val)

    for fatigue in sl_fatigue_list:
        asym = fatigue.get_asymmetry(variable_name)
        summary = fatigue.get_summary()
        desc_stats = fatigue.get_descriptive_stats()
        asym_perc = None
        if (asym.total_sum > 0):
            asym_perc = (asym.total_asymmetry / asym.total_sum) * 100

        ab = pandas.DataFrame(
            {
                'complexity_level': [fatigue.complexity_level],
                'fatigue_level': [fatigue.fatigue_level],
                'total_duration': [summary.total_duration],
                'left_duration': [summary.left_duration],
                'right_duration': [summary.right_duration],
                'total_steps': [summary.total_steps],
                'left_steps': [summary.left_step_count],
                'right_steps': [summary.right_step_count],
                'left_avg_accum_grf_sec': [summary.left_avg_accumulated_grf_sec],
                'right_avg_accum_grf_sec': [summary.right_avg_accumulated_grf_sec],
                'grf_training_asymmetry': [asym.training_asymmetry],
                'grf_kinematic_asymmetry': [asym.kinematic_asymmetry],
                'grf_total_asymmetry': [asym.total_asymmetry],
                'grf_total_sum': [asym.total_sum],
                'grf_asym_percent': [asym_perc],
                'left_adduc_ROM_mean': [desc_stats.left_adduc_ROM_mean],
                'left_adduc_ROM_stddev': [desc_stats.left_adduc_ROM_stddev],
                'right_adduc_ROM_mean': [desc_stats.right_adduc_ROM_mean],
                'right_adduc_ROM_stddev': [desc_stats.right_adduc_ROM_stddev],
                'left_adduc_motion_covered_mean': [desc_stats.left_adduc_motion_covered_mean],
                'left_adduc_motion_covered_stddev': [desc_stats.left_adduc_motion_covered_stddev],
                'right_adduc_motion_covered_mean': [desc_stats.right_adduc_motion_covered_mean],
                'right_adduc_motion_covered_stddev': [desc_stats.right_adduc_motion_covered_stddev],
                'left_flex_ROM_mean': [desc_stats.left_flex_ROM_mean],
                'left_flex_ROM_stddev': [desc_stats.left_flex_ROM_stddev],
                'right_flex_ROM_mean': [desc_stats.right_flex_ROM_mean],
                'right_flex_ROM_stddev': [desc_stats.right_flex_ROM_stddev],
                'left_flex_motion_covered_mean': [desc_stats.left_flex_motion_covered_mean],
                'left_flex_motion_covered_stddev': [desc_stats.left_flex_motion_covered_stddev],
                'right_flex_motion_covered_mean': [desc_stats.right_flex_motion_covered_mean],
                'right_flex_motion_covered_stddev': [desc_stats.right_flex_motion_covered_stddev],
                'left_adduc_ROM_hip_mean': [desc_stats.left_adduc_ROM_hip_mean],
                'left_adduc_ROM_hip_stddev': [desc_stats.left_adduc_ROM_hip_stddev],
                'right_adduc_ROM_hip_mean': [desc_stats.right_adduc_ROM_hip_mean],
                'right_adduc_ROM_hip_stddev': [desc_stats.right_adduc_ROM_hip_stddev],
                'left_adduc_motion_covered_hip_mean': [desc_stats.left_adduc_motion_covered_hip_mean],
                'left_adduc_motion_covered_hip_stddev': [desc_stats.left_adduc_motion_covered_hip_stddev],
                'right_adduc_motion_covered_hip_mean': [desc_stats.right_adduc_motion_covered_hip_mean],
                'right_adduc_motion_covered_hip_stddev': [desc_stats.right_adduc_motion_covered_hip_stddev],
                'left_flex_ROM_hip_mean': [desc_stats.left_flex_ROM_hip_mean],
                'left_flex_ROM_hip_stddev': [desc_stats.left_flex_ROM_hip_stddev],
                'right_flex_ROM_hip_mean': [desc_stats.right_flex_ROM_hip_mean],
                'right_flex_ROM_hip_stddev': [desc_stats.right_flex_ROM_hip_stddev],
                'left_flex_motion_covered_hip_mean': [desc_stats.left_flex_motion_covered_hip_mean],
                'left_flex_motion_covered_hip_stddev': [desc_stats.left_flex_motion_covered_hip_stddev],
                'right_flex_motion_covered_hip_mean': [desc_stats.right_flex_motion_covered_hip_mean],
                'right_flex_motion_covered_hip_stddev': [desc_stats.right_flex_motion_covered_hip_stddev],
                'left_adduc_ROM_time_corr': [desc_stats.left_adduc_ROM_time_corr],
                'right_adduc_ROM_time_corr': [desc_stats.right_adduc_ROM_time_corr],
                'left_adduc_motion_covered_time_corr': [desc_stats.left_adduc_motion_covered_time_corr],
                'right_adduc_motion_covered_time_corr': [desc_stats.right_adduc_motion_covered_time_corr]
            }, index=["Single Leg"])
        fatigue_frame = fatigue_frame.append(ab)

    for fatigue in dl_fatigue_list:
        asym = fatigue.get_asymmetry(variable_name)
        summary = fatigue.get_summary()
        desc_stats = fatigue.get_descriptive_stats()
        asym_perc = None
        if (asym.total_sum > 0):
            asym_perc = (asym.total_asymmetry / asym.total_sum) * 100

        ab = pandas.DataFrame(
            {
                'complexity_level': [fatigue.complexity_level],
                'fatigue_level': [fatigue.fatigue_level],
                'total_duration': [summary.total_duration],
                'left_duration': [summary.left_duration],
                'right_duration': [summary.right_duration],
                'total_steps': [summary.total_steps],
                'left_steps': [summary.left_step_count],
                'right_steps': [summary.right_step_count],
                'left_avg_accum_grf_sec': [summary.left_avg_accumulated_grf_sec],
                'right_avg_accum_grf_sec': [summary.right_avg_accumulated_grf_sec],
                'grf_training_asymmetry': [asym.training_asymmetry],
                'grf_kinematic_asymmetry': [asym.kinematic_asymmetry],
                'grf_total_asymmetry': [asym.total_asymmetry],
                'grf_total_sum': [asym.total_sum],
                'grf_asym_percent': [asym_perc],
                'left_adduc_ROM_mean': [desc_stats.left_adduc_ROM_mean],
                'left_adduc_ROM_stddev': [desc_stats.left_adduc_ROM_stddev],
                'right_adduc_ROM_mean': [desc_stats.right_adduc_ROM_mean],
                'right_adduc_ROM_stddev': [desc_stats.right_adduc_ROM_stddev],
                'left_adduc_motion_covered_mean': [desc_stats.left_adduc_motion_covered_mean],
                'left_adduc_motion_covered_stddev': [desc_stats.left_adduc_motion_covered_stddev],
                'right_adduc_motion_covered_mean': [desc_stats.right_adduc_motion_covered_mean],
                'right_adduc_motion_covered_stddev': [desc_stats.right_adduc_motion_covered_stddev],
                'left_flex_ROM_mean': [desc_stats.left_flex_ROM_mean],
                'left_flex_ROM_stddev': [desc_stats.left_flex_ROM_stddev],
                'right_flex_ROM_mean': [desc_stats.right_flex_ROM_mean],
                'right_flex_ROM_stddev': [desc_stats.right_flex_ROM_stddev],
                'left_flex_motion_covered_mean': [desc_stats.left_flex_motion_covered_mean],
                'left_flex_motion_covered_stddev': [desc_stats.left_flex_motion_covered_stddev],
                'right_flex_motion_covered_mean': [desc_stats.right_flex_motion_covered_mean],
                'right_flex_motion_covered_stddev': [desc_stats.right_flex_motion_covered_stddev],
                'left_adduc_ROM_hip_mean': [desc_stats.left_adduc_ROM_hip_mean],
                'left_adduc_ROM_hip_stddev': [desc_stats.left_adduc_ROM_hip_stddev],
                'right_adduc_ROM_hip_mean': [desc_stats.right_adduc_ROM_hip_mean],
                'right_adduc_ROM_hip_stddev': [desc_stats.right_adduc_ROM_hip_stddev],
                'left_adduc_motion_covered_hip_mean': [desc_stats.left_adduc_motion_covered_hip_mean],
                'left_adduc_motion_covered_hip_stddev': [desc_stats.left_adduc_motion_covered_hip_stddev],
                'right_adduc_motion_covered_hip_mean': [desc_stats.right_adduc_motion_covered_hip_mean],
                'right_adduc_motion_covered_hip_stddev': [desc_stats.right_adduc_motion_covered_hip_stddev],
                'left_flex_ROM_hip_mean': [desc_stats.left_flex_ROM_hip_mean],
                'left_flex_ROM_hip_stddev': [desc_stats.left_flex_ROM_hip_stddev],
                'right_flex_ROM_hip_mean': [desc_stats.right_flex_ROM_hip_mean],
                'right_flex_ROM_hip_stddev': [desc_stats.right_flex_ROM_hip_stddev],
                'left_flex_motion_covered_hip_mean': [desc_stats.left_flex_motion_covered_hip_mean],
                'left_flex_motion_covered_hip_stddev': [desc_stats.left_flex_motion_covered_hip_stddev],
                'right_flex_motion_covered_hip_mean': [desc_stats.right_flex_motion_covered_hip_mean],
                'right_flex_motion_covered_hip_stddev': [desc_stats.right_flex_motion_covered_hip_stddev],
                'left_adduc_ROM_time_corr': [desc_stats.left_adduc_ROM_time_corr],
                'right_adduc_ROM_time_corr': [desc_stats.right_adduc_ROM_time_corr],
                'left_adduc_motion_covered_time_corr': [desc_stats.left_adduc_motion_covered_time_corr],
                'right_adduc_motion_covered_time_corr': [desc_stats.right_adduc_motion_covered_time_corr]
            }, index=["Double Leg"])
        fatigue_frame = fatigue_frame.append(ab)


def get_asymmetry_data_frame(mc_sl_list, mc_dl_list, variable_name):

    complexity_frame = pandas.DataFrame()

    for keys, msl  in mc_sl_list.items():
        asym = msl.get_asymmetry(variable_name)
        summary = msl.get_summary()
        desc_stats = msl.get_descriptive_stats()
        asym_perc = None
        if (asym.total_sum > 0):
            asym_perc = (asym.total_asymmetry / asym.total_sum) * 100

        ab = pandas.DataFrame(
            {
                'complexity_level': [msl.complexity_level],
                'row_name': [msl.row_name],
                'column_name': [msl.column_name],
                'total_duration': [summary.total_duration],
                'left_duration': [summary.left_duration],
                'right_duration': [summary.right_duration],
                'total_steps': [summary.total_steps],
                'left_steps': [summary.left_step_count],
                'right_steps': [summary.right_step_count],
                'left_avg_accum_grf_sec': [summary.left_avg_accumulated_grf_sec],
                'right_avg_accum_grf_sec': [summary.right_avg_accumulated_grf_sec],
                'grf_training_asymmetry': [asym.training_asymmetry],
                'grf_kinematic_asymmetry': [asym.kinematic_asymmetry],
                'grf_total_asymmetry': [asym.total_asymmetry],
                'grf_total_sum': [asym.total_sum],
                'grf_asym_percent': [asym_perc],
                'left_adduc_ROM_mean': [desc_stats.left_adduc_ROM_mean],
                'left_adduc_ROM_stddev': [desc_stats.left_adduc_ROM_stddev],
                'right_adduc_ROM_mean': [desc_stats.right_adduc_ROM_mean],
                'right_adduc_ROM_stddev': [desc_stats.right_adduc_ROM_stddev],
                'left_adduc_motion_covered_mean': [desc_stats.left_adduc_motion_covered_mean],
                'left_adduc_motion_covered_stddev': [desc_stats.left_adduc_motion_covered_stddev],
                'right_adduc_motion_covered_mean': [desc_stats.right_adduc_motion_covered_mean],
                'right_adduc_motion_covered_stddev': [desc_stats.right_adduc_motion_covered_stddev],
                'left_flex_ROM_mean': [desc_stats.left_flex_ROM_mean],
                'left_flex_ROM_stddev': [desc_stats.left_flex_ROM_stddev],
                'right_flex_ROM_mean': [desc_stats.right_flex_ROM_mean],
                'right_flex_ROM_stddev': [desc_stats.right_flex_ROM_stddev],
                'left_flex_motion_covered_mean': [desc_stats.left_flex_motion_covered_mean],
                'left_flex_motion_covered_stddev': [desc_stats.left_flex_motion_covered_stddev],
                'right_flex_motion_covered_mean': [desc_stats.right_flex_motion_covered_mean],
                'right_flex_motion_covered_stddev': [desc_stats.right_flex_motion_covered_stddev],
                'left_adduc_ROM_hip_mean': [desc_stats.left_adduc_ROM_hip_mean],
                'left_adduc_ROM_hip_stddev': [desc_stats.left_adduc_ROM_hip_stddev],
                'right_adduc_ROM_hip_mean': [desc_stats.right_adduc_ROM_hip_mean],
                'right_adduc_ROM_hip_stddev': [desc_stats.right_adduc_ROM_hip_stddev],
                'left_adduc_motion_covered_hip_mean': [desc_stats.left_adduc_motion_covered_hip_mean],
                'left_adduc_motion_covered_hip_stddev': [desc_stats.left_adduc_motion_covered_hip_stddev],
                'right_adduc_motion_covered_hip_mean': [desc_stats.right_adduc_motion_covered_hip_mean],
                'right_adduc_motion_covered_hip_stddev': [desc_stats.right_adduc_motion_covered_hip_stddev],
                'left_flex_ROM_hip_mean': [desc_stats.left_flex_ROM_hip_mean],
                'left_flex_ROM_hip_stddev': [desc_stats.left_flex_ROM_hip_stddev],
                'right_flex_ROM_hip_mean': [desc_stats.right_flex_ROM_hip_mean],
                'right_flex_ROM_hip_stddev': [desc_stats.right_flex_ROM_hip_stddev],
                'left_flex_motion_covered_hip_mean': [desc_stats.left_flex_motion_covered_hip_mean],
                'left_flex_motion_covered_hip_stddev': [desc_stats.left_flex_motion_covered_hip_stddev],
                'right_flex_motion_covered_hip_mean': [desc_stats.right_flex_motion_covered_hip_mean],
                'right_flex_motion_covered_hip_stddev': [desc_stats.right_flex_motion_covered_hip_stddev],
                'left_adduc_ROM_time_corr': [desc_stats.left_adduc_ROM_time_corr],
                'right_adduc_ROM_time_corr': [desc_stats.right_adduc_ROM_time_corr],
                'left_adduc_motion_covered_time_corr': [desc_stats.left_adduc_motion_covered_time_corr],
                'right_adduc_motion_covered_time_corr': [desc_stats.right_adduc_motion_covered_time_corr]
            }, index=["Single Leg"])
        complexity_frame = complexity_frame.append(ab)

    for keys, mdl  in mc_dl_list.items():
        asym = mdl.get_asymmetry(variable_name)
        summary = mdl.get_summary()
        desc_stats = mdl.get_descriptive_stats()
        asym_perc = None
        if (asym.total_sum > 0):
            asym_perc = (asym.total_asymmetry / asym.total_sum) * 100

        ab = pandas.DataFrame(
            {
                'complexity_level': [mdl.complexity_level],
                'row_name': [mdl.row_name],
                'column_name': [mdl.column_name],
                'total_duration': [summary.total_duration],
                'left_duration': [summary.left_duration],
                'right_duration': [summary.right_duration],
                'total_steps': [summary.total_steps],
                'left_steps': [summary.left_step_count],
                'right_steps': [summary.right_step_count],
                'left_avg_accum_grf_sec': [summary.left_avg_accumulated_grf_sec],
                'right_avg_accum_grf_sec': [summary.right_avg_accumulated_grf_sec],
                'grf_training_asymmetry': [asym.training_asymmetry],
                'grf_kinematic_asymmetry': [asym.kinematic_asymmetry],
                'grf_total_asymmetry': [asym.total_asymmetry],
                'grf_total_sum': [asym.total_sum],
                'grf_asym_percent': [asym_perc],
                'left_adduc_ROM_mean': [desc_stats.left_adduc_ROM_mean],
                'left_adduc_ROM_stddev': [desc_stats.left_adduc_ROM_stddev],
                'right_adduc_ROM_mean': [desc_stats.right_adduc_ROM_mean],
                'right_adduc_ROM_stddev': [desc_stats.right_adduc_ROM_stddev],
                'left_adduc_motion_covered_mean': [desc_stats.left_adduc_motion_covered_mean],
                'left_adduc_motion_covered_stddev': [desc_stats.left_adduc_motion_covered_stddev],
                'right_adduc_motion_covered_mean': [desc_stats.right_adduc_motion_covered_mean],
                'right_adduc_motion_covered_stddev': [desc_stats.right_adduc_motion_covered_stddev],
                'left_flex_ROM_mean': [desc_stats.left_flex_ROM_mean],
                'left_flex_ROM_stddev': [desc_stats.left_flex_ROM_stddev],
                'right_flex_ROM_mean': [desc_stats.right_flex_ROM_mean],
                'right_flex_ROM_stddev': [desc_stats.right_flex_ROM_stddev],
                'left_flex_motion_covered_mean': [desc_stats.left_flex_motion_covered_mean],
                'left_flex_motion_covered_stddev': [desc_stats.left_flex_motion_covered_stddev],
                'right_flex_motion_covered_mean': [desc_stats.right_flex_motion_covered_mean],
                'right_flex_motion_covered_stddev': [desc_stats.right_flex_motion_covered_stddev],
                'left_adduc_ROM_hip_mean': [desc_stats.left_adduc_ROM_hip_mean],
                'left_adduc_ROM_hip_stddev': [desc_stats.left_adduc_ROM_hip_stddev],
                'right_adduc_ROM_hip_mean': [desc_stats.right_adduc_ROM_hip_mean],
                'right_adduc_ROM_hip_stddev': [desc_stats.right_adduc_ROM_hip_stddev],
                'left_adduc_motion_covered_hip_mean': [desc_stats.left_adduc_motion_covered_hip_mean],
                'left_adduc_motion_covered_hip_stddev': [desc_stats.left_adduc_motion_covered_hip_stddev],
                'right_adduc_motion_covered_hip_mean': [desc_stats.right_adduc_motion_covered_hip_mean],
                'right_adduc_motion_covered_hip_stddev': [desc_stats.right_adduc_motion_covered_hip_stddev],
                'left_flex_ROM_hip_mean': [desc_stats.left_flex_ROM_hip_mean],
                'left_flex_ROM_hip_stddev': [desc_stats.left_flex_ROM_hip_stddev],
                'right_flex_ROM_hip_mean': [desc_stats.right_flex_ROM_hip_mean],
                'right_flex_ROM_hip_stddev': [desc_stats.right_flex_ROM_hip_stddev],
                'left_flex_motion_covered_hip_mean': [desc_stats.left_flex_motion_covered_hip_mean],
                'left_flex_motion_covered_hip_stddev': [desc_stats.left_flex_motion_covered_hip_stddev],
                'right_flex_motion_covered_hip_mean': [desc_stats.right_flex_motion_covered_hip_mean],
                'right_flex_motion_covered_hip_stddev': [desc_stats.right_flex_motion_covered_hip_stddev],
                'left_adduc_ROM_time_corr': [desc_stats.left_adduc_ROM_time_corr],
                'right_adduc_ROM_time_corr': [desc_stats.right_adduc_ROM_time_corr],
                'left_adduc_motion_covered_time_corr': [desc_stats.left_adduc_motion_covered_time_corr],
                'right_adduc_motion_covered_time_corr': [desc_stats.right_adduc_motion_covered_time_corr]
            }, index=["Double Leg"])
        complexity_frame = complexity_frame.append(ab)

    return complexity_frame


def get_kruskal_data_frame(mc_sl_list, mc_dl_list):

    kruskal_calcs_frame = pandas.DataFrame()

    for keys, mcsl in mc_sl_list.items():
        kruskal_calcs = mcsl.get_kruskal_calculations()
        ab = pandas.DataFrame(
            {
                'complexity_level': [mcsl.complexity_level],
                'row_name': [mcsl.row_name],
                'column_name': [mcsl.column_name],
                'adduc_ROM': [kruskal_calcs.adduc_ROM],
                'adduc_motion_covered': [kruskal_calcs.adduc_motion_covered],
                'flex_ROM': [kruskal_calcs.flex_ROM],
                'flex_motion_covered': [kruskal_calcs.flex_motion_covered],
                'adduc_ROM_hip': [kruskal_calcs.adduc_ROM_hip],
                'adduc_motion_covered_hip': [kruskal_calcs.adduc_motion_covered_hip],
                'flex_ROM_hip': [kruskal_calcs.flex_ROM_hip],
                'flex_motion_covered_hip': [kruskal_calcs.flex_motion_covered_hip]
            }, index=["Single Leg"])
        kruskal_calcs_frame = kruskal_calcs_frame.append(ab)

    for keys, mcdl in mc_dl_list.items():
        kruskal_calcs = mcdl.get_kruskal_calculations()
        ab = pandas.DataFrame(
            {
                'complexity_level': [mcdl.complexity_level],
                'row_name': [mcdl.row_name],
                'column_name': [mcdl.column_name],
                'adduc_ROM': [kruskal_calcs.adduc_ROM],
                'adduc_motion_covered': [kruskal_calcs.adduc_motion_covered],
                'flex_ROM': [kruskal_calcs.flex_ROM],
                'flex_motion_covered': [kruskal_calcs.flex_motion_covered],
                'adduc_ROM_hip': [kruskal_calcs.adduc_ROM_hip],
                'adduc_motion_covered_hip': [kruskal_calcs.adduc_motion_covered_hip],
                'flex_ROM_hip': [kruskal_calcs.flex_ROM_hip],
                'flex_motion_covered_hip': [kruskal_calcs.flex_motion_covered_hip]
            }, index=["Double Leg"])
        kruskal_calcs_frame = kruskal_calcs_frame.append(ab)

    return kruskal_calcs_frame


def get_fatigue_events(mc_sl_list, mc_dl_list):


    fatigue_events = []

    for keys, mcsl in mc_sl_list.items():
        differs = mcsl.get_decay_parameters()
        for difs in differs:
            # ab = pandas.DataFrame(
            #   {
            #      'complexity_level':[mcsl.complexity_level],
            #     'row_name':[mcsl.row_name],
            #      'column_name':[mcsl.column_name],
            #      'adduc_ROM_LF':[difs.adduc_ROM_LF],
            #      'adduc_ROM_RF':[difs.adduc_ROM_RF],
            #      'adduc_pronation_LF':[difs.adduc_pronation_LF],
            #      'adduc_pronation_RF':[difs.adduc_pronation_RF],
            #      'adduc_supination_LF':[difs.adduc_supination_LF],
            #      'adduc_supination_RF':[difs.adduc_supination_RF],
            #      'flex_ROM_LF':[difs.flex_ROM_LF],
            #      'flex_ROM_RF':[difs.flex_ROM_RF],
            #      'dorsiflexion_LF':[difs.dorsiflexion_LF],
            #      'plantarflexion_LF':[difs.plantarflexion_LF],
            #      'dorsiflexion_RF':[difs.dorsiflexion_RF],
            #      'plantarflexion_RF':[difs.plantarflexion_RF],
            #      'adduc_ROM_hip_LF':[difs.adduc_ROM_hip_LF],
            #      'adduc_ROM_hip_RF':[difs.adduc_ROM_hip_RF],
            #      'adduc_positive_hip_LF':[difs.adduc_positive_hip_LF],
            #      'adduc_positive_hip_RF':[difs.adduc_positive_hip_RF],
            #      'adduc_negative_hip_LF':[difs.adduc_negative_hip_LF],
            #      'adduc_negative_hip_RF':[difs.adduc_negative_hip_RF],
            #      'flex_ROM_hip_LF':[difs.flex_ROM_hip_LF],
            #      'flex_ROM_hip_RF':[difs.flex_ROM_hip_RF],
            #      'flex_positive_hip_LF':[difs.flex_positive_hip_LF],
            #      'flex_positive_hip_RF':[difs.flex_positive_hip_RF],
            #      'flex_negative_hip_LF':[difs.flex_negative_hip_LF],
            #      'flex_negative_hip_RF':[difs.flex_negative_hip_RF],
            #  },index=["Single Leg"])
            ab = FatigueEvent(mcsl.row_name, mcsl.column_name)
            ab.active_block_id = difs.active_block_id
            ab.complexity_level = difs.complexity_level
            ab.attribute_name = difs.attribute_name
            ab.attribute_label = difs.label
            ab.orientation = difs.orientation
            ab.cumulative_end_time = difs.end_time
            ab.z_score = difs.z_score
            ab.raw_value = difs.raw_value
            ab.stance = "Single Leg"
            ab.time_block = str(difs.time_block)

            #ab = pandas.DataFrame({
            #    'active_block': [difs.active_block_id],
            #    'row_name': [mcsl.row_name],
            #    'column_name': [mcsl.column_name],
            #    'complexity_level': [difs.complexity_level],
            #    'attribute_name': [difs.attribute_name],
            #    'label': [difs.label],
            #    'orientation': [difs.orientation],
            #    'cumulative_end_time': [difs.end_time],
            #    'z_score': [difs.z_score],
            #    'raw_value': [difs.raw_value]
            #}, index=["Single Leg"])
            #decay_frame = decay_frame.append(ab)
            fatigue_events.append(ab)
    # decay_frame.to_csv('C:\\UNC\\v6\\outliers_'+athlete+'_'+date+'v6.csv',sep=',',index_label='Stance',columns=[
    #    'active_block','complexity_level','attribute_name','label','orientation','cumulative_end_time','z_score','raw_value'])

    for keys, mcdl in mc_dl_list.items():
        differs = mcdl.get_decay_parameters()
        for difs in differs:
            # ab = pandas.DataFrame(
            #    {
            #        'complexity_level':[mcdl.complexity_level],
            #        'row_name':[mcdl.row_name],
            #        'column_name':[mcdl.column_name],
            #        'adduc_ROM_LF':[difs.adduc_ROM_LF],
            #        'adduc_ROM_RF':[difs.adduc_ROM_RF],
            #        'adduc_pronation_LF':[difs.adduc_pronation_LF],
            #        'adduc_pronation_RF':[difs.adduc_pronation_RF],
            #        'adduc_supination_LF':[difs.adduc_supination_LF],
            #        'adduc_supination_RF':[difs.adduc_supination_RF],
            #        'flex_ROM_LF':[difs.flex_ROM_LF],
            #        'flex_ROM_RF':[difs.flex_ROM_RF],
            #        'dorsiflexion_LF':[difs.dorsiflexion_LF],
            #        'plantarflexion_LF':[difs.plantarflexion_LF],
            #        'dorsiflexion_RF':[difs.dorsiflexion_RF],
            #        'plantarflexion_RF':[difs.plantarflexion_RF],
            #        'adduc_ROM_hip_LF':[difs.adduc_ROM_hip_LF],
            #        'adduc_ROM_hip_RF':[difs.adduc_ROM_hip_RF],
            #        'adduc_positive_hip_LF':[difs.adduc_positive_hip_LF],
            #        'adduc_positive_hip_RF':[difs.adduc_positive_hip_RF],
            #        'adduc_negative_hip_LF':[difs.adduc_negative_hip_LF],
            #        'adduc_negative_hip_RF':[difs.adduc_negative_hip_RF],
            #        'flex_ROM_hip_LF':[difs.flex_ROM_hip_LF],
            #        'flex_ROM_hip_RF':[difs.flex_ROM_hip_RF],
            #        'flex_positive_hip_LF':[difs.flex_positive_hip_LF],
            #        'flex_positive_hip_RF':[difs.flex_positive_hip_RF],
            #        'flex_negative_hip_LF':[difs.flex_negative_hip_LF],
            #        'flex_negative_hip_RF':[difs.flex_negative_hip_RF],
            #    },index=["Double Leg"])

            #ab = pandas.DataFrame({
            #    'active_block': [difs.active_block_id],
            #    'row_name': [mcdl.row_name],
            #    'column_name': [mcdl.column_name],
            #    'complexity_level': [difs.complexity_level],
            #    'attribute_name': [difs.attribute_name],
            #    'label': [difs.label],
            #    'orientation': [difs.orientation],
            #    'cumulative_end_time': [difs.end_time],
            #    'z_score': [difs.z_score],
            #    'raw_value': [difs.raw_value]
            #}, index=["Double Leg"])
            #decay_frame = decay_frame.append(ab)

            ab = FatigueEvent(mcdl.row_name, mcdl.column_name)
            ab.active_block_id = difs.active_block_id
            ab.complexity_level = difs.complexity_level
            ab.attribute_name = difs.attribute_name
            ab.attribute_label = difs.label
            ab.orientation = difs.orientation
            ab.cumulative_end_time = difs.end_time
            ab.z_score = difs.z_score
            ab.raw_value = difs.raw_value
            ab.stance = "Double Leg"
            ab.time_block = str(difs.time_block)
            fatigue_events.append(ab)

    return fatigue_events
