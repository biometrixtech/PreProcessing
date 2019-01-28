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


def query_mongo_ab(col, user, date, output_path):
    #client = MongoClient('34.210.169.8',username='statsAdmin',password='ButThisGoes211',authSource='admin', authMechanism='SCRAM-SHA-1')
    #db = client.get_database('movementStats')
    #col = db.get_collection(collection)
    #users = list(col.distinct("userId"))
    #for u in users:

    load_parameters([
        'MONGO_HOST',
        'MONGO_USER',
        'MONGO_PASSWORD',
        'MONGO_DATABASE',
        'MONGO_REPLICASET',
        'MONGO_COLLECTION_ACTIVEBLOCKS',
    ], 'mongo')

    #col = get_mongo_collection('ACTIVEBLOCKS')

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
                    'totalAccelAvg':[b.get('totalAccelAvg')],
                    #'contactDurationLF5':[b.get('contactDurationLF5')],
                    'contactDurationLF':[contactDurationLF],
                    #'contactDurationLF95':[b.get('contactDurationLF95')],
                    #'contactDurationLFStd':[b.get('contactDurationLFStd')],
                    #'contactDurationRF5':[b.get('contactDurationRF5')],
                    'contactDurationRF':[contactDurationRF],
                    #'contactDurationRF95':[b.get('contactDurationRF95')],
                    #'contactDurationRFStd':[b.get('contactDurationRFStd')],
                    'contactDurationPercDiffLFRF':[contactDurationPercDiffLFRF],
                    #'peakGrfLF5':[b.get('peakGrfLF5')],
                    'peakGrfLF':[peakGrfLF],
                    #'peakGrfLF95':[b.get('peakGrfLF95')],
                    #'peakGrfLFStd':[b.get('peakGrfLFStd')],
                    #'peakGrfRF5':[b.get('peakGrfRF5')],
                    'peakGrfRF':[peakGrfRF],
                    #'peakGrfRF95':[b.get('peakGrfRF95')],
                    #'peakGrfRFStd':[b.get('peakGrfRFStd')],
                    'peakGRFPercDiffLFRF':[peakGRFPercDiffLFRF],
                    'percOptimal':[b.get('percOptimal')],
                    #'control':[b.get('control')],
                    #'hipControl':[b.get('hipControl')],
                    #'ankleControl':[b.get('ankleControl')],
                    #'controlLF':[b.get('controlLF')],
                    #'controlRF':[b.get('controlRF')],
                    #'symmetry':[b.get('symmetry')],
                    #'hipSymmetry':[b.get('hipSymmetry')],
                    #'ankleSymmetry':[b.get('ankleSymmetry')],
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
                    #'totalAccelAvg':[b.get('totalAccelAvg')],
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
                    'totalAccelAvg',
                    #'contactDurationLF5',
                    'contactDurationLF',
                    #'contactDurationLF95',
                    #'contactDurationLFStd',
                    #'contactDurationRF5',
                    'contactDurationRF',
                    #'contactDurationRF95',
                    #'contactDurationRFStd',
                    'contactDurationPercDiffLFRF',
                    #'peakGrfLF5',
                    'peakGrfLF',
                    #'peakGrfLF95',
                    #'peakGrfLFStd',
                    #'peakGrfRF5',
                    'peakGrfRF',
                    #'peakGrfRF95',
                    #'peakGrfRFStd',
                    'peakGRFPercDiffLFRF',
                    'percOptimal',
                    #'control',
                    #'hipControl',
                    #'ankleControl',
                    #'controlLF',
                    #'controlRF',
                    #'symmetry',
                    #'hipSymmetry',
                    #'ankleSymmetry',
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
                    #'totalAccelAvg',
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
                    'totalAccelAvg',
                    #'contactDurationLF5',
                    'contactDurationLF',
                    #'contactDurationLF95',
                    #'contactDurationLFStd',
                    #'contactDurationRF5',
                    'contactDurationRF',
                    #'contactDurationRF95',
                    #'contactDurationRFStd',
                    'contactDurationPercDiffLFRF',
                    #'peakGrfLF5',
                    'peakGrfLF',
                    #'peakGrfLF95',
                    #'peakGrfLFStd',
                    #'peakGrfRF5',
                    'peakGrfRF',
                    #'peakGrfRF95',
                    #'peakGrfRFStd',
                    'peakGRFPercDiffLFRF',
                    'percOptimal',
                    #'control',
                    #'hipControl',
                    #'ankleControl',
                    #'controlLF',
                    #'controlRF',
                    #'symmetry',
                    #'hipSymmetry',
                    #'ankleSymmetry',
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
                    #'totalAccelAvg',
                    'irregularAccel'])
            cnt=cnt+1


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
            # categorize_unit_blocks(collection,athlete,date, var_list)
if __name__ == "__main__":
    main()