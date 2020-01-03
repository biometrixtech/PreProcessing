import os
import time
import json
import requests

from aws_xray_sdk.core import xray_recorder
os.environ['ENVIRONMENT'] = 'test'
xray_recorder.configure(sampling=False)
xray_recorder.begin_segment(name="test")

from utils import format_datetime, parse_datetime
from datetime import datetime, timedelta
import tests.mock_users.test_users as test_users
import tests.mock_users.reset_users as reset_users
from tests.app.writemongo.datastore import MockDatastore
from app.jobs.advancedstats import get_unit_blocks, AdvancedstatsJob
from app.jobs.advancedstats.asymmetry_processor_job import AsymmetryProcessorJob
from app.jobs.advancedstats.complexity_matrix_job import ComplexityMatrixJob
import pandas as pd
from math import log
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
#from sklearn.utils import resample
from logic.elasticity_regression import ElasticityRegression



def remove_outliers(df, column_name):
    df[column_name + "_stdev"] = (df[column_name] - df[column_name].mean()) / df[
        column_name].std(ddof=0)
    df = df[abs(df[column_name + '_stdev']) <= 1.5]
    #df = df.drop(df.index[stdev_df.index])
    df = df.drop([column_name + "_stdev"], axis=1)
    return df


if __name__ == '__main__':
    sessions = [
                 "38c8215f-c60e-56e4-9c6e-58413f961360",
                 "0f465cc7-1489-5f32-a5a2-3e6a6cf91d8b",
                 "d8d0198c-b186-5158-86d6-e3b623af0ef1",

        "958dba09-c338-5118-86a3-d20a559f09c2",
        "c14f1728-b4f5-5fb4-845c-9dc830b3e9bf",


    ]
    apt_list = []
    hip_drop_list = []
    start_time = datetime.now()
    all_movement_patterns = []

    for s in range(0, len(sessions)):

        print(sessions[s])
        print(str((datetime.now() - start_time).seconds) + " seconds")
        active_blocks = get_unit_blocks(sessions[s], "")
        unit_blocks = []

        active_start = None
        active_end = None

        for a in active_blocks:
            if active_start is None:
                active_start = a["timeStart"]
            if active_end is None:
                active_end = a["timeEnd"]
            active_start = min(active_start, a["timeStart"])
            active_end = max(active_end, a["timeEnd"])
            unit_blocks.extend(a["unitBlocks"])

        seconds_duration = (parse_datetime(active_end) - parse_datetime(active_start)).seconds

        unit_blocks = [b for b in unit_blocks if b["cadence_zone"] is not None and b["cadence_zone"] != 10]
        unit_blocks = sorted(unit_blocks, key=lambda ub: ub['timeStart'])

        ds = MockDatastore(sessions[s], "today", "test", active_end)

        cmj = ComplexityMatrixJob(ds, unit_blocks)
        cmj.run()

        left_list = []
        right_list = []

        elasticity_regression = ElasticityRegression()
        movement_pattern = elasticity_regression.run_regressions(cmj.motion_complexity_single_leg['Single Leg'].left_steps,
                                                                 cmj.motion_complexity_single_leg['Single Leg'].right_steps)

        all_movement_patterns.append(movement_pattern)

    #     for left_step in cmj.motion_complexity_single_leg['Single Leg'].left_steps:
    #
    #         if left_step.hip_drop not in [None,0] and left_step.ankle_pitch_range not in [None,0] and left_step.anterior_pelvic_tilt_range not in [None,0]:
    #
    #             apt = log(left_step.anterior_pelvic_tilt_range)
    #             ankle_pitch = log(left_step.ankle_pitch_range)
    #             hip_drop = log(left_step.hip_drop)
    #             duration = log(left_step.duration)
    #             cadence_zone = left_step.cadence_zone
    #
    #             left_step_list = [apt, ankle_pitch, hip_drop, duration, cadence_zone]
    #             left_list.append(left_step_list)
    #
    #     for right_step in cmj.motion_complexity_single_leg['Single Leg'].right_steps:
    #
    #         if right_step.hip_drop not in [None,0] and right_step.ankle_pitch_range not in [None,0] and right_step.anterior_pelvic_tilt_range not in [None,0]:
    #             apt = log(right_step.anterior_pelvic_tilt_range)
    #             ankle_pitch = log(right_step.ankle_pitch_range)
    #             hip_drop = log(right_step.hip_drop)
    #             duration = log(right_step.duration)
    #             cadence_zone = right_step.cadence_zone
    #
    #             right_step_list = [apt, ankle_pitch, hip_drop, duration, cadence_zone]
    #             right_list.append(right_step_list)
    #
    #     columns_list = ['apt','ankle_pitch','hip_drop','duration','cadence_zone']
    #
    #     left_df = pd.DataFrame(left_list, columns=columns_list)
    #     right_df = pd.DataFrame(right_list, columns=columns_list)
    #
    #     left_df_cadence_20 = left_df[left_df['cadence_zone'] == 20.0]
    #     left_df_cadence_30 = left_df[left_df['cadence_zone'] == 30.0]
    #     left_df_cadence_40 = left_df[left_df['cadence_zone'] == 40.0]
    #     left_df_cadence_20.name = "20"
    #     left_df_cadence_30.name = "30"
    #     left_df_cadence_40.name = "40"
    #
    #     right_df_cadence_20 = right_df[right_df['cadence_zone'] == 20.0]
    #     right_df_cadence_30 = right_df[right_df['cadence_zone'] == 30.0]
    #     right_df_cadence_40 = right_df[right_df['cadence_zone'] == 40.0]
    #     right_df_cadence_20.name = "20"
    #     right_df_cadence_30.name = "30"
    #     right_df_cadence_40.name = "40"
    #
    #     for left_step_df in [left_df_cadence_20, left_df_cadence_30, left_df_cadence_40]:
    #
    #         left_apt_list = []
    #         left_hip_drop_list = []
    #         print("Starting Left" + left_step_df.name)
    #         print(str((datetime.now() - start_time).seconds) + " seconds")
    #         name = left_step_df.name
    #
    #         if len(left_step_df) > 0:
    #             # if len(left_step_df) > 1000:
    #             #     left_step_df = resample(left_step_df, replace=False, n_samples=1000, random_state=123)
    #             #     left_step_df.name = name
    #             left_apt = left_step_df[["ankle_pitch", "apt"]].copy()
    #             left_apt = remove_outliers(left_apt, "ankle_pitch")
    #             left_apt = remove_outliers(left_apt, "apt")
    #             print("Removed outliers")
    #             print(str((datetime.now() - start_time).seconds) + " seconds")
    #
    #             left_apt_x = left_apt[["ankle_pitch"]].copy()
    #             left_apt_y = left_apt[["apt"]].copy()
    #
    #             adf_apt_results = adfuller(left_step_df["apt"].values)  #use core values to ensure drift/trend is not removed with outliers
    #             adf_apt_stat = adf_apt_results[0]
    #             adf_critical_value_5 = adf_apt_results[4]['5%']
    #             apt_fatigue = False
    #             if adf_apt_stat > adf_critical_value_5:
    #                 apt_fatigue = True
    #
    #             left_apt_x = sm.add_constant(left_apt_x)
    #
    #             left_model_apt = sm.OLS(endog=left_apt_y, exog=left_apt_x)
    #             left_apt_results = left_model_apt.fit()
    #
    #             # for b in range(0,6):
    #             #     print(b)
    #             #     print(str((datetime.now() - start_time).seconds) + " seconds")
    #             #     left_model_apt = sm.OLS(endog=left_apt_y, exog=left_apt_x)
    #             #     left_apt_results = None
    #             #     left_apt_results = left_model_apt.fit()
    #             #     outliers = left_apt_results.outlier_test()
    #             #     outliers = outliers.reset_index(drop=True)
    #             #     outliers_df = outliers[outliers['bonf(p)'] < 1.0]
    #             #     if len(outliers_df) > 0:
    #             #         left_apt_y = left_apt_y.drop(left_apt_y.index[outliers_df.index])
    #             #         left_apt_x = left_apt_x.drop(left_apt_x.index[outliers_df.index])
    #             #         left_apt_y = left_apt_y.reset_index(drop=True)
    #             #         left_apt_x = left_apt_x.reset_index(drop=True)
    #
    #             left_apt_list.append(sessions[s])
    #             left_apt_list.append(left_step_df.name)  #cadence
    #             left_apt_list.append("left")
    #             left_apt_list.append(left_apt_results.nobs)
    #             left_apt_list.extend(left_apt_results.params.values) # const, ankle_pitch, hip_drop
    #             left_apt_list.extend(left_apt_results.tvalues.values) # const, ankle_pitch, hip_drop
    #             left_apt_list.extend(left_apt_results.bse.values)  # const, ankle_pitch, hip_drop - std error
    #             left_apt_list.append(apt_fatigue)
    #             apt_list.append(left_apt_list)
    #             print("Finished regression")
    #             print(str((datetime.now() - start_time).seconds) + " seconds")
    #
    #             # left_hip_drop_x = left_step_df[["ankle_pitch", "apt"]].copy()
    #             # left_hip_drop_y = left_step_df[["hip_drop"]].copy()
    #             # left_hip_drop_x = sm.add_constant(left_hip_drop_x)
    #             #
    #             # left_model_hip_drop = sm.OLS(endog=left_hip_drop_y, exog=left_hip_drop_x)
    #             # left_hip_drop_results = left_model_hip_drop.fit()
    #             #
    #             # left_hip_drop_list.append(sessions[s])
    #             # left_hip_drop_list.append(left_step_df.name)  #cadence
    #             # left_hip_drop_list.append("left")
    #             # left_hip_drop_list.append(left_hip_drop_results.nobs)
    #             # left_hip_drop_list.extend(left_hip_drop_results.params.values) # const, ankle_pitch, hip_drop
    #             # left_hip_drop_list.extend(left_hip_drop_results.tvalues.values) # const, ankle_pitch, hip_drop
    #             # left_hip_drop_list.extend(left_hip_drop_results.bse.values)  # const, ankle_pitch, hip_drop - std error
    #             # hip_drop_list.append(left_hip_drop_list)
    #
    #     for right_step_df in [right_df_cadence_20, right_df_cadence_30, right_df_cadence_40]:
    #
    #         right_apt_list = []
    #         right_hip_drop_list = []
    #         print("Starting Right" + right_step_df.name)
    #         print(str((datetime.now() - start_time).seconds) + " seconds")
    #         name = right_step_df.name
    #
    #         if len(right_step_df) > 0:
    #             # if len(right_step_df) > 1000:
    #             #     right_step_df = resample(right_step_df, replace=False, n_samples=1000, random_state=123)
    #             #     right_step_df.name = name
    #             right_apt = right_step_df[["ankle_pitch", "apt"]].copy()
    #             right_apt = remove_outliers(right_apt, "ankle_pitch")
    #             right_apt = remove_outliers(right_apt, "apt")
    #             print("Removed outliers")
    #             print(str((datetime.now() - start_time).seconds) + " seconds")
    #
    #             right_apt_x = right_apt[["ankle_pitch"]].copy()
    #             right_apt_y = right_apt[["apt"]].copy()
    #
    #             adf_apt_results = adfuller(right_step_df["apt"].values)
    #             adf_apt_stat = adf_apt_results[0]
    #             adf_critical_value_5 = adf_apt_results[4]['5%']
    #             apt_fatigue = False
    #             if adf_apt_stat > adf_critical_value_5:
    #                 apt_fatigue = True
    #
    #             right_apt_x = sm.add_constant(right_apt_x)
    #
    #             right_model_apt = sm.OLS(endog=right_apt_y, exog=right_apt_x)
    #             right_apt_results = right_model_apt.fit()
    #
    #             # for b in range(0,6):
    #             #     print(b)
    #             #     print(str((datetime.now() - start_time).seconds) + " seconds")
    #             #     right_model_apt = sm.OLS(endog=right_apt_y, exog=right_apt_x)
    #             #
    #             #     right_apt_results = right_model_apt.fit()
    #             #     outliers = right_apt_results.outlier_test()
    #             #     outliers = outliers.reset_index(drop=True)
    #             #
    #             #     outliers_df = outliers[outliers['bonf(p)'] < 1.0]
    #             #     if len(outliers_df) > 0:
    #             #         right_apt_y = right_apt_y.drop(right_apt_y.index[outliers_df.index])
    #             #         right_apt_x = right_apt_x.drop(right_apt_x.index[outliers_df.index])
    #             #         right_apt_y = right_apt_y.reset_index(drop=True)
    #             #         right_apt_x = right_apt_x.reset_index(drop=True)
    #
    #             right_apt_list.append(sessions[s])
    #             right_apt_list.append(right_step_df.name)  #cadence
    #             right_apt_list.append("right")
    #             right_apt_list.append(right_apt_results.nobs)
    #             right_apt_list.extend(right_apt_results.params.values) # const, ankle_pitch, hip_drop
    #             right_apt_list.extend(right_apt_results.tvalues.values) # const, ankle_pitch, hip_drop
    #             right_apt_list.extend(right_apt_results.bse.values)  # const, ankle_pitch, hip_drop - std error
    #             right_apt_list.append(apt_fatigue)
    #             apt_list.append(right_apt_list)
    #             print("Finished regression")
    #             print(str((datetime.now() - start_time).seconds) + " seconds")
    #
    #             # right_hip_drop_x = right_step_df[["ankle_pitch", "apt"]].copy()
    #             # right_hip_drop_y = right_step_df[["hip_drop"]].copy()
    #             # right_hip_drop_x = sm.add_constant(right_hip_drop_x)
    #             # right_hip_drop_model = sm.OLS(endog=right_hip_drop_y, exog=right_hip_drop_x)
    #             # right_hip_drop_results = right_hip_drop_model.fit()
    #             # right_hip_drop_list.append(sessions[s])
    #             # right_hip_drop_list.append(right_step_df.name)  #cadence
    #             # right_hip_drop_list.append("right")
    #             # right_hip_drop_list.append(right_apt_results.nobs)
    #             # right_hip_drop_list.extend(right_hip_drop_results.params.values) # const, ankle_pitch, hip_drop
    #             # right_hip_drop_list.extend(right_hip_drop_results.tvalues.values) # const, ankle_pitch, hip_drop
    #             # right_hip_drop_list.extend(right_hip_drop_results.bse.values)  # const, ankle_pitch, hip_drop - std error
    #             # hip_drop_list.append(right_hip_drop_list)
    #
    # #apt_df = pd.DataFrame(apt_list, columns=['session', 'cadence', 'side', 'obs', 'const_coef', 'ankle_pitch_coef',
    # #                                         'hip_drop_coef', 'const_tvalue', 'ankle_pitch_tvalue', 'hip_drop_tvalue',
    # #                                         'const_se', 'ankle_pitch_se', 'hip_drop_se'])
    # apt_df = pd.DataFrame(apt_list, columns=['session','cadence','side','obs','const_coef','ankle_pitch_coef','const_tvalue','ankle_pitch_tvalue','const_se','ankle_pitch_se','fatigue'])
    # #hip_drop_df = pd.DataFrame(hip_drop_list, columns=['session','cadence','side','obs','const_coef','ankle_pitch_coef','apt_coef','const_tvalue','ankle_pitch_tvalue','apt_tvalue','const_se','ankle_pitch_se','apt_se'])
    #
    # #apt_df.to_csv('apt_results.csv', columns=['session', 'cadence', 'side', 'obs','const_coef', 'const_tvalue', 'const_se', 'hip_drop_coef', 'hip_drop_tvalue', 'hip_drop_se', 'ankle_pitch_coef', 'ankle_pitch_tvalue', 'ankle_pitch_se'])
    # apt_df.to_csv('apt_results_stdev_nodownsample.csv',
    #               columns=['session', 'cadence', 'side', 'obs', 'const_coef', 'const_tvalue', 'const_se',
    #                        'ankle_pitch_coef', 'ankle_pitch_tvalue','ankle_pitch_se','fatigue'])
    # # hip_drop_df.to_csv('hip_drop_results.csv',
    # #               columns=['session', 'cadence', 'side', 'obs', 'const_coef', 'const_tvalue', 'const_se', 'apt_coef',
    # #                        'apt_tvalue', 'apt_se', 'ankle_pitch_coef', 'ankle_pitch_tvalue',
    # #                        'ankle_pitch_se'])
    k=0