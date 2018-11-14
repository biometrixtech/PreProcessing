from datetime import datetime
from advancedStats.models.unit_block import UnitBlock
from advancedStats.summary_analysis import get_unit_blocks
from advancedStats.models.training_volume_metrics import IntensityBySeconds


def create_intensity_matrix(user, date):
    mongo_unit_blocks = get_unit_blocks(user, date)
    intensity = IntensityBySeconds()

    if len(mongo_unit_blocks) > 0:

        low_intensity_time = 0
        med_intensity_time = 0
        high_intensity_time = 0
        total_duration = 0

        for ub in mongo_unit_blocks:
            if len(ub) > 0:

                unit_bock_count = len(ub.get('unitBlocks'))

                for n in range(0, unit_bock_count):
                    ub_data = ub.get('unitBlocks')[n]
                    ub_rec = UnitBlock(ub_data)
                    time_start = ub.get('unitBlocks')[n].get('timeStart')
                    time_end = ub.get('unitBlocks')[n].get('timeEnd')
                    try:
                        time_start_object = datetime.strptime(time_start, '%Y-%m-%d %H:%M:%S.%f')
                    except ValueError:
                        time_start_object = datetime.strptime(time_start, '%Y-%m-%d %H:%M:%S')
                    try:
                        time_end_object = datetime.strptime(time_end, '%Y-%m-%d %H:%M:%S.%f')
                    except ValueError:
                        time_end_object = datetime.strptime(time_end, '%Y-%m-%d %H:%M:%S')

                    total_duration += ub_rec.duration
                    if ub_rec.total_accel_avg < 45:
                        low_intensity_time += (time_end_object - time_start_object).seconds
                    elif ub_rec.total_accel_avg >= 45 and ub_rec.total_accel_avg < 105:
                        med_intensity_time += (time_end_object - time_start_object).seconds
                    else:
                        high_intensity_time += (time_end_object - time_start_object).seconds

        intensity.low_intensity_seconds += low_intensity_time
        intensity.moderate_intensity_seconds += med_intensity_time
        intensity.high_intensity_seconds += high_intensity_time
        intensity.total_seconds += total_duration
        intensity.low_intensity_seconds += (low_intensity_time / total_duration) * 100
        intensity.moderate_intensity_percentage += (med_intensity_time / total_duration) * 100
        intensity.high_intensity_percentage += (high_intensity_time / total_duration) * 100
        intensity.total_intensity_percentage += (total_duration / total_duration) * 100

    return intensity
