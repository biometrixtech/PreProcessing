from aws_xray_sdk.core import xray_recorder
xray_recorder.configure(sampling=False)
xray_recorder.begin_segment(name="test")

import os
import json
from app.jobs.advancedstats.asymmetry_processor_job import AsymmetryProcessorJob
from app.jobs.advancedstats.complexity_matrix_job import ComplexityMatrixJob
from tests.app.writemongo.datastore import MockDatastore

path = '../../../../testdata/advanced/'

files = [  # 'f93e004d-Gabby-treadmill-073019-kit2831-normalPlacement-beforeFoamRoll_0.json',
    # '7b6c7bba-Gabby-treadmill-073019-kit2c39-highPlacement-beforeFoamRoll_0.json',
    # '07b9b744-Gabby-treadmill-073019-kit2BE8-offcenterPlacement-beforeFoamRoll_0.json',
    'f78a9e26_0.json',
    '7bbff8e0_0.json',
    'e3223bf2_0.json',
]

def test_get_asymmetery():

    output_file_name = "asymmetry_results_expanded_3_gaps.csv"
    output_file_path = os.path.join(path, output_file_name)
    output_file = open(output_file_path, 'w')
    line = ('file,variable, time_block, start_time, end_time, significant, left_median, right_median, left_min, left_max, right_min, right_max, left_q1, left_q2, left_q3, left_q4, right_q1, right_q2, right_q3, right_q4')
    output_file.write(line + '\n')

    for file in files:
        file_path = os.path.join(path, file)
        with open(file_path, 'r') as f:
            data = json.load(f)
            unit_blocks = data['unitBlocks']
            ds = MockDatastore("gabby", "2019-08-02", None)

            cmj = ComplexityMatrixJob(ds, unit_blocks)
            cmj.run()
            asymmetry_events = AsymmetryProcessorJob(ds, unit_blocks, cmj.motion_complexity_single_leg)._get_movement_asymmetries()

            for a in asymmetry_events:

                text_line = (file + ",anterior_pelvic_tilt_range," + str(a.time_block) + "," + str(
                    a.start_time) + "," + str(a.end_time) + "," + str(a.significant) + "," + str(a.left_median) + "," + str(a.right_median) + "," +
                             str(a.left_min) + "," + str(a.left_max) + "," + str(
                            a.right_min) + "," +
                             str(a.right_max) + "," + str(
                            a.left_q1_sum) + "," + str(a.left_q2_sum) + "," +
                             str(a.left_q3_sum) + "," + str(a.left_q4_sum) + "," + str(
                            a.right_q1_sum) + "," + str(
                            a.right_q2_sum) + "," + str(a.right_q3_sum) + "," + str(a.right_q4_sum) + "\n")
                output_file.write(text_line)
        k=0

    output_file.close()
