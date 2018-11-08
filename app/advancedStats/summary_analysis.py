from pymongo import MongoClient
from bson.objectid import ObjectId
import pandas
from datetime import datetime
from models.variable import CategorizationVariable
from models.unit_block import UnitBlock
from pymongo import ASCENDING
from config import load_parameters, get_mongo_collection


def get_unit_blocks(user, date):

    load_parameters([
        'MONGO_HOST',
        'MONGO_USER',
        'MONGO_PASSWORD',
        'MONGO_DATABASE',
        'MONGO_REPLICASET',
        'MONGO_COLLECTION_ACTIVEBLOCKS',
    ], 'mongo')

    col = get_mongo_collection('ACTIVEBLOCKS')

    # unit_blocks = list(col.find({'userId': {'$eq': user},'eventDate':date},{'unitBlocks':1,'_id':0}))
    unit_blocks = list(col.find({'userId': {'$eq': user}, 'eventDate': date},
                                {'unitBlocks': 1, '_id': 1, 'timeStart': 1, 'timeEnd': 1}).sort('unitBlocks.timeStart',
                                                                                                direction=ASCENDING))
    return unit_blocks


def query_mongo_ab(collection, user, date, output_path):
    client = MongoClient('34.210.169.8',username='statsAdmin',password='ButThisGoes211',authSource='admin', authMechanism='SCRAM-SHA-1')
    db = client.get_database('movementStats')
    col = db.get_collection(collection)
    #users = list(col.distinct("userId"))
    #for u in users:
    cnt = 0
    bcnt=0
    curDate = ''
    docs = list(col.find({'userId': {'$eq': user},                               
                                'eventDate': {'$eq': date}}))
       
    if(len(docs)>0):
        sessionTimeStart = docs[0].get('timeStart')

        try:
            sessionTimeStart_object = datetime.strptime(sessionTimeStart, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            sessionTimeStart_object = datetime.strptime(sessionTimeStart, '%Y-%m-%d %H:%M:%S')

        for b in docs:


            objId =  str(b.get('_id'))
            if(curDate!=b.get('eventDate')):
                curDate = b.get('eventDate')
                cnt = 0
                bcnt=0
                sessionTimeStart = b.get('timeStart')
                try:
                    sessionTimeStart_object = datetime.strptime(sessionTimeStart, '%Y-%m-%d %H:%M:%S.%f')
                except ValueError:
                    sessionTimeStart_object = datetime.strptime(sessionTimeStart, '%Y-%m-%d %H:%M:%S')
            eventDate = b.get('eventDate')
           
            bcnt=bcnt+1 
           
            timeStart = b.get('timeStart')
            timeEnd = b.get('timeEnd')
            try:
                timeStart_object = datetime.strptime(timeStart, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                timeStart_object = datetime.strptime(timeStart, '%Y-%m-%d %H:%M:%S')
            try:
                timeEnd_object = datetime.strptime(timeEnd, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                timeEnd_object = datetime.strptime(timeEnd, '%Y-%m-%d %H:%M:%S')
            
            timeStart_string = timeStart_object.time().strftime("%H:%M:%S")
            timeEnd_string = timeEnd_object.time().strftime("%H:%M:%S")
            cumulative_start_time = (timeStart_object- sessionTimeStart_object).seconds
            cumulative_end_time = (timeEnd_object- sessionTimeStart_object).seconds
            contactDurationLF = b.get('contactDurationLF')
            contactDurationRF = b.get('contactDurationRF')
            peakGrfLF = b.get('peakGrfLF')
            peakGrfRF = b.get('peakGrfRF')
            contactDurationPercDiffLFRF = None
            if(contactDurationLF!=None and contactDurationRF != None):
                contactDurationPercDiffLFRF = abs(contactDurationLF-contactDurationRF)/max(contactDurationLF,contactDurationRF)
            peakGRFPercDiffLFRF = None
            if(peakGrfLF!=None and peakGrfRF != None):
                peakGRFPercDiffLFRF = abs(peakGrfLF-peakGrfRF)/max(peakGrfLF,peakGrfRF)
                        
        
            ab = pandas.DataFrame(
                {
                    'userId':[user],
                    'eventDate':[eventDate],
                    'activeBlock':[objId],
                    'abNum':[bcnt],
                    'timeStart': [timeStart_string],
                    'timeEnd':[timeEnd_string],
                    'cumulative_end_time':[cumulative_end_time],
                    'cumulative_start_time':[cumulative_start_time],
                    'duration':[b.get('duration')],
                    'load':[b.get('totalAccelAvg')],
                    'contactDurationLF5':[b.get('contactDurationLF5')],
                    'contactDurationLF':[contactDurationLF],
                    'contactDurationLF95':[b.get('contactDurationLF95')],
                    'contactDurationLFStd':[b.get('contactDurationLFStd')],
                    'contactDurationRF5':[b.get('contactDurationRF5')],
                    'contactDurationRF':[contactDurationRF],
                    'contactDurationRF95':[b.get('contactDurationRF95')],
                    'contactDurationRFStd':[b.get('contactDurationRFStd')],
                    'percDiff1':[contactDurationPercDiffLFRF],
                    'peakGrfLF5':[b.get('peakGrfLF5')],
                    'peakGrfLF':[peakGrfLF],
                    'peakGrfLF95':[b.get('peakGrfLF95')],
                    'peakGrfLFStd':[b.get('peakGrfLFStd')],
                    'peakGrfRF5':[b.get('peakGrfRF5')],
                    'peakGrfRF':[peakGrfRF],
                    'peakGrfRF95':[b.get('peakGrfRF95')],
                    'peakGrfRFStd':[b.get('peakGrfRFStd')],
                    'percDiff2':[peakGRFPercDiffLFRF],
                    'percOptimal':[b.get('percOptimal')],
                    'control':[b.get('control')],
                    'hipControl':[b.get('hipControl')],
                    'ankleControl':[b.get('ankleControl')],
                    'controlLF':[b.get('controlLF')],
                    'controlRF':[b.get('controlRF')],
                    'symmetry':[b.get('symmetry')],
                    'hipSymmetry':[b.get('hipSymmetry')],
                    'ankleSymmetry':[b.get('ankleSymmetry')],
                    'totalGRF':[b.get('totalGRF')],
                    'totalGRFAvg':[b.get('totalGRFAvg')],
                    'optimalGRF':[b.get('optimalGRF')],
                    'irregularGRF':[b.get('irregularGRF')],
                    'LFgRF':[b.get('LFgRF')],
                    'RFgRF':[b.get('RFgRF')],
                    'leftGRF':[b.get('leftGRF')],
                    'rightGRF':[b.get('rightGRF')],
                    'singleLegGRF':[b.get('singleLegGRF')],
                    'percLeftGRF':[b.get('percLeftGRF')],
                    'percRightGRF':[b.get('percRightGRF')],
                    'percLRGRFDiff':[b.get('percLRGRFDiff')],          
                    'totalAccel':[b.get('totalAccel')],
                    'totalAccelAvg':[b.get('totalAccelAvg')],
                    'irregularAccel':[b.get('irregularAccel')]                          
                    }) 
   
            if cnt==0:
                ab.to_csv(output_path+'ab-'+user+'_'+eventDate+'.csv',sep=',',columns=['userId',
                    'eventDate',
                    'activeBlock',
                    'abNum',
                    'timeStart',
                    'timeEnd',
                    'cumulative_end_time',
                    'cumulative_start_time',
                    'duration',
                    'load',
                    'contactDurationLF5',
                    'contactDurationLF',
                    'contactDurationLF95',
                    'contactDurationLFStd',
                    'contactDurationRF5',
                    'contactDurationRF',
                    'contactDurationRF95',
                    'contactDurationRFStd',
                    'percDiff1',
                    'peakGrfLF5',
                    'peakGrfLF',
                    'peakGrfLF95',
                    'peakGrfLFStd',
                    'peakGrfRF5',
                    'peakGrfRF',
                    'peakGrfRF95',
                    'peakGrfRFStd',
                    'percDiff2',
                    'percOptimal',
                    'control',
                    'hipControl',
                    'ankleControl',
                    'controlLF',
                    'controlRF',
                    'symmetry',
                    'hipSymmetry',
                    'ankleSymmetry',
                    'totalGRF',
                    'totalGRFAvg',
                    'optimalGRF',
                    'irregularGRF',
                    'LFgRF',
                    'RFgRF',
                    'leftGRF',
                    'rightGRF',
                    'singleLegGRF',
                    'percLeftGRF',
                    'percRightGRF',
                    'percLRGRFDiff',          
                    'totalAccel',
                    'totalAccelAvg',
                    'irregularAccel'
                    ])   
            else:
                ab.to_csv(output_path+'ab-'+user+'_'+eventDate+'.csv',sep=',',mode='a',header=False,columns=['userId',
                    'eventDate',
                    'activeBlock',
                    'abNum',
                    'timeStart',
                    'timeEnd',
                    'cumulative_end_time',
                    'cumulative_start_time',
                    'duration',
                    'load',
                    'contactDurationLF5',
                    'contactDurationLF',
                    'contactDurationLF95',
                    'contactDurationLFStd',
                    'contactDurationRF5',
                    'contactDurationRF',
                    'contactDurationRF95',
                    'contactDurationRFStd',
                    'percDiff1',
                    'peakGrfLF5',
                    'peakGrfLF',
                    'peakGrfLF95',
                    'peakGrfLFStd',
                    'peakGrfRF5',
                    'peakGrfRF',
                    'peakGrfRF95',
                    'peakGrfRFStd',
                    'percDiff2',
                    'percOptimal',
                    'control',
                    'hipControl',
                    'ankleControl',
                    'controlLF',
                    'controlRF',
                    'symmetry',
                    'hipSymmetry',
                    'ankleSymmetry',
                    'totalGRF',
                    'totalGRFAvg',
                    'optimalGRF',
                    'irregularGRF',
                    'LFgRF',
                    'RFgRF',
                    'leftGRF',
                    'rightGRF',
                    'singleLegGRF',
                    'percLeftGRF',
                    'percRightGRF',
                    'percLRGRFDiff',          
                    'totalAccel',
                    'totalAccelAvg',
                    'irregularAccel'])
            cnt=cnt+1

def get_initialized_data_frame(variable):
    cross_tab = pandas.DataFrame()     
    cross_tab.at[variable.name,"Red:GRF"] = 0
    cross_tab.at[variable.name,"Red:CMA"] = 0
    cross_tab.at[variable.name,"Red:Time"] = 0
    cross_tab.at[variable.name,"Yellow:GRF"] = 0
    cross_tab.at[variable.name,"Yellow:CMA"] = 0
    cross_tab.at[variable.name,"Yellow:Time"] = 0
    cross_tab.at[variable.name,"Green:GRF"] = 0
    cross_tab.at[variable.name,"Green:CMA"] = 0
    cross_tab.at[variable.name,"Green:Time"] = 0
    cross_tab.at[variable.name,"Total:GRF"] = 0
    cross_tab.at[variable.name,"Total:CMA"] = 0
    cross_tab.at[variable.name,"Total:Time"] = 0
    cross_tab.at[variable.name,"Total:SessionTime"] = 0
    return cross_tab

def get_initialized_intensity_frame(variable):
    cross_tab = pandas.DataFrame()     
    cross_tab.at[variable,"Low"] = 0
    cross_tab.at[variable,"Med"] = 0
    cross_tab.at[variable,"High"] = 0
    cross_tab.at[variable,"Total"] = 0
    return cross_tab

def create_precentage_data_frame(variable_matrix, variable_list):
    percentage_matrix = pandas.DataFrame()
    for variable in variable_list:
        variable_frame = get_initialized_data_frame(variable)
        percentage_matrix = percentage_matrix.append(variable_frame)
        percentage_matrix.at[variable.name,"Red:GRF"] = (variable_matrix.at[variable.name,"Red:GRF"]/variable_matrix.at[variable.name,"Total:GRF"])*100
        percentage_matrix.at[variable.name,"Red:CMA"] = (variable_matrix.at[variable.name,"Red:CMA"]/variable_matrix.at[variable.name,"Total:CMA"])*100
        percentage_matrix.at[variable.name,"Red:Time"] = (variable_matrix.at[variable.name,"Red:Time"]/variable_matrix.at[variable.name,"Total:Time"])*100
        percentage_matrix.at[variable.name,"Yellow:GRF"] = (variable_matrix.at[variable.name,"Yellow:GRF"]/variable_matrix.at[variable.name,"Total:GRF"])*100
        percentage_matrix.at[variable.name,"Yellow:CMA"] = (variable_matrix.at[variable.name,"Yellow:CMA"]/variable_matrix.at[variable.name,"Total:CMA"])*100
        percentage_matrix.at[variable.name,"Yellow:Time"] = (variable_matrix.at[variable.name,"Yellow:Time"]/variable_matrix.at[variable.name,"Total:Time"])*100
        percentage_matrix.at[variable.name,"Green:GRF"] = (variable_matrix.at[variable.name,"Green:GRF"]/variable_matrix.at[variable.name,"Total:GRF"])*100
        percentage_matrix.at[variable.name,"Green:CMA"] = (variable_matrix.at[variable.name,"Green:CMA"]/variable_matrix.at[variable.name,"Total:CMA"])*100
        percentage_matrix.at[variable.name,"Green:Time"] = (variable_matrix.at[variable.name,"Green:Time"]/variable_matrix.at[variable.name,"Total:Time"])*100
        percentage_matrix.at[variable.name,"Total:GRF"] = variable_matrix.at[variable.name,"Total:GRF"]
        percentage_matrix.at[variable.name,"Total:CMA"] = variable_matrix.at[variable.name,"Total:CMA"]
        percentage_matrix.at[variable.name,"Total:Time"] = variable_matrix.at[variable.name,"Total:Time"]
        percentage_matrix.at[variable.name,"Total:SessionTime"] = variable_matrix.at[variable.name,"Total:SessionTime"]

    return percentage_matrix
    

def create_intensity_matrix(user, date):
    mongo_unit_blocks = get_unit_blocks(user, date)
    intensity_frame = pandas.DataFrame()

    if (len(mongo_unit_blocks) > 0):

        low_intensity_time = 0
        med_intensity_time = 0
        high_intensity_time = 0
        total_duration = 0


        if_seconds = get_initialized_intensity_frame("Seconds")
        if_percent = get_initialized_intensity_frame("Seconds %")
        intensity_frame = intensity_frame.append(if_seconds)
        intensity_frame = intensity_frame.append(if_percent)

        for ub in mongo_unit_blocks:
            if len(ub) > 0:

                unit_bock_count = len(ub.get('unitBlocks'))

                for n in range(0, unit_bock_count):
                    ubData = ub.get('unitBlocks')[n]
                    ub_rec = UnitBlock(ubData)
                    timeStart = ub.get('unitBlocks')[n].get('timeStart')
                    timeEnd = ub.get('unitBlocks')[n].get('timeEnd')
                    try:
                        timeStart_object = datetime.strptime(timeStart, '%Y-%m-%d %H:%M:%S.%f')
                    except ValueError:
                        timeStart_object = datetime.strptime(timeStart, '%Y-%m-%d %H:%M:%S')
                    try:
                        timeEnd_object = datetime.strptime(timeEnd, '%Y-%m-%d %H:%M:%S.%f')
                    except ValueError:
                        timeEnd_object = datetime.strptime(timeEnd, '%Y-%m-%d %H:%M:%S')

                    total_duration += ub_rec.duration
                    if (ub_rec.total_accel_avg < 45):
                        low_intensity_time += (timeEnd_object - timeStart_object).seconds
                    elif (ub_rec.total_accel_avg >= 45 and ub_rec.total_accel_avg < 105):
                        med_intensity_time += (timeEnd_object - timeStart_object).seconds
                    else:
                        high_intensity_time += (timeEnd_object - timeStart_object).seconds

        intensity_frame.at["Seconds", "Low"] += low_intensity_time
        intensity_frame.at["Seconds", "Med"] += med_intensity_time
        intensity_frame.at["Seconds", "High"] += high_intensity_time
        intensity_frame.at["Seconds", "Total"] += total_duration
        intensity_frame.at["Seconds %", "Low"] += (low_intensity_time / total_duration) * 100
        intensity_frame.at["Seconds %", "Med"] += (med_intensity_time / total_duration) * 100
        intensity_frame.at["Seconds %", "High"] += (high_intensity_time / total_duration) * 100
        intensity_frame.at["Seconds %", "Total"] += (total_duration / total_duration) * 100

    return intensity_frame


def create_variable_matrix(user, date, variable_list):
    mongo_unit_blocks = get_unit_blocks(user, date)
    variable_matrix = pandas.DataFrame()

    if (len(mongo_unit_blocks) > 0):

        for variable in variable_list:
            variable_frame = get_initialized_data_frame(variable)

            variable_matrix = variable_matrix.append(variable_frame)

        sessionTimeStart = mongo_unit_blocks[0].get('unitBlocks')[0].get('timeStart')
        try:
            sessionTimeStart_object = datetime.strptime(sessionTimeStart, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            sessionTimeStart_object = datetime.strptime(sessionTimeStart, '%Y-%m-%d %H:%M:%S')

        for ub in mongo_unit_blocks:
            if len(ub) > 0:

                unit_bock_count = len(ub.get('unitBlocks'))

                for n in range(0, unit_bock_count):
                    ubData = ub.get('unitBlocks')[n]
                    ub_rec = UnitBlock(ubData)

                    timeEnd = ub.get('unitBlocks')[n].get('timeEnd')

                    try:
                        timeEnd_object = datetime.strptime(timeEnd, '%Y-%m-%d %H:%M:%S.%f')
                    except ValueError:
                        timeEnd_object = datetime.strptime(timeEnd, '%Y-%m-%d %H:%M:%S')

                    cumulative_end_time = (timeEnd_object - sessionTimeStart_object).seconds

                    for cat_variable in variable_list:
                        variable_matrix = tally_cross_tab(variable_matrix, cat_variable, ub_rec, cumulative_end_time)

    return variable_matrix


def create_percentage_matrix(user, date, variable_list):
    mongo_unit_blocks = get_unit_blocks(user, date)
    percentage_matrix = pandas.DataFrame()
    if (len(mongo_unit_blocks) > 0):
        variable_matrix = pandas.DataFrame()

        for variable in variable_list:
            variable_frame = get_initialized_data_frame(variable)

            variable_matrix = variable_matrix.append(variable_frame)

        sessionTimeStart = mongo_unit_blocks[0].get('unitBlocks')[0].get('timeStart')
        try:
            sessionTimeStart_object = datetime.strptime(sessionTimeStart, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            sessionTimeStart_object = datetime.strptime(sessionTimeStart, '%Y-%m-%d %H:%M:%S')

        for ub in mongo_unit_blocks:
            if len(ub) > 0:

                unit_bock_count = len(ub.get('unitBlocks'))

                for n in range(0, unit_bock_count):
                    ubData = ub.get('unitBlocks')[n]
                    ub_rec = UnitBlock(ubData)

                    timeEnd = ub.get('unitBlocks')[n].get('timeEnd')

                    try:
                        timeEnd_object = datetime.strptime(timeEnd, '%Y-%m-%d %H:%M:%S.%f')
                    except ValueError:
                        timeEnd_object = datetime.strptime(timeEnd, '%Y-%m-%d %H:%M:%S')

                    cumulative_end_time = (timeEnd_object - sessionTimeStart_object).seconds

                    for cat_variable in variable_list:
                        variable_matrix = tally_cross_tab(variable_matrix, cat_variable, ub_rec, cumulative_end_time)

        percentage_matrix = create_precentage_data_frame(variable_matrix, variable_list)

    return percentage_matrix


def categorize_unit_blocks(collection, user, date, variable_list):
    mongo_unit_blocks = mongodb.get_unit_blocks(collection, user, date)
    if(len(mongo_unit_blocks)>0):
        variable_matrix = pandas.DataFrame()
    
        low_intensity_time = 0
        med_intensity_time = 0
        high_intensity_time = 0
        total_duration = 0

        for variable in variable_list:
            variable_frame = get_initialized_data_frame(variable)
        
            variable_matrix = variable_matrix.append(variable_frame)
    
        intensity_frame = pandas.DataFrame()
        if_seconds = get_initialized_intensity_frame("Seconds")
        if_percent = get_initialized_intensity_frame("Seconds %")
        intensity_frame = intensity_frame.append(if_seconds)
        intensity_frame = intensity_frame.append(if_percent)

        sessionTimeStart = mongo_unit_blocks[0].get('unitBlocks')[0].get('timeStart')
        try:
            sessionTimeStart_object = datetime.strptime(sessionTimeStart, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            sessionTimeStart_object = datetime.strptime(sessionTimeStart, '%Y-%m-%d %H:%M:%S')

        for ub in mongo_unit_blocks:
            if len(ub)>0:
               
                    unit_bock_count = len(ub.get('unitBlocks'))
               
                    for n in range(0,unit_bock_count):
                        ubData = ub.get('unitBlocks')[n]
                        ub_rec = UnitBlock(ubData)
                        timeStart = ub.get('unitBlocks')[n].get('timeStart')
                        timeEnd = ub.get('unitBlocks')[n].get('timeEnd')
                        try:
                            timeStart_object = datetime.strptime(timeStart, '%Y-%m-%d %H:%M:%S.%f')
                        except ValueError:
                            timeStart_object = datetime.strptime(timeStart, '%Y-%m-%d %H:%M:%S')
                        try:
                            timeEnd_object = datetime.strptime(timeEnd, '%Y-%m-%d %H:%M:%S.%f')
                        except ValueError:
                            timeEnd_object = datetime.strptime(timeEnd, '%Y-%m-%d %H:%M:%S')
                        timeStart_string = timeStart_object.time().strftime("%H:%M:%S")
                        timeEnd_string = timeEnd_object.time().strftime("%H:%M:%S")
                        cumulative_start_time = (timeStart_object- sessionTimeStart_object).seconds
                        cumulative_end_time = (timeEnd_object- sessionTimeStart_object).seconds
                        total_duration += ub_rec.duration
                        if(ub_rec.total_accel_avg<45):
                            low_intensity_time += (timeEnd_object- timeStart_object).seconds
                        elif(ub_rec.total_accel_avg>=45 and ub_rec.total_accel_avg<105):
                            med_intensity_time += (timeEnd_object- timeStart_object).seconds
                        else:
                            high_intensity_time += (timeEnd_object- timeStart_object).seconds

                        for cat_variable in variable_list:
                            variable_matrix = tally_cross_tab(variable_matrix, cat_variable, ub_rec,cumulative_end_time)
    
        intensity_frame.at["Seconds","Low"] += low_intensity_time
        intensity_frame.at["Seconds","Med"] += med_intensity_time
        intensity_frame.at["Seconds","High"] += high_intensity_time
        intensity_frame.at["Seconds","Total"] += total_duration
        intensity_frame.at["Seconds %","Low"] += (low_intensity_time/total_duration)*100
        intensity_frame.at["Seconds %","Med"] += (med_intensity_time/total_duration)*100
        intensity_frame.at["Seconds %","High"] += (high_intensity_time/total_duration)*100
        intensity_frame.at["Seconds %","Total"] += (total_duration/total_duration)*100
        percentage_matrix = create_precentage_data_frame(variable_matrix, variable_list)
        intensity_frame.to_csv('C:\\UNC\\v6\\intensity_matrix_'+user+'_'+date+'v6.csv',sep=',',index_label='variable')
        variable_matrix.to_csv('C:\\UNC\\v6\\var_matrix_'+user+'_'+date+'v6.csv',sep=',',index_label='variable')
        percentage_matrix.to_csv('C:\\UNC\\v6\\perc_matrix_'+user+'_'+date+'v6.csv',sep=',',index_label='variable')

                   
def tally_cross_tab(cross_tab, cat_variable, unit_block_data, total_session_time):
    variable_value = getattr(unit_block_data,cat_variable.name)
    if(variable_value is not None):
        if(cat_variable.invereted==False):
            if(variable_value > cat_variable.yellow_high):
                cross_tab.at[cat_variable.name,"Red:Time"] += unit_block_data.duration
                cross_tab.at[cat_variable.name,"Red:GRF"] += unit_block_data.total_grf
                cross_tab.at[cat_variable.name,"Red:CMA"] += unit_block_data.total_accel
            if(variable_value > cat_variable.green_high and variable_value <=cat_variable.yellow_high):
                cross_tab.at[cat_variable.name,"Yellow:Time"] += unit_block_data.duration
                cross_tab.at[cat_variable.name,"Yellow:GRF"] += unit_block_data.total_grf
                cross_tab.at[cat_variable.name,"Yellow:CMA"] += unit_block_data.total_accel
            if(variable_value >= cat_variable.green_low and variable_value <= cat_variable.green_high):
                cross_tab.at[cat_variable.name,"Green:Time"] += unit_block_data.duration
                cross_tab.at[cat_variable.name,"Green:GRF"] += unit_block_data.total_grf
                cross_tab.at[cat_variable.name,"Green:CMA"] += unit_block_data.total_accel
        else:
            if(variable_value > cat_variable.yellow_high):
                cross_tab.at[cat_variable.name,"Green:Time"] += unit_block_data.duration
                cross_tab.at[cat_variable.name,"Green:GRF"] += unit_block_data.total_grf
                cross_tab.at[cat_variable.name,"Green:CMA"] += unit_block_data.total_accel
            if(variable_value > cat_variable.red_high and variable_value <=cat_variable.yellow_high):
                cross_tab.at[cat_variable.name,"Yellow:Time"] += unit_block_data.duration
                cross_tab.at[cat_variable.name,"Yellow:GRF"] += unit_block_data.total_grf
                cross_tab.at[cat_variable.name,"Yellow:CMA"] += unit_block_data.total_accel
            if(variable_value >= cat_variable.red_low and variable_value <= cat_variable.red_high):
                cross_tab.at[cat_variable.name,"Red:Time"] += unit_block_data.duration
                cross_tab.at[cat_variable.name,"Red:GRF"] += unit_block_data.total_grf
                cross_tab.at[cat_variable.name,"Red:CMA"] += unit_block_data.total_accel
    
    cross_tab.at[cat_variable.name,"Total:Time"] += unit_block_data.duration
    cross_tab.at[cat_variable.name,"Total:GRF"] += unit_block_data.total_grf
    cross_tab.at[cat_variable.name,"Total:CMA"] += unit_block_data.total_accel
    cross_tab.at[cat_variable.name,"Total:SessionTime"] = total_session_time #not additive

    return cross_tab


def query_mongo_ub(collection, user, date, output_path):
    client = MongoClient('34.210.169.8',username='statsAdmin',password='ButThisGoes211',authSource='admin', authMechanism='SCRAM-SHA-1')
    db = client.get_database('movementStats')
    col = db.get_collection(collection)
    #users = list(col.distinct("userId"))
    #for u in users:
    cnt = 0
    bcnt=0
    curDate = ''
    userdocs = list(col.aggregate([
                                    {'$match':{'userId':user, 'eventDate':date}},
                                    {'$project':
                                    {'_id':1, 
                                        'eventDate':1,
                                        'timeStart':1,
                                        'numberOfUnitBlocks':{'$size':'$unitBlocks'}
                                        }}]))
    if(len(userdocs)>0):
        sessionTimeStart = userdocs[0].get('timeStart')
        try:
            sessionTimeStart_object = datetime.strptime(sessionTimeStart, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            sessionTimeStart_object = datetime.strptime(sessionTimeStart, '%Y-%m-%d %H:%M:%S')

        for b in userdocs:
            
            objId =  str(b.get('_id'))
            if(curDate!=b.get('eventDate')):
                curDate = b.get('eventDate')
                cnt = 0
                bcnt=0
                sessionTimeStart = b.get('timeStart')
                try:
                    sessionTimeStart_object = datetime.strptime(sessionTimeStart, '%Y-%m-%d %H:%M:%S.%f')
                except ValueError:
                    sessionTimeStart_object = datetime.strptime(sessionTimeStart, '%Y-%m-%d %H:%M:%S')
            eventDate = b.get('eventDate')
            numUnitBlocks = b.get('numberOfUnitBlocks')
           
            
            unitBlocks = list(col.find({'userId': {'$eq': user},
                                        '_id':ObjectId(objId)},
                                        {'unitBlocks':1,
                                        '_id':0}))
            
            
          
            if len(unitBlocks)>0:
                bcnt=bcnt+1 
                unitBlockCount = len(unitBlocks[0].get('unitBlocks'))
             
                for n in range(0,unitBlockCount):
                    ubData = unitBlocks[0].get('unitBlocks')[n]
                    timeStart = unitBlocks[0].get('unitBlocks')[n].get('timeStart')
                    timeEnd = unitBlocks[0].get('unitBlocks')[n].get('timeEnd')
                    try:
                        timeStart_object = datetime.strptime(timeStart, '%Y-%m-%d %H:%M:%S.%f')
                    except ValueError:
                        timeStart_object = datetime.strptime(timeStart, '%Y-%m-%d %H:%M:%S')
                    try:
                        timeEnd_object = datetime.strptime(timeEnd, '%Y-%m-%d %H:%M:%S.%f')
                    except ValueError:
                        timeEnd_object = datetime.strptime(timeEnd, '%Y-%m-%d %H:%M:%S')
                    timeStart_string = timeStart_object.time().strftime("%H:%M:%S")
                    timeEnd_string = timeEnd_object.time().strftime("%H:%M:%S")
                    cumulative_start_time = (timeStart_object- sessionTimeStart_object).seconds
                    cumulative_end_time = (timeEnd_object- sessionTimeStart_object).seconds
                    contactDurationLF = ubData.get('contactDurationLF')
                    contactDurationRF = ubData.get('contactDurationRF')
                    peakGrfLF = ubData.get('peakGrfLF')
                    peakGrfRF = ubData.get('peakGrfRF')
                    contactDurationPercDiffLFRF = None
                    if(contactDurationLF!=None and contactDurationRF != None):
                        contactDurationPercDiffLFRF = abs(contactDurationLF-contactDurationRF)/max(contactDurationLF,contactDurationRF)
                    peakGRFPercDiffLFRF = None
                    if(peakGrfLF!=None and peakGrfRF != None):
                        peakGRFPercDiffLFRF = abs(peakGrfLF-peakGrfRF)/max(peakGrfLF,peakGrfRF)
                        
                    #ub = pandas.DataFrame(json_normalize(unitBlocks[0].get('unitBlocks')[n]))
                    ab = pandas.DataFrame(
                        {
                            'userId':[user],
                            'eventDate':[eventDate],
                            'activeBlock':[objId],
                            'abNum':[bcnt],
                            'timeStart': [timeStart_string],
                            'timeEnd':[timeEnd_string],
                            'cumulative_end_time':[cumulative_end_time],
                            'cumulative_start_time':[cumulative_start_time],
                            'duration':[ubData.get('duration')],
                            'load':[ubData.get('totalAccelAvg')],
                            'contactDurationLF5':[ubData.get('contactDurationLF5')],
                            'contactDurationLF':[contactDurationLF],
                            'contactDurationLF95':[ubData.get('contactDurationLF95')],
                            'contactDurationLFStd':[ubData.get('contactDurationLFStd')],
                            'contactDurationRF5':[ubData.get('contactDurationRF5')],
                            'contactDurationRF':[contactDurationRF],
                            'contactDurationRF95':[ubData.get('contactDurationRF95')],
                            'contactDurationRFStd':[ubData.get('contactDurationRFStd')],
                            'percDiff1':[contactDurationPercDiffLFRF],
                            'peakGrfLF5':[ubData.get('peakGrfLF5')],
                            'peakGrfLF':[peakGrfLF],
                            'peakGrfLF95':[ubData.get('peakGrfLF95')],
                            'peakGrfLFStd':[ubData.get('peakGrfLFStd')],
                            'peakGrfRF5':[ubData.get('peakGrfRF5')],
                            'peakGrfRF':[peakGrfRF],
                            'peakGrfRF95':[ubData.get('peakGrfRF95')],
                            'peakGrfRFStd':[ubData.get('peakGrfRFStd')],
                            'percDiff2':[peakGRFPercDiffLFRF],
                            'percOptimal':[ubData.get('percOptimal')],
                            'control':[ubData.get('control')],
                            'hipControl':[ubData.get('hipControl')],
                            'ankleControl':[ubData.get('ankleControl')],
                            'controlLF':[ubData.get('controlLF')],
                            'controlRF':[ubData.get('controlRF')],
                            'symmetry':[ubData.get('symmetry')],
                            'hipSymmetry':[ubData.get('hipSymmetry')],
                            'ankleSymmetry':[ubData.get('ankleSymmetry')],
                            'totalGRF':[ubData.get('totalGRF')],
                            'totalGRFAvg':[ubData.get('totalGRFAvg')],
                            'optimalGRF':[ubData.get('optimalGRF')],
                            'irregularGRF':[ubData.get('irregularGRF')],
                            'LFgRF':[ubData.get('LFgRF')],
                            'RFgRF':[ubData.get('RFgRF')],
                            'leftGRF':[ubData.get('leftGRF')],
                            'rightGRF':[ubData.get('rightGRF')],
                            'singleLegGRF':[ubData.get('singleLegGRF')],
                            'percLeftGRF':[ubData.get('percLeftGRF')],
                            'percRightGRF':[ubData.get('percRightGRF')],
                            'percLRGRFDiff':[ubData.get('percLRGRFDiff')],          
                            'totalAccel':[ubData.get('totalAccel')],
                            'totalAccelAvg':[ubData.get('totalAccelAvg')],
                            'irregularAccel':[ubData.get('irregularAccel')],
                            'peakGrfContactDurationLF5':[ubData.get('peakGrfContactDurationLF5')],
                            'peakGrfContactDurationLF':[ubData.get('peakGrfContactDurationLF')],
                            'peakGrfContactDurationLF95':[ubData.get('peakGrfContactDurationLF95')],
                            'peakGrfContactDurationLFStd':[ubData.get('peakGrfContactDurationLFStd')],
                            'peakGrfContactDurationRF5':[ubData.get('peakGrfContactDurationRF5')],
                            'peakGrfContactDurationRF':[ubData.get('peakGrfContactDurationRF')],
                            'peakGrfContactDurationRF95':[ubData.get('peakGrfContactDurationRF95')],
                            'peakGrfContactDurationRFStd':[ubData.get('peakGrfContactDurationRFStd')],
                            }) 
                    #nb = ub.join(ab)
                    if cnt==0:
                        ab.to_csv(output_path+user+'_'+eventDate+'.csv',sep=',',columns=['userId',
                            'eventDate',
                            'activeBlock',
                            'abNum',
                            'timeStart',
                            'timeEnd',
                            'cumulative_end_time',
                            'cumulative_start_time',
                            'duration',
                            'load',
                            'contactDurationLF5',
                            'contactDurationLF',
                            'contactDurationLF95',
                            'contactDurationLFStd',
                            'contactDurationRF5',
                            'contactDurationRF',
                            'contactDurationRF95',
                            'contactDurationRFStd',
                            'percDiff1',
                            'peakGrfLF5',
                            'peakGrfLF',
                            'peakGrfLF95',
                            'peakGrfLFStd',
                            'peakGrfRF5',
                            'peakGrfRF',
                            'peakGrfRF95',
                            'peakGrfRFStd',
                            'percDiff2',
                            'percOptimal',
                            'control',
                            'hipControl',
                            'ankleControl',
                            'controlLF',
                            'controlRF',
                            'symmetry',
                            'hipSymmetry',
                            'ankleSymmetry',
                            'totalGRF',
                            'totalGRFAvg',
                            'optimalGRF',
                            'irregularGRF',
                            'LFgRF',
                            'RFgRF',
                            'leftGRF',
                            'rightGRF',
                            'singleLegGRF',
                            'percLeftGRF',
                            'percRightGRF',
                            'percLRGRFDiff',          
                            'totalAccel',
                            'totalAccelAvg',
                            'irregularAccel',
                            'peakGrfContactDurationLF',
                            'peakGrfContactDurationLF5',
                            'peakGrfContactDurationLF95',
                            'peakGrfContactDurationLFStd',
                            'peakGrfContactDurationRF',
                            'peakGrfContactDurationRF5',
                            'peakGrfContactDurationRF95',
                            'peakGrfContactDurationRFStd',
                            ])   
                    else:
                        ab.to_csv(output_path+user+'_'+eventDate+'.csv',sep=',',mode='a',header=False,columns=['userId',
                            'eventDate',
                            'activeBlock',
                            'abNum',
                            'timeStart',
                            'timeEnd',
                            'cumulative_end_time',
                            'cumulative_start_time',
                            'duration',
                            'load',
                            'contactDurationLF5',
                            'contactDurationLF',
                            'contactDurationLF95',
                            'contactDurationLFStd',
                            'contactDurationRF5',
                            'contactDurationRF',
                            'contactDurationRF95',
                            'contactDurationRFStd',
                            'percDiff1',
                            'peakGrfLF5',
                            'peakGrfLF',
                            'peakGrfLF95',
                            'peakGrfLFStd',
                            'peakGrfRF5',
                            'peakGrfRF',
                            'peakGrfRF95',
                            'peakGrfRFStd',
                            'percDiff2',
                            'percOptimal',
                            'control',
                            'hipControl',
                            'ankleControl',
                            'controlLF',
                            'controlRF',
                            'symmetry',
                            'hipSymmetry',
                            'ankleSymmetry',
                            'totalGRF',
                            'totalGRFAvg',
                            'optimalGRF',
                            'irregularGRF',
                            'LFgRF',
                            'RFgRF',
                            'leftGRF',
                            'rightGRF',
                            'singleLegGRF',
                            'percLeftGRF',
                            'percRightGRF',
                            'percLRGRFDiff',          
                            'totalAccel',
                            'totalAccelAvg',
                            'irregularAccel',
                            'peakGrfContactDurationLF',
                            'peakGrfContactDurationLF5',
                            'peakGrfContactDurationLF95',
                            'peakGrfContactDurationLFStd',
                            'peakGrfContactDurationRF',
                            'peakGrfContactDurationRF5',
                            'peakGrfContactDurationRF95',
                            'peakGrfContactDurationRFStd'])
                    cnt=cnt+1
                       
            
def main():
    collection = "activeBlockStats_trials"
    date_list = ["2018-05-18"]
    user_list = ["Test"]
    for athlete in user_list:
        for date in date_list:
            var_list = []
            var_list.append(CategorizationVariable("peak_grf_perc_diff_lf",0,5,5,10,10,100, False))
            var_list.append(CategorizationVariable("peak_grf_perc_diff_rf",0,5,5,10,10,100, False))
            var_list.append(CategorizationVariable("gct_perc_diff_lf",0,5,5,10,10,100, False))
            var_list.append(CategorizationVariable("gct_perc_diff_rf",0,5,5,10,10,100, False))
            var_list.append(CategorizationVariable("peak_grf_gct_left_over",0,2.5,2.5,5,5,100, False))
            var_list.append(CategorizationVariable("peak_grf_gct_left_under",0,2.5,2.5,5,5,10, False))
            var_list.append(CategorizationVariable("peak_grf_gct_right_over",0,2.5,2.5,5,5,100, False))
            var_list.append(CategorizationVariable("peak_grf_gct_right_under",0,2.5,2.5,5,5,10, False))
            var_list.append(CategorizationVariable("hip_control",85,100,70,85,0,70, True))
            var_list.append(CategorizationVariable("control_lf",85,100,70,85,0,70, True))
            var_list.append(CategorizationVariable("control_rf",85,100,70,85,0,70, True))
            var_list.append(CategorizationVariable("symmetry",85,100,70,85,0,70, True))
            var_list.append(CategorizationVariable("hip_symmetry",85,100,70,85,0,70, True))
            var_list.append(CategorizationVariable("ankle_symmetry",85,100,70,85,0,70, True))
            categorize_unit_blocks(collection,athlete,date, var_list)
if __name__ == "__main__":
    main()