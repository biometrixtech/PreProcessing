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
        mongo_client = MongoClient(config.MONGO_HOST, replicaset=config.MONGO_REPLICASET, ssl=True)

        mongo_database = mongo_client[config.MONGO_DATABASE]

        # Authenticate
        mongo_database.authenticate(config.MONGO_USER, config.MONGO_PASSWORD,
                                    mechanism='SCRAM-SHA-1')

        mongo_collection = mongo_database[config.MONGO_COLLECTION]

        tmp_filename = '/tmp/readfile'
        copyfile(os.path.join(working_directory, 'scoring'), tmp_filename)
        logger.info("Copied data file to local FS")
        data = pandas.read_csv(tmp_filename, usecols=['obs_index',
                                                      'epoch_time',
                                                      'ms_elapsed',
                                                      'phase_lf',
                                                      'phase_rf',
                                                      'grf',
                                                      'grf_lf',
                                                      'grf_rf',
                                                      'const_grf',
                                                      'dest_grf',
                                                      'destr_multiplier',
                                                      'total_accel',
                                                      'stance',
                                                      'plane'])
        os.remove(tmp_filename)
        logger.info("Removed temporary file")

        # rename columns to match mongo
        data.columns = ['obsIndex', 'epochTime', 'msElapsed',
                        'phaseLF', 'phaseRF',
                        'total', 'LF', 'RF', 'constructive', 'destructive', 'destrMultiplier',
                        'totalAccel',
                        'stance', 'plane']
        data_out = {}
        data['msElapsed'] = data['msElapsed'].astype(float)
        data_out['teamId'] = input_data.get('TeamId', None)
        data_out['trainingGroups'] = input_data.get('TrainingGroupIds', None)
        data_out['userId'] = input_data.get('UserId', None)
        data_out['sessionId'] = input_data.get('SessionId', None)
        data_out['sessionType'] = '1'
        # data_out['sessionType'] = input_data.get('SessionType', None)
        # if data_out['sessionType'] is not None:
            # data_out['sessionType'] = str(data_out['sessionType'])
        data_out['userMass'] = float(input_data.get('UserMassKg', None))
        data_out['eventDate'] = input_data.get('EventDate', None)

        # Compute the max grf and totalAccel for each .5s window for use in program comp
        data['totalAccelUnscaled'] = data['totalAccel'] / data['msElapsed'] * 100000
        data['half_sec'] = pandas.DatetimeIndex(pandas.to_datetime(data.epochTime, unit='ms')).round('500ms')
        f = OrderedDict({'total': [numpy.max]})
        f['totalAccelUnscaled'] = [numpy.max]
        
        max_half_sec = data.groupby('half_sec').agg(f)
        max_half_sec.columns = ['totalNormMax', 'totalAccelMax']
        data = data.join(max_half_sec, on='half_sec')
        data.loc[:, 'totalNormMax'] = data.totalNormMax / data_out['userMass'] * 1000000 * 9.803

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
        total_ind = numpy.array([numpy.isfinite(k) for k in data['constructive']])
        data['total'] = data['total'].fillna(value=numpy.nan) * total_ind
        lf_ind = numpy.array([k in [0, 1, 4, 6] for k in data['phaseLF']])
        rf_ind = numpy.array([k in [0, 2, 5, 7] for k in data['phaseRF']])
        lf_ground = lf_ind * ~rf_ind  # only lf in ground
        rf_ground = ~lf_ind * rf_ind  # only rf in ground
        data['lf_only_grf'] = data['total'].fillna(value=numpy.nan) * lf_ground
        data['rf_only_grf'] = data['total'].fillna(value=numpy.nan) * rf_ground

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
        prog_comp = data.groupby(pandas.cut(data["totalNormMax"], grf_bins, labels=grf_labels))
        prog_comp_grf = pandas.DataFrame()
        prog_comp_grf['min'] = numpy.array(grf_bins[0:10]) * user_mass
        prog_comp_grf['max'] = None
        prog_comp_grf['binNumber'] = grf_labels
        for pc_var in agg_vars:
            prog_comp_grf[pc_var] = prog_comp[pc_var].sum()
        percOptimal = prog_comp_grf['constructive'] / prog_comp_grf['total'] * 100
        # adding grf distribution to percOptimal calculation
        lf_only_grf = prog_comp['lf_only_grf'].sum()
        rf_only_grf = prog_comp['rf_only_grf'].sum()
        perc_distr = numpy.abs(lf_only_grf - rf_only_grf) / (lf_only_grf + rf_only_grf) * 100
        perc_distr[numpy.isnan(perc_distr)] = 0.
        prog_comp_grf['percOptimal'] = (2. * percOptimal + (1. - perc_distr/100.)**2 * 100.) / 3.
        prog_comp_grf['percIrregular'] = 100. - prog_comp_grf['percOptimal']
        prog_comp_grf.columns = prog_comp_columns
        # use new definition of percOptimal in optimal and irregular GRF
        prog_comp_grf['optimalGRF'] = prog_comp_grf['percOptimal'] * prog_comp_grf['totalGRF'] / 100
        prog_comp_grf['irregularGRF'] = prog_comp_grf['percIrregular'] * prog_comp_grf['totalGRF'] / 100
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
        percOptimal = prog_comp_accel['constructive'] / prog_comp_accel['total'] * 100
        # adding grf distribution to percOptimal calculation
        lf_only_grf = prog_comp['lf_only_grf'].sum()
        rf_only_grf = prog_comp['rf_only_grf'].sum()
        perc_distr = numpy.abs(lf_only_grf - rf_only_grf) / (lf_only_grf + rf_only_grf) * 100
        perc_distr[numpy.isnan(perc_distr)] = 0.
        prog_comp_accel['percOptimal'] = (2. * percOptimal + (1. - perc_distr/100.)**2 * 100.) / 3.
        prog_comp_accel['percIrregular'] = 100. - prog_comp_accel['percOptimal']
        prog_comp_accel.columns = prog_comp_columns

        # use new definition of percOptimal in optimal and irregular GRF
        prog_comp_accel['optimalGRF'] = prog_comp_accel['percOptimal'] * prog_comp_accel['totalGRF'] / 100
        prog_comp_accel['irregularGRF'] = prog_comp_accel['percIrregular'] * prog_comp_accel['totalGRF'] / 100
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
        percOptimal = pc_plane['constructive'] / pc_plane['total'] * 100

        # update percOptimal with inclusion of grf distribution
        lf_only_grf = pc['lf_only_grf'].sum()
        rf_only_grf = pc['rf_only_grf'].sum()
        perc_distr = numpy.abs(lf_only_grf - rf_only_grf) / (lf_only_grf + rf_only_grf) * 100.
        perc_distr[numpy.isnan(perc_distr)] = 0.
        pc_plane['percOptimal'] = (2. * percOptimal + (1. - perc_distr/100.)**2 * 100.) / 3.
        pc_plane['percIrregular'] = 100. - pc_plane['percOptimal']
        pc_plane.columns = prog_comp_columns

        # update optimal and irregular GRF to use updated definition of percOptimal
        pc_plane['optimalGRF'] = pc_plane['percOptimal'] * pc_plane['totalGRF'] / 100
        pc_plane['irregularGRF'] = pc_plane['percIrregular'] * pc_plane['totalGRF'] / 100
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
        stance_bins = numpy.arange(10)
        pc = data.groupby(by='stance')
        pc_stance = pandas.DataFrame()
        pc_stance['min'] = None
        pc_stance['max'] = None
        pc_stance['binNumber'] = stance_bins
        for pc_var in agg_vars:
            pc_stance[pc_var] = pc[pc_var].sum()
        percOptimal = pc_stance['constructive'] / pc_stance['total'] * 100

        # update percOptimal with inclusion of grf distribution
        lf_only_grf = pc['lf_only_grf'].sum()
        rf_only_grf = pc['rf_only_grf'].sum()
        perc_distr = numpy.abs(lf_only_grf - rf_only_grf) / (lf_only_grf + rf_only_grf) * 100
        perc_distr[numpy.isnan(perc_distr)] = 0.
        pc_stance['percOptimal'] = (2. * percOptimal + (1. - perc_distr/100.)**2 * 100.) / 3.
        pc_stance['percIrregular'] = 100. - pc_stance['percOptimal']
        pc_stance.columns = prog_comp_columns

        # update optimal and irregular GRF to use updated definition of percOptimal
        pc_stance['optimalGRF'] = pc_stance['percOptimal'] * pc_stance['totalGRF'] / 100
        pc_stance['irregularGRF'] = pc_stance['percIrregular'] * pc_stance['totalGRF'] / 100

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
