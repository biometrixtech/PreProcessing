from enum import Enum
import numpy as np


class ActiveBlock(object):
    def __init__(self):
        self.start_index = None
        self.end_index = None
        self.unit_blocks = []

    def json_serialise(self):
        ret = {
                "start_index": self.start_index,
                "end_index": self.end_index,
                "unit_blocks": [ub.json_serialise() for ub in self.unit_blocks]}
        return ret

    def get_unit_blocks(self, data):
        ab_data = data.loc[self.start_index:self.end_index, :]
        unit_block_flag = ab_data.cadence_zone.values + ab_data.change_of_direction.values
        diff = np.abs(np.ediff1d(unit_block_flag, to_begin=-1))  # mark start of active block as start of first unit block
        diff[-1] = -1
        ub_changes = np.where(diff != 0)[0]
        if len(ub_changes) == 2:
            self.unit_blocks.append(UnitBlock(self.start_index, self.end_index))
        else:
            ub = UnitBlock(ub_changes[0] + self.start_index)
            started = True
            for i in range(1, len(ub_changes)):
                if started:
                    ub.end_index = ub_changes[i] + self.start_index
                    self.unit_blocks.append(ub)
                    if unit_block_flag[ub_changes[i]] != 0:
                        ub = UnitBlock(ub_changes[i] + self.start_index)
                        started = True
                    else:
                        started = False
                else:
                    ub = UnitBlock(ub_changes[i] + self.start_index)
                    started = True


class CadenceZone(Enum):
    walking = 10
    jogging = 20
    running = 30
    sprinting = 40


class UnitBlock(object):
    def __init__(self, start, end=None):
        self.start_index = start
        self.end_index = end
        self.cadence_zone = 0
        self.change_of_direction = False
        self.accelerating = False
        self.decelerating = False

    def json_serialise(self):
        ret = {
                "start_index": self.start_index,
                "end_index": self.end_index,
                "cadence_zone": self.cadence_zone,
                "change_of_direction": self.change_of_direction,
                "accelerating": self.accelerating,
                "decelerating": self.decelerating}
        return ret

    def set_complexity_flags(self, data):
        self.cadence_zone = data.cadence_zone[self.start_index]
        self.change_of_direction = True if data.change_of_direction[self.start_index] == 1 else False
