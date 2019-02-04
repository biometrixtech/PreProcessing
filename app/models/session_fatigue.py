from itertools import groupby
from operator import itemgetter


class SessionFatigue(object):
    def __init__(self, fatigue_events):
        self.fatigue_events = fatigue_events

    def session_summary(self):

        fatigue_list = []

        grouper = itemgetter("stance", "attribute_label", "orientation")
        result = []

        for key, grp in groupby(sorted(self.fatigue_events, key=grouper), grouper):
            temp_dict = dict(zip(["stance", "attribute_label", "orientation"], key))
            temp_dict["cnt"] = sum(item["count"] for item in grp)
            result.append(temp_dict)

        for r in result:
            f = FatigueBySession()
            f.stance = r["stance"]
            f.attribute_label = r["attribute_label"]
            f.orientation = r["orientation"]
            f.count = r["cnt"]
            fatigue_list.append(f)

        return fatigue_list

    def cma_grf_crosstab(self):

        crosstab_list = []

        val_list = ["Low", "Mod", "High"]
        stance_list = ["Single Leg", "Double Leg"]

        for s in stance_list:
            for c in val_list:
                for g in val_list:

                    crosstab = FatigueByCMAGRFCrossTab(c, g)
                    crosstab.stance = s
                    crosstab_list.append(crosstab)

        for e in self.fatigue_events:
            for c in crosstab_list:
                if c.cma_level == e.cma_level and c.grf_level == e.grf_level and c.stance == e.stance:
                    if e.raw_value < 0:  # negative decay rate
                        label = e.attribute_label+"_" + e.orientation.lower() + "_inc"
                        val = getattr(c, label)
                    else:
                        label = e.attribute_label+"_" + e.orientation.lower() + "_dec"
                        val = getattr(c, label)
                    setattr(c, label, val+1)

        return crosstab_list

    def active_block_crosstab(self):

        crosstab_list = []

        active_blocks = set(list(x.active_block_id for x in self.fatigue_events))

        for a in active_blocks:
            crosstab = FatigueByActiveBlockCrossTab()
            crosstab.active_block = a
            crosstab_list.append(crosstab)

        for e in self.fatigue_events:
            for c in crosstab_list:
                if e.active_block_id == c.active_block:
                    if e.raw_value < 0:  # negative decay rate
                        label = e.attribute_label+"_" + e.orientation.lower() + "_inc"
                        val = getattr(c, label)
                    else:
                        label = e.attribute_label+"_" + e.orientation.lower() + "_dec"
                        val = getattr(c, label)
                    setattr(c, label, val+1)
                    c.cumulative_end_time = e.cumulative_end_time
                    c.time_block = e.time_block

        return crosstab_list

    def cma_grf_summary(self):

        fatigue_list = []

        grouper = itemgetter("stance", "cma_level", "grf_level", "attribute_label", "orientation")
        result = []

        for key, grp in groupby(sorted(self.fatigue_events, key=grouper), grouper):
            temp_dict = dict(zip(["stance", "cma_level", "grf_level", "attribute_label", "orientation"], key))
            temp_dict["cnt"] = sum(item["count"] for item in grp)
            result.append(temp_dict)

        for r in result:
            f = FatigueByCMAGRF(r["cma_level"], r["grf_level"])
            f.stance = r["stance"]
            f.attribute_label = r["attribute_label"]
            f.orientation = r["orientation"]
            f.count = r["cnt"]
            fatigue_list.append(f)

        return fatigue_list

    def cma_time_block_summary(self):

        fatigue_list = []

        grouper = itemgetter("stance", "cma_level", "time_block", "attribute_label", "orientation")
        result = []

        for key, grp in groupby(sorted(self.fatigue_events, key=grouper), grouper):
            temp_dict = dict(zip(["stance", "cma_level", "time_block", "attribute_label", "orientation"], key))
            temp_dict["cnt"] = sum(item["count"] for item in grp)
            result.append(temp_dict)

        for r in result:
            f = FatigueByCMATimeBlock(r["cma_level"], r["time_block"])
            f.stance = r["stance"]
            f.attribute_label = r["attribute_label"]
            f.orientation = r["orientation"]
            f.count = r["cnt"]
            fatigue_list.append(f)

        return fatigue_list

    def grf_time_block_summary(self):

        fatigue_list = []

        grouper = itemgetter("stance", "grf_level", "time_block", "attribute_label", "orientation")
        result = []

        for key, grp in groupby(sorted(self.fatigue_events, key=grouper), grouper):
            temp_dict = dict(zip(["stance", "grf_level", "time_block", "attribute_label", "orientation"], key))
            temp_dict["cnt"] = sum(item["count"] for item in grp)
            result.append(temp_dict)

        for r in result:
            f = FatigueByGRFTimeBlock(r["grf_level"], r["time_block"])
            f.stance = r["stance"]
            f.attribute_label = r["attribute_label"]
            f.orientation = r["orientation"]
            f.count = r["cnt"]
            fatigue_list.append(f)

        return fatigue_list

    def cma_summary(self):

        fatigue_list = []

        grouper = itemgetter("stance", "cma_level", "attribute_label", "orientation")
        result = []

        for key, grp in groupby(sorted(self.fatigue_events, key=grouper), grouper):
            temp_dict = dict(zip(["stance", "cma_level", "attribute_label", "orientation"], key))
            temp_dict["cnt"] = sum(item["count"] for item in grp)
            result.append(temp_dict)

        for r in result:
            f = FatigueByCMA(r["cma_level"])
            f.stance = r["stance"]
            f.attribute_label = r["attribute_label"]
            f.orientation = r["orientation"]
            f.count = r["cnt"]
            fatigue_list.append(f)

        return fatigue_list

    def grf_summary(self):

        fatigue_list = []

        grouper = itemgetter("stance", "grf_level", "attribute_label", "orientation")
        result = []

        for key, grp in groupby(sorted(self.fatigue_events, key=grouper), grouper):
            temp_dict = dict(zip(["stance", "grf_level", "attribute_label", "orientation"], key))
            temp_dict["cnt"] = sum(item["count"] for item in grp)
            result.append(temp_dict)

        for r in result:
            f = FatigueByGRF(r["grf_level"])
            f.stance = r["stance"]
            f.attribute_label = r["attribute_label"]
            f.orientation = r["orientation"]
            f.count = r["cnt"]
            fatigue_list.append(f)

        return fatigue_list

    def time_block_summary(self):

        fatigue_list = []

        grouper = itemgetter("stance", "time_block", "attribute_label", "orientation")
        result = []

        for key, grp in groupby(sorted(self.fatigue_events, key=grouper), grouper):
            temp_dict = dict(zip(["stance", "time_block", "attribute_label", "orientation"], key))
            temp_dict["cnt"] = sum(item["count"] for item in grp)
            result.append(temp_dict)

        for r in result:
            f = FatigueByTimeBlock(r["time_block"])
            f.stance = r["stance"]
            f.attribute_label = r["attribute_label"]
            f.orientation = r["orientation"]
            f.count = r["cnt"]
            fatigue_list.append(f)

        return fatigue_list


class FatigueByCMATimeBlock(object):
    def __init__(self, cma_level, time_block):
        self.stance = ""
        self.cma_level = cma_level.replace("CMA", "")
        self.time_block = time_block
        self.attribute_name = ""
        self.attribute_label = ""
        self.orientation = ""
        self.count = 0


class FatigueByCMA(object):
    def __init__(self, cma_level):
        self.stance = ""
        self.cma_level = cma_level.replace("CMA", "")
        self.attribute_name = ""
        self.attribute_label = ""
        self.orientation = ""
        self.count = 0


class FatigueByGRF(object):
    def __init__(self, grf_level):
        self.stance = ""
        self.grf_level = grf_level.replace("GRF", "")
        self.attribute_name = ""
        self.attribute_label = ""
        self.orientation = ""
        self.count = 0


class FatigueByGRFTimeBlock(object):
    def __init__(self, grf_level, time_block):
        self.stance = ""
        self.grf_level = grf_level.replace("Grf", "")
        self.time_block = time_block
        self.attribute_name = ""
        self.attribute_label = ""
        self.orientation = ""
        self.count = 0


class FatigueByCMAGRF(object):
    def __init__(self, cma_level, grf_level):
        self.stance = ""
        self.cma_level = cma_level.replace("CMA", "")
        self.grf_level = grf_level.replace("Grf", "")
        self.attribute_name = ""
        self.attribute_label = ""
        self.orientation = ""
        self.count = 0
        self.expected_count = 0
        self.cma_df = 0
        self.grf_df = 0
        self.chi_square = 0.0
        self.chi_square_critical_value = 0.0


class FatigueByCMAGRFCrossTab(object):
    def __init__(self, cma_level, grf_level):
        self.stance = ""
        self.cma_level = cma_level.replace("CMA", "")
        self.grf_level = grf_level.replace("Grf", "")
        self.adduc_pos_hip_left_inc = 0
        self.adduc_pos_hip_right_inc = 0
        self.adduc_neg_hip_left_inc = 0
        self.adduc_neg_hip_right_inc = 0
        self.flex_pos_hip_left_inc = 0
        self.flex_pos_hip_right_inc = 0
        self.flex_neg_hip_left_inc = 0
        self.flex_neg_hip_right_inc = 0

        self.adduc_pos_hip_left_dec = 0
        self.adduc_pos_hip_right_dec = 0
        self.adduc_neg_hip_left_dec = 0
        self.adduc_neg_hip_right_dec = 0
        self.flex_pos_hip_left_dec = 0
        self.flex_pos_hip_right_dec = 0
        self.flex_neg_hip_left_dec = 0
        self.flex_neg_hip_right_dec = 0

        self.flex_rom_hip_left_inc = 0
        self.flex_rom_hip_right_inc = 0
        self.adduc_rom_hip_left_inc = 0
        self.adduc_rom_hip_right_inc = 0
        self.flex_rom_hip_left_dec = 0
        self.flex_rom_hip_right_dec = 0
        self.adduc_rom_hip_left_dec = 0
        self.adduc_rom_hip_right_dec = 0


class FatigueByActiveBlockCrossTab(object):
    def __init__(self):
        self.active_block = ""
        self.cumulative_end_time = None
        self.time_block = 0
        self.adduc_pos_hip_left_inc = 0
        self.adduc_pos_hip_right_inc = 0
        self.adduc_neg_hip_left_inc = 0
        self.adduc_neg_hip_right_inc = 0
        self.flex_pos_hip_left_inc = 0
        self.flex_pos_hip_right_inc = 0
        self.flex_neg_hip_left_inc = 0
        self.flex_neg_hip_right_inc = 0

        self.adduc_pos_hip_left_dec = 0
        self.adduc_pos_hip_right_dec = 0
        self.adduc_neg_hip_left_dec = 0
        self.adduc_neg_hip_right_dec = 0
        self.flex_pos_hip_left_dec = 0
        self.flex_pos_hip_right_dec = 0
        self.flex_neg_hip_left_dec = 0
        self.flex_neg_hip_right_dec = 0

        self.flex_rom_hip_left_inc = 0
        self.flex_rom_hip_right_inc = 0
        self.adduc_rom_hip_left_inc = 0
        self.adduc_rom_hip_right_inc = 0
        self.flex_rom_hip_left_dec = 0
        self.flex_rom_hip_right_dec = 0
        self.adduc_rom_hip_left_dec = 0
        self.adduc_rom_hip_right_dec = 0


# This is the final level summary from statistically significant combined events
class FatigueBySession(object):
    def __init__(self):
        self.stance = ""
        self.attribute_name = ""
        self.attribute_label = ""
        self.orientation = ""
        self.count = 0


# This is the final level summary from statistically significant combined events
class FatigueByTimeBlock(object):
    def __init__(self, time_block):
        self.stance = ""
        self.time_block = time_block
        self.attribute_name = ""
        self.attribute_label = ""
        self.orientation = ""
        self.count = 0
