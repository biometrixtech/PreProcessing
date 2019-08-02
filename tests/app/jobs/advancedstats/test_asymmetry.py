from aws_xray_sdk.core import xray_recorder
xray_recorder.configure(sampling=False)
xray_recorder.begin_segment(name="test")

import os
import json
from app.jobs.advancedstats.asymmetry_processor_job import AsymmetryProcessorJob
from app.jobs.advancedstats.complexity_matrix_job import ComplexityMatrixJob
from app.jobs.advancedstats.fatigue_processor_job import FatigueProcessorJob
from tests.app.writemongo.datastore import MockDatastore
from app.models.session_fatigue import SessionFatigue


def test_get_fatigue():
    path = '../../../../testdata/advanced/'
    file = 'f93e004d-Gabby-treadmill-073019-kit2831-normalPlacement-beforeFoamRoll_0.json'
    file_path = os.path.join(path, file)
    with open(file_path, 'r') as f:
        data = json.load(f)
        unit_blocks = data['unitBlocks']
        ds = MockDatastore("gabby", "2019-08-02", None)

        cmj = ComplexityMatrixJob(ds, unit_blocks)
        cmj.run()

        fatigue_events = FatigueProcessorJob(ds, cmj.motion_complexity_single_leg,
                                             cmj.motion_complexity_double_leg)._get_fatigue_events()
        session_fatigue = SessionFatigue(fatigue_events)

        cma_grf_list = session_fatigue.cma_grf_crosstab()

        k=0

def test_get_asymmetery():
    path = '../../../../testdata/advanced/'
    files = ['f93e004d-Gabby-treadmill-073019-kit2831-normalPlacement-beforeFoamRoll_0.json',
             '7b6c7bba-Gabby-treadmill-073019-kit2c39-highPlacement-beforeFoamRoll_0.json',
             '07b9b744-Gabby-treadmill-073019-kit2BE8-offcenterPlacement-beforeFoamRoll_0.json']
    asymmetry_dict = {}
    for file in files:
        file_path = os.path.join(path, file)
        with open(file_path, 'r') as f:
            data = json.load(f)
            unit_blocks = data['unitBlocks']
            ds = MockDatastore("gabby", "2019-08-02", None)

            cmj = ComplexityMatrixJob(ds, unit_blocks)
            cmj.run()
            asymmetry_events = AsymmetryProcessorJob(ds, unit_blocks, cmj.motion_complexity_single_leg, cmj.motion_complexity_double_leg)._get_movement_asymmetries()
            asymmetry_dict[file] = asymmetry_events
    k=0