import pandas as pd
from math import log
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
from models.movement_pattern import MovementPatterns, MovementPatternStats
import numpy as np


class ElasticityRegression(object):
    def __init__(self):
        pass

    def remove_outliers(self, df, column_name):
        df[column_name + "_stdev"] = (df[column_name] - df[column_name].mean()) / df[column_name].std(ddof=0)
        df = df[abs(df[column_name + '_stdev']) <= 1.5]
        #df = df.drop(df.index[stdev_df.index])
        df = df.drop([column_name + "_stdev"], axis=1)
        return df

    # def remove_nones(self, df, column_name):
    #     #indexes = df[df[column_name] ].index
    #     #df.drop(indexes, inplace=True)
    #     df = df.dropna(df[column_name], inplace=True)
    #     return df

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

        columns_list = ['peak_hip_vertical_accel', 'knee_valgus', 'apt', 'ankle_pitch', 'hip_drop', 'hip_rotation',
                        'duration', 'cadence_zone']

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

        left_knee_valgus_apt_list = self.regress_one_var(1, "apt", "knee_valgus", left_df_cadence_20, left_df_cadence_30, left_df_cadence_40)
        right_knee_valgus_apt_list = self.regress_one_var(2, "apt", "knee_valgus", right_df_cadence_20, right_df_cadence_30, right_df_cadence_40)

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

        left_hip_rotation_ankle_pitch_list = self.regress_one_var(1, "ankle_pitch", "hip_rotation", left_df_cadence_20, left_df_cadence_30, left_df_cadence_40)
        right_hip_rotation_ankle_pitch_list = self.regress_one_var(2, "ankle_pitch", "hip_rotation", right_df_cadence_20, right_df_cadence_30, right_df_cadence_40)

        left_hip_rotation_apt_list = self.regress_one_var(1, "apt", "hip_rotation", left_df_cadence_20, left_df_cadence_30, left_df_cadence_40)
        right_hip_rotation_apt_list = self.regress_one_var(2, "apt", "hip_rotation", right_df_cadence_20, right_df_cadence_30, right_df_cadence_40)

        movement_patterns.apt_ankle_pitch_stats.extend(left_apt_ankle_pitch_list)
        movement_patterns.apt_ankle_pitch_stats.extend(right_apt_ankle_pitch_list)
        movement_patterns.hip_drop_apt_stats.extend(left_hip_drop_apt_list)
        movement_patterns.hip_drop_apt_stats.extend(right_hip_drop_apt_list)
        movement_patterns.hip_drop_pva_stats.extend(left_hip_drop_pva_list)
        movement_patterns.hip_drop_pva_stats.extend(right_hip_drop_pva_list)
        movement_patterns.knee_valgus_hip_drop_stats.extend(left_knee_valgus_hip_drop_list)
        movement_patterns.knee_valgus_hip_drop_stats.extend(right_knee_valgus_hip_drop_list)
        movement_patterns.knee_valgus_pva_stats.extend(left_knee_valgus_pva_list)
        movement_patterns.knee_valgus_pva_stats.extend(right_knee_valgus_pva_list)
        movement_patterns.knee_valgus_apt_stats.extend(left_knee_valgus_apt_list)
        movement_patterns.knee_valgus_apt_stats.extend(right_knee_valgus_apt_list)
        movement_patterns.hip_rotation_ankle_pitch_stats.extend(left_hip_rotation_ankle_pitch_list)
        movement_patterns.hip_rotation_ankle_pitch_stats.extend(right_hip_rotation_ankle_pitch_list)
        movement_patterns.hip_rotation_apt_stats.extend(left_hip_rotation_apt_list)
        movement_patterns.hip_rotation_apt_stats.extend(right_hip_rotation_apt_list)

        return movement_patterns

    def get_variables_from_steps(self, steps):

        step_list = []

        for step in steps:

            if step.knee_valgus is not None:
                step.knee_valgus = step.knee_valgus + 1

            if step.anterior_pelvic_tilt_range is not None:
                step.anterior_pelvic_tilt_range = step.anterior_pelvic_tilt_range + 1

            if step.hip_drop is not None:
                step.hip_drop = step.hip_drop + 1

            if step.ankle_pitch_range is not None:
                step.ankle_pitch_range = step.ankle_pitch_range + 1

            if step.hip_rotation is not None:
                step.hip_rotation = step.hip_rotation + 1

            if (step.peak_hip_vertical_accel not in [None, 0] and
                    #step.knee_valgus not in [None, 0] and
                    step.hip_drop not in [None, 0] and
                    step.ankle_pitch_range not in [None, 0] and
                    step.anterior_pelvic_tilt_range not in [None, 0] #and step.hip_rotation not in [None, 0]
                    ):
                if (step.peak_hip_vertical_accel > 0 and
                        #step.knee_valgus > 0 and
                        step.hip_drop > 0 and
                        step.ankle_pitch_range > 0 and
                        step.anterior_pelvic_tilt_range > 0 #and step.hip_rotation > 0
                        ):
                    peak_hip_vertical_accel = log(step.peak_hip_vertical_accel)
                    hip_drop = log(step.hip_drop)
                    ankle_pitch = log(step.ankle_pitch_range)
                    apt = log(step.anterior_pelvic_tilt_range)
                    if step.knee_valgus is not None and step.knee_valgus > 0:
                        knee_valgus = log(step.knee_valgus)
                    else:
                        knee_valgus = np.nan
                    if step.hip_rotation is not None and step.hip_rotation > 0:
                        hip_rotation = log(step.hip_rotation)
                    else:
                        hip_rotation = np.nan

                    duration = log(step.duration)
                    cadence_zone = step.cadence_zone

                    variable_step_list = [peak_hip_vertical_accel, knee_valgus, apt, ankle_pitch, hip_drop, hip_rotation,
                                          duration, cadence_zone]
                    step_list.append(variable_step_list)

        return step_list

    def regress_one_var(self,  side, x, y,df_cadence_20, df_cadence_30, df_cadence_40):

        movement_pattern_stats_list = []
        cadence_position  = 0
        cadence = ["20", "30", "40"]
        for step_df in [df_cadence_20, df_cadence_30, df_cadence_40]:

            movement_pattern_stats = MovementPatternStats(side, cadence[cadence_position])

            if len(step_df) > 0:
                # if len(step_df) > 1000:
                #     step_df = resample(step_df, replace=False, n_samples=1000, random_state=123)
                #     step_df.name = name

                # check to make sure we don't have a column of the same value (like what happens with knee valgus)
                if step_df[[x]].nunique()[0] == 1 or step_df[[y]].nunique()[0] == 1:
                    movement_pattern_stats.adf = -1
                    movement_pattern_stats.adf_critical = 0
                    movement_pattern_stats.obs = len(step_df)
                    movement_pattern_stats.elasticity = 0
                    movement_pattern_stats.elasticity_t = 0
                    movement_pattern_stats.elasticity_se = 0
                else:
                    step_elasticity = step_df[[x, y]].copy()
                    step_elasticity.dropna(inplace=True)

                    if len(step_elasticity) > 0:
                        step_elasticity = self.remove_outliers(step_elasticity, x)
                        step_elasticity = self.remove_outliers(step_elasticity, y)

                        step_elasticity_x = step_elasticity[[x]].copy()
                        step_elasticity_y = step_elasticity[[y]].copy()

                        # use core values to ensure drift/trend is not removed with outliers
                        try:
                            adf_results = adfuller(step_elasticity_y[y])
                            movement_pattern_stats.adf = adf_results[0]
                            movement_pattern_stats.adf_critical = adf_results[4]['5%']
                        except ValueError:
                            movement_pattern_stats.adf = -1
                            movement_pattern_stats.adf_critical = 0

                        step_elasticity_x = sm.add_constant(step_elasticity_x)

                        try:
                            step_model = sm.OLS(endog=step_elasticity_y, exog=step_elasticity_x)
                            step_results = step_model.fit()

                            movement_pattern_stats.obs = step_results.nobs
                            movement_pattern_stats.elasticity = step_results.params.values[1]
                            movement_pattern_stats.elasticity_t = step_results.tvalues.values[1]
                            movement_pattern_stats.elasticity_se = step_results.bse.values[1]
                        except ValueError:
                            movement_pattern_stats.obs = len(step_df)
                            movement_pattern_stats.elasticity = 0
                            movement_pattern_stats.elasticity_t = 0
                            movement_pattern_stats.elasticity_se = 0

                    else:
                        movement_pattern_stats.adf = -1
                        movement_pattern_stats.adf_critical = 0
                        movement_pattern_stats.obs = 0
                        movement_pattern_stats.elasticity = 0
                        movement_pattern_stats.elasticity_t = 0
                        movement_pattern_stats.elasticity_se = 0
                    movement_pattern_stats_list.append(movement_pattern_stats)

            cadence_position += 1

        return movement_pattern_stats_list