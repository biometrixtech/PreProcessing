from __future__ import print_function
import pandas
import os
import cStringIO
import boto3
from logic.training_volume_logic import TrainingVolumeProcessor
from config import get_mongo_collection
import summary_analysis
# import logic.complexity_matrix_logic
from logic.fatigue_logic import FatigueProcessor
from logic.asymmetry_logic import AsymmetryProcessor
from logic import complexity_matrix_logic
from models.fatigue import SessionFatigue

def script_handler(working_directory, input_data):
    print("Running Advanced aggregations")

    try:
        mongo_collection_blocks = get_mongo_collection('ACTIVEBLOCKS')

        user_id = input_data.get('UserId', None)
        event_date = input_data.get('EventDate')

        # user_id = "Maggie"
        # event_date = "2018-04-24"

        # output_path = "~/demo5/"
        output_path = working_directory

        # write out active blocks
        summary_analysis.query_mongo_ab(mongo_collection_blocks, user_id, event_date, output_path)
        write_file_to_s3(output_path+'ab-'+user_id+'_'+event_date+'.csv', '_'.join([event_date, user_id]) + "/ab.csv")
        mc_sl_list, mc_dl_list = complexity_matrix_logic.get_complexity_matrices(user_id, event_date)

        training_volume_processor = TrainingVolumeProcessor()
        fatigue_processor = FatigueProcessor()
        asymmetry_processor = AsymmetryProcessor(user_id, event_date, "", mc_sl_list, mc_dl_list)

        session_training_volume_data = training_volume_processor.get_session_training_volume_data(user_id, event_date)

        fatigue_events = fatigue_processor.get_fatigue_events(mc_sl_list, mc_dl_list)

        session_fatigue = SessionFatigue(user_id, event_date, "", fatigue_events)

        fatigue_cma_grf_crosstab = session_fatigue.cma_grf_crosstab()

        fatigue_ab_crosstab = session_fatigue.active_block_crosstab()

        session_asymmetry = asymmetry_processor.get_session_asymmetry()
        movement_events = asymmetry_processor.get_movement_asymmetries()
        loading_events = asymmetry_processor.get_loading_asymmetries()

        write_session_workload_summary(event_date, output_path, session_training_volume_data, user_id)
        write_intensity_bands(event_date, output_path, session_training_volume_data, user_id)
        write_fatigue_cross_tab(event_date, fatigue_cma_grf_crosstab, output_path, user_id)
        write_fatigue_active_block_cross_tab(fatigue_ab_crosstab, event_date, output_path, user_id)
        write_rel_magnitude(event_date, output_path, session_asymmetry, user_id)
        write_loading_movement_asymmetry(event_date, loading_events, movement_events, output_path, user_id)


    except Exception as e:
        print(e)
        print('Process did not complete successfully! See error below!')
        raise


def write_session_workload_summary(event_date, output_path, session_training_volume_data, user_id):
    training_data = pandas.DataFrame({
        'accumulated_grf': [session_training_volume_data.accumulated_grf],
        'cma': [session_training_volume_data.cma],
        'active_time': [session_training_volume_data.active_time],
        'gct_left': [session_training_volume_data.ground_contact_time_left],
        'gct_right': [session_training_volume_data.ground_contact_time_right],
        'avg_peak_grf_left': [session_training_volume_data.average_peak_vertical_grf_lf],
        'avg_peak_grf_right': [session_training_volume_data.average_peak_vertical_grf_rf],
        'avg_grf': [session_training_volume_data.average_total_GRF],
        'agg_peak_accel': [session_training_volume_data.average_peak_acceleration],

    }, index=["Summary"])
    training_data.to_csv(output_path + 'session_workload_summary' + user_id + '_' + event_date + '.csv', sep=',',
                         index_label='Level')
    file_name =  '_'.join([event_date, user_id]) + '/session_workload_summary.csv'
    write_file_to_s3(output_path + 'session_workload_summary' + user_id + '_' + event_date + '.csv', file_name)


def write_intensity_bands(event_date, output_path, session_training_volume_data, user_id):
    intensity_df = pandas.DataFrame()
    intensity_df = intensity_df.append(convert_intensity_band_to_csv(session_training_volume_data.intensity_bands.low))
    intensity_df = intensity_df.append(convert_intensity_band_to_csv(session_training_volume_data.intensity_bands.moderate))
    intensity_df = intensity_df.append(convert_intensity_band_to_csv(session_training_volume_data.intensity_bands.high))
    intensity_df = intensity_df.append(convert_intensity_band_to_csv(session_training_volume_data.intensity_bands.total))
    columns=[
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
            'right_gct_percentage', ]
    intensity_df.to_csv(output_path + 'session_intensity_bands' + user_id + '_' + event_date + '.csv', sep=',',
                        index_label='Level', columns=columns)
    file_name = '_'.join([event_date, user_id]) + '/session_intensity_bands.csv'
    write_file_to_s3(output_path + 'session_intensity_bands' + user_id + '_' + event_date + '.csv', file_name)


def write_fatigue_cross_tab(event_date, fatigue_cma_grf_crosstab, output_path, user_id):
    fatigue_frame = pandas.DataFrame()
    for f in fatigue_cma_grf_crosstab:
        ab = pandas.DataFrame({
            # 'stance': [f.stance],
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

    columns = [
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
                ]
    if fatigue_frame.shape[0] > 0:
        fatigue_frame.to_csv(output_path + 'fatigue_xtab_' + user_id + '_' + event_date + '.csv', sep=',',
                             index_label='Stance', columns=columns)
        file_name = '_'.join([event_date, user_id]) + '/fatigue_xtab.csv'
        write_file_to_s3(output_path + 'fatigue_xtab_' + user_id + '_' + event_date + '.csv', file_name)


def write_fatigue_active_block_cross_tab(fatigue_ab_crosstab, event_date, output_path, user_id):
    fatigue_frame = pandas.DataFrame()
    for f in fatigue_ab_crosstab:
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

    columns = [
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
                ]
    if fatigue_frame.shape[0] > 0:
        fatigue_frame.to_csv(output_path + 'fatigue_ab_xtab_' + user_id + '_' + event_date + '.csv', sep=',',
                             index_label='Active Block', columns=columns)
        file_name = '_'.join([event_date, user_id]) + '/fatigue_ab_xtab.csv'
        write_file_to_s3(output_path + 'fatigue_ab_xtab_' + user_id + '_' + event_date + '.csv', file_name)


def write_loading_movement_asymmetry(event_date, loading_events, movement_events, output_path, user_id):
    df = pandas.DataFrame()
    for d in movement_events:
        for f in loading_events:
            if d.cma_level == f.cma_level and d.grf_level == f.grf_level and d.stance == f.stance:
                ab = pandas.DataFrame({
                    # 'complexity_level': [f.complexity_level],
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
    columns = [
              # 'complexity_level',
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
              ]
    df.to_csv(output_path + 'loading_movement_asymm_' + user_id + '_' + event_date + '.csv', sep=',',
              index_label='Stance', columns=columns)
    file_name = '_'.join([event_date, user_id]) + '/loading_movement_asymm.csv'
    write_file_to_s3(output_path + 'loading_movement_asymm_' + user_id + '_' + event_date + '.csv', file_name)


def write_rel_magnitude(event_date, output_path, session_asymmmetry, user_id):
    df = pandas.DataFrame()
    for var, f in session_asymmmetry.loading_asymmetry_summaries.items():
        ab = pandas.DataFrame({
            'sort_order': [f.sort_order],
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
    df = df.sort("sort_order")
    columns = [
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
              ]
    df.to_csv(output_path + 'rel_magnitude_asymmetry_' + user_id + '_' + event_date + '.csv', sep=',',
              index_label='Variable', columns=columns
              )
    file_name = '_'.join([event_date, user_id]) + '/rel_magnitude_asymmetry.csv'
    write_file_to_s3(output_path + 'rel_magnitude_asymmetry_' + user_id + '_' + event_date + '.csv', file_name)


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


def write_file_to_s3(local_file, file_name):
    s3_client = boto3.client('s3')
    s3_bucket = "biometrix-preprocessing-{env}-us-west-2-advanced-stats".format(env=os.environ['ENVIRONMENT'])
    s3_client.upload_file(local_file, s3_bucket, file_name)

if __name__ == '__main__':
    from config import load_parameters
    load_parameters([
        'MONGO_HOST',
        'MONGO_USER',
        'MONGO_PASSWORD',
        'MONGO_DATABASE',
        'MONGO_REPLICASET',
        'MONGO_COLLECTION_ACTIVEBLOCKS',
    ], 'mongo')

    input_data = {"UserId": "fd263811-b299-461f-9e79-895c69612bac",
                  "EventDate": "2018-12-17"}

    script_handler('~/', input_data)
