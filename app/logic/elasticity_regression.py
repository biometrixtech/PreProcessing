import pandas as pd
from math import log
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
from models.movement_pattern import MovementPatterns, MovementPatternStats


class ElasticityRegression(object):
    def __init__(self):
        pass

    def remove_outliers(self, df, column_name):
        df[column_name + "_stdev"] = (df[column_name] - df[column_name].mean()) / df[
            column_name].std(ddof=0)
        df = df[abs(df[column_name + '_stdev']) <= 1.5]
        #df = df.drop(df.index[stdev_df.index])
        df = df.drop([column_name + "_stdev"], axis=1)
        return df

    def run_regressions(self, left_steps, right_steps):

        left_list = []
        right_list = []

        for left_step in left_steps:

            if (left_step.hip_drop not in [None, 0] and
                    left_step.ankle_pitch_range not in [None, 0] and
                    left_step.anterior_pelvic_tilt_range not in [None, 0]):
                apt = log(left_step.anterior_pelvic_tilt_range)
                ankle_pitch = log(left_step.ankle_pitch_range)
                hip_drop = log(left_step.hip_drop)
                duration = log(left_step.duration)
                cadence_zone = left_step.cadence_zone

                left_step_list = [apt, ankle_pitch, hip_drop, duration, cadence_zone]
                left_list.append(left_step_list)

        for right_step in right_steps:

            if (right_step.hip_drop not in [None, 0] and
                    right_step.ankle_pitch_range not in [None, 0] and
                    right_step.anterior_pelvic_tilt_range not in [None, 0]):
                apt = log(right_step.anterior_pelvic_tilt_range)
                ankle_pitch = log(right_step.ankle_pitch_range)
                hip_drop = log(right_step.hip_drop)
                duration = log(right_step.duration)
                cadence_zone = right_step.cadence_zone

                right_step_list = [apt, ankle_pitch, hip_drop, duration, cadence_zone]
                right_list.append(right_step_list)

        columns_list = ['apt', 'ankle_pitch', 'hip_drop', 'duration', 'cadence_zone']

        left_df = pd.DataFrame(left_list, columns=columns_list)
        right_df = pd.DataFrame(right_list, columns=columns_list)

        left_df_cadence_20 = left_df[left_df['cadence_zone'] == 20.0]
        left_df_cadence_30 = left_df[left_df['cadence_zone'] == 30.0]
        left_df_cadence_40 = left_df[left_df['cadence_zone'] == 40.0]
        left_df_cadence_20.name = "20"
        left_df_cadence_30.name = "30"
        left_df_cadence_40.name = "40"

        right_df_cadence_20 = right_df[right_df['cadence_zone'] == 20.0]
        right_df_cadence_30 = right_df[right_df['cadence_zone'] == 30.0]
        right_df_cadence_40 = right_df[right_df['cadence_zone'] == 40.0]
        right_df_cadence_20.name = "20"
        right_df_cadence_30.name = "30"
        right_df_cadence_40.name = "40"

        movement_patterns = MovementPatterns()

        left_movement_pattern_list = self.regress_apt_ankle_pitch(1, left_df_cadence_20, left_df_cadence_30, left_df_cadence_40)
        right_movement_pattern_list = self.regress_apt_ankle_pitch(2, right_df_cadence_20, right_df_cadence_30, right_df_cadence_40)

        movement_patterns.apt_ankle_pitch_stats.extend(left_movement_pattern_list)
        movement_patterns.apt_ankle_pitch_stats.extend(right_movement_pattern_list)

        return movement_patterns

    def regress_apt_ankle_pitch(self, side, df_cadence_20, df_cadence_30, df_cadence_40):

        movement_pattern_stats_list = []
        cadence_position  = 0
        cadence = ["20", "30", "40"]
        for step_df in [df_cadence_20, df_cadence_30, df_cadence_40]:

            movement_pattern_stats = MovementPatternStats(side, cadence[cadence_position])
            left_apt_list = []
            left_hip_drop_list = []

            if len(step_df) > 0:
                # if len(step_df) > 1000:
                #     step_df = resample(step_df, replace=False, n_samples=1000, random_state=123)
                #     step_df.name = name
                step_apt = step_df[["ankle_pitch", "apt"]].copy()
                step_apt = self.remove_outliers(step_apt, "ankle_pitch")
                step_apt = self.remove_outliers(step_apt, "apt")

                step_apt_x = step_apt[["ankle_pitch"]].copy()
                step_apt_y = step_apt[["apt"]].copy()

                # use core values to ensure drift/trend is not removed with outliers
                adf_apt_results = adfuller(step_df["apt"].values)
                movement_pattern_stats.adf = adf_apt_results[0]
                movement_pattern_stats.adf_critical = adf_apt_results[4]['5%']
                # apt_fatigue = False
                # if adf_apt_stat > adf_critical_value_5:
                #     apt_fatigue = True

                step_apt_x = sm.add_constant(step_apt_x)

                step_model_apt = sm.OLS(endog=step_apt_y, exog=step_apt_x)
                step_apt_results = step_model_apt.fit()

                #left_apt_list.append(step_df.name)  # cadence
                #left_apt_list.append("left")
                movement_pattern_stats.obs = step_apt_results.nobs
                #left_apt_list.append(step_apt_results.nobs)
                movement_pattern_stats.elasticity = step_apt_results.params.values[1]
                #left_apt_list.extend(step_apt_results.params.values)  # const, ankle_pitch, hip_drop
                movement_pattern_stats.elasticity_t = step_apt_results.tvalues.values[1]
                #left_apt_list.extend(step_apt_results.tvalues.values)  # const, ankle_pitch, hip_drop
                movement_pattern_stats.elasticity_se = step_apt_results.bse.values[1]
                #left_apt_list.extend(step_apt_results.bse.values)  # const, ankle_pitch, hip_drop - std error
                #left_apt_list.append(apt_fatigue)
                #apt_list.append(left_apt_list)
                movement_pattern_stats_list.append(movement_pattern_stats)
            cadence_position += 1

        return movement_pattern_stats_list