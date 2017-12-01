from __future__ import print_function

from collections import namedtuple
from pymongo import MongoClient
from shutil import copyfile
import logging
import os
import pandas
import numpy
import sys
from collections import OrderedDict

from vars_in_mongo import prog_comp_vars

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
Config = namedtuple('Config', [
    'AWS',
    'ENVIRONMENT',
    'MONGO_HOST',
    'MONGO_USER',
    'MONGO_PASSWORD',
    'MONGO_DATABASE',
    'MONGO_COLLECTION',
    'MONGO_REPLICASET',
])


def script_handler(working_directory, input_data):
    logger.info('Running program composition aggregation  on "{}"'.format(working_directory.split('/')[-1]))

    try:
        config = Config(
            AWS=False,
            ENVIRONMENT=os.environ['ENVIRONMENT'],
            MONGO_HOST=os.environ['MONGO_HOST_SESSION'],
            MONGO_USER=os.environ['MONGO_USER_SESSION'],
            MONGO_PASSWORD=os.environ['MONGO_PASSWORD_SESSION'],
            MONGO_DATABASE=os.environ['MONGO_DATABASE_SESSION'],
            MONGO_COLLECTION=os.environ['MONGO_COLLECTION_PROGCOMP'],
            MONGO_REPLICASET=os.environ['MONGO_REPLICASET_SESSION'] if os.environ['MONGO_REPLICASET_SESSION'] != '---' else None,
        )

        # first collection
        mongo_client = MongoClient(config.MONGO_HOST, replicaset=config.MONGO_REPLICASET)

        mongo_database = mongo_client[config.MONGO_DATABASE]

        # Authenticate
        mongo_database.authenticate(config.MONGO_USER, config.MONGO_PASSWORD,
                                    mechanism='SCRAM-SHA-1')

        mongo_collection = mongo_database[config.MONGO_COLLECTION]

        tmp_filename = '/tmp/readfile'
        copyfile(os.path.join(working_directory, 'scoring'), tmp_filename)
        logger.info("Copied data file to local FS")
        data = pandas.read_csv(tmp_filename)
        os.remove(tmp_filename)
        logger.info("Removed temporary file")

        # rename columns to match mongo
        data.columns = ['obsIndex', 'timeStamp', 'epochTime', 'msElapsed', 'sessionDuration',
                        'loadingLF', 'loadingRF',
                        'phaseLF', 'phaseRF', 'lfImpactPhase', 'rfImpactPhase',
                        'total', 'LF', 'RF', 'constructive', 'destructive', 'destrMultiplier', 'sessionGRFElapsed',
                        'symmetry', 'symmetryL', 'symmetryR', 'hipSymmetry', 'hipSymmetryL', 'hipSymmetryR',
                        'ankleSymmetry', 'ankleSymmetryL', 'ankleSymmetryR',
                        'consistency', 'hipConsistency', 'ankleConsistency', 'consistencyLF', 'consistencyRF',
                        'control', 'hipControl', 'ankleControl', 'controlLF', 'controlRF',
                        'contraHipDropLF', 'contraHipDropRF', 'ankleRotLF', 'ankleRotRF', 'footPositionLF',
                        'footPositionRF',
                        'landPatternLF', 'landPatternRF', 'landTime',
                        'rateForceAbsorptionLF', 'rateForceAbsorptionRF', 'rateForceProductionLF',
                        'rateForceProductionRF', 'totalAccel',
                        'stance', 'plane', 'rot', 'lat', 'vert', 'horz']
        data_out = {}
        data['msElapsed'] = data['msElapsed'].astype(float)
        data_out['teamId'] = input_data.get('TeamId', None)
        data_out['trainingGroups'] = input_data.get('TrainingGroupId', None)
        data_out['userId'] = input_data.get('UserId', None)
        data_out['sessionId'] = input_data.get('SessionEventId', None)
        data_out['sessionType'] = input_data.get('SessionType', None)
        if data_out['sessionType'] is not None:
            data_out['sessionType'] = str(data_out['sessionType'])
        data_out['userMass'] = input_data.get('UserMass', 155) * 4.4482
        data_out['eventDate'] = input_data.get('EventDate', None)

        # Compute the max grf and totalAccel for each .5s window for use in program comp
        data['totalAccelUnscaled'] = data['totalAccel'] / data['msElapsed'] * 100000
        data['half_sec'] = pandas.DatetimeIndex(pandas.to_datetime(data.epochTime, unit='ms')).round('500ms')
        f = OrderedDict({'total': [numpy.max]})
        f['totalAccelUnscaled'] = [numpy.max]
        
        max_half_sec = data.groupby('half_sec').agg(f)
        max_half_sec.columns = ['totalNormMax', 'totalAccelMax']
        data = data.join(max_half_sec, on='half_sec')
        data.loc[:, 'totalNormMax'] = data.totalNormMax / data_out['userMass'] * 1000000

        prog_comp_columns = ['min',
                             'max',
                             'binNumber',
                             'totalGRF',
                             'optimalGRF',
                             'irregularGRF',
                             'totalAcceleration',
                             'msElapsed',
                             'percOptimal',
                             'percIrregular']

        agg_vars = ['total', 'constructive', 'destructive', 'totalAccel', 'msElapsed']

        # replace nans with None
        # data = data.where((pandas.notnull(data)), None)
        # logger.info("Filtered out null values")
        total_ind = numpy.array([k != 3 for k in data.phaseLF])
        data['total'] = data['total'].fillna(value=numpy.nan) * total_ind

        # get program compositions
        data_out['grfProgramComposition'] = _grf_prog_comp(data, data_out['userMass'], agg_vars,
                                                           prog_comp_columns)
        data_out['totalAccelProgramComposition'] = _accel_prog_comp(data, agg_vars, prog_comp_columns)
        data_out['planeProgramComposition'] = _plane_prog_comp(data, agg_vars, prog_comp_columns)
        data_out['stanceProgramComposition'] = _stance_prog_comp(data, agg_vars, prog_comp_columns)

        record_out = OrderedDict()
        for prog_var in prog_comp_vars:
            try:
                record_out[prog_var] = data_out[prog_var]
            except KeyError:
                record_out[prog_var] = None

        query = {'sessionId': data_out['sessionId']}
        mongo_collection.replace_one(query, record_out, upsert=True)

        logger.info("Finished writing record")

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise


def _grf_prog_comp(data, user_mass, agg_vars, prog_comp_columns):
        grf_bins = numpy.array([0, 1.40505589, 1.68606707, 1.96707825, 2.24808943, 2.52910061,
                                2.81011179, 3.09112296, 3.37213414, 3.65314532, 100])
        grf_labels = range(10)
        agg_vars = ['total', 'constructive', 'destructive', 'totalAccel', 'msElapsed']
        prog_comp = data.groupby(pandas.cut(data["totalNormMax"], grf_bins, labels=grf_labels))
        prog_comp_grf = pandas.DataFrame()
        prog_comp_grf['min'] = numpy.array(grf_bins[0:10]) * user_mass
        prog_comp_grf['max'] = None
        prog_comp_grf['binNumber'] = grf_labels
        for pc_var in agg_vars:
            prog_comp_grf[pc_var] = prog_comp[pc_var].sum()
        prog_comp_grf['percOptimal'] = prog_comp_grf['constructive'] / prog_comp_grf['total'] * 100
        prog_comp_grf['percIrregular'] = prog_comp_grf['destructive'] / prog_comp_grf['total'] * 100
        prog_comp_grf.columns = prog_comp_columns
        prog_comp_grf = prog_comp_grf.where((pandas.notnull(prog_comp_grf)), None)
        grf = prog_comp_grf.to_dict(orient='records')
        grf_sorted = []
        for data_bin in grf:
            if data_bin['totalGRF'] is None:
                continue
            sorted_bin = OrderedDict()
            for var in prog_comp_columns:
                if var=='binNumber':
                    sorted_bin[var] = int(data_bin[var])
                else:
                    sorted_bin[var] = data_bin[var]
            grf_sorted.append(sorted_bin)
        return grf_sorted


def _accel_prog_comp(data, agg_vars, prog_comp_columns):
        accel_bins = numpy.array([0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0, 105.0, 200.0, 325.0, 10000])
        accel_labels = range(10)
        prog_comp = data.groupby(pandas.cut(data["totalAccelMax"], accel_bins, labels=accel_labels))
        prog_comp_accel = pandas.DataFrame()
        prog_comp_accel['min'] = numpy.array(accel_bins[0:10])
        prog_comp_accel['max'] = None
        prog_comp_accel['binNumber'] = accel_labels
        for pc_var in agg_vars:
            prog_comp_accel[pc_var] = prog_comp[pc_var].sum()
        prog_comp_accel['percOptimal'] = prog_comp_accel['constructive'] / prog_comp_accel['total'] * 100
        prog_comp_accel['percIrregular'] = prog_comp_accel['destructive'] / prog_comp_accel['total'] * 100
        prog_comp_accel.columns = prog_comp_columns
        prog_comp_accel = prog_comp_accel.where((pandas.notnull(prog_comp_accel)), None)
        accel = prog_comp_accel.to_dict(orient='records')
        accel_sorted = []
        for data_bin in accel:
            if data_bin['totalGRF'] is None:
                continue
            sorted_bin = OrderedDict()
            for var in prog_comp_columns:
                if var=='binNumber':
                    sorted_bin[var] = int(data_bin[var])
                else:
                    sorted_bin[var] = data_bin[var]
            accel_sorted.append(sorted_bin)
        return accel_sorted


def _plane_prog_comp(data, agg_vars, prog_comp_columns):
        plane_inds = numpy.arange(16)
        plane_bins = numpy.arange(5)
        pc = data.groupby(by='plane')
        pc_plane = pandas.DataFrame()
        pc_plane['min'] = None
        pc_plane['max'] = None
        pc_plane['binNumber'] = plane_inds
        for pc_var in agg_vars:
            pc_plane[pc_var] = pc[pc_var].sum()
        pc_plane['percOptimal'] = pc_plane['constructive'] / pc_plane['total'] * 100
        pc_plane['percIrregular'] = pc_plane['destructive'] / pc_plane['total'] * 100
        pc_plane.columns = prog_comp_columns
        stat_bins = [0]
        rot_bins = [1, 5, 6, 7, 11, 12, 13, 15]
        lat_bins = [2, 5, 8, 9, 11, 12, 14, 15]
        vert_bins = [3, 6, 8, 10, 11, 13, 14, 15]
        horz_bins = [4, 7, 9, 10, 12, 13, 14, 15]
        stat = pc_plane[numpy.array([i in stat_bins for i in pc_plane.binNumber])]
        rot = pc_plane[numpy.array([i in rot_bins for i in pc_plane.binNumber])]
        lat = pc_plane[numpy.array([i in lat_bins for i in pc_plane.binNumber])]
        vert = pc_plane[numpy.array([i in vert_bins for i in pc_plane.binNumber])]
        horz = pc_plane[numpy.array([i in horz_bins for i in pc_plane.binNumber])]
        prog_comp = pandas.DataFrame()
        prog_comp = prog_comp.append(stat.sum(), ignore_index=True)
        prog_comp = prog_comp.append(rot.sum(), ignore_index=True)
        prog_comp = prog_comp.append(lat.sum(), ignore_index=True)
        prog_comp = prog_comp.append(vert.sum(), ignore_index=True)
        prog_comp = prog_comp.append(horz.sum(), ignore_index=True)
        prog_comp['percOptimal'] = prog_comp['optimalGRF'] / prog_comp['totalGRF'] * 100
        prog_comp['percIrregular'] = prog_comp['irregularGRF'] / prog_comp['totalGRF'] * 100
        prog_comp['binNumber'] = plane_bins

        plane = prog_comp.to_dict(orient='records')
        plane_sorted = []
        for data_bin in plane:
            if numpy.isnan(data_bin['percOptimal']):
                continue
            sorted_bin = OrderedDict()
            for var in prog_comp_columns:
                if numpy.isnan(data_bin[var]):
                    sorted_bin[var] = None
                elif var=='binNumber':
                    sorted_bin[var] = int(data_bin[var])
                else:
                    sorted_bin[var] = data_bin[var]
            plane_sorted.append(sorted_bin)
        return plane_sorted


def _stance_prog_comp(data, agg_vars, prog_comp_columns):
        stance_bins = numpy.arange(6)
        pc = data.groupby(by='stance')
        pc_stance = pandas.DataFrame()
        pc_stance['min'] = None
        pc_stance['max'] = None
        pc_stance['binNumber'] = stance_bins
        for pc_var in agg_vars:
            pc_stance[pc_var] = pc[pc_var].sum()
        pc_stance['percOptimal'] = pc_stance['constructive'] / pc_stance['total'] * 100
        pc_stance['percIrregular'] = pc_stance['destructive'] / pc_stance['total'] * 100
        pc_stance.columns = prog_comp_columns

        stance = pc_stance.to_dict(orient='records')
        stance_sorted = []
        for data_bin in stance:
            if numpy.isnan(data_bin['percOptimal']):
                continue
            sorted_bin = OrderedDict()
            for var in prog_comp_columns:
                if numpy.isnan(data_bin[var]):
                    sorted_bin[var] = None
                elif var=='binNumber':
                    sorted_bin[var] = int(data_bin[var])
                else:
                    sorted_bin[var] = data_bin[var]
            stance_sorted.append(sorted_bin)
        return stance_sorted



if __name__ == '__main__':
    import time
    start = time.time()
    input_data = OrderedDict()
    input_data['TeamId'] = 'test_team'
    input_data['TrainingGroupId'] = ['test_tg1', 'test_tg2']
    input_data['UserId'] = 'test_user'
    input_data['SessionEventId'] = 'test_session'
    input_data['SessionType'] = '1'
    input_data['UserMass'] = 133
    input_data['EventDate'] = '2017-03-20'

    os.environ['ENVIRONMENT'] = 'Dev'
    os.environ['MONGO_HOST_SESSION'] = 'ec2-34-210-169-8.us-west-2.compute.amazonaws.com:27017'
    os.environ['MONGO_USER_SESSION'] = 'statsUser'
    os.environ['MONGO_PASSWORD_SESSION'] = 'BioMx211'
    os.environ['MONGO_DATABASE_SESSION'] = 'movementStats'
    os.environ['MONGO_COLLECTION_PROGCOMP'] = 'progCompStats_test2'
    os.environ['MONGO_REPLICASET_SESSION'] = '---'
    file_name = 'C:\\Users\\Administrator\\Desktop\\python_aggregation\\605a9a17-24bf-4fdc-b539-02adbb28a628'
    prog_comp = script_handler(file_name, input_data)
    print(time.time() - start)
