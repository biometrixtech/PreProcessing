from itertools import groupby
from operator import itemgetter


class FatigueEvent(object):
    def __init__(self, grf_level, cma_level):
        self.stance = ""
        self.active_block_id = ""
        self.complexity_level = ""
        self.grf_level = grf_level.replace("Grf", "")
        self.cma_level = cma_level.replace("CMA", "")
        self.time_block = ""
        self.attribute_name = ""
        self.attribute_label = ""
        self.orientation = ""
        self.cumulative_end_time = None
        self.z_score = 0.0
        self.raw_value = 0.0
        self.count = 1

    def __getitem__(self, item):
        return getattr(self, item)


class SessionFatigue(object):
    def __init__(self, user_id, event_date, session_id, fatigue_events):
        self.user_id = user_id
        self.event_date = event_date
        self.session_id = session_id
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
