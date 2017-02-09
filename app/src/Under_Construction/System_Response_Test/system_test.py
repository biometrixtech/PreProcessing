# -*- coding: utf-8 -*-
"""
Created on Tue Dec 06 14:56:52 2016

@author: court
"""

import numpy as np
import itertools
#from applyOffset import generate_offset
from tqdm import tqdm
import runBaseFeet as bf
import runSessionCalibration as sc
import abbrevAnalytics as aa
import sys
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd

#%% create locations of error

good_sensors = list(itertools.product([True,False], repeat=3))
good_files = list(itertools.product([True,False], repeat=3))

combo = np.zeros((65, 6), dtype=bool)
ind = 0
EXT_COMBO = np.zeros((1,6), dtype=bool)
for i in range(len(good_sensors)):
    for k in range(len(good_files)):
        ind = ind+1
        combo[ind,:] = good_sensors[i] + good_files[k]
        if sum(good_files[k]) != 0:
            if sum(good_sensors[i]) != 0:
                EXT_COMBO = np.vstack((EXT_COMBO, combo[ind,:]))

#%%

def run_full_system_test(base_path, calib_path, practice_path,
                         variable_string, tolerance_decimal):

    date_object = datetime.now()
    formatted_date = date_object.strftime('%d-%m-%Y')

    text_file = open(variable_string + "_at_" + str(tolerance_decimal) + \
        "_offset_error_tolerance_report.txt","w")

    text_file.write("Report of " + variable_string + " with " + \
        str(tolerance_decimal) + \
        " tolerance to erroneous Euler angle offsets.\n\n")
    text_file.write("Test run on " + formatted_date + ".\n\n")

    # set original data as standard of comparison
    standard_base = bf.record_special_feet(base_path, base_path,
                                           base_bool=True,
                                           left_bool=True,
                                           hip_bool=True,
                                           right_bool=True, offset=0)

    stand_base = 'standard_base_' + base_path

    standard_base.to_csv(stand_base, index=False)

    standard_calib, standard_calib_transforms = sc.run_calibration(calib_path,
                                   calib_path, stand_base,
                                   calib_bool=True,
                                   left_bool=True,
                                   hip_bool=True,
                                   right_bool=True, offset=0)

    standard_analytics_data = aa.abbrev_analytics(practice_path,
                                                  standard_calib_transforms,
                                                  session_bool=True,
                                                  left_bool=True,
                                                  hip_bool=True,
                                                  right_bool=True, offset=0)

    standard_analytics_data = standard_analytics_data.data
#    plt.figure(1)
#    plt.plot(standard_analytics_data.LaZ)

    standard_data, test_var, standard_var_type = select_test_variables(
                                                 standard_calib_transforms,
                                                 standard_analytics_data,
                                                 variable_string)

    limit_indicator = np.zeros((len(EXT_COMBO),31))


    # define initial offset
    off_ind = 10
    offset = off(off_ind)

#    for i in tqdm(range(len(EXT_COMBO))):
    for i in tqdm([48]):
#    for i in [41]:

        parameters = tuple(EXT_COMBO[i])

        left_bool = parameters[0]
        hip_bool = parameters[1]
        right_bool = parameters[2]
        base_bool = parameters[3]
        calib_bool = parameters[4]
        practice_bool = parameters[5]

        offset_var, offset_var_type = run_system(base_path, base_bool,
                                      left_bool, hip_bool, right_bool, offset,
                                      calib_path, calib_bool, practice_path,
                                      practice_bool, variable_string)

        limit_indicator[i, off_ind] = find_significance_of_diff(offset_var_type,
                                     standard_var_type, test_var, offset_var,
                                     tolerance_decimal)

        if limit_indicator[i, off_ind] == 1:
            # go back to offset = 5
            off_ind = 5
            offset = off(off_ind)

            offset_var, offset_var_type = run_system(base_path, base_bool,
                                          left_bool, hip_bool, right_bool,
                                          offset, calib_path, calib_bool,
                                          practice_path, practice_bool,
                                          variable_string)

            limit_indicator[i, off_ind] = find_significance_of_diff(
                                         offset_var_type, standard_var_type,
                                         test_var, offset_var,
                                         tolerance_decimal)

            if limit_indicator[i, off_ind] == 1:
                # go back to offset = 3
                off_ind = 3
                offset = off(off_ind)

                offset_var, offset_var_type = run_system(base_path, base_bool,
                                              left_bool, hip_bool, right_bool,
                                              offset, calib_path, calib_bool,
                                              practice_path, practice_bool,
                                              variable_string)

                limit_indicator[i, off_ind] = find_significance_of_diff(
                                             offset_var_type,
                                             standard_var_type,
                                             test_var, offset_var,
                                             tolerance_decimal)
                                             
                if limit_indicator[i, off_ind] == 1:
                    # go back to offset = 1
                    off_ind = 1
                    offset = off(off_ind)

                    offset_var, offset_var_type = run_system(base_path,
                                                  base_bool, left_bool,
                                                  hip_bool, right_bool,
                                                  offset, calib_path,
                                                  calib_bool, practice_path,
                                                  practice_bool,
                                                  variable_string)
    
                    limit_indicator[i, off_ind] = find_significance_of_diff(
                                                 offset_var_type,
                                                 standard_var_type,
                                                 test_var, offset_var,
                                                 tolerance_decimal)

                    if limit_indicator[i, off_ind] == 1:
                        limit = '1'

                    elif limit_indicator[i, off_ind] == 0:
                        off_ind = 2
                        offset = off(off_ind)

                        offset_var, offset_var_type = run_system(base_path,
                                                      base_bool, left_bool,
                                                      hip_bool, right_bool,
                                                      offset, calib_path,
                                                      calib_bool, practice_path,
                                                      practice_bool,
                                                      variable_string)

                        limit_indicator[i, off_ind] = find_significance_of_diff(
                                                     offset_var_type,
                                                     standard_var_type,
                                                     test_var, offset_var,
                                                     tolerance_decimal)

                        if limit_indicator[i, off_ind] == 1:
                            limit = '2'

                        elif limit_indicator[i, off_ind] == 0:
                            limit = '3'

                        else:
                            print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                            sys.exit()

                    else:
                        print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                        sys.exit()

                elif limit_indicator[i, off_ind] == 0:
                    # go to offset = 4
                    off_ind = 4
                    offset = off(off_ind)

                    offset_var, offset_var_type = run_system(base_path,
                                                  base_bool, left_bool,
                                                  hip_bool, right_bool,
                                                  offset, calib_path,
                                                  calib_bool, practice_path,
                                                  practice_bool,
                                                  variable_string)

                    limit_indicator[i, off_ind] = find_significance_of_diff(
                                                 offset_var_type,
                                                 standard_var_type,
                                                 test_var, offset_var,
                                                 tolerance_decimal)

                    if limit_indicator[i, off_ind] == 1:
                        limit = '4'

                    elif limit_indicator[i, off_ind] == 0:
                        limit = '5'

                    else:
                        print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                        sys.exit()

                else:
                    print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                    sys.exit()

            elif limit_indicator[i, off_ind] == 0:
                # go forward to offset = 8
                off_ind = 8
                offset = off(off_ind)

                offset_var, offset_var_type = run_system(base_path,
                                              base_bool, left_bool,
                                              hip_bool, right_bool,
                                              offset, calib_path,
                                              calib_bool, practice_path,
                                              practice_bool,
                                              variable_string)

                limit_indicator[i, off_ind] = find_significance_of_diff(
                                             offset_var_type,
                                             standard_var_type,
                                             test_var, offset_var,
                                             tolerance_decimal)
                
                if limit_indicator[i, off_ind] == 1:
                    off_ind = 6
                    offset = off(off_ind)

                    offset_var, offset_var_type = run_system(base_path,
                                                  base_bool, left_bool,
                                                  hip_bool, right_bool,
                                                  offset, calib_path,
                                                  calib_bool, practice_path,
                                                  practice_bool,
                                                  variable_string)

                    limit_indicator[i, off_ind] = find_significance_of_diff(
                                                 offset_var_type,
                                                 standard_var_type,
                                                 test_var, offset_var,
                                                 tolerance_decimal)

                    if limit_indicator[i, off_ind] == 1:
                        limit = '6'

                    elif limit_indicator[i, off_ind] == 0:
                        off_ind = 7
                        offset = off(off_ind)

                        offset_var, offset_var_type = run_system(base_path,
                                                      base_bool, left_bool,
                                                      hip_bool, right_bool,
                                                      offset, calib_path,
                                                      calib_bool, practice_path,
                                                      practice_bool,
                                                      variable_string)

                        limit_indicator[i, off_ind] = find_significance_of_diff(
                                                     offset_var_type,
                                                     standard_var_type,
                                                     test_var, offset_var,
                                                     tolerance_decimal)

                        if limit_indicator[i, off_ind] == 1:
                            limit = '7'

                        elif limit_indicator[i, off_ind] == 0:
                            limit = '8'

                        else:
                            print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                            sys.exit()

                    else:
                        print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                        sys.exit()

                elif limit_indicator[i, off_ind] == 0:
                    off_ind = 9
                    offset = off(off_ind)

                    offset_var, offset_var_type = run_system(base_path,
                                                  base_bool, left_bool,
                                                  hip_bool, right_bool,
                                                  offset, calib_path,
                                                  calib_bool, practice_path,
                                                  practice_bool,
                                                  variable_string)

                    limit_indicator[i, off_ind] = find_significance_of_diff(
                                                 offset_var_type,
                                                 standard_var_type,
                                                 test_var, offset_var,
                                                 tolerance_decimal)

                    if limit_indicator[i, off_ind] == 1:
                        limit = '9'

                    elif limit_indicator[i, off_ind] == 0:
                        limit = '10'

                    else:
                        print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                        sys.exit()

                else:
                    print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                    sys.exit()

            else:
                print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                sys.exit()
            
        elif limit_indicator[i, off_ind] == 0:
            # go forward to offset = 20
            off_ind = 20
            offset = off(off_ind)

            offset_var, offset_var_type = run_system(base_path,
                                          base_bool, left_bool,
                                          hip_bool, right_bool,
                                          offset, calib_path,
                                          calib_bool, practice_path,
                                          practice_bool,
                                          variable_string)

            limit_indicator[i, off_ind] = find_significance_of_diff(
                                         offset_var_type,
                                         standard_var_type,
                                         test_var, offset_var,
                                         tolerance_decimal)

            if limit_indicator[i, off_ind] == 1:
                off_ind = 15
                offset = off(off_ind)

                offset_var, offset_var_type = run_system(base_path,
                                              base_bool, left_bool,
                                              hip_bool, right_bool,
                                              offset, calib_path,
                                              calib_bool, practice_path,
                                              practice_bool,
                                              variable_string)

                limit_indicator[i, off_ind] = find_significance_of_diff(
                                             offset_var_type,
                                             standard_var_type,
                                             test_var, offset_var,
                                             tolerance_decimal)

                if limit_indicator[i, off_ind] == 1:
                    off_ind = 13
                    offset = off(off_ind)

                    offset_var, offset_var_type = run_system(base_path,
                                                  base_bool, left_bool,
                                                  hip_bool, right_bool,
                                                  offset, calib_path,
                                                  calib_bool, practice_path,
                                                  practice_bool,
                                                  variable_string)

                    limit_indicator[i, off_ind] = find_significance_of_diff(
                                                 offset_var_type,
                                                 standard_var_type,
                                                 test_var, offset_var,
                                                 tolerance_decimal)

                    if limit_indicator[i, off_ind] == 1:
                        off_ind = 11
                        offset = off(off_ind)

                        offset_var, offset_var_type = run_system(base_path,
                                                      base_bool, left_bool,
                                                      hip_bool, right_bool,
                                                      offset, calib_path,
                                                      calib_bool, practice_path,
                                                      practice_bool,
                                                      variable_string)

                        limit_indicator[i, off_ind] = find_significance_of_diff(
                                                     offset_var_type,
                                                     standard_var_type,
                                                     test_var, offset_var,
                                                     tolerance_decimal)

                        if limit_indicator[i, off_ind] == 1:
                            limit = '11'

                        elif limit_indicator[i, off_ind] == 0:
                            off_ind = 12
                            offset = off(off_ind)

                            offset_var, offset_var_type = run_system(base_path,
                                                          base_bool, left_bool,
                                                          hip_bool, right_bool,
                                                          offset, calib_path,
                                                          calib_bool, practice_path,
                                                          practice_bool,
                                                          variable_string)
    
                            limit_indicator[i, off_ind] = find_significance_of_diff(
                                                         offset_var_type,
                                                         standard_var_type,
                                                         test_var, offset_var,
                                                         tolerance_decimal)

                            if limit_indicator[i, off_ind] == 1:
                                limit = '12'

                            elif limit_indicator[i, off_ind] == 0:
                                limit = '13'

                            else:
                                print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                                sys.exit()

                        else:
                            print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                            sys.exit()

                    elif limit_indicator[i, off_ind] == 0:
                        off_ind = 14
                        offset = off(off_ind)

                        offset_var, offset_var_type = run_system(base_path,
                                                      base_bool, left_bool,
                                                      hip_bool, right_bool,
                                                      offset, calib_path,
                                                      calib_bool, practice_path,
                                                      practice_bool,
                                                      variable_string)

                        limit_indicator[i, off_ind] = find_significance_of_diff(
                                                     offset_var_type,
                                                     standard_var_type,
                                                     test_var, offset_var,
                                                     tolerance_decimal)

                        if limit_indicator[i, off_ind] == 1:
                            limit = '14'

                        elif limit_indicator[i, off_ind] == 0:
                            limit = '15'

                        else:
                            print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                            sys.exit()
 
                    else:
                        print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                        sys.exit()

                elif limit_indicator[i, off_ind] == 0:
                    off_ind = 18
                    offset = off(off_ind)

                    offset_var, offset_var_type = run_system(base_path,
                                                  base_bool, left_bool,
                                                  hip_bool, right_bool,
                                                  offset, calib_path,
                                                  calib_bool, practice_path,
                                                  practice_bool,
                                                  variable_string)

                    limit_indicator[i, off_ind] = find_significance_of_diff(
                                                 offset_var_type,
                                                 standard_var_type,
                                                 test_var, offset_var,
                                                 tolerance_decimal)

                    if limit_indicator[i, off_ind] == 1:
                        off_ind = 16
                        offset = off(off_ind)

                        offset_var, offset_var_type = run_system(base_path,
                                                      base_bool, left_bool,
                                                      hip_bool, right_bool,
                                                      offset, calib_path,
                                                      calib_bool, practice_path,
                                                      practice_bool,
                                                      variable_string)

                        limit_indicator[i, off_ind] = find_significance_of_diff(
                                                     offset_var_type,
                                                     standard_var_type,
                                                     test_var, offset_var,
                                                     tolerance_decimal)

                        if limit_indicator[i, off_ind] == 1:
                            limit = '16'

                        elif limit_indicator[i, off_ind] == 0:
                            off_ind = 17
                            offset = off(off_ind)

                            offset_var, offset_var_type = run_system(base_path,
                                                          base_bool, left_bool,
                                                          hip_bool, right_bool,
                                                          offset, calib_path,
                                                          calib_bool, practice_path,
                                                          practice_bool,
                                                          variable_string)
    
                            limit_indicator[i, off_ind] = find_significance_of_diff(
                                                         offset_var_type,
                                                         standard_var_type,
                                                         test_var, offset_var,
                                                         tolerance_decimal)

                            if limit_indicator[i, off_ind] == 1:
                                limit = '17'

                            elif limit_indicator[i, off_ind] == 0:
                                limit = '18'

                            else:
                                print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                                sys.exit()

                        else:
                            print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                            sys.exit()

                    elif limit_indicator[i, off_ind] == 0:
                        off_ind = 19
                        offset = off(off_ind)

                        offset_var, offset_var_type = run_system(base_path,
                                                      base_bool, left_bool,
                                                      hip_bool, right_bool,
                                                      offset, calib_path,
                                                      calib_bool, practice_path,
                                                      practice_bool,
                                                      variable_string)

                        limit_indicator[i, off_ind] = find_significance_of_diff(
                                                     offset_var_type,
                                                     standard_var_type,
                                                     test_var, offset_var,
                                                     tolerance_decimal)

                        if limit_indicator[i, off_ind] == 1:
                            limit = '19'

                        elif limit_indicator[i, off_ind] == 0:
                            limit = '20'

                        else:
                            print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                            sys.exit()

                    else:
                        print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                        sys.exit()

                else:
                    print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                    sys.exit()

            elif limit_indicator[i, off_ind] == 0:
                off_ind = 30
                offset = off(off_ind)

                offset_var, offset_var_type = run_system(base_path,
                                              base_bool, left_bool,
                                              hip_bool, right_bool,
                                              offset, calib_path,
                                              calib_bool, practice_path,
                                              practice_bool,
                                              variable_string)

                limit_indicator[i, off_ind] = find_significance_of_diff(
                                             offset_var_type,
                                             standard_var_type,
                                             test_var, offset_var,
                                             tolerance_decimal)

                if limit_indicator[i, off_ind] == 1:
                    off_ind = 25
                    offset = off(off_ind)

                    offset_var, offset_var_type = run_system(base_path,
                                                  base_bool, left_bool,
                                                  hip_bool, right_bool,
                                                  offset, calib_path,
                                                  calib_bool, practice_path,
                                                  practice_bool,
                                                  variable_string)

                    limit_indicator[i, off_ind] = find_significance_of_diff(
                                                 offset_var_type,
                                                 standard_var_type,
                                                 test_var, offset_var,
                                                 tolerance_decimal)

                    if limit_indicator[i, off_ind] == 1:
                        off_ind = 23
                        offset = off(off_ind)

                        offset_var, offset_var_type = run_system(base_path,
                                                      base_bool, left_bool,
                                                      hip_bool, right_bool,
                                                      offset, calib_path,
                                                      calib_bool, practice_path,
                                                      practice_bool,
                                                      variable_string)

                        limit_indicator[i, off_ind] = find_significance_of_diff(
                                                     offset_var_type,
                                                     standard_var_type,
                                                     test_var, offset_var,
                                                     tolerance_decimal)

                        if limit_indicator[i, off_ind] == 1:
                            off_ind = 21
                            offset = off(off_ind)

                            offset_var, offset_var_type = run_system(base_path,
                                                          base_bool, left_bool,
                                                          hip_bool, right_bool,
                                                          offset, calib_path,
                                                          calib_bool, practice_path,
                                                          practice_bool,
                                                          variable_string)
    
                            limit_indicator[i, off_ind] = find_significance_of_diff(
                                                         offset_var_type,
                                                         standard_var_type,
                                                         test_var, offset_var,
                                                         tolerance_decimal)

                            if limit_indicator[i, off_ind] == 1:
                                limit = '21'

                            elif limit_indicator[i, off_ind] == 0:
                                off_ind = 22
                                offset = off(off_ind)

                                offset_var, offset_var_type = run_system(base_path,
                                                              base_bool, left_bool,
                                                              hip_bool, right_bool,
                                                              offset, calib_path,
                                                              calib_bool, practice_path,
                                                              practice_bool,
                                                              variable_string)
        
                                limit_indicator[i, off_ind] = find_significance_of_diff(
                                                             offset_var_type,
                                                             standard_var_type,
                                                             test_var, offset_var,
                                                             tolerance_decimal)

                                if limit_indicator[i, off_ind] == 1:
                                    limit = '22'

                                elif limit_indicator[i, off_ind] == 0:
                                    limit = '23'

                                else:
                                    print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                                    sys.exit()

                            else:
                                print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                                sys.exit()

                        elif limit_indicator[i, off_ind] == 0:
                            off_ind = 24
                            offset = off(off_ind)

                            offset_var, offset_var_type = run_system(base_path,
                                                          base_bool, left_bool,
                                                          hip_bool, right_bool,
                                                          offset, calib_path,
                                                          calib_bool, practice_path,
                                                          practice_bool,
                                                          variable_string)
    
                            limit_indicator[i, off_ind] = find_significance_of_diff(
                                                         offset_var_type,
                                                         standard_var_type,
                                                         test_var, offset_var,
                                                         tolerance_decimal)

                            if limit_indicator[i, off_ind] == 1:
                                limit = '24'

                            elif limit_indicator[i, off_ind] == 0:
                                limit = '25'

                            else:
                                print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                                sys.exit()

                        else:
                            print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                            sys.exit()

                    elif limit_indicator[i, off_ind] == 0:
                        off_ind = 28
                        offset = off(off_ind)

                        offset_var, offset_var_type = run_system(base_path,
                                                      base_bool, left_bool,
                                                      hip_bool, right_bool,
                                                      offset, calib_path,
                                                      calib_bool, practice_path,
                                                      practice_bool,
                                                      variable_string)

                        limit_indicator[i, off_ind] = find_significance_of_diff(
                                                     offset_var_type,
                                                     standard_var_type,
                                                     test_var, offset_var,
                                                     tolerance_decimal)

                        if limit_indicator[i, off_ind] == 1:
                            off_ind = 26
                            offset = off(off_ind)

                            offset_var, offset_var_type = run_system(base_path,
                                                          base_bool, left_bool,
                                                          hip_bool, right_bool,
                                                          offset, calib_path,
                                                          calib_bool, practice_path,
                                                          practice_bool,
                                                          variable_string)

                            limit_indicator[i, off_ind] = find_significance_of_diff(
                                                         offset_var_type,
                                                         standard_var_type,
                                                         test_var, offset_var,
                                                         tolerance_decimal)

                            if limit_indicator[i, off_ind] == 1:
                                limit = '26'

                            elif limit_indicator[i, off_ind] == 0:
                                off_ind = 27
                                offset = off(off_ind)

                                offset_var, offset_var_type = run_system(base_path,
                                                              base_bool, left_bool,
                                                              hip_bool, right_bool,
                                                              offset, calib_path,
                                                              calib_bool, practice_path,
                                                              practice_bool,
                                                              variable_string)

                                limit_indicator[i, off_ind] = find_significance_of_diff(
                                                             offset_var_type,
                                                             standard_var_type,
                                                             test_var, offset_var,
                                                             tolerance_decimal)

                                if limit_indicator[i, off_ind] == 1:
                                    limit = '27'

                                elif limit_indicator[i, off_ind] == 0:
                                    limit = '28'

                                else:
                                    print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                                    sys.exit()

                            else:
                                print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                                sys.exit()

                        elif limit_indicator[i, off_ind] == 0:
                            off_ind = 29
                            offset = off(off_ind)

                            offset_var, offset_var_type = run_system(base_path,
                                                          base_bool, left_bool,
                                                          hip_bool, right_bool,
                                                          offset, calib_path,
                                                          calib_bool, practice_path,
                                                          practice_bool,
                                                          variable_string)

                            limit_indicator[i, off_ind] = find_significance_of_diff(
                                                         offset_var_type,
                                                         standard_var_type,
                                                         test_var, offset_var,
                                                         tolerance_decimal)

                            if limit_indicator[i, off_ind] == 1:
                                limit = '29'

                            elif limit_indicator[i, off_ind] == 0:
                                limit = '30'

                            else:
                                print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                                sys.exit()

                        else:
                            print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                            sys.exit()

                    else:
                        print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                        sys.exit()

                elif limit_indicator[i, off_ind] == 0:
                    limit = '> 30'

                else:
                    print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                    sys.exit()

            else:
                print "VAR_TYPE_ERROR", limit_indicator[i, off_ind]
                sys.exit()

        else:
            print "VAR_TYPE_ERROR"
            sys.exit()
            limit = 'off: ' + offset_var_type + '\nstand: ' + standard_var_type

        string = get_string_when_limit_reached(parameters, variable_string, limit)
        text_file.write(string)
        limit_indicator = np.zeros((len(EXT_COMBO),31))
        limit = 'NaN'

    text_file.close()


def off(deg):

    offset = np.radians(deg)
    offset = np.asarray([[offset]])
    
    return offset


def run_system(base_path, base_bool, left_bool, hip_bool, right_bool, offset,
               calib_path, calib_bool, practice_path, practice_bool,
               variable_string):

    offset_base = bf.record_special_feet(base_path, base_path, base_bool,
                                         left_bool, hip_bool, right_bool,
                                         offset)

    off_base = 'standard_base' + base_path

    offset_base.to_csv(off_base, index=False)

    offset_calib, offset_calib_transforms = sc.run_calibration(calib_path,
                               calib_path, off_base, calib_bool,
                               left_bool, hip_bool, right_bool, offset)

    offset_analytics_data = aa.abbrev_analytics(practice_path,
                              offset_calib_transforms, practice_bool,
                              left_bool, hip_bool, right_bool, offset)

    offset_analytics_data = offset_analytics_data.data

    offset_data, offset_var, offset_var_type = select_test_variables(
                              offset_calib_transforms,
                              offset_analytics_data, variable_string)

    return offset_var, offset_var_type

#%%
def find_significance_of_diff(offset_var_type, standard_var_type, test_var,
                              offset_var, tolerance_decimal):

    limit_indicator = 0
    if offset_var_type == 'float' and standard_var_type == 'float':
#        diff = (test_var - offset_var)/((test_var + offset_var)/2)
#        if any(diff) > tolerance_decimal:
#            limit_indicator = 1
#        else:
#            pass
#        limit_indicator = 0
#        print sum(np.isfinite(test_var)), sum(np.isfinite(offset_var))
        tol = abs(test_var * tolerance_decimal)
#        print test_var[np.isfinite(test_var)]
        diff = (test_var - offset_var)/test_var
#        print diff[np.isfinite(diff)]
        lim_reached = abs(diff) > tol
        lim_reached = sum(lim_reached)/float(sum(np.isfinite(offset_var)))
        
#        if any(lim_reached) == False:
#        for x in lim_reached:
        if lim_reached > 0.01: # NEED TO DEFINE HARD CODED VALUE HERE
            limit_indicator = 1
        print lim_reached, tolerance_decimal, limit_indicator
    elif offset_var_type == 'int' and standard_var_type == 'int':
#        print np.mean(test_var)
#        diff = test_var - offset_var
#        non_zero = np.nonzero(diff)[0]
        diff = np.mean(test_var != offset_var)
#        print (len(test_var) - len(non_zero))/((len(test_var) + len(non_zero))/2)
#        if (len(test_var) - len(non_zero))/((len(test_var) \
#            + len(non_zero))/2) > tolerance_decimal:
        if diff > tolerance_decimal:
            limit_indicator = 1
        print np.mean(test_var)
        print test_var[(test_var != offset_var)], "DIFFERENCE HERE"
        print diff, tolerance_decimal, limit_indicator
    else:
        limit_indicator = 2
        print offset_var_type, standard_var_type

    return limit_indicator

#%%
def get_string_when_limit_reached(parameters, variable_string, degrees):

    offset_left = ''
    offset_hip = ''
    offset_right = ''
    offset_in_base = ''
    offset_in_calib = ''
    offset_in_practice = ''

    if parameters[0] == True:
        offset_left = 'and left sensor is offset, '
    if parameters[1] == True:
        offset_hip = 'and hip sensor is offset, '
    if parameters[2] == True:
        offset_right = 'and right sensor is offset, '
    if parameters[3] == True:
        offset_in_base = 'in base file, '
    if parameters[4] == True:
        offset_in_calib = 'in session calib file, '
    if parameters[5] == True:
        offset_in_practice = 'in practice file, '
    string = 'If offset is ' + offset_in_base + offset_in_calib \
        + offset_in_practice + offset_left + offset_hip + offset_right \
        + '\n        ' + variable_string + ' breaks when offset = ' + degrees \
        + ' degrees.\n\n'
    
    return string


def select_test_variables(calib_transforms, analytics_data,
                          variable_string):
    var_type = 'UNASSIGNED'
    if variable_string == 'hip_bf_transform':
        data = calib_transforms
        test_var = calib_transforms[0]
        var_type = 'float'
    elif variable_string == 'lf_bf_transform':
        data = calib_transforms
        test_var = calib_transforms[1]
        var_type = 'float'
    elif variable_string == 'rf_bf_transform':
        data = calib_transforms
        test_var = calib_transforms[2]
        var_type = 'float'
    elif variable_string == 'hip_n_transform':
        data = calib_transforms
        test_var = calib_transforms[3]
        var_type = 'float'
    elif variable_string == 'lf_n_transform':
        data = calib_transforms
        test_var = calib_transforms[4]
        var_type = 'float'
    elif variable_string == 'rf_n_transform':
        data = calib_transforms
        test_var = calib_transforms[5]
        var_type = 'float'
    elif variable_string == 'hip_pitch_transform':
        data = calib_transforms
        test_var = calib_transforms[6]
        var_type = 'float'
    elif variable_string == 'hip_roll_transform':
        data = calib_transforms
        test_var = calib_transforms[7]
        var_type = 'float'
    elif variable_string == 'lf_roll_transform':
        data = calib_transforms
        test_var = calib_transforms[8]
        var_type = 'float'
    elif variable_string == 'rf_roll_transform':
        data = calib_transforms
        test_var = calib_transforms[9]
        var_type = 'float'
    elif variable_string == 'phase_lf':
        data = analytics_data
        test_var = analytics_data.phase_lf
        var_type = 'int'
    elif variable_string == 'phase_rf':
        data = analytics_data
        var_type = 'int'
        test_var = analytics_data.phase_rf
    elif variable_string == 'total_accel':
        data = analytics_data
        var_type = 'float'
        test_var = analytics_data.total_accel
    elif variable_string == 'single_leg_stationary':
        data = analytics_data
        var_type = 'int'
        test_var = analytics_data.single_leg_stationary
    elif variable_string == 'single_leg_dynamic':
        data = analytics_data
        test_var = analytics_data.single_leg_dynamic
        var_type = 'int'
    elif variable_string == 'double_leg':
        data = analytics_data
        test_var = analytics_data.double_leg
        var_type = 'int'
    elif variable_string == 'feet_eliminated':
        data = analytics_data
        test_var = analytics_data.feet_eliminated
        var_type = 'int'
    elif variable_string == 'rot_binary':
        data = analytics_data
        test_var = analytics_data.rot_binary
        var_type = 'int'
    elif variable_string == 'lat_binary':
        data = analytics_data
        test_var = analytics_data.lat_binary
        var_type = 'int'
    elif variable_string == 'vert_binary':
        data = analytics_data
        test_var = analytics_data.vert_binary
        var_type = 'int'
    elif variable_string == 'horz_binary':
        data = analytics_data
        test_var = analytics_data.horz_binary
        var_type = 'int'
    elif variable_string == 'stationary_binary':
        data = analytics_data
        test_var = analytics_data.stationary_binary
        var_type = 'int'
    elif variable_string == 'contra_hip_drop_lf':
        data = analytics_data
        test_var = analytics_data.contra_hip_drop_lf
        var_type = 'float'
    elif variable_string == 'contra_hip_drop_rf':
        data = analytics_data
        test_var = analytics_data.contra_hip_drop_rf
        var_type = 'float'
    elif variable_string == 'rot':
        data = analytics_data
        test_var = analytics_data.rot
        var_type = 'float'
    elif variable_string == 'lat':
        data = analytics_data
        test_var = analytics_data.lat
        var_type = 'float'
    elif variable_string == 'vert':
        data = analytics_data
        test_var = analytics_data.vert
        var_type = 'float'
    elif variable_string == 'horz':
        data = analytics_data
        test_var = analytics_data.horz
        var_type = 'float'
    elif variable_string == 'land_pattern_lf':
        data = analytics_data
        test_var = analytics_data.land_pattern_lf
        var_type = 'float'
    elif variable_string == 'land_pattern_rf':
        data = analytics_data
        test_var = analytics_data.land_pattern_rf
        var_type = 'float'
    elif variable_string == 'ankle_rot_lf':
        data = analytics_data
        test_var = analytics_data.ankle_rot_lf
        var_type = 'float'
    elif variable_string == 'ankle_rot_rf':
        data = analytics_data
        test_var = analytics_data.ankle_rot_rf
        var_type = 'float'
    else:
        print "CHECK YOUR VARIABLE STRING'S SPELLING"
        sys.exit()

    return data, test_var, var_type


if __name__ == '__main__':

    base_path = 'dipesh_baseAnatomicalCalibration.csv'
    calib_path = 'dipesh_sessionAnatomicalCalibration.csv'
    practice_path = 'dipesh_merged_II.csv'
    data = pd.read_csv('dipesh_merged_II.csv')
#    plt.figure(3)
#    plt.plot(data.LaY)
    variable_string = 'ankle_rot_lf'
    tolerance_decimal = 0.1
    run_full_system_test(base_path, calib_path, practice_path,
                         variable_string, tolerance_decimal)