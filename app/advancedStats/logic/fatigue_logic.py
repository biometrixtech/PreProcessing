from advancedStats.models.fatigue import FatigueEvent


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