# -*- coding: utf-8 -*-
"""
Created on Fri Oct 21 20:22:15 2016

@author: court
"""

import numpy as np
import pandas as pd
import psycopg2
import sys
import boto3
import cStringIO

import dataObject as do
import phaseDetection as phase
import movementAttrib as matrib
import prePreProcessing as ppp
import coordinateFrameTransformation as coord
import createTables as ct
from errors import ErrorId, ErrorMessageTraining, RPushDataTraining


"""
Training system execution script: used when coaches record exercises to train 
the system to recognize them in athlete workouts. Returns data for completed
exercise, as well as characteristic binaries to be reported back to the coaches
as tags for the exercise's type.

"""


class _sort_variables(object):
    
    """
    Creates objects for sorting from variable name and value.
    
    Args:
        name - str
        number - ndarray (1D)
        
    Return:
        object with name and value attributes, readied for sorting
    
    """
    def __init__(self, name, number):
        """
        Creates name and number attributes
        """
        self.name = name
        self.number = number
 
    def __repr__(self):
        """
        Defines representation of attributes when called
        """
        return '{}: {}'.format(self.name,self.number)
                                 
    def __cmp__(self, other):
        """
        Compares values of consecutive objects, prepares for sorting
        """
        if hasattr(other, 'number'):
            return self.number.tolist().__gt__(other.number.tolist())
            
            
class _bin_return(object):
    """
    Saves boolean values to be returned as True as attribute '.bins'
    """
    def __init__(self,bin_vals):
        self.bins = bin_vals


def dynamicName(sdata):
    names = sdata.dtype.names[1:]
    width = len(names)+1
    data = sdata.view((float, width))
    return data


class TrainingExecution(object): #Abstract setUp class
    def __init__(self, sensor_data, file_name):
        
        ###Connect to the database
        try:
            conn = psycopg2.connect("""dbname='biometrix' user='paul' 
            host='ec2-52-36-42-125.us-west-2.compute.amazonaws.com' 
            password='063084cb3b65802dbe01030756e1edf1f2d985ba'""")
        except:
            self.result = 'Fail! Unable to connect to database'
            sys.exit()
        
        cur = conn.cursor()
        
        #Query to read user_id and exercise_id linked to the given data_filename
        quer_read_ids = """select user_id, exercise_id from training_events
                    where sensor_data_filename = (%s);"""
                    
        
        quer_read_offsets = """select hip_n_transform, hip_bf_transform,
                    lf_n_transform, lf_bf_transform,
                    rf_n_transform, lf_bf_transform from
                    session_anatomical_calibration_events where
                    id = (select session_anatomical_calibration_event_id
                    from training_events where sensor_data_filename = (%s));"""
    
        quer_success = """update training_events set
                    rotational = (%s),
                    vertical = (%s),
                    horizontal = (%s),
                    stationary = (%s),
                    lateral = (%s),
                    single_leg = (%s),
                    double_leg = (%s),
                    feet_eliminated = (%s),
                    total_acceleration = (%s)
                    where sensor_data_filename = (%s);"""
        
        #Read the user_id, exercise_id
        cur.execute(quer_read_ids, (file_name,))
        ids_read = cur.fetchall()[0]
        user_id = ids_read[0]
        exercise_id = ids_read[1]
        
        
        #Read transformation offset values
        cur.execute(quer_read_offsets, (file_name,))
        offsets_read = cur.fetchall()[0]
        hip_n_transform = np.array(offsets_read[0]).reshape(-1,1)
        hip_bf_transform = np.array(offsets_read[1]).reshape(-1,1)
        lf_n_transform = np.array(offsets_read[2]).reshape(-1,1)
        lf_bf_transform = np.array(offsets_read[3]).reshape(-1,1)
        rf_n_transform = np.array(offsets_read[4]).reshape(-1,1)
        rf_bf_transform = np.array(offsets_read[5]).reshape(-1,1)
   
        #Connect to AWS S3 container
        S3 = boto3.resource('s3')
        
        #define container to write to
        cont_write = 'biometrix-trainingprocessedcontainer' 
        out_file = "processed_"+file_name

        # read data
        sdata = np.genfromtxt(sensor_data, dtype=float, delimiter=',',
                              names=True) # create ndarray from path

        columns = sdata.dtype.names        
        data = dynamicName(sdata)
        self.data = do.RawFrame(data, columns)
        self.data.user_id = np.array([user_id]*len(self.data.LaX)).reshape(-1,1)
        self.data.exercise_id = np.array([exercise_id]*len(self.data.LaX)).\
                                reshape(-1,1)
                
        
        # PRE-PRE-PROCESSING                
        epoch_time = sdata['epoch_time']
        corrupt_magn = sdata['corrupt_magn']
            
        # check for missing values for each of acceleration and quaternion values
        columns = ['LaX','LaY','LaZ','LqX','LqY','LqZ','HaX',
                   'HaY','HaZ','HqX','HqY','HqZ','RaX','RaY','RaZ',
                   'RqX','RqY','RqZ']
    
        for var in columns:
            out, m_ind = ppp.handling_missing_data(epoch_time,
                                                   sdata[var].reshape(-1,1),
                                                    corrupt_magn.reshape(-1,1)) 
            sdata[var] = out.reshape(-1,)        
            if (m_ind == ErrorId.corrupt_magn.value 
                or m_ind == ErrorId.missing.value):
                sdata = sdata
                break
        
        # re-assigning the values after data has passed through 
        # handling_missing_data function
        for i in columns:
            setattr(self.data, i, sdata[i].reshape(-1,1))
             
        # determine the real quartenion
        # Left foot
        lq_xyz = np.hstack([self.data.LqX, self.data.LqY, self.data.LqZ])
        lq_wxyz = ppp.calc_quaternions(lq_xyz)
        self.data.LqW = lq_wxyz[:,0].reshape(-1,1)
        self.data.LqX = lq_wxyz[:,1].reshape(-1,1)
        self.data.LqY = lq_wxyz[:,2].reshape(-1,1)
        self.data.LqZ = lq_wxyz[:,3].reshape(-1,1)
        # Hip
        hq_xyz = np.hstack([self.data.HqX, self.data.HqY, self.data.HqZ])
        hq_wxyz = ppp.calc_quaternions(hq_xyz)
        self.data.HqW = hq_wxyz[:,0].reshape(-1,1)
        self.data.HqX = hq_wxyz[:,1].reshape(-1,1)
        self.data.HqY = hq_wxyz[:,2].reshape(-1,1)
        self.data.HqZ = hq_wxyz[:,3].reshape(-1,1)
        # Right foot
        rq_xyz = np.hstack([self.data.RqX, self.data.RqY, self.data.RqZ])
        rq_wxyz = ppp.calc_quaternions(rq_xyz)
        self.data.RqW = rq_wxyz[:,0].reshape(-1,1)
        self.data.RqX = rq_wxyz[:,1].reshape(-1,1)
        self.data.RqY = rq_wxyz[:,2].reshape(-1,1)
        self.data.RqZ = rq_wxyz[:,3].reshape(-1,1)

        # convert epoch time to date time and determine milliseconds elapsed
        self.data.time_stamp, self.data.ms_elapsed \
            = ppp.convert_epochtime_datetime_mselapsed(self.data.epoch_time)
            
    
        # COORDINATE FRAME TRANSFORMATION
            
        d, d_neutral= coord.transform_data(self.data, hip_bf_transform,
                                           lf_bf_transform,rf_bf_transform,
                                           lf_n_transform,rf_n_transform,
                                           hip_n_transform)
        d_neutral = np.array(d_neutral)
        #Left foot body transformed data        
        self.data.LaX = d[:,1].reshape(-1,1)
        self.data.LaY = d[:,2].reshape(-1,1)  
        self.data.LaZ = d[:,3].reshape(-1,1)  
        self.data.LeX = d[:,4].reshape(-1,1)    
        self.data.LeY = d[:,5].reshape(-1,1)  
        self.data.LeZ = d[:,6].reshape(-1,1)  
        self.data.LqW = d[:,7].reshape(-1,1)    
        self.data.LqX = d[:,8].reshape(-1,1)  
        self.data.LqY = d[:,9].reshape(-1,1)  
        self.data.LqZ = d[:,10].reshape(-1,1)  
        #Hip body transformed data
        self.data.HaX = d[:,11].reshape(-1,1)    
        self.data.HaY = d[:,12].reshape(-1,1)  
        self.data.HaZ = d[:,13].reshape(-1,1)  
        self.data.HeX = d[:,14].reshape(-1,1)    
        self.data.HeY = d[:,15].reshape(-1,1)  
        self.data.HeZ = d[:,16].reshape(-1,1)  
        self.data.HqW = d[:,17].reshape(-1,1)    
        self.data.HqX = d[:,18].reshape(-1,1)  
        self.data.HqY = d[:,19].reshape(-1,1)  
        self.data.HqZ = d[:,20].reshape(-1,1)  
        #Right foot body transformed data
        self.data.RaX = d[:,21].reshape(-1,1)    
        self.data.RaY = d[:,22].reshape(-1,1)  
        self.data.RaZ = d[:,23].reshape(-1,1)  
        self.data.ReX = d[:,24].reshape(-1,1)    
        self.data.ReY = d[:,25].reshape(-1,1)  
        self.data.ReZ = d[:,26].reshape(-1,1)  
        self.data.RqW = d[:,27].reshape(-1,1)    
        self.data.RqX = d[:,28].reshape(-1,1)  
        self.data.RqY = d[:,29].reshape(-1,1)  
        self.data.RqZ = d[:,30].reshape(-1,1)
        
        # if recording period too short, throw error
        if len(self.data.HaX)<2000:
            msg = "Exercise duration too short"
            r_push_data = {"action":"run_ression_calibration"}
            user_id = user_id
            self.result = "Fail!"
            
            ######rPush INSERT GOES HERE
            
            self.data.failure_type=1
            
        elif m_ind!=0:
            msg = ErrorMessageTraining(m_ind).error_message
            r_push_data = RPushDataTraining(m_ind).value
            user_id = user_id
            
            self.result = "Fail"
            
            #rPush INSERT GOES HERE
            
        else:
            # SAMPLING RATE
            hz = 250       
           
            # PHASE DETECTION
            self.data.phase_l, self.data.phase_r \
                = phase.combine_phase(self.data.LaZ, self.data.RaZ, hz)
        
            # calculate instantaneous totalAccel, plane and stance binaries
            hip_acc = np.hstack([self.data.HaX, self.data.HaY, self.data.HaZ])
            hip_eul = np.hstack([self.data.HeX, self.data.HeY, self.data.HeZ])
            self.data.lat,self.data.vert,self.data.horz,self.data.rot,\
                self.data.lat_binary,self.data.vert_binary,\
                self.data.horz_binary,self.data.rot_binary,\
                self.data.stationary_binary,self.data.total_accel\
                = matrib.plane_analysis(hip_acc,hip_eul,hz)
            self.data.standing,self.data.not_standing \
                = matrib.standing_or_not(hip_eul,hz)
            self.data.double_leg,self.data.single_leg,\
                self.data.feet_eliminated = matrib.double_or_single_leg(
                self.data.phase_l,self.data.phase_r,self.data.standing,hz)
          
            # process instantaneous accel values to give meaning for whole 
                # activity
            _tot_acc_without_nans = np.nan_to_num(self.data.total_accel)
            self.data.max_accel = np.percentile(_tot_acc_without_nans,95)
            
            # find percentage of activity spent in each plane of motion
            _perc_lat = sum(self.data.lat_binary)/len(hip_acc)
            _perc_vert = sum(self.data.vert_binary)/len(hip_acc)
            _perc_horz = sum(self.data.horz_binary)/len(hip_acc)
            _perc_rot = sum(self.data.rot_binary)/len(hip_acc)
            _perc_stat = sum(self.data.stationary_binary)/len(hip_acc)
            
            _perc_doub = sum(self.data.double_leg)/len(hip_eul)
            _perc_sing = sum(self.data.single_leg)/len(hip_eul)
            _perc_ft_elim = sum(self.data.feet_eliminated)/len(hip_eul)
            
            # sort the binaries based on percentages (greatest to least)
            _plane_perc = [_sort_variables('lat',_perc_lat),
                           _sort_variables('vert',_perc_vert),
                           _sort_variables('horz',_perc_horz),
                           _sort_variables('rot',_perc_rot),
                           _sort_variables('stat',_perc_stat)]
            _stance_perc= [_sort_variables('doub',_perc_doub),
                           _sort_variables('sing',_perc_sing),
                           _sort_variables('ft_elim',_perc_ft_elim)]
            _sorted_plane_perc = sorted(_plane_perc, key=lambda x: x.number,
                                        reverse=True)
            _sorted_stance_perc= sorted(_stance_perc, key=lambda x: x.number,
                                        reverse=True)

            # find differences between ordered percentages
            plane_diff_1_to_2 = _sorted_plane_perc[0].number \
                                - _sorted_plane_perc[1].number
            plane_diff_2_to_3 = _sorted_plane_perc[1].number \
                                - _sorted_plane_perc[2].number
            plane_diff_3_to_4 = _sorted_plane_perc[2].number \
                                - _sorted_plane_perc[3].number
            stance_diff_1_to_2 = _sorted_stance_perc[0].number \
                                - _sorted_stance_perc[1].number
            stance_diff_2_to_3 = _sorted_stance_perc[1].number \
                                - _sorted_stance_perc[2].number
            
            # decide how many planes of motion and stances to return as True
            if plane_diff_1_to_2 < 0.1 and plane_diff_2_to_3 > 0.20:
                
                _plane_bins = _bin_return([_sorted_plane_perc[0].name,
                                         _sorted_plane_perc[1].name])
                                         
            elif plane_diff_1_to_2 < 0.1 and plane_diff_2_to_3 < 0.1 \
                and plane_diff_3_to_4 > 0.1:
                
                _plane_bins = _bin_return([_sorted_plane_perc[0].name,
                                         _sorted_plane_perc[1].name,
                                         _sorted_plane_perc[2].name])
                                         
            else:
                _plane_bins = _bin_return([_sorted_plane_perc[0].name])
                
            if stance_diff_1_to_2 < 0.1 and stance_diff_2_to_3 > 0.1:
                
                _stance_bins = _bin_return([_sorted_stance_perc[0].name,
                                          _sorted_stance_perc[1].name])
            else:
                
                _stance_bins = _bin_return([_sorted_stance_perc[0].name])
                
            # give appropriate booleans value if they met criteria of 
                # percentage of total activity with respect to the others
            if 'horz' in _plane_bins.bins:
                self.data.horizontal_exerc = True
            else:
                self.data.horizontal_exerc = False
            if 'lat' in _plane_bins.bins:
                self.data.lateral_exerc = True
            else:
                self.data.lateral_exerc = False
            if 'rot' in _plane_bins.bins:
                self.data.rotational_exerc = True
            else:
                self.data.rotational_exerc = False
            if 'vert' in _plane_bins.bins:
                self.data.vertical_exerc = True
            else:
                self.data.vertical_exerc = False
            if 'stat' in _plane_bins.bins:
                self.data.stationary_exerc = True
            else:
                self.data.stationary_exerc = False
            if 'doub' in _stance_bins.bins:
                self.data.double_leg_exerc = True
            else:
                self.data.double_leg_exerc = False
            if 'sing' in _stance_bins.bins:
                self.data.single_leg_exerc = True
            else:
                self.data.single_leg_exerc = False
            if 'ft_elim' in _stance_bins.bins:
                self.data.feet_eliminated_exerc = True
            else:
                self.data.feet_eliminated_exerc = False
        
            #Write relevant calculated values to training_events table
            cur.execute(quer_success, (self.data.rotational_exerc,
                                       self.data.vertical_exerc,
                                       self.data.horizontal_exerc,
                                       self.data.stationary_exerc,
                                       self.data.lateral_exerc,
                                       self.data.single_leg_exerc,
                                       self.data.double_leg_exerc,
                                       self.data.feet_eliminated_exerc,
                                       self.data.max_accel,
                                       file_name
                                       ))
            conn.commit()
            conn.close()
            
            #rPush
            msg = ErrorMessageTraining(m_ind).error_message
            r_push_data = RPushDataTraining(m_ind).value
            user_id = user_id
            ###rPUSH INSERT GOES HERE
            
            self.data.failure_type=0
                  
            # Save processed data to S3 container
            training_data = ct.create_training_data(len(self.data.LaX),
                                                    self.data)
            training_data_pd = pd.DataFrame(training_data)
            f = cStringIO.StringIO()
            training_data_pd.to_csv(f, index = False)
            f.seek(0)
            S3.Bucket(cont_write).put_object(Key=out_file, Body=f)

            self.result  = "Success!"

        
if __name__ == "__main__":
    
    import time
#    import os
#    import re
#    import sys
    start_time = time.time()
    f = 'trainingset_sngllegsqt.csv'
    training_var = TrainingExecution(f, f)
#    file_paths = os.listdir("data")
##    print file_paths
#    for f in file_paths:
#        
#        f = "data\\"+f
##        print f
#        movement_var = training_execution(f)
    
    #### THESE ARE THE VALUES THAT WE NEED TO SAVE FOR THE APP####
    print ''
    print 'horizontal', training_var.data.horizontal_exerc 
    print 'lateral', training_var.data.lateral_exerc 
    print 'rotational', training_var.data.rotational_exerc 
    print 'vertical', training_var.data.vertical_exerc
    print 'stationary', training_var.data.stationary_exerc
    print 'double_leg', training_var.data.double_leg_exerc
    print 'single_leg', training_var.data.single_leg_exerc
    print 'feet_eliminated', training_var.data.feet_eliminated_exerc    
    print 'max accel', training_var.data.max_accel
    print ''
    print "My program took", time.time() - start_time, "to run" 