import numpy as np


def aggregate(data, record):
    """
    Aggregates different variables for block/unitBlocks
    """
    # GRF aggregation
    record['totalGRF'] = None
    record['optimalGRF'] = None
    record['irregularGRF'] = None
    record['LFgRF'] = None
    record['RFgRF'] = None
    record['leftGRF'] = None
    record['rightGRF'] = None
    record['singleLegGRF'] = None
    record['percLeftGRF'] = None
    record['percRightGRF'] = None
    record['percLRGRFDiff'] = None

    # accel aggregation
    record['totalAccel'] = np.nansum(data['total_accel'])
    record['irregularAccel'] = np.nansum(data['irregular_accel'])

    # control aggregation
    record['control'] = np.sum(data['control']*data['aZ']) / numpy.sum(data['aZ'])
    record['hipControl'] = None
    record['ankleControl'] = None
    record['controlLF'] = None
    record['controlRF'] = None

    # symmetry aggregation
    record['symmetry'] = None
    record['hipSymmetry'] = None
    record['ankleSymmetry'] = None

    # consistency aggregation
    record['consistency'] = None
    record['hipConsistency'] = None
    record['ankleConsistency'] = None
    record['consistencyLF'] = None
    record['consistencyRF'] = None

    # enforce validity of scores
    scor_cols = ['symmetry',
                 'hipSymmetry',
                 'ankleSymmetry',
                 'consistency',
                 'hipConsistency',
                 'ankleConsistency',
                 'consistencyLF',
                 'consistencyRF',
                 'control',
                 'hipControl',
                 'ankleControl',
                 'controlLF',
                 'controlRF']
    for key in scor_cols:
        value = record[key]
        try:
            if np.isnan(value):
                record[key] = None
            elif value >= 100:
                record[key] = 100
        except TypeError:
            pass

    # fatigue
    perc_optimal_block = (record['totalAccel'] - record['irregularAccel']) / record['totalAccel']
    record['percOptimal'] = perc_optimal_block * 100
    record['percIrregular'] = (1 - perc_optimal_block) * 100

    return record
