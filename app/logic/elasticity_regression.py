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

        # apt - ankle pitch

        # hip drop - apt
        # hip drop - peak_hip_vertical_accel

        # knee valgus - hip drop
        # knee valgus - peak_hip_vertical_accel

        left_list = self.get_variables_from_steps(left_steps)

        right_list = self.get_variables_from_steps(right_steps)

        columns_list = ['peak_hip_vertical_accel', 'knee_valgus', 'apt', 'ankle_pitch', 'hip_drop', 'duration', 'cadence_zone']

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

        left_apt_ankle_pitch_list = self.regress_one_var(1, "ankle_pitch", "apt", left_df_cadence_20, left_df_cadence_30, left_df_cadence_40)
        right_apt_ankle_pitch_list = self.regress_one_var(2, "ankle_pitch", "apt", right_df_cadence_20, right_df_cadence_30, right_df_cadence_40)

        left_hip_drop_apt_list = self.regress_one_var(1, "apt", "hip_drop", left_df_cadence_20, left_df_cadence_30, left_df_cadence_40)
        right_hip_drop_apt_list = self.regress_one_var(2, "apt", "hip_drop", right_df_cadence_20, right_df_cadence_30, right_df_cadence_40)

        left_hip_drop_pva_list = self.regress_one_var(1, "peak_hip_vertical_accel", "hip_drop", left_df_cadence_20, left_df_cadence_30, left_df_cadence_40)
        right_hip_drop_pva_list = self.regress_one_var(2, "peak_hip_vertical_accel", "hip_drop", right_df_cadence_20, right_df_cadence_30, right_df_cadence_40)

        left_knee_valgus_hip_drop_list = self.regress_one_var(1, "hip_drop", "knee_valgus", left_df_cadence_20, left_df_cadence_30,
                                                      left_df_cadence_40)
        right_knee_valgus_hip_drop_list = self.regress_one_var(2, "hip_drop", "knee_valgus", right_df_cadence_20, right_df_cadence_30,
                                                       right_df_cadence_40)

        left_knee_valgus_pva_list = self.regress_one_var(1, "peak_hip_vertical_accel", "knee_valgus", left_df_cadence_20,
                                                      left_df_cadence_30, left_df_cadence_40)
        right_knee_valgus_pva_list = self.regress_one_var(2, "peak_hip_vertical_accel", "knee_valgus", right_df_cadence_20,
                                                       right_df_cadence_30, right_df_cadence_40)

        movement_patterns.apt_ankle_pitch_stats.extend(left_apt_ankle_pitch_list)
        movement_patterns.apt_ankle_pitch_stats.extend(right_apt_ankle_pitch_list)
        movement_patterns.hip_drop_apt_stats.extend(left_hip_drop_apt_list)
        movement_patterns.hip_drop_apt_stats.extend(right_hip_drop_apt_list)
        movement_patterns.hip_drop_pva_stats.extend(left_hip_drop_pva_list)
        movement_patterns.hip_drop_pva_stats.extend(right_hip_drop_pva_list)
        movement_patterns.knee_valgus_hip_drop_stat(left_knee_valgus_hip_drop_list)
        movement_patterns.knee_valgus_hip_drop_stat(right_knee_valgus_hip_drop_list)
        movement_patterns.knee_valgus_pva_stat(left_knee_valgus_pva_list)
        movement_patterns.knee_valgus_pva_stat(right_knee_valgus_pva_list)

        return movement_patterns

    def get_variables_from_steps(self, steps):

        step_list = []

        for step in steps:

            if step.peak_hip_vertical_accel_95 == 0:
                step.peak_hip_vertical_accel_95 = 0.001

            if (step.peak_hip_vertical_accel_95 not in [None, 0] and
                    step.knee_valgus not in [None, 0] and
                    step.hip_drop not in [None, 0] and
                    step.ankle_pitch_range not in [None, 0] and
                    step.anterior_pelvic_tilt_range not in [None, 0]):
                peak_hip_vertical_accel = log(step.peak_hip_vertical_accel_95)
                knee_valgus = log(step.knee_valgus)
                hip_drop = log(step.hip_drop)
                ankle_pitch = log(step.ankle_pitch_range)
                apt = log(step.anterior_pelvic_tilt_range)

                duration = log(step.duration)
                cadence_zone = step.cadence_zone

                left_step_list = [peak_hip_vertical_accel, knee_valgus, apt, ankle_pitch, hip_drop, duration,
                                  cadence_zone]
                step_list.append(left_step_list)

        return step_list

    def regress_one_var(self, x, y, side, df_cadence_20, df_cadence_30, df_cadence_40):

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
                step_apt = step_df[[x, y]].copy()
                step_apt = self.remove_outliers(step_apt, x)
                step_apt = self.remove_outliers(step_apt, y)

                step_apt_x = step_apt[[x]].copy()
                step_apt_y = step_apt[[y]].copy()

                # use core values to ensure drift/trend is not removed with outliers
                adf_apt_results = adfuller(step_df[y].values)
                movement_pattern_stats.adf = adf_apt_results[0]
                movement_pattern_stats.adf_critical = adf_apt_results[4]['5%']

                step_apt_x = sm.add_constant(step_apt_x)

                step_model_apt = sm.OLS(endog=step_apt_y, exog=step_apt_x)
                step_apt_results = step_model_apt.fit()

                movement_pattern_stats.obs = step_apt_results.nobs
                movement_pattern_stats.elasticity = step_apt_results.params.values[1]
                movement_pattern_stats.elasticity_t = step_apt_results.tvalues.values[1]
                movement_pattern_stats.elasticity_se = step_apt_results.bse.values[1]
                movement_pattern_stats_list.append(movement_pattern_stats)
            cadence_position += 1

        return movement_pattern_stats_list