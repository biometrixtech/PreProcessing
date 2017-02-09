# -*- coding: utf-8 -*-
"""
Created on Tue Dec 06 14:56:52 2016

@author: court
"""

import runBaseFeet as bf
import runSessionCalibration as sc
import abbrevAnalytics as aa

#%% create locations of error

def run_system(base_path, calib_path, practice_path):

    base = bf.record_special_feet(base_path, base_path)

    base_name = 'base_' + base_path

    base.to_csv(base_name, index=False)

    calib, calib_transforms = sc.run_calibration(calib_path,
                               calib_path, base_name)

    calib_name = 'calib_' + calib_path
    calib.to_csv(calib_name, index=False)

    analytics_data = aa.abbrev_analytics(practice_path,
                              calib_transforms)

#    analytics_data = analytics_data.data


if __name__ == '__main__':

    base_path = 'garage_1_standing.csv'
    calib_path = 'garage_1_standing.csv'
    practice_path = 'garage_1_moving.csv'
    run_system(base_path, calib_path, practice_path)