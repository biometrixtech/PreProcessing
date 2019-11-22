from ._unit_block_job import UnitBlockJob
from models.complexity_matrix import ComplexityMatrix
from models.step import Step
from utils import parse_datetime
from collections import deque


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

        unit_block_count = 0

        right_queue = deque()
        left_queue = deque()

        for unit_block_data in self._unit_blocks:

            if len(unit_block_data) > 0:
                active_block = str(unit_block_data.get('_id'))
                if previous_active_block != active_block:
                    active_block_count += 1
                    previous_active_block = active_block
                # else:
                #     previous_active_block = active_block
                #
                # for unit_block_data in ub.get('unitBlocks'):
                cadence_zone = unit_block_data.get('cadence_zone')

                left_steps = unit_block_data.get('stepsLF')
                left_steps = sorted(left_steps, key=lambda ub: ub['startTime'])
                #for n, lf_step in enumerate(unit_block_data.get('stepsLF')):
                for n, lf_step in enumerate(left_steps):
                    left_step = Step(lf_step, accumulated_grf_lf, 'Left', active_block, unit_block_count, session_position,
                                     session_time_start)
                    left_step.active_block_number = active_block_count
                    if left_step.peak_grf is not None:
                        accumulated_grf_lf += left_step.peak_grf
                    else:
                        accumulated_grf_lf += 0
                    left_step.cadence_zone = cadence_zone
                    if left_step.stance_calc == 4:
                        dl_comp_matrix.add_step(left_step)
                    elif left_step.stance_calc == 2:
                        if left_step.max_ankle_pitch_time is not None:
                            right_queue.append((left_step.max_ankle_pitch_time, left_step.ankle_pitch))
                        sl_comp_matrix.add_step(left_step)

                right_steps = unit_block_data.get('stepsRF')
                right_steps = sorted(right_steps, key=lambda ub: ub['startTime'])
                # for n, rf_step in enumerate(unit_block_data.get('stepsRF')):
                for n, rf_step in enumerate(right_steps):

                    right_step = Step(rf_step, accumulated_grf_rf, 'Right', active_block, unit_block_count, session_position,
                                      session_time_start)

                    # stop_purging = False
                    #
                    # while not stop_purging:
                    #     if len(right_queue) == 0:
                    #         stop_purging = True
                    #     elif right_step.step_start_time > parse_datetime(right_queue[0][0]):
                    #         right_queue.popleft()
                    #     else:
                    #         stop_purging = True
                    #
                    # if len(right_queue) > 0 and right_step.step_start_time <=  parse_datetime(right_queue[0][0]) <= right_step.step_end_time:
                    #     left_ankle_pitch = right_queue.popleft()
                    #     right_step.ankle_pitch_range = left_ankle_pitch[1]
                    self.process_step_and_queue(right_queue, right_step)

                    if right_step.max_ankle_pitch_time is not None:
                        left_queue.append((right_step.max_ankle_pitch_time, right_step.ankle_pitch))

                    right_step.active_block_number = active_block_count
                    if right_step.peak_grf is not None:
                        accumulated_grf_rf += right_step.peak_grf
                    else:
                        accumulated_grf_rf += 0
                    right_step.cadence_zone = cadence_zone
                    if right_step.stance_calc == 4:
                        dl_comp_matrix.add_step(right_step)
                    elif right_step.stance_calc == 2:
                        sl_comp_matrix.add_step(right_step)

                for left_step in sl_comp_matrix.cells['Single Leg'].left_steps:

                    self.process_step_and_queue(left_queue, left_step)

                session_position = session_position + 1
            unit_block_count += 1

        self._motion_complexity_single_leg = {}
        self._motion_complexity_single_leg.update(sl_comp_matrix.cells)

        self._motion_complexity_double_leg = {}
        self._motion_complexity_double_leg.update(dl_comp_matrix.cells)

    def process_step_and_queue(self, queue, step):

        stop_purging = False

        while not stop_purging:
            if len(queue) == 0:
                stop_purging = True
            elif step.step_start_time > parse_datetime(queue[0][0]):
                queue.popleft()
            else:
                stop_purging = True
        if len(queue) > 0 and step.step_start_time <= parse_datetime(
                queue[0][0]) <= step.step_end_time:
            opposite_ankle_pitch = queue.popleft()
            step.ankle_pitch_range = opposite_ankle_pitch[1]

    @property
    def motion_complexity_single_leg(self):
        return self._motion_complexity_single_leg

    @property
    def motion_complexity_double_leg(self):
        return self._motion_complexity_double_leg
