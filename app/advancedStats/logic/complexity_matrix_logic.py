from datetime import datetime

from pymongo import ASCENDING

from models.complexity_matrix import ComplexityMatrix
from models.step import Step
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
                    #accumulated_grf_LF += left_step.total_grf
                    if left_step.peak_grf is not None:
                        accumulated_grf_LF += left_step.peak_grf
                    else:
                        accumulated_grf_LF += 0
                    if (left_step.stance_calc == 4):
                        dl_comp_matrix.add_step(left_step)
                    elif (left_step.stance_calc == 2):
                        sl_comp_matrix.add_step(left_step)

                rf_steps = ubData.get('stepsRF')
                for rf_step in rf_steps:
                    right_step = Step(rf_step, accumulated_grf_RF, 'Right', active_block, n, session_position,
                                      sessionTimeStart_object)
                    right_step.active_block_number = active_block_count
                    # accumulated_grf_RF += right_step.total_grf
                    if right_step.peak_grf is not None:
                        accumulated_grf_RF += right_step.peak_grf
                    else:
                        accumulated_grf_RF += 0
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