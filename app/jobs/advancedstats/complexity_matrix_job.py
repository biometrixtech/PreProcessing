from ._unit_block_job import UnitBlockJob
from models.complexity_matrix import ComplexityMatrix
from models.step import Step
from utils import parse_datetime


class ComplexityMatrixJob(UnitBlockJob):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._motion_complexity_single_leg = None
        self._motion_complexity_double_leg = None

    def _run(self):
        dl_comp_matrix = ComplexityMatrix("Double Leg")
        sl_comp_matrix = ComplexityMatrix("Single Leg")

        accumulated_grf_lf = 0
        accumulated_grf_rf = 0
        session_position = 0
        session_time_start = parse_datetime(self._unit_blocks[0].get('timeStart'))

        active_block_count = 0
        previous_active_block = ""

        for ub in self._unit_blocks:

            if len(ub) > 0:
                active_block = str(ub.get('_id'))
                if previous_active_block != active_block:
                    active_block_count += 1
                else:
                    previous_active_block = active_block

                for unit_block_data in ub.get('unitBlocks'):

                    for n, lf_step in enumerate(unit_block_data.get('stepsLF')):
                        left_step = Step(lf_step, accumulated_grf_lf, 'Left', active_block, n, session_position,
                                         session_time_start)
                        left_step.active_block_number = active_block_count
                        if left_step.peak_grf is not None:
                            accumulated_grf_lf += left_step.peak_grf
                        else:
                            accumulated_grf_lf += 0
                        if left_step.stance_calc == 4:
                            dl_comp_matrix.add_step(left_step)
                        elif left_step.stance_calc == 2:
                            sl_comp_matrix.add_step(left_step)

                    for n, rf_step in enumerate(unit_block_data.get('stepsRF')):
                        right_step = Step(rf_step, accumulated_grf_rf, 'Right', active_block, n, session_position,
                                          session_time_start)
                        right_step.active_block_number = active_block_count
                        if right_step.peak_grf is not None:
                            accumulated_grf_rf += right_step.peak_grf
                        else:
                            accumulated_grf_rf += 0
                        if right_step.stance_calc == 4:
                            dl_comp_matrix.add_step(right_step)
                        elif right_step.stance_calc == 2:
                            sl_comp_matrix.add_step(right_step)
                    session_position = session_position + 1

        self._motion_complexity_single_leg = {}
        self._motion_complexity_single_leg.update(sl_comp_matrix.cells)

        self._motion_complexity_double_leg = {}
        self._motion_complexity_double_leg.update(dl_comp_matrix.cells)

    @property
    def motion_complexity_single_leg(self):
        return self._motion_complexity_single_leg

    @property
    def motion_complexity_double_leg(self):
        return self._motion_complexity_double_leg
